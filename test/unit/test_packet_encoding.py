"""
Offline encoder tests: assert the exact bytes ``_send_packet`` and
``_send_v3_packet`` put on the wire (SOF, channel mask, payload, checksum/CRC).
"""
import threading

import pytest

import smartusbhub as m
from smartusbhub import (
    CMD_SET_CHANNEL_POWER,
    CMD_SET_DEVICE_ADDRESS,
    CMD_GET_CHANNEL_MEASUREMENTS,
    SmartUSBHub,
    V3_HEADER_LEN,
    V3_MAX_DATA_LEN,
)
from fake_device import cal_crc16


class RecordingSerial:
    def __init__(self):
        self.is_open = True
        self.written = []

    def write(self, packet):
        self.written.append(bytes(packet))
        return len(packet)


def make_encoder_hub():
    hub = object.__new__(SmartUSBHub)
    hub.ser = RecordingSerial()
    hub._send_lock = threading.Lock()
    hub._last_send_time = 0
    hub._min_send_interval = 0
    hub._mcu_response_wait = 0
    return hub


@pytest.mark.unit
def test_send_packet_builds_v1_frame_with_checksum():
    hub = make_encoder_hub()

    packet = hub._send_packet(CMD_SET_CHANNEL_POWER, (1, 3), 1)

    # mask for channels 1 and 3 == 0b101 == 0x05; payload = [mask, value]
    assert packet[:5] == bytes([0x55, 0x5A, CMD_SET_CHANNEL_POWER, 0x05, 0x01])
    checksum = (CMD_SET_CHANNEL_POWER + 0x05 + 0x01) & 0xFF
    assert packet[5] == checksum
    assert hub.ser.written[-1] == bytes(packet)


@pytest.mark.unit
def test_send_packet_defaults_to_single_zero_payload():
    hub = make_encoder_hub()

    packet = hub._send_packet(CMD_SET_CHANNEL_POWER, (2,))

    assert list(packet) == [0x55, 0x5A, CMD_SET_CHANNEL_POWER, 0x02, 0x00,
                            (CMD_SET_CHANNEL_POWER + 0x02 + 0x00) & 0xFF]


@pytest.mark.unit
def test_send_packet_none_channels_uses_zero_mask():
    hub = make_encoder_hub()

    packet = hub._send_packet(m.CMD_GET_OPERATE_MODE, None, None)

    assert packet[3] == 0x00  # channel mask


@pytest.mark.unit
def test_send_packet_device_address_passes_raw_mask():
    hub = make_encoder_hub()

    # set_device_address sends the MSB as the "channel" field, LSB as data.
    packet = hub._send_packet(CMD_SET_DEVICE_ADDRESS, 0x12, 0x34)

    assert packet[3] == 0x12
    assert packet[4] == 0x34
    assert packet[5] == (CMD_SET_DEVICE_ADDRESS + 0x12 + 0x34) & 0xFF


@pytest.mark.unit
def test_send_packet_list_payload_is_appended():
    hub = make_encoder_hub()

    packet = hub._send_packet(m.CMD_SET_DEFAULT_POWER_STATUS, (1,), [1, 0])

    # payload = [mask=0x01, enable=1, status=0]
    assert list(packet[3:6]) == [0x01, 0x01, 0x00]
    assert packet[6] == (m.CMD_SET_DEFAULT_POWER_STATUS + 0x01 + 0x01 + 0x00) & 0xFF


@pytest.mark.unit
def test_send_v3_packet_builds_valid_crc():
    hub = make_encoder_hub()

    payload = [0x7F, 0x02]
    packet = hub._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, payload)

    assert packet[:4] == bytes([0x55, 0xAB, 0xCD, 0xEF])
    assert packet[4] == CMD_GET_CHANNEL_MEASUREMENTS
    assert packet[6] | (packet[7] << 8) == len(payload)

    # CRC field is computed over the frame with the CRC bytes zeroed.
    crc_data = bytearray(packet)
    crc_data[8] = 0
    crc_data[9] = 0
    expected = cal_crc16(crc_data)
    assert packet[8] | (packet[9] << 8) == expected
    assert packet[V3_HEADER_LEN:] == bytes(payload)


@pytest.mark.unit
def test_send_v3_packet_rejects_oversized_payload():
    hub = make_encoder_hub()

    with pytest.raises(ValueError):
        hub._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, b"\x00" * (V3_MAX_DATA_LEN + 1))


@pytest.mark.unit
def test_send_v3_packet_accepts_single_int_payload():
    hub = make_encoder_hub()

    packet = hub._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, 0x05)

    assert packet[V3_HEADER_LEN:] == bytes([0x05])
