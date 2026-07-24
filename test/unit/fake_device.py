"""
Offline device simulator for SmartUSBHub loopback tests.

``FakeHubDevice`` emulates the MCU at the wire level: it parses the V1/V2/V3
frames the SDK writes and produces protocol-correct reply frames. ``FakeHubSerial``
is a minimal ``serial.Serial`` stand-in backed by the simulator.

``make_live_hub`` wires a real :class:`SmartUSBHub` instance to the simulator,
reusing the SDK's own ``__init__`` (ack events, frame-handler table, receive
thread) so the full send -> encode -> rx-loop -> parse -> dispatch -> handler ->
ACK path is exercised without any hardware.
"""
import threading

import smartusbhub as m
from smartusbhub import SmartUSBHub


def cal_crc16(data):
    """CRC16 matching ``SmartUSBHub._cal_crc16`` (poly 0x8005, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8005 if crc & 0x0001 else crc >> 1
    return crc & 0xFFFF


def frame_v1(cmd, channel, value):
    """Build a 6-byte V1 frame."""
    return bytes([0x55, 0x5A, cmd, channel, value, (cmd + channel + value) & 0xFF])


def frame_v2(cmd, channel, value0, value1):
    """Build a 7-byte V2 frame (two payload bytes)."""
    checksum = (cmd + channel + value0 + value1) & 0xFF
    return bytes([0x55, 0x5A, cmd, channel, value0, value1, checksum])


def frame_v3(cmd, payload=b"", flags=0):
    """Build a variable-length V3 frame with a valid CRC16."""
    payload = bytes(payload)
    frame = bytearray([
        0x55, 0xAB, 0xCD, 0xEF,
        cmd & 0xFF,
        flags & 0xFF,
        len(payload) & 0xFF,
        (len(payload) >> 8) & 0xFF,
        0x00, 0x00,
    ]) + payload
    crc = cal_crc16(frame)
    frame[8] = crc & 0xFF
    frame[9] = (crc >> 8) & 0xFF
    return bytes(frame)


def _channels_from_mask(mask):
    channels, ch = [], 1
    while mask:
        if mask & 1:
            channels.append(ch)
        mask >>= 1
        ch += 1
    return channels


class FakeHubDevice:
    """Stateful wire-level simulator for a Smart USB Hub."""

    def __init__(self, product_type=0x03, max_channels=7, firmware_major=2):
        self.product_type = product_type
        self.max_channels = max_channels
        self.firmware_major = firmware_major
        self.firmware_version = 7
        self.hardware_version = 1
        self.operate_mode = 0
        self.button_control = 1
        self.auto_restore = 0
        self.address = 0x0000
        n = max_channels
        self.power = {ch: 0 for ch in range(1, n + 1)}
        self.dataline = {ch: 0 for ch in range(1, n + 1)}
        self.voltage = {ch: 0 for ch in range(1, n + 1)}
        self.current = {ch: 0 for ch in range(1, n + 1)}
        self.default_power = {ch: (0, 0) for ch in range(1, n + 1)}
        self.default_dataline = {ch: (0, 0) for ch in range(1, n + 1)}
        self.oc_active_mask = 0
        self.oc_latch_mask = 0
        # Diagnostics for assertions.
        self.received_packets = []
        self.command_counts = {}

    # -- helpers -----------------------------------------------------------
    def _per_channel(self, mask, value_of):
        """One reply frame per channel in ``mask`` (single-bit channel field)."""
        out = bytearray()
        for ch in _channels_from_mask(mask):
            out += value_of(ch)
        return bytes(out)

    # -- main entry --------------------------------------------------------
    def respond(self, packet):
        """Parse a host request frame and return the device reply bytes."""
        self.received_packets.append(bytes(packet))

        if len(packet) >= 4 and packet[0] == 0x55 and packet[1] == 0xAB:
            return self._respond_v3(packet)
        if len(packet) < 6 or packet[0] != 0x55 or packet[1] != 0x5A:
            return b""

        cmd = packet[2]
        mask = packet[3]
        data = list(packet[4:-1])  # payload after channel mask, minus checksum
        self.command_counts[cmd] = self.command_counts.get(cmd, 0) + 1
        return self._respond_v1v2(cmd, mask, data)

    def _respond_v1v2(self, cmd, mask, data):
        C = m
        d0 = data[0] if data else 0

        if cmd == C.CMD_SET_CHANNEL_POWER:
            for ch in _channels_from_mask(mask):
                self.power[ch] = d0
            return frame_v1(cmd, mask, d0)
        if cmd == C.CMD_GET_CHANNEL_POWER_STATUS:
            return self._per_channel(mask, lambda ch: frame_v1(cmd, 1 << (ch - 1), self.power[ch]))
        if cmd == C.CMD_SET_CHANNEL_POWER_INTERLOCK:
            if mask == 0:
                for ch in self.power:
                    self.power[ch] = 0
            else:
                for ch in _channels_from_mask(mask):
                    self.power[ch] = 1
            return frame_v1(cmd, mask, d0)
        if cmd == C.CMD_SET_CHANNEL_DATALINE:
            for ch in _channels_from_mask(mask):
                self.dataline[ch] = d0
            return frame_v1(cmd, mask, d0)
        if cmd == C.CMD_GET_CHANNEL_DATALINE_STATUS:
            return self._per_channel(mask, lambda ch: frame_v1(cmd, 1 << (ch - 1), self.dataline[ch]))
        if cmd == C.CMD_GET_CHANNEL_VOLTAGE:
            ch = _channels_from_mask(mask)[0]
            mv = self.voltage[ch]
            return frame_v2(cmd, mask, (mv >> 8) & 0xFF, mv & 0xFF)
        if cmd == C.CMD_GET_CHANNEL_CURRENT:
            ch = _channels_from_mask(mask)[0]
            ma = self.current[ch]
            return frame_v2(cmd, mask, (ma >> 8) & 0xFF, ma & 0xFF)
        if cmd == C.CMD_GET_CHANNEL_OC_STATUS:
            return frame_v1(cmd, self.oc_active_mask, self.oc_latch_mask)
        if cmd == C.CMD_CLEAR_CHANNEL_OC_LATCH:
            for ch in _channels_from_mask(mask):
                self.oc_latch_mask &= ~(1 << (ch - 1))
            return frame_v1(cmd, self.oc_active_mask, self.oc_latch_mask)
        if cmd == C.CMD_SET_DEFAULT_POWER_STATUS:
            enable, status = (data + [0, 0])[:2]
            for ch in _channels_from_mask(mask):
                self.default_power[ch] = (enable, status)
            return frame_v2(cmd, mask, enable, status)
        if cmd == C.CMD_GET_DEFAULT_POWER_STATUS:
            return self._per_channel(
                mask, lambda ch: frame_v2(cmd, 1 << (ch - 1), *self.default_power[ch]))
        if cmd == C.CMD_SET_DEFAULT_DATALINE_STATUS:
            enable, status = (data + [0, 0])[:2]
            for ch in _channels_from_mask(mask):
                self.default_dataline[ch] = (enable, status)
            return frame_v2(cmd, mask, enable, status)
        if cmd == C.CMD_GET_DEFAULT_DATALINE_STATUS:
            return self._per_channel(
                mask, lambda ch: frame_v2(cmd, 1 << (ch - 1), *self.default_dataline[ch]))
        if cmd == C.CMD_SET_OPERATE_MODE:
            self.operate_mode = d0
            return frame_v1(cmd, 0, d0)
        if cmd == C.CMD_GET_OPERATE_MODE:
            return frame_v1(cmd, 0, self.operate_mode)
        if cmd == C.CMD_SET_BUTTON_CONTROL:
            self.button_control = d0
            return frame_v1(cmd, 0, d0)
        if cmd == C.CMD_GET_BUTTON_CONTROL_STATUS:
            return frame_v1(cmd, 0, self.button_control)
        if cmd == C.CMD_SET_AUTO_RESTORE:
            self.auto_restore = d0
            return frame_v1(cmd, 0, d0)
        if cmd == C.CMD_GET_AUTO_RESTORE_STATUS:
            return frame_v1(cmd, 0, self.auto_restore)
        if cmd == C.CMD_SET_DEVICE_ADDRESS:
            self.address = (mask << 8) | d0  # mask carries the MSB
            return frame_v1(cmd, mask, d0)
        if cmd == C.CMD_GET_DEVICE_ADDRESS:
            return frame_v1(cmd, (self.address >> 8) & 0xFF, self.address & 0xFF)
        if cmd == C.CMD_REBOOT_MCU:
            return frame_v1(cmd, 0, 0)
        if cmd == C.CMD_FACTORY_RESET:
            return frame_v1(cmd, 0, 0)
        if cmd == C.CMD_GET_FIRMWARE_VERSION:
            major = 0 if self.firmware_major == 1 else self.firmware_major
            return frame_v1(cmd, major, self.firmware_version)
        if cmd == C.CMD_GET_HARDWARE_VERSION:
            return frame_v1(cmd, 0, self.hardware_version)
        if cmd == C.CMD_GET_PRODUCT_TYPE:
            return frame_v1(cmd, 0, self.product_type)
        if cmd == C.CMD_GET_MAX_CHANNELS:
            return frame_v1(cmd, 0, self.max_channels)
        if cmd == C.CMD_GET_SERIAL_NO:
            return frame_v1(cmd, 0, 0)
        return b""  # unknown command: stay silent

    def _respond_v3(self, packet):
        cmd = packet[4]
        flags = packet[5]
        data_len = packet[6] | (packet[7] << 8)
        payload = packet[m.V3_HEADER_LEN:m.V3_HEADER_LEN + data_len]
        if cmd != m.CMD_GET_CHANNEL_MEASUREMENTS:
            return b""
        channel_mask = payload[0] if payload else 0
        meas_flags = payload[1] if len(payload) > 1 else 0
        # Stream enable/disable requests are acknowledged with a normal frame.
        stream_notify = bool(meas_flags & m.V3_MEAS_FLAG_STREAM_ENABLE)
        reply_flags = m.V3_FLAG_STREAM if stream_notify else 0
        return self.build_measurement_frame(channel_mask, flags=reply_flags)

    def build_measurement_frame(self, channel_mask, period_ms=20, tick=0x11223344,
                                fresh_mask=None, valid_mask=None, flags=0):
        """Build a V3 measurement frame for the given channel mask."""
        channels = _channels_from_mask(channel_mask)
        if fresh_mask is None:
            fresh_mask = channel_mask
        if valid_mask is None:
            valid_mask = channel_mask
        payload = bytearray([
            channel_mask, fresh_mask, valid_mask, period_ms & 0xFF,
            tick & 0xFF, (tick >> 8) & 0xFF, (tick >> 16) & 0xFF, (tick >> 24) & 0xFF,
        ])
        for ch in channels:
            mv = self.voltage.get(ch, 0)
            ma = self.current.get(ch, 0)
            payload += bytes([mv & 0xFF, (mv >> 8) & 0xFF, ma & 0xFF, (ma >> 8) & 0xFF])
        return frame_v3(m.CMD_GET_CHANNEL_MEASUREMENTS, payload, flags=flags)


class FakeHubSerial:
    """Minimal ``serial.Serial`` replacement backed by a ``FakeHubDevice``."""

    def __init__(self, device, auto_respond=True):
        self.device = device
        self.auto_respond = auto_respond
        self.is_open = True
        self._rx = bytearray()
        self._lock = threading.Lock()
        self.written = []

    @property
    def in_waiting(self):
        with self._lock:
            return len(self._rx)

    def read(self, size=1):
        with self._lock:
            data = bytes(self._rx[:size])
            del self._rx[:size]
            return data

    def write(self, packet):
        packet = bytes(packet)
        self.written.append(packet)
        if self.auto_respond:
            reply = self.device.respond(packet)
            if reply:
                self.feed(reply)
        return len(packet)

    def feed(self, data):
        """Inject raw bytes into the receive buffer (unsolicited frames)."""
        with self._lock:
            self._rx.extend(data)

    def reset_input_buffer(self):
        with self._lock:
            self._rx.clear()

    def flush(self):
        pass

    def close(self):
        self.is_open = False


def make_live_hub(monkeypatch, device=None, product_type=0x03, max_channels=7,
                  auto_respond=True, com_timeout=0.3, real_device_info=False):
    """
    Construct a real ``SmartUSBHub`` wired to a ``FakeHubDevice``.

    Reuses the SDK's own ``__init__`` (and the real receive thread) so tests
    exercise the genuine send/parse/dispatch path. ``get_device_info`` is stubbed
    to skip the slow identity handshake; identity is taken from ``device``.

    :param real_device_info: If True, run the SDK's real identity handshake
        against the simulator instead of the fast stub.

    :returns: (hub, device, fake_serial)
    """
    if device is None:
        device = FakeHubDevice(product_type=product_type, max_channels=max_channels)
    fake = FakeHubSerial(device, auto_respond=auto_respond)

    monkeypatch.setattr(m.serial, "Serial", lambda *a, **k: fake)
    monkeypatch.setattr(SmartUSBHub, "_acquire_port_lock",
                        classmethod(lambda cls, port: True))
    monkeypatch.setattr(SmartUSBHub, "_release_port_lock",
                        classmethod(lambda cls, port: None))

    def fake_device_info(self):
        self.product_type = device.product_type
        self.max_channels = device.max_channels
        self.operate_mode = device.operate_mode
        self.firmware_version = device.firmware_version
        self.firmware_version_major = device.firmware_major
        self.firmware_version_minor = device.firmware_version
        self.hardware_version = device.hardware_version
        self.button_control_status = device.button_control
        self.auto_restore_status = device.auto_restore
        self.device_address = device.address
        self.serial_no = "N/A"
        return {}

    if not real_device_info:
        monkeypatch.setattr(SmartUSBHub, "get_device_info", fake_device_info)

    port = "/dev/cu.fake-loopback"
    SmartUSBHub._connected_ports.discard(port)
    hub = SmartUSBHub(port)
    hub.com_timeout = com_timeout
    hub._min_send_interval = 0
    hub._mcu_response_wait = 0
    hub._fake = fake
    hub._device = device
    return hub, device, fake
