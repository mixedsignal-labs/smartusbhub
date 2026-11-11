# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""Control SmartUSBHub devices through the USB CDC command port.

See README.md for usage and docs/protocol.md for frame formats and commands.
"""

import os
import time
import atexit
import hashlib
import json
import copy
import logging
import warnings
import weakref
import tempfile
import threading
from collections import deque
from functools import wraps

import serial
import serial.tools.list_ports

__version__ = "1.3.1"

# Detect file-lock backends; Windows uses a named mutex in _PortLock.acquire.
# Define both flags so either can be checked regardless of the available backend.
HAS_FCNTL = False
HAS_MSVCRT = False
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        pass
class LegacyAPIWarning(FutureWarning):
    """Visible migration notice for a supported, previously published API."""


def _warn_legacy_api(name, replacement):
    warnings.warn(f"{name} is a legacy API. Migrate to {replacement}.",
                  LegacyAPIWarning, stacklevel=3)


class FirmwareUpdateRecommendedWarning(UserWarning):
    """Non-blocking notice: old firmware remains usable through compatibility APIs."""


class SmartUSBHubError(Exception):
    """
    Base class for all errors raised by this library.

    Catch this to handle any SmartUSBHub-specific failure regardless of subtype.
    """
    pass

class PortBusyError(SmartUSBHubError, ValueError):
    """
    Raised when a serial port is already in use by another instance or process.

    Also subclasses ``ValueError`` for backward compatibility with callers that
    previously caught the ``ValueError`` raised on a busy port.
    """
    pass


class PortPermissionError(SmartUSBHubError, PermissionError):
    """
    Raised when the operating system denies access to a serial port.

    Kept distinct from :class:`PortBusyError` so command-line applications can
    provide an actionable permissions hint instead of incorrectly reporting
    that another process owns the port.
    """
    pass


class DeviceConnectionError(SmartUSBHubError):
    """
    Raised when a device does not respond during connection setup.

    Typically means the port is not a SmartUSBHub or the device is unresponsive.
    """
    pass

class FeatureNotSupportedError(SmartUSBHubError, ValueError):
    """
    Raised when a requested feature is not supported by the connected product model.

    Also subclasses ``ValueError`` for backward compatibility.
    """
    pass


class DeviceAuthenticationError(SmartUSBHubError):
    """Base class for optional genuine-device authentication failures."""
    pass


class DeviceAuthenticationCommunicationError(DeviceAuthenticationError):
    """The authentication exchange timed out or returned a malformed response."""
    pass


class DeviceAuthenticationRejectedError(DeviceAuthenticationError):
    """The certificate or challenge proof could not establish device authenticity."""
    pass


class AuthenticationNotSupportedError(DeviceAuthenticationError):
    """The connected firmware does not implement genuine-device authentication."""
    pass


class AuthenticationTrustError(DeviceAuthenticationError):
    """The caller did not provide a usable trusted issuer public key."""
    pass


class AuthenticationDependencyError(DeviceAuthenticationError, ImportError):
    """The optional ``cryptography`` package needed for verification is missing."""
    pass


# --- Command codes -----------------------------------------------------------
CMD_GET_CHANNEL_POWER_STATUS        = 0x00
CMD_SET_CHANNEL_POWER               = 0x01
CMD_SET_CHANNEL_POWER_INTERLOCK     = 0x02  # select one powered channel, or turn all off
CMD_GET_CHANNEL_VOLTAGE             = 0x03  # V2 reply in mV
CMD_GET_CHANNEL_CURRENT             = 0x04  # V2 reply in mA
CMD_SET_CHANNEL_DATALINE            = 0x05  # set USB2 D+/D- data-line switch state
CMD_GET_CHANNEL_DATALINE_STATUS     = 0x08  # query USB2 D+/D- data-line switch state

CMD_SET_BUTTON_CONTROL              = 0x09
CMD_GET_BUTTON_CONTROL_STATUS       = 0x0A

CMD_SET_DEFAULT_POWER_STATUS        = 0x0B  # set boot/default VBUS power state
CMD_GET_DEFAULT_POWER_STATUS        = 0x0C  # query boot/default VBUS power state
CMD_SET_DEFAULT_DATALINE_STATUS     = 0x0D  # set boot/default USB2 data-line state
CMD_GET_DEFAULT_DATALINE_STATUS     = 0x0E  # query boot/default USB2 data-line state

CMD_SET_AUTO_RESTORE                = 0x0F  # enable or disable power-loss auto-restore
CMD_GET_AUTO_RESTORE_STATUS         = 0x10  # query power-loss auto-restore state

CMD_SET_OPERATE_MODE                = 0x06
CMD_GET_OPERATE_MODE                = 0x07

CMD_SET_DEVICE_ADDRESS              = 0x11
CMD_GET_DEVICE_ADDRESS              = 0x12

CMD_GET_CHANNEL_MEASUREMENTS        = 0x1A  # V3 query/stream: voltage/current/power samples
CMD_LAB_RECOVERY                    = 0x27  # USB3 RevB opt-in laboratory lease
CMD_LAB_CAPTURE                     = 0x28  # USB3 RevB coherent snapshot batches
CMD_MEASUREMENT_FILTER              = 0x29  # 0=instantaneous, 1=measurement hardware internal avg8
CMD_MEASUREMENT_RATE                = 0x2A  # Device-declared uint16 LE output sample rate
CMD_ALERT_CONFIG                    = 0x30
CMD_GET_ALERT_STATUS                = 0x31
CMD_CLEAR_ALERT_LATCH               = 0x32
CMD_ALERT_EVENT_SUBSCRIPTION        = 0x33
CMD_ALERT_EVENT                     = 0x34
CMD_RESET_PROTECTION_TRIP           = 0x35
CMD_GET_CHANNEL_POWER_MASK          = 0x36  # V1: channel=low8, value=high8
CMD_GET_CHANNEL_USB2_DATALINE_MASK   = 0x37
CMD_GET_CHANNEL_USB3_DATALINE_MASK   = 0x38
CMD_GET_DEFAULT_POWER_MASK          = 0x39  # V1 request, V2 reply, two bits/channel
CMD_GET_DEFAULT_USB2_DATALINE_MASK   = 0x3A
CMD_GET_DEFAULT_USB3_DATALINE_MASK   = 0x3B
ALERT_TYPES = ("overcurrent", "undercurrent", "overvoltage", "undervoltage", "overpower")
CMD_SET_DEFAULT_USB3_DATALINE_STATUS = 0x2D
CMD_GET_DEFAULT_USB3_DATALINE_STATUS = 0x2E
CMD_RESET_HUB                       = 0x2C  # V3 empty request/reply; capability-gated
CMD_GET_CAPABILITIES                = 0x2B  # current V3: implemented capabilities as UTF-8 JSON
CMD_GET_CHANNEL_OC_STATUS           = 0x1B  # query/unsolicited: channel=active_mask, value=latch_mask
CMD_CLEAR_CHANNEL_OC_LATCH          = 0x1C  # clear the sticky OC latch for a channel mask
CMD_IDENTIFY_DEVICE                 = 0x1D  # quick blink status LED to locate device
CMD_SET_CHANNEL_NAME                = 0x1E  # V3 payload: [channel(1-based), utf8 name]
CMD_GET_CHANNEL_NAME                = 0x1F  # V3 payload: request/response [channel(1-based), utf8 name]
CMD_SET_DEVICE_ALIAS                = 0x20  # V3 payload: utf8 alias
CMD_SET_CHANNEL_USB3_DATALINE       = 0x15
CMD_GET_CHANNEL_USB3_DATALINE_STATUS = 0x16
CMD_SET_UPSTREAM_HOST               = 0x22
CMD_GET_UPSTREAM_HOST               = 0x23
CMD_DEBUG_LOG                   = 0x24
CMD_GET_DEBUG_TEMPERATURE           = 0x25
CMD_SET_DEBUG_LOG_ENABLE            = 0x26
CMD_GET_DEVICE_ALIAS                = 0x21  # V3 payload response: utf8 alias
CMD_AUTH_GET_CERTIFICATE            = 0xD0  # V3 response: status + compact certificate
CMD_AUTH_CHALLENGE                  = 0xD1  # V3 request: nonce[32], response: status + r||s
CMD_REBOOT_MCU                      = 0xF7
CMD_GET_SERIAL_NO                   = 0xF9
CMD_GET_PRODUCT_TYPE                = 0xF0
CMD_GET_MAX_CHANNELS                = 0xF1
CMD_GET_PROTOCOL_FORMAT             = 0xF2  # V1 bootstrap: reply channel=3, data=header length
CMD_FACTORY_RESET                   = 0xFC  # restore persistent settings to factory defaults
CMD_GET_FIRMWARE_VERSION            = 0xFD
CMD_GET_HARDWARE_VERSION            = 0xFE

# --- V3 framing constants ----------------------------------------------------
V3_MAGIC                            = (0x55, 0xAB, 0xCD, 0xEF)  # 4-byte SOF magic
V3_LEGACY_HEADER_LEN                = 10
V3_HEADER_LEN                       = 16   # request ID u16, status u8, reserved[3]
V3_MAX_DATA_LEN                     = 1024
V3_MAX_FRAME_LEN                    = V3_HEADER_LEN + V3_MAX_DATA_LEN
V3_FLAG_STREAM                      = 0x01
V3_FLAG_RESPONSE                    = 0x02
V3_FLAG_REQUEST                     = 0x04
V3_ASSEMBLY_TIMEOUT                 = 0.25
V3_MEAS_FLAG_FORCE_SAMPLE           = 0x01
V3_MEAS_FLAG_STREAM_ENABLE          = 0x02
V3_MEAS_FLAG_STREAM_DISABLE         = 0x04
V3_STATUS_OK                        = 0x00
V3_STATUS_UNSUPPORTED_COMMAND       = 0x01
V3_STATUS_UNSUPPORTED_FEATURE       = 0x02
V3_STATUS_INVALID_ARGUMENT          = 0x03
V3_STATUS_BUSY                      = 0x04
V3_STATUS_NOT_READY                 = 0x05
V3_STATUS_IO_ERROR                  = 0x06
V3_STATUS_INTERNAL_ERROR            = 0x07

# --- Genuine authentication -------------------------------------------------
AUTH_STATUS_OK                      = 0x00
AUTH_STATUS_UNSUPPORTED             = 0x01
AUTH_STATUS_INVALID_REQUEST         = 0x02
AUTH_STATUS_NOT_PROVISIONED         = 0x03
AUTH_STATUS_INVALID_PROVISIONING    = 0x04
AUTH_STATUS_SIGNING_FAILED          = 0x05

AUTH_CERTIFICATE_SIZE               = 125
AUTH_NONCE_SIZE                     = 32
AUTH_SIGNATURE_SIZE                 = 64
AUTH_CHALLENGE_TIMEOUT_MIN           = 6.0  # Allow sufficient time for device-side processing.
AUTH_CHALLENGE_DOMAIN               = b"MSL-SMARTUSBHUB-AUTH-V1"
AUTH_CERT_MAGIC                     = b"MSL1"
AUTH_CERT_VERSION                   = 1
AUTH_ALGORITHM_P256_SHA256          = 1


def load_trusted_issuers(path):
    """Load the public official-app issuer mapping generated by ``auth_keygen.py``.

    The JSON file is public material, not a secret. It has the shape
    ``{"format_version": 1, "issuers": {"1": {"public_key_pem": "..."}}}``.
    The returned mapping can be passed directly to :meth:`authenticate_device`.
    """
    try:
        with open(os.fspath(path), "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        raise AuthenticationTrustError(f"Cannot load authentication trust store: {path}") from exc
    if document.get("format_version") != 1 or not isinstance(document.get("issuers"), dict):
        raise AuthenticationTrustError("Authentication trust store format is invalid.")
    trusted = {}
    for issuer_id, record in document["issuers"].items():
        try:
            numeric_id = int(issuer_id)
        except (TypeError, ValueError) as exc:
            raise AuthenticationTrustError(f"Invalid issuer ID in trust store: {issuer_id}") from exc
        if isinstance(record, dict):
            material = record.get("public_key_pem")
        else:
            material = record
        if not isinstance(material, str) or not material.strip():
            raise AuthenticationTrustError(f"Issuer {numeric_id} has no public key.")
        trusted[numeric_id] = material
    if not trusted:
        raise AuthenticationTrustError("Authentication trust store contains no issuers.")
    return trusted

# --- Operating modes ---------------------------------------------------------
# Channels are addressed by 1-based number throughout the public API (e.g.
# set_channel_power(1, 2, state=1)); the wire-level bitmask is derived
# internally, so no per-channel constants are exposed.
OPERATE_MODE_NORMAL = 0
OPERATE_MODE_INTERLOCK = 1

# Product identity/display metadata. New products need no capability entry here.
PRODUCT_CATALOG = {
    0x00: {
        "name": "HBP_USB2_4CH",
        "channels": 4,
        "description": "USB2.0 4-channel hub"
    },
    0x01: {
        "name": "HBL_USB2_2CH",
        "channels": 2,
        "description": "USB2.0 2-channel hub"
    },
    0x02: {
        "name": "HBP_USB2_7CH",
        "channels": 7,
        "description": "USB2.0 7-channel hub"
    },
    0x03: {
        "name": "HBP_USB2_7CH_ADV",
        "channels": 7,
        "description": "USB2.0 7-channel hub with multichannel measurement unit voltage/current monitoring"
    },
    0x04: {
        "name": "HBP_USB3_4CH",
        "channels": 4,
        "description": "USB3.0 4-channel RevB hub with hardware measurement unit monitoring and dual-host selection"
    },
    0x05: {
        "name": "HBL_USB2_4CH",
        "channels": 4,
        "description": "USB2.0 4-channel power-control hub"
    }
}

# Frozen compatibility knowledge for firmware that cannot declare capabilities.
# Do not add new products/features here; implement GET_CAPABILITIES in firmware.
_LEGACY_PRODUCT_CAPABILITIES = {
    0x00: {
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1
    },
    0x01: {
        "enable_adc": False,
        "enable_usb2_data_switch": False,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1
    },
    # Legacy standard 7CH firmware used 0x03 only after detecting all multichannel measurement units.
    0x02: {
        "enable_adc": False,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "enable_overcurrent": True,
        "ack_timeout": 0.1
    },
    0x03: {
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "enable_overcurrent": True,
        "ack_timeout": 0.1
    },
    # Historical measurement hardware/capture traffic needs more control-response headroom.
    0x04: {
        "enable_upstream_host_switch": True,
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": True,
        "enable_ilim_switch": False,
        "ack_timeout": 0.5
    },
    0x05: {
        "enable_adc": False,
        "enable_usb2_data_switch": False,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "enable_overcurrent": False,
        "ack_timeout": 0.1
    }
}

# Backward-compatible public view for older callers of get_product_info().
# Connected-device feature decisions never read enable_* from this merged view.
PRODUCT_TYPE_TABLE = {
    key: dict(info, **_LEGACY_PRODUCT_CAPABILITIES.get(key, {}))
    for key, info in PRODUCT_CATALOG.items()
}

_CAPABILITY_NAMES = (
    "power", "measurement", "board_temperature", "usb2_data_switch",
    "usb3_data_switch", "upstream_host_switch", "overcurrent",
    "current_limit_switch", "identify", "device_alias", "channel_names",
    "button_control", "auto_restore", "interlock", "authentication", "debug_log", "alerts",
)
_FEATURE_CAPABILITY = {
    "adc": "measurement", "usb2_data_switch": "usb2_data_switch",
    "usb3_data_switch": "usb3_data_switch", "upstream_host_switch": "upstream_host_switch",
    "ilim_switch": "current_limit_switch", "overcurrent": "overcurrent",
    "board_temperature": "board_temperature",
}

# Library logging follows the standard practice of attaching only a NullHandler;
# the consuming application is responsible for configuring handlers and levels.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Tests may disable the per-instance command lock; leave enabled in production.
ENABLE_SYNC_LOCK = True


def synchronized(method):
    """
    Hold ``self.lock`` for the whole method when ``ENABLE_SYNC_LOCK`` is True.
    """

    @wraps(method)
    def _synchronized(self, *args, **kwargs):
        if ENABLE_SYNC_LOCK:
            with self.lock:
                return method(self, *args, **kwargs)
        return method(self, *args, **kwargs)
    return _synchronized


class _Codec:
    """
    Stateless V1/V2/V3 encoding and parsing, with shared checksum and sizing rules.
    """

    # Reply frames that use the 7-byte V2 framing (two payload bytes); every other
    # V1/V2 reply uses the 6-byte V1 framing. This is the per-command sizing table
    # the parser and the receive loop both consult.
    V2_REPLY_COMMANDS = (
        CMD_GET_DEFAULT_POWER_MASK, CMD_GET_DEFAULT_USB2_DATALINE_MASK,
        CMD_GET_DEFAULT_USB3_DATALINE_MASK,
        CMD_GET_CHANNEL_VOLTAGE, CMD_GET_CHANNEL_CURRENT,
        CMD_SET_DEFAULT_POWER_STATUS, CMD_SET_DEFAULT_DATALINE_STATUS,
        CMD_GET_DEFAULT_POWER_STATUS, CMD_GET_DEFAULT_DATALINE_STATUS,
    )

    @staticmethod
    def crc16(data):
        """Compute a CRC16 over ``data`` (poly 0x8005, init 0xFFFF), used by V3."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x8005
                else:
                    crc = crc >> 1
        return crc & 0xFFFF

    @staticmethod
    def encode_v1v2(cmd, channel_mask, data):
        """
        Build a V1/V2 bytearray ``55 5A | cmd | channel | data... | checksum``.

        ``channel_mask`` is the command-specific channel byte, not always a mask.
        ``data`` contains the payload bytes following it.
        """
        payload = [channel_mask] + list(data)
        packet = bytearray([0x55, 0x5A, cmd])
        packet.extend(payload)
        packet.append((cmd + sum(payload)) & 0xFF)
        return packet

    @staticmethod
    def encode_v3(cmd, payload=b"", *, header_len=V3_HEADER_LEN,
                  request_id=1, flags=V3_FLAG_REQUEST, status=V3_STATUS_OK):
        """Encode a V3 frame.

        CRC covers the whole header and payload, with bytes 8:10 zeroed.
        No inference from payload bytes or firmware version is performed.
        """
        if payload is None:
            payload = b""
        elif isinstance(payload, int):
            payload = bytes([payload])
        payload = bytes(payload)
        if header_len not in (V3_LEGACY_HEADER_LEN, V3_HEADER_LEN):
            raise ValueError("Unsupported V3 header length")
        if len(payload) > V3_MAX_DATA_LEN:
            raise ValueError(f"V3 payload too large: {len(payload)} > {V3_MAX_DATA_LEN}")
        if flags not in (V3_FLAG_REQUEST, V3_FLAG_RESPONSE, V3_FLAG_STREAM):
            raise ValueError("Exactly one V3 message type is required")
        if not 0 <= request_id <= 65535 or not 0 <= status <= 255:
            raise ValueError("Invalid V3 request ID or status")
        if flags == V3_FLAG_REQUEST and (not request_id or status):
            raise ValueError("Requests require a nonzero ID and zero status")
        if flags == V3_FLAG_STREAM and (request_id or status):
            raise ValueError("Events require zero ID and status")
        wire_flags = flags if header_len == V3_HEADER_LEN else (flags & V3_FLAG_STREAM)
        packet = bytearray([0x55, 0xAB, 0xCD, 0xEF, cmd & 255, wire_flags,
                            len(payload) & 255, len(payload) >> 8, 0, 0])
        if header_len == V3_HEADER_LEN:
            packet.extend([request_id & 255, request_id >> 8, status, 0, 0, 0])
        packet.extend(payload)
        crc = _Codec.crc16(packet)
        packet[8], packet[9] = crc & 255, crc >> 8
        return packet

    @staticmethod
    def parse_frame(data, *, header_len=V3_HEADER_LEN):
        """
        Parse one frame from the front of ``data`` (V1/V2/V3).

        :param data: Raw bytes received from the device.

        :returns: Tuple (cmd, channel, value, length) on success, else None when the
            buffer holds only a partial frame or the frame is invalid. For V3 frames,
            channel is 0 and value includes "v3", "stream", "payload";
            current V3 additionally supplies "request_id", "status", "flags".
        """
        if len(data) < 6:
            return None

        # Header format is selected once by the V1 bootstrap, never guessed.
        if data[:2] == bytes(V3_MAGIC[:2]):
            if header_len not in (V3_LEGACY_HEADER_LEN, V3_HEADER_LEN):
                return None
            if len(data) < header_len or data[:4] != bytes(V3_MAGIC):
                return None
            cmd, flags = data[4], data[5]
            data_length = data[6] | (data[7] << 8)
            if data_length > V3_MAX_DATA_LEN:
                return None
            total_length = header_len + data_length
            if len(data) < total_length:
                return None
            received_crc16 = data[8] | (data[9] << 8)
            crc_data = bytearray(data[:total_length])
            crc_data[8:10] = b"\0\0"
            if _Codec.crc16(crc_data) != received_crc16:
                return None
            result = {"v3": True, "stream": bool(flags & V3_FLAG_STREAM),
                      "payload": bytes(data[header_len:total_length])}
            if header_len == V3_HEADER_LEN:
                request_id = data[10] | (data[11] << 8)
                status = data[12]
                if flags not in (V3_FLAG_REQUEST, V3_FLAG_RESPONSE, V3_FLAG_STREAM):
                    return None
                if any(data[13:16]):
                    return None
                if flags == V3_FLAG_REQUEST and (not request_id or status):
                    return None
                if flags == V3_FLAG_STREAM and (request_id or status):
                    return None
                result.update(request_id=request_id, status=status, flags=flags)
            elif flags & ~V3_FLAG_STREAM:
                return None
            return cmd, 0, result, total_length

        # V1/V2 protocol: SOF 0x55 0x5A.
        if data[0] != 0x55 or data[1] != 0x5A:
            return None

        cmd = data[2]
        channel = data[3]

        if cmd in _Codec.V2_REPLY_COMMANDS:
            # V2 frame: two payload bytes.
            if len(data) < 7:
                return None
            value_0 = data[4]
            value_1 = data[5]
            checksum = data[6]
            if (cmd + channel + value_0 + value_1) & 0xFF != checksum:
                logger.debug(f"Invalid V2 checksum for channel {channel}")
                return None
            return (cmd, channel, [value_0, value_1], 7)

        # V1 frame: single payload byte.
        value = data[4]
        checksum = data[5]
        if (cmd + channel + value) & 0xFF != checksum:
            return None
        return (cmd, channel, value, 6)


class _FrameReader:
    """Incremental V1/V2/V3 framing with an idle timeout for partial frames."""

    def __init__(self, header_len=V3_HEADER_LEN, timeout=V3_ASSEMBLY_TIMEOUT):
        self.header_len = header_len
        self.timeout = timeout
        self.buffer = bytearray()
        self.last_byte_at = None
        self.discarded = 0

    def feed(self, data=b"", now=None):
        now = time.monotonic() if now is None else now
        if self.buffer and self.last_byte_at is not None and now - self.last_byte_at > self.timeout:
            # Drop the stale start, then search retained bytes for a later frame.
            del self.buffer[0]
            self.discarded += 1
            self.last_byte_at = now
        if data:
            self.buffer.extend(data)
            self.last_byte_at = now
        frames = []
        while len(self.buffer) >= 2:
            b = self.buffer
            if b[:2] == bytes(V3_MAGIC[:2]):
                if len(b) < 4:
                    break
                if b[:4] != bytes(V3_MAGIC):
                    del b[0]; self.discarded += 1
                    continue
                if len(b) < 10:
                    break
                length = b[6] | (b[7] << 8)
                if length <= V3_MAX_DATA_LEN and len(b) < self.header_len + length:
                    break
            elif b[:2] == b"\x55\x5a":
                if len(b) < 3:
                    break
                required = 7 if b[2] in _Codec.V2_REPLY_COMMANDS else 6
                if len(b) < required:
                    break
            else:
                del b[0]; self.discarded += 1
                continue
            parsed = _Codec.parse_frame(b, header_len=self.header_len)
            if parsed is None:
                del b[0]; self.discarded += 1
                continue
            frames.append(parsed)
            del b[:parsed[3]]
        return frames


class _CommandEvent(threading.Event):
    """Keep existing boolean APIs while distinguishing a rejection from timeout."""

    def __init__(self):
        super().__init__()
        self.protocol_status = V3_STATUS_OK
        self.response_ok = True
        self.on_timeout = None

    def clear(self):
        self.on_timeout = None
        self.protocol_status = V3_STATUS_OK
        self.response_ok = True
        super().clear()

    def wait(self, timeout=None):
        completed = super().wait(timeout)
        if not completed and self.on_timeout is not None:
            self.on_timeout()
        return completed and self.protocol_status == V3_STATUS_OK and self.response_ok


def detect_v3_header_length(port, timeout=0.3):
    """Read-only V1 discovery for raw tools that exclusively own ``port``.

    Devices without current V3 discovery use the compatibility path.
    Use before starting a stream. Normal SDK connections negotiate internally.
    """
    port.write(_Codec.encode_v1v2(CMD_GET_PROTOCOL_FORMAT, 0, [0]))
    reader = _FrameReader(header_len=V3_LEGACY_HEADER_LEN)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for cmd, channel, value, _ in reader.feed(port.read(max(1, port.in_waiting))):
            if cmd == CMD_GET_PROTOCOL_FORMAT:
                if (channel, value) == (3, V3_HEADER_LEN):
                    return V3_HEADER_LEN
                if (channel, value) == (255, 255):
                    return V3_LEGACY_HEADER_LEN
                raise DeviceConnectionError("Unsupported protocol discovery response")
    return V3_LEGACY_HEADER_LEN


class _PortLock:
    """
    Coordinate serial-port ownership across cooperating processes.

    Windows uses a named mutex and falls back to OS serial-port exclusivity if
    mutex creation is unavailable. Other platforms use the available file-lock
    backend, normally ``fcntl`` on Unix/macOS. Without a backend, only the
    caller's in-process port registry provides this coordination check.
    """

    _locks = {}        # {port: ("mutex", HANDLE) on Windows, file handle elsewhere}
    _lock_dir = None   # lock-file directory (lazily created)

    @classmethod
    def _get_lock_dir(cls):
        """Return the absolute lock-file directory, creating it if needed."""
        if cls._lock_dir is None:
            cls._lock_dir = os.path.join(tempfile.gettempdir(), 'smartusbhub_locks')
            os.makedirs(cls._lock_dir, exist_ok=True)
        return cls._lock_dir

    @classmethod
    def _check_process_exists(cls, pid):
        """Return whether the OS probe confirms that ``pid`` exists."""
        try:
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            os.kill(pid, 0)  # signal 0 only probes for existence
            return True
        except (OSError, ProcessLookupError, AttributeError):
            return False

    @classmethod
    def _clear_stale_lock(cls, lock_file_path):
        """Try to remove a lock file whose recorded owner appears to have exited."""
        if not os.path.exists(lock_file_path):
            return
        try:
            with open(lock_file_path, 'r') as f:
                pid_str = f.read().strip()
            if pid_str.isdigit() and not cls._check_process_exists(int(pid_str)):
                logger.debug(f"Removing stale lock file {lock_file_path}")
                os.remove(lock_file_path)
        except Exception as e:
            logger.debug(f"Error inspecting lock file {lock_file_path}: {e}")

    @classmethod
    def acquire(cls, port):
        """
        Try to acquire the platform's non-blocking port coordination lock.

        File-lock contention triggers a stale-PID cleanup attempt and one retry.
        Windows mutex setup failures fall back to OS serial-port exclusivity.

        :param port: Serial port name.

        :returns: True if acquired or using a fallback, False on contention or error.
        """
        if port in cls._locks:
            return True

        safe_port_name = port.replace('/', '_').replace('\\', '_').replace(':', '_')

        # msvcrt.locking() is unreliable inside some PyInstaller onefile builds
        # on Windows and can raise EINVAL for an otherwise valid lock file. A
        # named kernel mutex provides the exact lifetime semantics needed here:
        # it exists while this process keeps the handle open and is reclaimed
        # automatically if the process exits or crashes.
        if os.name == 'nt':
            try:
                import ctypes
                from ctypes import wintypes

                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel32.CreateMutexW.argtypes = (
                    wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
                kernel32.CreateMutexW.restype = wintypes.HANDLE
                kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
                kernel32.CloseHandle.restype = wintypes.BOOL

                mutex_name = f'Local\\SmartUSBHub_Port_{safe_port_name.upper()}'
                # CreateMutexW documents ERROR_ALREADY_EXISTS via last-error.
                # Clear any stale thread-local value first so a previous Win32
                # call cannot make a newly created mutex look pre-existing.
                ctypes.set_last_error(0)
                handle = kernel32.CreateMutexW(None, False, mutex_name)
                if not handle:
                    error_code = ctypes.get_last_error()
                    logger.warning(
                        "Failed to create Windows port mutex %s: winerror=%s; "
                        "falling back to the OS serial-port exclusivity check",
                        mutex_name, error_code)
                    # Never reject a usable COM port because the optional
                    # coordination layer failed. Windows CreateFile (used by
                    # pyserial) still opens COM ports exclusively and remains
                    # the authoritative busy-port check.
                    return True
                if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
                    kernel32.CloseHandle(handle)
                    logger.warning("Port %s is locked by another process", port)
                    return False

                cls._locks[port] = ('mutex', handle)
                logger.debug("Acquired Windows mutex %s for port %s", mutex_name, port)
                return True
            except Exception as e:
                logger.warning(
                    "Windows mutex unavailable for port %s: %r; falling back "
                    "to the OS serial-port exclusivity check", port, e)
                return True

        lock_file_path = os.path.join(cls._get_lock_dir(), f'{safe_port_name}.lock')

        if not HAS_FCNTL and not HAS_MSVCRT:
            logger.warning("File locking is unsupported on this platform; "
                           "falling back to a process-local check only.")
            return True

        for attempt in (0, 1):
            # Retry once after attempting stale-lock cleanup; the file may remain.
            try:
                lock_file = open(lock_file_path, 'a+')
                try:
                    if HAS_FCNTL:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    else:
                        lock_file.seek(0)
                        if os.path.getsize(lock_file_path) == 0:
                            lock_file.write('0')
                            lock_file.flush()
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                except (IOError, OSError):
                    lock_file.close()
                    if attempt == 0:
                        cls._clear_stale_lock(lock_file_path)
                        continue
                    logger.warning(f"Port {port} is locked by another process")
                    return False

                cls._locks[port] = lock_file
                lock_file.seek(0)
                lock_file.truncate()
                lock_file.write(str(os.getpid()))
                lock_file.flush()
                logger.debug(f"Acquired file lock for port {port}")
                return True
            except Exception as e:
                logger.error(f"Failed to acquire lock for port {port}: {e}")
                return False
        return False

    @classmethod
    def release(cls, port):
        """Release the held mutex or file lock for ``port``, if any."""
        lock_handle = cls._locks.pop(port, None)
        if lock_handle is None:
            return
        if isinstance(lock_handle, tuple) and lock_handle[0] == 'mutex':
            try:
                import ctypes
                from ctypes import wintypes

                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
                kernel32.CloseHandle.restype = wintypes.BOOL
                if not kernel32.CloseHandle(lock_handle[1]):
                    logger.error(
                        "Failed to release Windows mutex for port %s: winerror=%s",
                        port, ctypes.get_last_error())
                else:
                    logger.debug("Released Windows mutex for port %s", port)
            except Exception as e:
                logger.error("Failed to release Windows mutex for port %s: %r", port, e)
            return

        lock_file = lock_handle
        try:
            if HAS_FCNTL:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif HAS_MSVCRT:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            logger.debug(f"Released file lock for port {port}")
        except Exception as e:
            logger.error(f"Failed to release lock for port {port}: {e}")


class SmartUSBHub:
    """
    High-level interface to an industrial Smart USB Hub over its USB CDC
    serial port.

    Provides per-port control of power and data connections, voltage/current
    monitoring, default-state configuration and factory reset. Suitable for
    automated test systems and hardware development.

    Instances may be used as context managers; the device is disconnected on exit:

    .. code-block:: python

       with SmartUSBHub(port) as hub:
           hub.set_channel_power(1, state=1)
    """

    # Process-local registry of open ports and their device addresses. Used to
    # detect double-open within a process; cross-process coordination lives in
    # ``_PortLock``.
    _lifecycle_lock = threading.RLock()
    _connected_ports = set()
    _connected_addresses = {}        # {port: address}
    _instances = weakref.WeakSet()   # live instances, for atexit cleanup

    @classmethod
    def _acquire_port_lock(cls, port):
        return _PortLock.acquire(port)

    @classmethod
    def _release_port_lock(cls, port):
        return _PortLock.release(port)

    @classmethod
    def _cleanup_all_instances(cls):
        """Disconnect every live instance. Registered with atexit for safe shutdown."""
        for instance in list(cls._instances):
            try:
                instance.disconnect()
            except Exception:
                pass

    # Commands that the device acknowledges and that the host may wait on.
    _ACK_COMMANDS = (
        CMD_GET_DEFAULT_POWER_MASK, CMD_GET_DEFAULT_USB2_DATALINE_MASK,
        CMD_GET_DEFAULT_USB3_DATALINE_MASK,
        CMD_GET_CHANNEL_POWER_MASK, CMD_GET_CHANNEL_USB2_DATALINE_MASK,
        CMD_GET_CHANNEL_USB3_DATALINE_MASK,
        CMD_GET_OPERATE_MODE, CMD_SET_OPERATE_MODE,
        CMD_SET_CHANNEL_POWER, CMD_GET_CHANNEL_POWER_STATUS,
        CMD_SET_CHANNEL_POWER_INTERLOCK,
        CMD_GET_CHANNEL_VOLTAGE, CMD_GET_CHANNEL_CURRENT,
        CMD_GET_CHANNEL_MEASUREMENTS,
        CMD_LAB_CAPTURE, CMD_MEASUREMENT_FILTER,
        CMD_MEASUREMENT_RATE, CMD_GET_CAPABILITIES, CMD_RESET_HUB,
        CMD_SET_DEFAULT_USB3_DATALINE_STATUS, CMD_GET_DEFAULT_USB3_DATALINE_STATUS,
        CMD_ALERT_CONFIG, CMD_GET_ALERT_STATUS, CMD_CLEAR_ALERT_LATCH,
        CMD_ALERT_EVENT_SUBSCRIPTION, CMD_RESET_PROTECTION_TRIP,
        CMD_GET_CHANNEL_OC_STATUS, CMD_CLEAR_CHANNEL_OC_LATCH,
        CMD_IDENTIFY_DEVICE,
        CMD_SET_CHANNEL_NAME, CMD_GET_CHANNEL_NAME,
        CMD_SET_DEVICE_ALIAS, CMD_GET_DEVICE_ALIAS,
        CMD_SET_UPSTREAM_HOST, CMD_GET_UPSTREAM_HOST,
        CMD_SET_DEBUG_LOG_ENABLE, CMD_GET_DEBUG_TEMPERATURE,
        CMD_SET_CHANNEL_USB3_DATALINE, CMD_GET_CHANNEL_USB3_DATALINE_STATUS,
        CMD_AUTH_GET_CERTIFICATE, CMD_AUTH_CHALLENGE,
        CMD_SET_CHANNEL_DATALINE, CMD_GET_CHANNEL_DATALINE_STATUS,
        CMD_SET_BUTTON_CONTROL, CMD_GET_BUTTON_CONTROL_STATUS,
        CMD_SET_DEFAULT_POWER_STATUS, CMD_GET_DEFAULT_POWER_STATUS,
        CMD_SET_DEFAULT_DATALINE_STATUS, CMD_GET_DEFAULT_DATALINE_STATUS,
        CMD_SET_AUTO_RESTORE, CMD_GET_AUTO_RESTORE_STATUS,
        CMD_SET_DEVICE_ADDRESS, CMD_GET_DEVICE_ADDRESS,
        CMD_REBOOT_MCU, CMD_GET_PRODUCT_TYPE, CMD_GET_MAX_CHANNELS,
        CMD_GET_SERIAL_NO, CMD_FACTORY_RESET, CMD_GET_PROTOCOL_FORMAT,
        CMD_GET_FIRMWARE_VERSION, CMD_GET_HARDWARE_VERSION,
    )

    # Wire framing tables live on the codec; alias here so the receive loop's
    # frame-sizing (``self._V2_REPLY_COMMANDS``) reads the same single source.
    _V2_REPLY_COMMANDS = _Codec.V2_REPLY_COMMANDS

    _STATUS_MASK_QUERIES = {
        CMD_GET_CHANNEL_POWER_MASK: (CMD_GET_CHANNEL_POWER_STATUS, "channel_power_status"),
        CMD_GET_CHANNEL_USB2_DATALINE_MASK: (CMD_GET_CHANNEL_DATALINE_STATUS, "channel_dataline_status"),
        CMD_GET_CHANNEL_USB3_DATALINE_MASK: (CMD_GET_CHANNEL_USB3_DATALINE_STATUS, "channel_usb3_dataline_status"),
    }

    _DEFAULT_MASK_QUERIES = {
        CMD_GET_DEFAULT_POWER_MASK: (
            CMD_GET_DEFAULT_POWER_STATUS, "channel_default_power_flag", "channel_default_power_status"),
        CMD_GET_DEFAULT_USB2_DATALINE_MASK: (
            CMD_GET_DEFAULT_DATALINE_STATUS, "channel_default_dataline_flag", "channel_default_dataline_status"),
        CMD_GET_DEFAULT_USB3_DATALINE_MASK: (
            CMD_GET_DEFAULT_USB3_DATALINE_STATUS, "channel_default_usb3_data_flag", "channel_default_usb3_data_status"),
    }

    def __init__(self, port):
        """
        Open a Smart USB Hub on the given serial port and read its identity.

        Acquires a process-local and cross-process lock on the port, opens the
        serial link at 115200 baud, starts the background receive thread and
        queries device information. The constructor blocks until the device
        identity is read or the attempt times out.

        :param port: Serial port name (e.g. "/dev/ttyUSB0" or "COM3").

        :raises PortBusyError: If the port is already in use by another instance or process.

        :raises DeviceConnectionError: If the device does not respond during setup.

        :raises serial.SerialException: For other serial-layer failures.
        """
        self.port = port
        self.name = f"smarthub_id:{port.split('/')[-1]}"

        with self._lifecycle_lock:
            if port in SmartUSBHub._connected_ports:
                raise PortBusyError(
                    f"Port {port} is already in use by another SmartUSBHub instance. "
                    f"Disconnect the existing instance first or use a different port.")

            if not self._acquire_port_lock(port):
                raise PortBusyError(
                    f"Port {port} is already in use by another process. "
                    f"Disconnect the existing connection first or use a different port.")

            try:
                self.ser = serial.Serial(port, 115200, timeout=0.5)
                SmartUSBHub._connected_ports.add(port)
                SmartUSBHub._instances.add(self)
            except serial.SerialException as e:
                self._release_port_lock(port)
                msg = str(e).lower()
                if "permission denied" in msg or "operation not permitted" in msg:
                    raise PortPermissionError(
                        f"Permission denied while opening port {port}.")
                if ("resource busy" in msg or "device or resource busy" in msg
                        or "access is denied" in msg):
                    raise PortBusyError(
                        f"Port {port} is already in use. Disconnect the existing connection first.")
                raise

        # Default ACK timeout; refined per product model once the type is known.
        self.com_timeout = 0.1
        logger.info(f"SmartUSBHub initialized on port {self.port}")

        # One ACK Event per command; the receive thread sets it when a matching
        # frame arrives and the calling thread waits on it.
        self.ack_events = {cmd: _CommandEvent() for cmd in self._ACK_COMMANDS}
        self.callbacks = {cmd: None for cmd in self.ack_events}
        self.callbacks[CMD_DEBUG_LOG] = None
        self.callbacks[CMD_ALERT_EVENT] = None
        self._alert_replies = {}
        self.last_alert_event = None

        # Maps an incoming command code to the handler that updates cached state.
        self._frame_handlers = {
            CMD_SET_CHANNEL_POWER: self._handle_set_channel_power_status,
            CMD_GET_CHANNEL_POWER_STATUS: self._handle_get_channel_power_status,
            CMD_SET_CHANNEL_POWER_INTERLOCK: self._handle_power_interlock_control,
            CMD_GET_CHANNEL_OC_STATUS: self._handle_oc_status,
            CMD_CLEAR_CHANNEL_OC_LATCH: self._handle_oc_status,
            CMD_GET_CHANNEL_VOLTAGE: self._handle_get_channel_voltage,
            CMD_GET_CHANNEL_CURRENT: self._handle_get_channel_current,
            CMD_GET_CHANNEL_MEASUREMENTS: self._handle_get_channel_measurements,
            CMD_LAB_CAPTURE: self._handle_capture,
            CMD_MEASUREMENT_FILTER: self._handle_measurement_filter,
            CMD_MEASUREMENT_RATE: self._handle_measurement_rate,
            CMD_GET_CAPABILITIES: self._handle_capabilities,
            CMD_SET_DEFAULT_USB3_DATALINE_STATUS: self._handle_default_usb3_response,
            CMD_GET_DEFAULT_USB3_DATALINE_STATUS: self._handle_default_usb3_response,
            CMD_ALERT_CONFIG: self._handle_alert_response,
            CMD_GET_ALERT_STATUS: self._handle_alert_response,
            CMD_CLEAR_ALERT_LATCH: self._handle_alert_response,
            CMD_ALERT_EVENT_SUBSCRIPTION: self._handle_alert_response,
            CMD_RESET_PROTECTION_TRIP: self._handle_alert_response,
            CMD_ALERT_EVENT: self._handle_alert_event,
            CMD_SET_CHANNEL_DATALINE: self._handle_set_channel_dataline,
            CMD_IDENTIFY_DEVICE: self._handle_identify_device,
            CMD_SET_CHANNEL_NAME: self._handle_channel_name,
            CMD_GET_CHANNEL_NAME: self._handle_channel_name,
            CMD_SET_DEVICE_ALIAS: self._handle_device_alias,
            CMD_GET_DEVICE_ALIAS: self._handle_device_alias,
            CMD_AUTH_GET_CERTIFICATE: self._handle_auth_certificate,
            CMD_AUTH_CHALLENGE: self._handle_auth_challenge,
            CMD_GET_CHANNEL_DATALINE_STATUS: self._handle_get_channel_dataline,
            CMD_SET_BUTTON_CONTROL: self._handle_set_button_control,
            CMD_GET_BUTTON_CONTROL_STATUS: self._handle_get_button_control,
            CMD_SET_DEFAULT_POWER_STATUS: self._handle_set_default_power_status,
            CMD_GET_DEFAULT_POWER_STATUS: self._handle_get_default_power_status,
            CMD_SET_DEFAULT_DATALINE_STATUS: self._handle_set_default_dataline_status,
            CMD_GET_DEFAULT_DATALINE_STATUS: self._handle_get_default_dataline_status,
            CMD_SET_AUTO_RESTORE: self._handle_set_auto_restore,
            CMD_GET_AUTO_RESTORE_STATUS: self._handle_get_auto_restore_status,
            CMD_GET_OPERATE_MODE: self._handle_get_operate_mode,
            CMD_SET_OPERATE_MODE: self._handle_set_operate_mode,
            CMD_SET_CHANNEL_USB3_DATALINE: self._handle_usb3_dataline,
            CMD_GET_CHANNEL_USB3_DATALINE_STATUS: self._handle_usb3_dataline,
            CMD_SET_UPSTREAM_HOST: self._handle_upstream_host,
            CMD_GET_UPSTREAM_HOST: self._handle_upstream_host,
            CMD_SET_DEVICE_ADDRESS: self._handle_set_device_address,
            CMD_GET_DEVICE_ADDRESS: self._handle_get_device_address,
            CMD_REBOOT_MCU: self._handle_reboot_mcu,
            CMD_FACTORY_RESET: self._handle_factory_reset,
            CMD_GET_FIRMWARE_VERSION: self._handle_firmware_version,
            CMD_GET_HARDWARE_VERSION: self._handle_hardware_version,
            CMD_GET_PRODUCT_TYPE: self._handle_product_type,
            CMD_GET_MAX_CHANNELS: self._handle_get_max_channels,
            CMD_GET_SERIAL_NO: self._handle_serial_no,
            CMD_GET_PROTOCOL_FORMAT: self._handle_protocol_format,
        }

        # Public commands may compose other synchronized commands (for example
        # power-on checks/resets protection). Keep cross-thread serialization
        # while allowing those calls to reenter on the owning thread.
        self.lock = threading.RLock()
        self._send_lock = threading.Lock()  # serializes raw serial writes
        self._v3_lock = threading.RLock()
        self._v3_header_len = V3_LEGACY_HEADER_LEN
        self._v3_protocol_known = False
        self._v3_next_id = int.from_bytes(os.urandom(2), "little") or 1
        self._v3_pending = {}
        self._v3_async_deadlines = {}
        self._v3_recent_ids = {}
        self._v3_recent_order = deque()
        self.last_protocol_error = None

        # Limit bursts of writes; callers wait for replies without a fixed settle delay.
        self._last_send_time = 0
        self._min_send_interval = 0.001   # >= 1 ms between writes (burst guard)
        self._mcu_response_wait = 0.000   # no settle; the reply is awaited explicitly
        # A nonzero receive poll interval avoids busy-spinning; shorter intervals
        # reduce reply-detection latency at the cost of more CPU wakeups.
        self._rx_poll_interval = 0.001

        self.disconnect_callback = None

        # Cached device identity / configuration.
        self.hardware_version = None
        self.firmware_version = None
        self.firmware_version_major = None
        self.firmware_version_minor = None
        self.product_type = None
        self.max_channels = None
        self.serial_no = None
        self.operate_mode = None
        self.auto_restore_status = None
        self.button_control_status = None
        self.device_address = None
        self.device_alias = ""

        # Cached per-channel state, keyed by 1-based channel number.
        self.channel_default_power_flag = {}
        self.channel_default_power_status = {}
        self.channel_names = {}
        self.channel_default_dataline_flag = {}
        self.channel_default_dataline_status = {}
        self.channel_default_usb3_data_flag = {}
        self.channel_default_usb3_data_status = {}
        self.channel_power_status = {}
        self.channel_dataline_status = {}
        self.channel_usb3_dataline_status = {}
        self.channel_oc_active = {}   # {ch: bool} current FLAG# state
        self.channel_oc_latch = {}    # {ch: bool} sticky latch, cleared by command
        self.channel_voltages = {}
        self.channel_currents = {}
        self.channel_powers = {}
        self.channel_measurement_fresh = {}
        self.channel_measurement_valid = {}
        self.channel_measurement_sample_tick = {}

        # Signalled by the receive thread after every dispatched frame, so a
        # caller can wait for content-based completion (e.g. a multi-channel read
        # collecting one reply frame per channel) instead of a fixed settle delay.
        self._frame_condition = threading.Condition()

        # V3 measurement-stream bookkeeping.
        self._measurement_stream_condition = threading.Condition()
        self._measurement_stream_seq = 0
        self._measurement_stream_received_at = None
        self._measurement_stream_tick = None
        self._measurement_stream_period_ms = None
        self._capture_stream_enabled = False
        self._capture_queue = deque()
        self.measurement_queue_drops = 0
        self.capture_statistics = {}
        self.measurement_filter = 0
        self.measurement_sample_rate = 250
        self._sample_rate_reply = None
        self._capture_reply = None
        self._filter_reply = None
        self._last_v3_status = {}
        self._device_capabilities = None
        self._capabilities_checked = False
        self._protocol_upgrade_warned = False
        self._capability_query_section = None
        self._capability_details_loaded = set()
        self._auth_certificate_response = None
        self._auth_challenge_response = None
        self.authentication_info = None

        # Consecutive ACK failures before an MCU recovery is attempted.
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

        try:
            self._start()
            # Allow a previous partial command to time out in the MCU parser.
            time.sleep(0.15)
            self.get_device_info()

            if self.operate_mode is None:
                logger.error("Failed to read operate mode; device is not responding.")
                raise DeviceConnectionError(
                    f"Device on port {self.port} did not respond to the operate-mode query. "
                    f"The port may not be a SmartUSBHub, or the device is unresponsive.")

            if self.device_address is not None:
                SmartUSBHub._connected_addresses[port] = self.device_address

            logger.info(f"Hardware version: V1.{self.hardware_version}")
            logger.info(f"Firmware version: {self.get_firmware_version_string()}")
            logger.info(f"Operate mode: {'normal' if self.operate_mode == 0 else 'interlock'}")
            logger.info(f"Button control: {'enabled' if self.button_control_status == 1 else 'disabled'}")
        except Exception:
            self.disconnect()
            raise

    def __enter__(self):
        """
        Enter the runtime context and return this instance.

        :returns: self
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context, disconnecting the device.

        :returns: False (exceptions are never suppressed).
        """
        self.disconnect()
        return False

    def close(self):
        """Close the connection. Alias for ``disconnect()``."""
        self.disconnect()

    def _handle_alert_response(self, channel, value):
        if isinstance(value, dict) and value.get("v3") and not value.get("stream"):
            # _dispatch_frame already verifies command + request ID + status.
            self._alert_replies[value["_alert_cmd"]] = bytes(value["payload"])

    def _handle_alert_event(self, channel, value):
        if not isinstance(value, dict) or not value.get("stream"):
            return
        p = value.get("payload", b"")
        if len(p) != 12 or not 1 <= p[8] <= self.max_channels or p[10] > 1 or p[11] > 1:
            return
        event = dict(sequence=int.from_bytes(p[:4], "little"),
                     tick_ms=int.from_bytes(p[4:8], "little"), channel=p[8],
                     causes=p[9], action="power_off_lock" if p[10] else "notify", power=bool(p[11]))
        self.last_alert_event = event
        self._invoke_callback(CMD_ALERT_EVENT, p[8], dict(event))

    def _alert_exchange(self, cmd, payload=b""):
        if self._get_capabilities().get("alerts", {}).get("supported") is not True:
            raise FeatureNotSupportedError("Device does not declare measurement hardware alert support")
        event = self.ack_events[cmd]
        event.clear()
        self._alert_replies.pop(cmd, None)
        self._send_v3_packet(cmd, payload)
        if not event.wait(max(0.5, self.com_timeout)):
            return None
        return self._alert_replies.pop(cmd, None)

    @staticmethod
    def _alert_type(kind):
        try:
            return ALERT_TYPES.index(kind)
        except ValueError:
            raise ValueError("kind must be one of " + ", ".join(ALERT_TYPES)) from None

    @staticmethod
    def _decode_alert_config(p):
        if p is None or len(p) != 14 or p[1] >= len(ALERT_TYPES):
            return None
        return dict(channel=p[0], kind=ALERT_TYPES[p[1]], enabled=bool(p[2]),
                    samples=p[3], action="power_off_lock" if p[4] else "notify",
                    threshold=int.from_bytes(p[6:10], "little"),
                    raw_threshold=int.from_bytes(p[10:14], "little"))

    @synchronized
    def get_alert_config(self, channel, kind):
        """Read the applied comparator rule. Threshold units: mA, mV or mW."""
        if type(channel) is not int or not 1 <= channel <= self.max_channels:
            raise ValueError("Invalid channel")
        return self._decode_alert_config(self._alert_exchange(CMD_ALERT_CONFIG, bytes([channel, self._alert_type(kind)])))

    @synchronized
    def get_alert_defaults(self, channel, kind):
        """Read MCU factory defaults without changing the active rule."""
        if type(channel) is not int or not 1 <= channel <= self.max_channels:
            raise ValueError("Invalid channel")
        return self._decode_alert_config(self._alert_exchange(
            CMD_ALERT_CONFIG, bytes([channel, self._alert_type(kind), 0])))

    @synchronized
    def set_alert_config(self, channel, kind, threshold, enabled=True, samples=1, action="notify"):
        """Set one rule; return applied rule or None on failure.

        USB3 FW1.0.0 persists settings to App Flash before success. Identical settings do not erase Flash.

        power_off_lock disconnects power/data and blocks all power-on paths.
        UC/UV are ignored while off and for100ms after switching on. Comparator
        thresholds are quantized; raw_threshold is the verified register value.
        """
        t = self._alert_type(kind)
        if type(channel) is not int or not 1 <= channel <= self.max_channels:
            raise ValueError("Invalid channel")
        if type(threshold) is not int or not 0 <= threshold < (5000, 5000, 9000, 9000, 45000)[t]:
            raise ValueError("Threshold outside comparator range")
        if type(enabled) is not bool or type(samples) is not int or samples not in (1, 4, 8, 16):
            raise ValueError("enabled must be bool; samples must be1,4,8 or16")
        if action not in ("notify", "power_off_lock"):
            raise ValueError("Invalid alert action")
        payload = bytes([channel, t, enabled, samples, action == "power_off_lock", 0]) + threshold.to_bytes(4, "little")
        # Capture holds the measurement hardware bus at a higher RTOS priority. Configuration
        # needs an uninterrupted threshold/readback/REFRESH session.
        streaming = self._capture_stream_enabled
        if streaming and not self._capture_stream(False):
            raise RuntimeError("无法暂停采集，告警配置未发送")
        try:
            return self._decode_alert_config(self._alert_exchange(CMD_ALERT_CONFIG, payload))
        finally:
            if streaming and not self._capture_stream(True):
                raise RuntimeError("告警配置已处理，但采集恢复失败，请检查采集状态")

    @synchronized
    def get_alert_status(self):
        """Query MCU-cached status without consuming chip read-to-clear registers."""
        p = self._alert_exchange(CMD_GET_ALERT_STATUS)
        if p is None or len(p) != 32 or p[0] != 1:
            return None
        return dict(ready=bool(p[1]), io_fault=bool(p[2]), subscribed=bool(p[3]),
                    sequence=int.from_bytes(p[4:8], "little"), tick_ms=int.from_bytes(p[8:12], "little"),
                    dropped_events=int.from_bytes(p[12:16], "little"),
                    channels={ch+1: dict(active=p[16+4*ch], history=p[17+4*ch],
                              trip=p[18+4*ch], power=bool(p[19+4*ch])) for ch in range(4)})

    def _alert_mask(self, channel_mask):
        if type(channel_mask) is not int or not 1 <= channel_mask < (1 << self.max_channels):
            raise ValueError("Invalid channel mask")
        return bytes([channel_mask])

    @synchronized
    def clear_alert_latch(self, channel_mask):
        """Clear alert history.

        :param int channel_mask: Channel bitmask; bit 0 selects CH1.
        :returns: Whether the device confirmed the mask.
        :rtype: bool
        :raises FeatureNotSupportedError: Alerts are unsupported.
        :raises ValueError: Invalid channel mask."""
        p = self._alert_mask(channel_mask)
        return self._alert_exchange(CMD_CLEAR_ALERT_LATCH, p) == p

    @synchronized
    def reset_protection_trip(self, channel_mask):
        """Unlock off ports only after a fresh healthy monitor read; never powers on.

        A cleared comparator with power off cannot prove a load fault was removed.
        A subsequent power-on is an explicit retry, and may trip again.
        """
        p = self._alert_mask(channel_mask)
        return self._alert_exchange(CMD_RESET_PROTECTION_TRIP, p) == p

    @synchronized
    def subscribe_alert_events(self, enabled=True):
        """Register CMD_ALERT_EVENT callback first; callback runs on receive thread."""
        if type(enabled) is not bool:
            raise ValueError("enabled must be bool")
        p = bytes([enabled])
        return self._alert_exchange(CMD_ALERT_EVENT_SUBSCRIPTION, p) == p

    def set_debug_log_enabled(self, enabled):
        """Subscribe/unsubscribe to MCU-pushed V3 log frames (0x24, STREAM).

        Reply to 0x26 is delivered through register_callback; no ACK recovery.
        Call once per connection and disable before closing the session.
        """
        self._send_v3_packet(CMD_SET_DEBUG_LOG_ENABLE, bytes([bool(enabled)]))

    def request_board_temperature(self):
        """Request board temperature asynchronously; no temperature is returned.

        Register a CMD_GET_DEBUG_TEMPERATURE callback before requesting.
        Logs arrive independently; this request does not enable logging.
        """
        self._send_v3_packet(CMD_GET_DEBUG_TEMPERATURE, b"")

    def register_disconnect_callback(self, callback):
        """Deprecated alias for register_callback("disconnect", callback)."""
        _warn_legacy_api('register_disconnect_callback()', 'register_callback("disconnect", callback)')
        return self.register_callback("disconnect", callback)

    def register_callback(self, cmd, callback):
        """Register a command callback or a host-side disconnect event.

        Command callbacks run on the receive thread with ``(channel, value)``;
        ``value`` is command-specific: an integer, list, or decoded dictionary.
        "disconnect" invokes a zero-argument callback on unexpected connection
        loss, after port cleanup, on the receive thread. Explicit disconnect()
        does not invoke it. Pass None to unregister either kind of callback.
        Each key has one callback; registering again replaces the previous one.
        """
        if cmd == "disconnect":
            if callback is not None and not callable(callback):
                raise TypeError("disconnect callback must be callable or None")
            self.disconnect_callback = callback
            return
        if cmd in self.callbacks:
            self.callbacks[cmd] = callback
            logger.info(f"Callback registered for command {cmd:#04x}")
        else:
            logger.warning(f"Invalid command {cmd:#04x}; cannot register callback.")

    def _invoke_callback(self, cmd, *args, **kwargs):
        """Invoke the registered callback; log its errors without stopping reception."""
        callback = self.callbacks.get(cmd)
        if callback:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback for command {cmd:#04x}: {e}")

    @staticmethod
    def get_product_info(product_type_id):
        """
        Look up product metadata and deprecated legacy capability fields.

        For a connected device use get_capability() to read the MCU declaration.

        :param product_type_id: Product-type ID (see ``PRODUCT_TYPE_TABLE``).

        :returns: The product-info dict, or None if the ID is unknown.
        """
        return PRODUCT_TYPE_TABLE.get(product_type_id)

    def _check_feature_support(self, feature_name):
        """Use device declarations; infer only for legacy firmware."""
        if feature_name not in _FEATURE_CAPABILITY:
            raise FeatureNotSupportedError(f"Unknown feature name: {feature_name}")
        if self.capabilities_source == "legacy":
            if self.product_type is None:
                self.product_type = self.get_product_type()
            if self.product_type not in _LEGACY_PRODUCT_CAPABILITIES:
                raise FeatureNotSupportedError(f"Unknown product type: {self.product_type!r}")
        group = self._get_capabilities()[_FEATURE_CAPABILITY[feature_name]]
        return group.get("supported") is True

    @classmethod
    def scan_available_ports(cls):
        """
        Scan for serial ports whose USB VID/PID match a Smart USB Hub.

        :returns: List of matching port device names.
        """
        return [p.device for p in serial.tools.list_ports.comports()
                if p.vid == 0x1A86 and p.pid == 0xfe0c]

    @classmethod
    def scan_candidates(cls):
        """
        Return structured operating-system metadata for SmartUSBHub CMD ports.

        This method only enumerates USB serial devices; it never opens a port or
        changes device state.  Fields unavailable on a platform are returned as
        ``None``.

        :returns: List of dictionaries containing port, VID/PID and USB
            descriptor metadata.
        """
        candidates = []
        for item in serial.tools.list_ports.comports():
            if item.vid != 0x1A86 or item.pid != 0xfe0c:
                continue
            candidates.append({
                "port": item.device,
                "vid": item.vid,
                "pid": item.pid,
                "serial": getattr(item, "serial_number", None),
                "manufacturer": getattr(item, "manufacturer", None),
                "product": getattr(item, "product", None),
                "description": getattr(item, "description", None),
                "location": getattr(item, "location", None),
                "interface": getattr(item, "interface", None),
                "hwid": getattr(item, "hwid", None),
            })
        candidates.sort(key=lambda value: value["port"])
        return candidates

    @property
    def capabilities_source(self):
        """device / legacy / unavailable; capability absence is never support."""
        if getattr(self, "_device_capabilities", None) is not None:
            return "device"
        if getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN) == V3_HEADER_LEN:
            return "unavailable"
        return "legacy"

    def _legacy_capabilities(self):
        """The sole product/version-based capability adapter."""
        row = _LEGACY_PRODUCT_CAPABILITIES.get(self.product_type, {})
        major = getattr(self, "firmware_version_major", None)
        modern = isinstance(major, int) and major >= 2
        capabilities = {}
        fields = {"measurement": "enable_adc", "usb2_data_switch": "enable_usb2_data_switch",
                  "usb3_data_switch": "enable_usb3_data_switch", "overcurrent": "enable_overcurrent",
                  "upstream_host_switch": "enable_upstream_host_switch",
                  "current_limit_switch": "enable_ilim_switch"}
        for name, field in fields.items():
            supported = bool(row.get(field, False))
            controllable = supported
            if name == "upstream_host_switch":
                controllable = supported and isinstance(major, int) and major >= 3
            elif name == "current_limit_switch":
                controllable = False
            capabilities[name] = dict(supported=supported, controllable=controllable)
        capabilities["measurement"]["stream"] = modern and capabilities["measurement"]["supported"] and not self._uses_legacy_measurement_queries()
        version = (major or 0, getattr(self, "firmware_version_minor", 0) or 0)
        batch = self.product_type == 0x04 and version >= (3, 13)
        capabilities["measurement"]["capture"] = batch
        capabilities["measurement"]["sample_rates"] = ([10, 100, 500] if version >= (3, 14) else [500]) if batch else []
        capabilities["measurement"]["filters"] = ["instant", "avg8"] if batch else []
        for name in ("power", "auto_restore", "interlock"):
            capabilities[name] = dict(supported=True, controllable=True)
        for name in ("identify", "device_alias", "channel_names"):
            capabilities[name] = dict(supported=modern, controllable=modern)
        # Legacy firmware does not declare these. UI may use a legacy probe.
        for name in ("board_temperature", "button_control", "authentication", "debug_log"):
            capabilities[name] = dict(supported=None, controllable=False)
        capabilities["board_temperature"]["readable"] = None
        return capabilities

    def _get_capabilities(self):
        """Return cached capability declarations or the legacy compatibility view.

        Missing fields on a declaring device remain unknown (supported=None),
        never backfilled from its model. Returned values are independent copies.
        :returns: Capability entries with supported and controllable fields.
        :rtype: dict
        """
        if self.capabilities_source == "legacy":
            return self._legacy_capabilities()
        remote = getattr(self, "_device_capabilities", None) or {}
        capabilities = {}
        for name in set(_CAPABILITY_NAMES) | (set(remote) - {"schema", "channels", "detail_groups", "section", "model", "protocol"}):
            value = remote.get(name)
            if type(value) is bool:
                capabilities[name] = dict(supported=value, controllable=value and name in _CAPABILITY_NAMES)
            elif isinstance(value, dict) and type(value.get("supported")) is bool:
                capabilities[name] = copy.deepcopy(value)
                capabilities[name].setdefault("controllable", False)
                if name not in _CAPABILITY_NAMES:
                    capabilities[name]["controllable"] = False
            else:
                capabilities[name] = dict(supported=None, controllable=False)
        # These capabilities have no public SDK configuration method.
        for name in ("board_temperature", "current_limit_switch"):
            capabilities[name]["controllable"] = False
        if isinstance(remote.get("protocol"), dict):
            capabilities["protocol"] = copy.deepcopy(remote["protocol"])
        return capabilities

    def _handle_capabilities(self, channel, value):
        if not isinstance(value, dict) or not value.get("v3"):
            return
        try:
            data = json.loads(value["payload"].decode("utf-8"))
            if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != 1:
                return
            section = data.get("section")
            expected = getattr(self, "_capability_query_section", None)
            if section != expected:
                return
            if section is not None:
                if section not in ("measurement", "alerts", "device") or self._device_capabilities is None:
                    return
                detail = data.get(section)
                if not isinstance(detail, dict) or type(detail.get("supported")) is not bool:
                    return
                original = self._device_capabilities.get(section, {})
                if original and detail["supported"] != original.get("supported"):
                    return  # A detail/readiness reply cannot change the declaration.
                if "specs" in detail and not isinstance(detail["specs"], dict):
                    return
                if "source" in detail and detail["source"] is not None and not isinstance(detail["source"], str):
                    return
                # Specifications cannot override the summary's functional flags.
                self._device_capabilities.setdefault(section, {"supported": detail["supported"]})
                for key in detail:
                    if key not in original or key in ("source", "specs"):
                        self._device_capabilities[section][key] = copy.deepcopy(detail[key])
                self._capability_details_loaded.add(section)
                return
            for key in ("measurement", "board_temperature"):
                group = data.get(key)
                if not isinstance(group, dict) or type(group.get("supported")) is not bool:
                    return
            for key in _CAPABILITY_NAMES:
                if key not in data:
                    continue
                group = data[key]
                if type(group) is bool:
                    continue
                if not isinstance(group, dict) or type(group.get("supported")) is not bool:
                    return
                if "controllable" in group and type(group["controllable"]) is not bool:
                    return
            if "channels" in data and (type(data["channels"]) is not int or not 1 <= data["channels"] <= 16):
                return
            groups = data.get("detail_groups", [])
            if not isinstance(groups, list) or not all(isinstance(name, str) for name in groups):
                return
            self._device_capabilities = data
            self._capability_details_loaded = set()
        except (KeyError, UnicodeDecodeError, ValueError, TypeError):
            logger.warning("Invalid device capability JSON")

    def _query_device_capabilities(self):
        if getattr(self, "_capabilities_checked", False):
            return
        if getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN) != V3_HEADER_LEN:
            self._capabilities_checked = True
            return
        event = self.ack_events[CMD_GET_CAPABILITIES]
        def query(section=None):
            self._capability_query_section = section
            try:
                for _ in range(2):
                    event.clear()
                    self._send_v3_packet(CMD_GET_CAPABILITIES, section.encode("ascii") if section else b"")
                    if event.wait(max(0.3, self.com_timeout)):
                        if section is None and self._device_capabilities is not None:
                            return
                        if section in self._capability_details_loaded:
                            return
                    if event.protocol_status in (V3_STATUS_UNSUPPORTED_COMMAND, V3_STATUS_UNSUPPORTED_FEATURE):
                        return
            finally:
                self._capability_query_section = None
        query()
        if self._device_capabilities is not None:
            advertised = self._device_capabilities.get("detail_groups", [])
            for section in ("measurement", "device", "alerts"):
                if section in advertised and self._device_capabilities.get(section, {}).get("supported", True):
                    query(section)
        self._capabilities_checked = True

    @synchronized
    def get_capability(self, refresh=False):
        """Return the MCU JSON document with advertised details merged.

        No legacy/model-derived flags are added. None means no MCU declaration.
        refresh=True requests the summary and known advertised sections again.
        :param bool refresh: Query the declaration again.
        :returns: Independent MCU declaration, or None.
        :rtype: dict or None
        """
        previous = getattr(self, "_device_capabilities", None)
        if refresh:
            self._device_capabilities = None
            self._capabilities_checked = False
        self._query_device_capabilities()
        document = getattr(self, "_device_capabilities", None)
        if document is None and refresh:
            self._device_capabilities = previous
        return copy.deepcopy(document)

    def get_identity(self):
        """
        Return cached device identity using raw values suitable for JSON.

        Unlike :meth:`get_device_info`, unavailable values remain ``None``
        rather than being formatted as ``"N/A"``.
        """
        product_info = PRODUCT_CATALOG.get(self.product_type)
        return {
            "port": self.port,
            "serial": (None if self.serial_no in (None, "", "N/A") else self.serial_no),
            "address": self.device_address,
            "alias": self.device_alias or None,
            "product_type": self.product_type,
            "model": self._declared_model() or (product_info.get("name") if product_info else None),
            "channels": self.max_channels,
            "hardware_version": self.hardware_version,
            "firmware_version_major": self.firmware_version_major,
            "firmware_version_minor": self.firmware_version_minor,
            "operate_mode": (
                "normal" if self.operate_mode == OPERATE_MODE_NORMAL
                else "interlock" if self.operate_mode == OPERATE_MODE_INTERLOCK
                else None
            ),
            "auto_restore": (
                bool(self.auto_restore_status)
                if self.auto_restore_status is not None else None
            ),
            "button_control": (
                bool(self.button_control_status)
                if self.button_control_status is not None else None
            ),
        }

    @classmethod
    def scan_and_connect(cls, exclude_ports=None, device_address=None):
        """
        Scan for Smart USB Hub devices and connect to the first valid one.

        :param exclude_ports: Set of ports to skip; defaults to ports already connected.

        :param device_address: If given, only connect to a device reporting this address. Note: addresses default to 0, so multiple devices may share one; prefer selecting by port. See :meth:`scan_and_connect_by_address`.

        :returns: A connected SmartUSBHub instance, or None if none was found.
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()

        for port_info in serial.tools.list_ports.comports():
            port_name = port_info.device
            if port_name in exclude_ports:
                logger.debug(f"Skipping already connected port {port_name}")
                continue
            if port_info.vid != 0x1A86 or port_info.pid != 0xfe0c:
                continue

            logger.debug(f"Trying to connect to port {port_name}")
            try:
                hub = cls(port_name)
                if device_address is not None and hub.device_address != device_address:
                    logger.debug(f"Address mismatch on {port_name}: "
                                 f"expected {device_address:#04x}, got {hub.device_address:#04x}")
                    hub.disconnect()
                    continue
                if device_address is not None:
                    logger.info(f"Found device with address {device_address:#04x} on port {port_name}")
                return hub
            except (SmartUSBHubError, serial.SerialException) as e:
                logger.warning(f"Failed to connect to {port_name}: {e}")
                continue

        if device_address is not None:
            logger.warning(f"No Smart USB Hub found with address {device_address:#04x}, "
                           f"or all devices are already connected.")
        else:
            logger.warning("No Smart USB Hub found, or all devices are already connected.")
        return None

    @classmethod
    def scan_and_connect_by_address(cls, device_address):
        """
        Connect to a Smart USB Hub by device address.

        .. warning::

           Addresses default to 0, so multiple devices may share one address, making this selection unreliable. Use ``SmartUSBHub(port)`` to select a serial port, or assign distinct addresses first.

        :param device_address: Device address to match (0x0000 - 0xFFFF).

        :returns: A connected SmartUSBHub instance, or None if no match was found.
        """
        _warn_legacy_api('scan_and_connect_by_address()', 'scan_and_connect(device_address=...)')
        return cls.scan_and_connect(device_address=device_address)

    @classmethod
    def auto_connect(cls, exclude_ports=None, feature_filter=None):
        """
        Scan and connect to the first available device, skipping busy ones.

        Busy or failing ports are skipped, as in :meth:`scan_and_connect`.

        :param exclude_ports: Set of ports to skip; defaults to ports already connected.

        :param feature_filter: If given, only connect to a device supporting this feature (see ``_check_feature_support`` for valid names).

        :returns: A connected SmartUSBHub instance, or None if none is available.
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()

        ports = cls.scan_available_ports()
        if not ports:
            logger.warning("No Smart USB Hub devices found")
            return None

        logger.info(f"Found {len(ports)} device(s): {ports}")
        for port in ports:
            if port in exclude_ports:
                logger.debug(f"Skipping already connected port {port}")
                continue

            logger.info(f"Trying to connect to {port}...")
            try:
                hub = cls(port)
            except PortBusyError:
                logger.info(f"Port {port} is already in use, trying next device...")
                continue
            except (SmartUSBHubError, serial.SerialException) as e:
                logger.warning(f"Failed to connect to {port}: {e}, trying next device...")
                continue

            logger.info(f"Successfully connected to {port}")
            if feature_filter is not None and not hub._check_feature_support(feature_filter):
                logger.info(f"Device on {port} does not support '{feature_filter}', trying next device...")
                hub.disconnect()
                continue
            return hub

        logger.warning("All devices are unavailable (occupied or connection failed)")
        return None

    def _start(self):
        """
        Start the background receive thread.

        The daemon thread allows interpreter shutdown; ``disconnect`` and the
        atexit hook handle connection cleanup.
        """
        self.stop_event = threading.Event()
        self.uart_recv_thread = threading.Thread(
            target=self._uart_recv_task, name=f"{self.name}-rx", daemon=True)
        self.uart_recv_thread.start()

    def disconnect(self):
        """
        Disconnect from the device and stop the receive thread.

        Idempotent and safe to call multiple times (e.g. via context-manager exit
        and atexit). Releases the process-local port registration and any held
        cross-process coordination lock.
        """
        # Claim cleanup once, including concurrent explicit and receive failures.
        # A closed instance must never release a later connection's port lock.
        with self._lifecycle_lock:
            if getattr(self, '_disconnect_started', False):
                return
            self._disconnect_started = True

        stop_event = getattr(self, 'stop_event', None)
        if stop_event is not None:
            stop_event.set()

        thread = getattr(self, 'uart_recv_thread', None)
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1)

        ser = getattr(self, 'ser', None)
        if ser is not None and ser.is_open:
            try:
                ser.flush()
            except Exception:
                pass
            # Closing must still be attempted when flushing an unplugged serial
            # device raises.  Otherwise the OS handle can survive long enough to
            # make the immediate reconnect fail even after registry cleanup.
            try:
                ser.close()
            except Exception:
                pass
        self.ser = None
        if hasattr(self, "_v3_lock"):
            with self._v3_lock:
                self._v3_pending.clear()
                getattr(self, "_v3_async_deadlines", {}).clear()
                self._v3_header_len = V3_LEGACY_HEADER_LEN
                self._v3_protocol_known = False
                self._device_capabilities = None
                self._capabilities_checked = False
                self._capability_query_section = None
                self._capability_details_loaded.clear()

        with self._lifecycle_lock:
            SmartUSBHub._connected_ports.discard(self.port)
            SmartUSBHub._connected_addresses.pop(self.port, None)
            SmartUSBHub._instances.discard(self)
            self._release_port_lock(self.port)

    def is_connected(self):
        """
        Report whether the serial port is currently open.

        :returns: True if connected, False otherwise.
        """
        ser = getattr(self, 'ser', None)
        return bool(ser and ser.is_open)

    def _cal_crc16(self, data):
        """Compute a CRC16 (poly 0x8005, init 0xFFFF). See ``_Codec.crc16``."""
        return _Codec.crc16(data)

    def _parse_protocol_frame(self, data):
        """
        Parse one frame from the front of a received byte buffer (V1/V2/V3).

        Thin wrapper over ``_Codec.parse_frame``; see there for the frame layouts
        and the return shape.
        """
        return _Codec.parse_frame(data, header_len=getattr(self, "_v3_header_len", V3_HEADER_LEN))

    def _uart_recv_task(self):
        """
        Background loop that reads the serial link and dispatches complete frames.

        Runs until ``stop_event`` is set or the serial link fails. On an unexpected
        disconnect the registered disconnect callback (if any) is invoked.
        """
        reader = _FrameReader(header_len=getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN))
        while not self.stop_event.is_set():
            try:
                self._expire_async_v3_requests()
                reader.header_len = getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN)
                incoming = b""
                if self.ser is not None and self.ser.in_waiting > 0:
                    incoming = self.ser.read(self.ser.in_waiting)
                for cmd, channel, value, length in reader.feed(incoming):
                    self._dispatch_frame(cmd, channel, value)
            except (OSError, AttributeError, serial.SerialException) as e:
                # ENXIO also occurs on an unexpected USB disappearance. Only
                # an explicit stop makes a receive failure expected.
                is_expected = self.stop_event.is_set()

                if is_expected:
                    logger.debug(f"UART disconnected (expected): {e}")
                else:
                    logger.error("Error reading from UART port=%s errno=%s: %s",
                                 self.port, getattr(e, "errno", None), e,
                                 exc_info=True)

                # A failed receive loop must perform the same lifecycle cleanup
                # as an explicit disconnect.  Merely dropping ``self.ser`` leaves
                # the process-local port registry and cross-process lock held, so
                # every later reconnect is rejected as busy until the process
                # exits.  Capture the callback first because disconnect is also
                # allowed to clear it in future implementations.
                disconnect_callback = self.disconnect_callback
                self.disconnect_callback = None
                self.disconnect()
                if not is_expected and disconnect_callback:
                    disconnect_callback()
                if not is_expected:
                    logger.error("UART disconnected")
                break
            time.sleep(self._rx_poll_interval)

    def _handle_protocol_format(self, channel, value):
        self._protocol_format_reply = (channel, value)

    def _negotiate_v3_protocol(self):
        if getattr(self, "_v3_protocol_known", False):
            return
        event = self.ack_events[CMD_GET_PROTOCOL_FORMAT]
        for _ in range(2):
            event.clear()
            self._protocol_format_reply = None
            self._send_packet(CMD_GET_PROTOCOL_FORMAT, None, 0)
            if event.wait(max(0.2, self.com_timeout)):
                if self._protocol_format_reply not in ((3, V3_HEADER_LEN), (255, 255)):
                    raise DeviceConnectionError("Unsupported V3 protocol format")
                self._v3_header_len = V3_HEADER_LEN if self._protocol_format_reply == (3, V3_HEADER_LEN) else V3_LEGACY_HEADER_LEN
                self._v3_protocol_known = True
                return
        # Legacy devices may silently ignore this read-only command.
        self._v3_protocol_known = True

    def _dispatch_frame(self, cmd, channel, value):
        if isinstance(value, dict) and "request_id" in value:
            with self._v3_lock:
                self._expire_async_v3_requests()
                if value["flags"] == V3_FLAG_REQUEST:
                    return
                if not value["stream"]:
                    pending = self._v3_pending.get(cmd)
                    # Serial bodies solicited by a V1 query have no request ID.
                    v1_serial = (cmd == CMD_GET_SERIAL_NO and value["request_id"] == 0
                                 and pending is None)
                    if not v1_serial and pending != value["request_id"]:
                        logger.debug("Discarding unmatched V3 response cmd=%02X id=%s", cmd, value["request_id"])
                        return
                    if not v1_serial:
                        self._cancel_v3_request(cmd, pending)
                    self._last_v3_status[cmd] = value["status"]
                    if value["status"] != V3_STATUS_OK:
                        if cmd == CMD_AUTH_GET_CERTIFICATE:
                            self._auth_certificate_response = value["payload"]
                        elif cmd == CMD_AUTH_CHALLENGE:
                            self._auth_challenge_response = value["payload"]
                        self.last_protocol_error = {"cmd": cmd, "request_id": value["request_id"],
                                                    "status": value["status"]}
                        self._last_v3_status[cmd] = value["status"]
                        event = self.ack_events.get(cmd)
                        if event is not None:
                            event.protocol_status = value["status"]
                            event.set()
                        # Deliver diagnostics to callback-only consumers (e.g. board
                        # temperature), while keeping success caches untouched.
                        self._invoke_callback(cmd, channel, value)
                        return
                    self.last_protocol_error = None
                self._dispatch_frame_impl(cmd, channel, value)
        else:
            self._dispatch_frame_impl(cmd, channel, value)

    def _dispatch_frame_impl(self, cmd, channel, value):
        """
        Route one decoded frame to its state handler and ACK / wake sinks.

        This is the seam between the transport (read + frame the bytes) and the
        session (update state, satisfy waiters). Called only from the receive
        thread, one call per complete frame.
        """
        # Persistent V1/V2 setters retain their success frames. Firmware uses
        # out-of-domain values to report a failed save; such replies acknowledge
        # receipt without claiming that the configuration was stored.
        if cmd in (CMD_SET_OPERATE_MODE, CMD_SET_BUTTON_CONTROL, CMD_SET_AUTO_RESTORE):
            self.ack_events[cmd].response_ok = channel == 0 and value in (0, 1)
        elif cmd in (CMD_SET_DEFAULT_POWER_STATUS, CMD_SET_DEFAULT_DATALINE_STATUS):
            self.ack_events[cmd].response_ok = (isinstance(value, list) and len(value) == 2
                                                 and all(v in (0, 1) for v in value))
        elif cmd == CMD_FACTORY_RESET:
            self.ack_events[cmd].response_ok = channel == 0 and value == 0
        if cmd in self._STATUS_MASK_QUERIES:
            if not self._handle_channel_status_mask(cmd, channel, value):
                return
        if cmd in self._DEFAULT_MASK_QUERIES:
            if not self._handle_default_status_mask(cmd, channel, value):
                return
        handler = self._frame_handlers.get(cmd)
        if handler is not None:
            if cmd in (CMD_ALERT_CONFIG, CMD_GET_ALERT_STATUS, CMD_CLEAR_ALERT_LATCH, CMD_ALERT_EVENT_SUBSCRIPTION, CMD_RESET_PROTECTION_TRIP) and isinstance(value, dict):
                value = dict(value, _alert_cmd=cmd)
            handler(channel, value)

        # Stream frames are unsolicited notifications and must not satisfy a
        # pending ACK wait.
        is_stream_notify = (isinstance(value, dict)
                            and value.get("v3") and value.get("stream"))
        if cmd == CMD_DEBUG_LOG and is_stream_notify:
            self._invoke_callback(cmd, channel, value)
        if cmd in self.ack_events and not is_stream_notify:
            self._invoke_callback(cmd, channel, value)
            self.ack_events[cmd].set()

        # Wake anyone waiting for content-based completion (see
        # _wait_for_channel_cache); cheap and unconditional.
        with self._frame_condition:
            self._frame_condition.notify_all()

    def _wait_for_channel_cache(self, cache, channels, timeout=None, additional_caches=()):
        """
        Block until every channel in ``channels`` is present in ``cache``, or timeout.

        The receiver notifies ``_frame_condition`` after each frame. Callers must
        remove existing entries for these channels before sending the query.
        Legacy V1/V2 replies have no request ID, so a late reply from an earlier
        query can still populate the cache.

        :param cache: Per-channel state dict the receive thread populates.

        :param channels: Channels that must all be present.

        :param timeout: Max wait in seconds; defaults to ``self.com_timeout``.

        :param additional_caches: Other per-channel dictionaries that must also
            contain every requested channel (e.g. default enable/value pairs).

        :returns: True if all channels arrived, False on timeout.
        """
        if timeout is None:
            timeout = self.com_timeout
        deadline = time.monotonic() + timeout
        with self._frame_condition:
            while not all(ch in current for current in (cache,) + additional_caches
                          for ch in channels):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._frame_condition.wait(remaining)
        return True

    def _convert_channel(self, channel_mask):
        """
        Convert a channel bitmask into a list of 1-based channel numbers.

        :param channel_mask: Bitmask (bit0 = channel 1, bit1 = channel 2, ...).

        :returns: List of channel numbers present in the mask.
        """
        channels = []
        ch = 1
        while channel_mask:
            if channel_mask & 0x01:
                channels.append(ch)
            channel_mask >>= 1
            ch += 1
        return channels

    def _send_packet(self, cmd, channels, data=None):
        """
        Build and send a V1/V2 packet to the device.

        Serializes writes and applies the configured minimum write interval and
        post-write settle delay, independently of ``ENABLE_SYNC_LOCK``.

        :param cmd: Command byte.

        :param channels: Channel list, or the raw address high byte for CMD_SET_DEVICE_ADDRESS.

        :param data: Extra payload byte(s); defaults to a single 0x00 byte.

        :returns: The bytearray that was written.
        """
        if cmd == CMD_SET_DEVICE_ADDRESS:
            channel_mask = channels
        elif channels is None:
            channel_mask = 0
        else:
            channel_mask = self._channel_mask(channels)

        if data is None:
            data = [0x00]
        elif not isinstance(data, list):
            data = [data]

        packet = _Codec.encode_v1v2(cmd, channel_mask, data)

        with self._send_lock:
            elapsed = time.time() - self._last_send_time
            if elapsed < self._min_send_interval:
                time.sleep(self._min_send_interval - elapsed)
            if self.ser and self.ser.is_open:
                self.ser.write(packet)
            self._last_send_time = time.time()
            time.sleep(self._mcu_response_wait)
            logger.debug(f"Sent command: {packet.hex()}")
        return packet

    def _cancel_v3_request(self, cmd, request_id):
        with self._v3_lock:
            if self._v3_pending.get(cmd) == request_id:
                self._v3_pending.pop(cmd, None)
                getattr(self, "_v3_async_deadlines", {}).pop(cmd, None)

    def _track_async_v3_request(self, cmd):
        """Retire fire-and-forget requests even when nobody calls Event.wait()."""
        if getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN) != V3_HEADER_LEN:
            return
        with self._v3_lock:
            request_id = self._v3_pending.get(cmd)
            if request_id is not None:
                self._v3_async_deadlines[cmd] = (request_id, time.monotonic() + self.com_timeout)

    def _expire_async_v3_requests(self):
        deadlines = getattr(self, "_v3_async_deadlines", {})
        if not deadlines:
            return
        with self._v3_lock:
            now = time.monotonic()
            for cmd, (request_id, deadline) in list(deadlines.items()):
                if now >= deadline:
                    self._cancel_v3_request(cmd, request_id)
                    deadlines.pop(cmd, None)

    def _send_v3_packet(self, cmd, payload=b""):
        """
        Build and send a V3 packet to the device.

        :param cmd: Command byte.

        :param payload: Payload as bytes, bytearray, list of ints, or a single int.

        :returns: The bytearray that was written.

        :raises ValueError: If the payload exceeds ``V3_MAX_DATA_LEN.``
        """
        header_len = getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN)
        request_id = 1
        if header_len == V3_HEADER_LEN:
            with self._v3_lock:
                self._expire_async_v3_requests()
                # Callback-only diagnostic polls may replace a lost earlier poll.
                if (cmd in self._v3_pending and cmd in self.ack_events and
                        cmd not in (CMD_GET_DEBUG_TEMPERATURE, CMD_SET_DEBUG_LOG_ENABLE)):
                    raise SmartUSBHubError(f"V3 command 0x{cmd:02X} is already awaiting a response")
                now = time.monotonic()
                if not hasattr(self, "_v3_recent_order"):
                    self._v3_recent_order = deque()
                while self._v3_recent_order and now - self._v3_recent_order[0][1] >= 60:
                    expired_id, _ = self._v3_recent_order.popleft()
                    self._v3_recent_ids.pop(expired_id, None)
                active = set(self._v3_pending.values())
                for _ in range(65535):
                    request_id = self._v3_next_id
                    self._v3_next_id = request_id % 65535 + 1
                    if request_id not in active and request_id not in self._v3_recent_ids:
                        break
                else:
                    raise SmartUSBHubError("V3 request IDs temporarily exhausted")
                # Encode before publication so invalid arguments leave no pending request.
                packet = _Codec.encode_v3(cmd, payload, request_id=request_id)
                self._v3_pending[cmd] = request_id
                self._v3_recent_ids[request_id] = now
                self._v3_recent_order.append((request_id, now))
                self.last_protocol_error = None
                event = self.ack_events.get(cmd)
                if event is not None:
                    event.clear()
                    event.on_timeout = lambda: self._cancel_v3_request(cmd, request_id)
        else:
            packet = _Codec.encode_v3(cmd, payload, header_len=header_len)
        if cmd == CMD_GET_CHANNEL_MEASUREMENTS:
            event = self.ack_events.get(cmd)
            if event is not None:
                flags = packet[header_len + 1] if len(packet) == header_len + 2 else 0
                event.measurement_control_ack = {
                    V3_MEAS_FLAG_STREAM_ENABLE: b"\x01",
                    V3_MEAS_FLAG_STREAM_DISABLE: b"\x00",
                }.get(flags)
        try:
            with self._send_lock:
                elapsed = time.time() - self._last_send_time
                if elapsed < self._min_send_interval:
                    time.sleep(self._min_send_interval - elapsed)
                if self.ser and self.ser.is_open:
                    written = self.ser.write(packet)
                    if written != len(packet):
                        raise DeviceConnectionError("Incomplete V3 serial write")
                self._last_send_time = time.time()
                time.sleep(self._mcu_response_wait)
        except Exception:
            if header_len == V3_HEADER_LEN:
                with self._v3_lock:
                    if self._v3_pending.get(cmd) == request_id:
                        self._v3_pending.pop(cmd, None)
            raise
        return packet

    def _wait_for_ack_with_recovery(self, cmd, timeout=None):
        """
        Wait for a command ACK, triggering MCU recovery after repeated failures.

        The caller must clear ``self.ack_events[cmd]`` immediately before sending
        the command (the same discipline the get_* methods follow). This wait then
        consumes exactly that command's ACK and clears the event again on success,
        so a satisfied ACK is consumed before the next wait. Current V3 also
        matches request IDs and retires timed-out requests; clearing an Event
        alone cannot distinguish late replies on legacy V1/V2 or non-current framing.

        :param cmd: Command code to wait on.

        :param timeout: Wait timeout in seconds; defaults to ``self.com_timeout``.

        :returns: True on an accepted ACK, False on rejection or timeout.
        """
        if timeout is None:
            timeout = self.com_timeout

        ack_event = self.ack_events.get(cmd)
        if not ack_event:
            return False

        # The event was cleared before the send, so a set flag means this command's
        # ACK arrived (possibly between the send and this wait, in which case wait()
        # returns at once). Clear it again so the next reuse starts clean.
        if ack_event.wait(timeout):
            ack_event.clear()
            self._consecutive_failures = 0
            return True

        if (getattr(ack_event, "protocol_status", V3_STATUS_OK) != V3_STATUS_OK
                or not getattr(ack_event, "response_ok", True)):
            return False
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._max_consecutive_failures:
            logger.warning(f"Too many consecutive failures ({self._consecutive_failures}); "
                           f"triggering MCU recovery...")
            self._trigger_mcu_recovery()
            self._consecutive_failures = 0
        return False

    def _trigger_mcu_recovery(self):
        """Give the MCU state machine time to recover and flush stale input."""
        logger.debug("Triggering MCU state-machine recovery...")
        time.sleep(0.15)  # Allow the MCU parser to time out a partial command.
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    self.ser.reset_input_buffer()
                    logger.debug("Cleared input buffer during recovery")
            except Exception as e:
                logger.warning(f"Failed to clear input buffer: {e}")

    # Frame handlers update cached state or response validity. The dispatcher
    # invokes callbacks and signals ACK events for command replies.
    def _handle_set_operate_mode(self, channel, value):
        """Log a set-operate-mode ACK; mode is refreshed by its query handler."""
        logger.debug("set_operate_mode ACK")

    def _handle_get_operate_mode(self, channel, value):
        """Cache the operating mode from a get-operate-mode reply."""
        self.operate_mode = value

    def _handle_set_channel_power_status(self, channel, value):
        """Validate a set-channel-power ACK without updating cached power state."""
        self.ack_events[CMD_SET_CHANNEL_POWER].response_ok = value in (0, 1)
        logger.debug("set_channel_power ACK: %s", value)

    def _handle_get_channel_power_status(self, channel, value):
        """Cache per-channel power state from a status reply."""
        if value not in (0, 1):
            return
        for ch in self._convert_channel(channel):
            self.channel_power_status[ch] = value
            logger.debug(f"power status: ch{ch} = {value}")

    def _handle_channel_status_mask(self, cmd, low, high):
        """Expand a validated whole-device V1 mask and preserve status callbacks."""
        if type(low) is not int or type(high) is not int:
            return False
        channels = self._resolve_channels(())
        count = len(channels)
        mask = low | (high << 8)
        if not 1 <= count <= 16 or mask & ~((1 << count) - 1):
            return False
        legacy_cmd, cache_name = self._STATUS_MASK_QUERIES[cmd]
        values = {ch: (mask >> (ch - 1)) & 1 for ch in channels}
        getattr(self, cache_name).update(values)
        for ch, state in values.items():
            self._invoke_callback(legacy_cmd, 1 << (ch - 1), state)
        return True

    def _get_channel_status(self, mask_cmd, channels):
        """Use declared aggregate queries, otherwise collect fresh legacy replies."""
        channels = self._resolve_channels(channels)
        available = self._resolve_channels(())
        if any(type(ch) is not int or ch not in available for ch in channels):
            raise ValueError("Invalid channel number")
        channels = tuple(dict.fromkeys(channels))
        legacy_cmd, cache_name = self._STATUS_MASK_QUERIES[mask_cmd]
        cache = getattr(self, cache_name)
        aggregate = (getattr(self, "_device_capabilities", None) or {}).get("channel_status_mask") is True
        if not aggregate and any(ch > 8 for ch in channels):
            raise FeatureNotSupportedError("Legacy status queries support channels 1 through 8")
        for ch in channels:
            cache.pop(ch, None)
        if aggregate:
            event = self.ack_events[mask_cmd]
            event.clear()
            self._send_packet(mask_cmd, None, 0)
            if not event.wait(self.com_timeout):
                logger.error("Status mask query 0x%02X timed out", mask_cmd)
                return None
        else:
            self._send_packet(legacy_cmd, channels)
            if not self._wait_for_channel_cache(cache, channels):
                missing = [ch for ch in channels if ch not in cache]
                logger.error("Status query 0x%02X timed out, missing channels %s", legacy_cmd, missing)
        return self._filter_channel_dict(cache, channels) or None

    def _handle_default_status_mask(self, cmd, low, data):
        """Expand a 24-bit default configuration with two bits per channel."""
        if type(low) is not int or not isinstance(data, list) or len(data) != 2:
            return False
        channels = self._resolve_channels(())
        packed = low | (data[0] << 8) | (data[1] << 16)
        if not 1 <= len(channels) <= 12 or packed >> (2 * len(channels)):
            return False
        legacy_cmd, flags_name, values_name = self._DEFAULT_MASK_QUERIES[cmd]
        flags, values = getattr(self, flags_name), getattr(self, values_name)
        flags.update({ch: (packed >> (2 * (ch - 1))) & 1 for ch in channels})
        values.update({ch: (packed >> (2 * (ch - 1) + 1)) & 1 for ch in channels})
        if cmd == CMD_GET_DEFAULT_USB3_DATALINE_MASK:
            # Current USB3 callback consumers use the old V3 payload shape.
            # That interface addresses up to eight channels.
            if len(channels) <= 8:
                payload = bytes([(1 << len(channels)) - 1,
                                 sum(flags[ch] << (ch - 1) for ch in channels),
                                 sum(values[ch] << (ch - 1) for ch in channels)])
                self._invoke_callback(legacy_cmd, 0, {
                    "v3": True, "stream": False, "payload": payload,
                    "request_id": 0, "status": V3_STATUS_OK,
                    "flags": V3_FLAG_RESPONSE, "transport": "v2",
                })
        else:
            for ch in channels:
                self._invoke_callback(legacy_cmd, 1 << (ch - 1), [flags[ch], values[ch]])
        return True

    def _get_default_status(self, cmd, channels, flags, values, mask_cmd):
        """Wait for all fresh default enable/value pairs, preserving partial results."""
        channels = self._resolve_channels(channels)
        available = self._resolve_channels(())
        if any(type(ch) is not int or ch not in available for ch in channels):
            raise ValueError("Invalid channel number")
        channels = tuple(dict.fromkeys(channels))
        device = (getattr(self, "_device_capabilities", None) or {}).get("device", {})
        aggregate = isinstance(device, dict) and device.get("default_status_mask") is True
        if aggregate and len(available) > 12:
            raise FeatureNotSupportedError("Aggregate default queries support up to 12 channels")
        if not aggregate and any(ch > 8 for ch in channels):
            raise FeatureNotSupportedError("Legacy default queries support channels 1 through 8")
        for ch in channels:
            flags.pop(ch, None)
            values.pop(ch, None)
        if aggregate:
            event = self.ack_events[mask_cmd]
            event.clear()
            self._send_packet(mask_cmd, None, 0)
            if not event.wait(self.com_timeout):
                logger.error("Default mask query 0x%02X timed out", mask_cmd)
                return None
        else:
            self._send_packet(cmd, channels, [0, 0])
            if not self._wait_for_channel_cache(flags, channels, additional_caches=(values,)):
                missing = [ch for ch in channels if ch not in flags or ch not in values]
                logger.error("Default query 0x%02X timed out, missing channels %s", cmd, missing)
        return {ch: {"enabled": flags[ch], "value": values[ch]}
                for ch in channels if ch in flags and ch in values} or None

    def _handle_power_interlock_control(self, channel, value):
        """Validate a power-interlock ACK without updating cached power state."""
        self.ack_events[CMD_SET_CHANNEL_POWER_INTERLOCK].response_ok = value in (0, 1)
        logger.debug("power_interlock ACK: %s", value)

    def _handle_oc_status(self, channel, value):
        """
        Update per-channel overcurrent state from an OC status frame.

        :param channel: Active-OC bitmask (FLAG# currently asserted).

        :param value: Latched-OC bitmask (sticky until cleared).
        """
        active_mask, latch_mask = channel, value
        logger.debug(f"OC status: active=0x{active_mask:02X} latch=0x{latch_mask:02X}")
        n = self.max_channels if isinstance(self.max_channels, int) and 0 < self.max_channels <= 16 else 7
        for ch in range(1, n + 1):
            idx = ch - 1
            self.channel_oc_active[ch] = bool(active_mask & (1 << idx))
            self.channel_oc_latch[ch] = bool(latch_mask & (1 << idx))

    def _handle_get_channel_voltage(self, channel, value):
        """Cache per-channel voltage (mV) from a V2 voltage reply."""
        if isinstance(value, list) and len(value) == 2:
            mv = (value[0] << 8) | value[1]
            for ch in self._convert_channel(channel):
                self.channel_voltages[ch] = mv
                logger.debug(f"voltage: ch{ch} = {mv} mV")
        else:
            logger.error("Invalid voltage value received")

    def _handle_get_channel_current(self, channel, value):
        """Cache per-channel current (mA) from a V2 current reply."""
        if isinstance(value, list) and len(value) == 2:
            ma = (value[0] << 8) | value[1]
            for ch in self._convert_channel(channel):
                self.channel_currents[ch] = ma
                logger.debug(f"current: ch{ch} = {ma} mA")
        else:
            logger.error("Invalid current value received")

    def _handle_get_channel_measurements(self, channel, value):
        """Route a measurement frame to the V3 or legacy decoder."""
        if isinstance(value, dict) and value.get("v3"):
            payload = value.get("payload", b"")
            event = getattr(self, "ack_events", {}).get(CMD_GET_CHANNEL_MEASUREMENTS)
            control_ack = getattr(event, "measurement_control_ack", None)
            decoded = (not value.get("stream") and control_ack is not None
                       and payload in (b"", control_ack))
            decoded = decoded or self._handle_v3_measurements(
                payload,
                update_stream=(not getattr(self, '_capture_stream_enabled', False)
                               or bool(value.get('stream'))))
            if not value.get("stream"):
                if event is not None:
                    event.response_ok = decoded
        else:
            self._handle_legacy_measurements(value)

    def supports_measurement_capture(self):
        """Whether the device declares batch capture, independent of its rate."""
        group = self._get_capabilities()["measurement"]
        return (group.get("supported") is True and group.get("capture") is True
                and bool(self.supported_sample_rates()))

    def _handle_measurement_filter(self, channel, value):
        payload = value.get('payload', b'') if isinstance(value, dict) else b''
        self._filter_reply = payload[0] if len(payload) == 1 else 255
        if self._filter_reply in (0, 1):
            self.measurement_filter = self._filter_reply

    def supported_sample_rates(self):
        """Return declared measurement sample rates in samples per second.

        :returns: Declared rates, or an empty tuple.
        :rtype: tuple
        """
        rates = self._get_capabilities()["measurement"].get("sample_rates", [])
        if isinstance(rates, list) and all(type(n) is int and 0 < n <= 65535 for n in rates):
            return tuple(rates)
        return ()

    def _handle_measurement_rate(self, channel, value):
        data = value.get('payload', b'') if isinstance(value, dict) else b''
        self._sample_rate_reply = int.from_bytes(data, 'little') if len(data) == 2 else 0
        if 0 < self._sample_rate_reply <= 65535:
            self.measurement_sample_rate = self._sample_rate_reply

    @synchronized
    def get_measurement_sample_rate(self):
        """Read the measurement sample rate.

        A device declaring only 500 samples/s returns 500 without a query.

        :returns: Rate in samples/s, or None on failed query.
        :rtype: int or None
        :raises FeatureNotSupportedError: No declared rates.
        """
        rates = self.supported_sample_rates()
        if not rates:
            raise FeatureNotSupportedError('Selectable sample rates require USB3 RevB')
        if rates == (500,):
            self.measurement_sample_rate = 500
            return 500
        event = self.ack_events[CMD_MEASUREMENT_RATE]
        event.clear(); self._sample_rate_reply = None
        self._send_v3_packet(CMD_MEASUREMENT_RATE)
        return self.measurement_sample_rate if event.wait(self.com_timeout) and self._sample_rate_reply in rates else None

    @synchronized
    def set_measurement_sample_rate(self, rate):
        """Select a declared measurement sample rate.

        Active capture is paused and resumed around the change.

        :param int rate: Rate in samples/s.
        :returns: Whether the change and capture recovery succeeded.
        :rtype: bool
        :raises ValueError: Rate is not a positive uint16.
        :raises FeatureNotSupportedError: Rate is not declared.
        """
        if type(rate) is not int or not 0 < rate <= 65535:
            raise ValueError("sample rate must be a positive uint16 declared by the device")
        rates = self.supported_sample_rates()
        if rate not in rates:
            raise FeatureNotSupportedError('Requested sample rate is not declared by this device')
        if rates == (500,):
            self.measurement_sample_rate = 500
            return True
        streaming = self._capture_stream_enabled
        if streaming and not self._capture_stream(False):
            return False
        event = self.ack_events[CMD_MEASUREMENT_RATE]
        event.clear(); self._sample_rate_reply = None
        self._send_v3_packet(CMD_MEASUREMENT_RATE, [rate & 255, rate >> 8])
        success = event.wait(self.com_timeout) and self._sample_rate_reply == rate
        if streaming:
            success = self._capture_stream(True) and success
        return bool(success)

    def _handle_capture(self, channel, value):
        if not isinstance(value, dict):
            return
        payload = value.get('payload', b'')
        if not value.get('stream'):
            self._capture_reply = payload[0] if len(payload) == 1 else 255
            return
        try:
            batch = decode_usb3_capture_batch(payload)
        except ValueError:
            logger.warning('Invalid capture batch')
            return
        with self._measurement_stream_condition:
            self.capture_statistics = {k: batch[k] for k in ('drops', 'errors', 'duplicates')}
            self.measurement_filter = batch['filter']
            self.measurement_sample_rate = batch['sample_rate']
            for record in batch['records']:
                tick = record['refresh_us'] // 1000
                sample = {}
                for ch in range(1, 5):
                    v, a = record['voltage_mv'][ch-1], record['current_ma'][ch-1]
                    self.channel_voltages[ch], self.channel_currents[ch] = v, a
                    self.channel_measurement_valid[ch] = True
                    self.channel_measurement_fresh[ch] = True
                    self.channel_measurement_sample_tick[ch] = tick
                    sample[ch] = dict(voltage=v, current=a, valid=True, fresh=True,
                                      stale=False, sample_tick=tick, sample_period_ms=1000 // batch['sample_rate'],
                                      sample_time_us=record['refresh_us'],
                                      sequence=record['sequence'],
                                      conversion_count=record['conversion_count'],
                                      filter=batch['filter'])
                    if 'power_uw' in record:
                        sample[ch]['power'] = record['power_uw'][ch-1] / 1000.0  # mW
                        self.channel_powers[ch] = sample[ch]['power']
                        sample[ch]['power_source'] = 'hardware_instant'
                if len(self._capture_queue) >= 2048:
                    self._capture_queue.popleft()
                    self.measurement_queue_drops += 1
                self._capture_queue.append(sample)
                self._measurement_stream_seq += 1
                self._measurement_stream_tick = tick
                self._measurement_stream_period_ms = 1000 // batch['sample_rate']
            if batch['records']:
                self._measurement_stream_received_at = time.monotonic()
            self._measurement_stream_condition.notify_all()

    def _capture_stream(self, enabled, wait_ack=True):
        event = self.ack_events[CMD_LAB_CAPTURE]
        event.clear()
        self._capture_reply = None
        if enabled:
            with self._measurement_stream_condition:
                self._capture_queue.clear()
                self.measurement_queue_drops = 0
            self._capture_stream_enabled = True
        payload = [int(bool(enabled))]
        if self.supported_sample_rates() != (500,):
            payload.append(3)
        self._send_v3_packet(CMD_LAB_CAPTURE, payload)
        if not wait_ack:
            self._track_async_v3_request(CMD_LAB_CAPTURE)
        success = (not wait_ack or
                   (event.wait(self.com_timeout) and self._capture_reply == int(bool(enabled))))
        if not enabled or not success:
            self._capture_stream_enabled = False
            with self._measurement_stream_condition:
                self._capture_queue.clear()
                self._measurement_stream_condition.notify_all()
        return success

    @synchronized
    def get_measurement_filter(self):
        """Read the measurement filter mode.

        :returns: 0 for instantaneous, 1 for eight-conversion averaging, or None on failure.
        :rtype: int or None
        :raises FeatureNotSupportedError: Filters are not declared.
        """
        if not self._get_capabilities()["measurement"].get("filters"):
            raise FeatureNotSupportedError('Device does not declare configurable measurement filters')
        event = self.ack_events[CMD_MEASUREMENT_FILTER]
        event.clear()
        self._filter_reply = None
        self._send_v3_packet(CMD_MEASUREMENT_FILTER)
        return self.measurement_filter if event.wait(self.com_timeout) and self._filter_reply in (0, 1) else None

    @synchronized
    def set_measurement_filter(self, mode):
        """Select measurement hardware instantaneous (0) or internal eight-conversion average (1).
        RAM only. Averaging window ~7.8ms at 1024SPS; output follows the selected sample rate.
        The stream is stopped/restarted; queued samples never mix settings.
        """
        if mode not in (0, 1):
            raise ValueError('filter must be 0 or 1')
        selected_filter = "avg8" if mode else "instant"
        if selected_filter not in self._get_capabilities()["measurement"].get("filters", []):
            raise FeatureNotSupportedError('Requested measurement filter is not declared by this device')
        streaming = self._capture_stream_enabled
        if streaming and not self._capture_stream(False):
            return False
        event = self.ack_events[CMD_MEASUREMENT_FILTER]
        event.clear()
        self._filter_reply = None
        self._send_v3_packet(CMD_MEASUREMENT_FILTER, [mode])
        success = event.wait(self.com_timeout) and self._filter_reply == mode
        if streaming:
            success = self._capture_stream(True) and success
        return bool(success)

    def _handle_legacy_measurements(self, value):
        """
        Decode a legacy (V2-style) batch measurement payload.

        :param value: Raw payload bytes: channel_mask [fresh_mask] then 4 bytes per channel.
        """
        if not isinstance(value, (bytes, bytearray)) or len(value) < 1:
            logger.error("Invalid measurement payload received")
            return

        channel_mask = value[0]
        channels = self._convert_channel(channel_mask)
        old_len = 1 + 4 * len(channels)
        new_len = 2 + 4 * len(channels)
        if len(value) >= new_len:
            fresh_mask, pos = value[1], 2
        elif len(value) >= old_len:
            fresh_mask, pos = channel_mask, 1
        else:
            logger.error("Truncated measurement payload received")
            return

        for ch in channels:
            if pos + 4 > len(value):
                logger.error("Truncated measurement payload received")
                break
            self.channel_voltages[ch] = (value[pos] << 8) | value[pos + 1]
            self.channel_currents[ch] = (value[pos + 2] << 8) | value[pos + 3]
            self.channel_measurement_fresh[ch] = bool(fresh_mask & (1 << (ch - 1)))
            logger.debug(f"measurement: ch{ch} = {self.channel_voltages[ch]} mV, "
                         f"{self.channel_currents[ch]} mA")
            pos += 4

    def _handle_v3_measurements(self, value, update_stream=True):
        """
        Decode a V3 batch/stream measurement payload and notify stream waiters.

        :param value: Raw V3 payload bytes.
        """
        if not isinstance(value, (bytes, bytearray)):
            logger.error("Invalid V3 measurement response")
            return False

        payload = bytes(value)
        if len(payload) < 8:
            logger.error("Invalid V3 measurement payload")
            return False

        channel_mask = payload[0]
        fresh_mask = payload[1]
        valid_mask = payload[2]
        sample_period_ms = payload[3]
        sample_tick = (payload[4] | (payload[5] << 8)
                       | (payload[6] << 16) | (payload[7] << 24))
        channels = self._convert_channel(channel_mask)
        record_size = 8
        if (getattr(self, "_v3_header_len", V3_HEADER_LEN) == V3_LEGACY_HEADER_LEN
                and len(payload) == 8 + 4 * len(channels)):
            # Shipped 10-byte V3 firmware predates the hardware power field.
            record_size = 4
        elif len(payload) != 8 + 8 * len(channels):
            logger.error("Invalid measurement length; upgrade device firmware and SDK together")
            return False
        self._last_v3_status[CMD_GET_CHANNEL_MEASUREMENTS] = V3_STATUS_OK
        pos = 8
        updated = []
        with self._measurement_stream_condition:
            for ch in channels:
                self.channel_voltages[ch] = payload[pos] | (payload[pos + 1] << 8)
                self.channel_currents[ch] = payload[pos + 2] | (payload[pos + 3] << 8)
                if record_size == 8:
                    self.channel_powers[ch] = int.from_bytes(payload[pos + 4:pos + 8], "little") / 1000.0
                else:
                    self.channel_powers.pop(ch, None)
                self.channel_measurement_fresh[ch] = bool(fresh_mask & (1 << (ch - 1)))
                self.channel_measurement_valid[ch] = bool(valid_mask & (1 << (ch - 1)))
                self.channel_measurement_sample_tick[ch] = sample_tick
                updated.append(ch)
                logger.debug(f"V3 measurement: ch{ch} = {self.channel_voltages[ch]} mV, "
                             f"{self.channel_currents[ch]} mA, period={sample_period_ms} ms, "
                             f"tick={sample_tick}")
                pos += record_size

            if updated and update_stream:
                self._measurement_stream_tick = sample_tick
                self._measurement_stream_period_ms = sample_period_ms
                self._measurement_stream_seq += 1
                self._measurement_stream_received_at = time.monotonic()
                self._measurement_stream_condition.notify_all()
        return True

    def _handle_set_channel_dataline(self, channel, value):
        """Cache per-channel USB2 data-line state from a set ACK."""
        for ch in self._convert_channel(channel):
            self.channel_dataline_status[ch] = value

    def _handle_get_channel_dataline(self, channel, value):
        """Cache per-channel USB2 data-line state from a status reply."""
        if value not in (0, 1):
            return
        for ch in self._convert_channel(channel):
            self.channel_dataline_status[ch] = value

    def _handle_get_button_control(self, channel, value):
        """Cache button-control state from a status reply."""
        self.button_control_status = value

    def _handle_set_button_control(self, channel, value):
        """Handle a set-button-control ACK (no state change)."""
        logger.debug("set_button_control ACK")

    def _store_default_status(self, channel, value, flag_dict, status_dict, label):
        """
        Cache default enable/value pairs for the channels in a frame.

        :param flag_dict: Destination dict for the enable flags.

        :param status_dict: Destination dict for the default values.

        :param label: Human-readable label for logging.
        """
        if isinstance(value, list) and len(value) == 2 and all(v in (0, 1) for v in value):
            enable, status = value
            for ch in self._convert_channel(channel):
                flag_dict[ch] = enable
                status_dict[ch] = status
                logger.debug(f"channel {ch} {'enable' if enable else 'disable'} default {label}, "
                             f"value: {'on' if status else 'off'}")
        else:
            logger.error(f"Invalid data for default {label} handler")

    def _handle_set_default_power_status(self, channel, value):
        """Cache default power status from a set ACK."""
        self._store_default_status(channel, value, self.channel_default_power_flag,
                                   self.channel_default_power_status, "power status")

    def _handle_get_default_power_status(self, channel, value):
        """Cache default power status from a get reply."""
        self._store_default_status(channel, value, self.channel_default_power_flag,
                                   self.channel_default_power_status, "power status")

    def _handle_set_default_dataline_status(self, channel, value):
        """Cache default data-line status from a set ACK."""
        self._store_default_status(channel, value, self.channel_default_dataline_flag,
                                   self.channel_default_dataline_status, "dataline status")

    def _handle_get_default_dataline_status(self, channel, value):
        """Cache default data-line status from a get reply."""
        self._store_default_status(channel, value, self.channel_default_dataline_flag,
                                   self.channel_default_dataline_status, "dataline status")

    def _handle_usb3_dataline(self, channel, value):
        if value in (0, 1):
            for ch in self._convert_channel(channel):
                self.channel_usb3_dataline_status[ch] = value

    def _handle_upstream_host(self, channel, value):
        self._upstream_host = value if channel == 0 and value in (0, 1, 2) else None

    def _handle_set_device_address(self, channel, value):
        """Cache the echoed address so the setter can verify its ACK."""
        self._device_address_reply = (channel << 8) | value
        logger.debug("set_device_address ACK")

    def _handle_get_device_address(self, channel, value):
        """Cache the device address from a reply (channel = MSB, value = LSB)."""
        self.device_address = (channel << 8) | value
        logger.debug(f"device address: {self.device_address}")

    def _handle_reboot_mcu(self, channel, value):
        """Handle a reboot-MCU ACK (no state change)."""
        logger.debug("reboot_mcu ACK")

    def _handle_identify_device(self, channel, value):
        """Handle an identify-device ACK (LED blink started on device)."""
        logger.debug("identify_device ACK")

    def _handle_channel_name(self, channel, value):
        """Cache a channel display name from a V3 response."""
        if not (isinstance(value, dict) and value.get("v3")):
            logger.debug("channel_name ACK without V3 payload")
            return
        payload = bytes(value.get("payload", b""))
        if len(payload) < 1:
            return
        ch = int(payload[0])
        if ch < 1:
            return
        try:
            name = payload[1:].decode("utf-8", errors="ignore").strip("\x00 \r\n\t")
        except Exception:
            name = ""
        self.channel_names[ch] = name or f"CH{ch}"

    def _handle_device_alias(self, channel, value):
        """Cache the device alias from a V3 response."""
        if not (isinstance(value, dict) and value.get("v3")):
            logger.debug("device_alias ACK without V3 payload")
            return
        payload = bytes(value.get("payload", b""))
        try:
            alias = payload.decode("utf-8", errors="ignore").strip("\x00 \r\n\t")
        except Exception:
            alias = ""
        self.device_alias = alias

    def _handle_auth_certificate(self, channel, value):
        """Cache the raw V3 status/certificate response for the waiting verifier."""
        if isinstance(value, dict) and value.get("v3"):
            self._auth_certificate_response = bytes(value.get("payload", b""))

    def _handle_auth_challenge(self, channel, value):
        """Cache the raw V3 status/signature response for the waiting verifier."""
        if isinstance(value, dict) and value.get("v3"):
            self._auth_challenge_response = bytes(value.get("payload", b""))

    def _handle_factory_reset(self, channel, value):
        """Handle a factory-reset ACK (no state change)."""
        logger.debug("factory_reset ACK")

    def _handle_firmware_version(self, channel, value):
        """Cache the firmware version from a reply."""
        if isinstance(channel, int) and channel > 0:
            self.firmware_version_major = channel
            self.firmware_version_minor = value
        else:
            self.firmware_version_major = 1
            self.firmware_version_minor = value
        self.firmware_version = value

    def _handle_hardware_version(self, channel, value):
        """Cache the hardware version from a reply."""
        self.hardware_version = value

    def _handle_product_type(self, channel, value):
        """Cache the product type from a reply."""
        self.product_type = value

    def _handle_get_max_channels(self, channel, value):
        """
        Cache the maximum channel count, inferring from product type if unsupported.

        Firmware that does not support the command replies with 0xFF; in that case
        the channel count is inferred from ``PRODUCT_TYPE_TABLE`` when possible.
        """
        if value == 0xFF or value > 16:
            logger.warning(f"Suspicious max_channels value: {value} (0x{value:02X}); "
                           f"the device may not support this command.")
            remote_channels = (getattr(self, "_device_capabilities", None) or {}).get("channels")
            if isinstance(remote_channels, int) and remote_channels > 0:
                self.max_channels = remote_channels
                return
            if value == 0xFF and self.product_type is not None and self.capabilities_source == "legacy":
                product_info = PRODUCT_CATALOG.get(self.product_type)
                if product_info is not None:
                    self.max_channels = product_info["channels"]
                    logger.info(f"Inferring max_channels={self.max_channels} "
                                f"from product type {product_info['name']}")
                    return
        self.max_channels = value

    def _handle_serial_no(self, channel, value):
        """
        Cache the serial number from a reply.

        New firmware replies with a V1 ACK whose value is the ASCII length, then
        a V3 payload containing the full serial string. Older firmware may only
        send the V1 ACK, so keep a graceful "N/A" fallback.
        """
        if isinstance(value, dict) and value.get("v3"):
            payload = value.get("payload", b"")
            try:
                serial = bytes(payload).decode("ascii", errors="ignore").strip("\x00 \r\n\t")
            except Exception:
                serial = ""
            self.serial_no = serial or "N/A"
            return
        if isinstance(value, int) and value == 0:
            self.serial_no = "N/A"

    def _handle_set_auto_restore(self, channel, value):
        """Handle a set-auto-restore ACK (no state change)."""
        logger.debug("set_auto_restore ACK")

    def _handle_get_auto_restore_status(self, channel, value):
        """Cache auto-restore state from a status reply."""
        self.auto_restore_status = value

    def _channel_mask(self, channels):
        """Validate and pack the eight-bit channel field without duplicate carries."""
        maximum = getattr(self, "max_channels", None)
        maximum = min(maximum, 8) if type(maximum) is int and maximum > 0 else 8
        mask = 0
        for channel in channels:
            if type(channel) is not int or not 1 <= channel <= maximum:
                raise ValueError("Invalid channel for eight-bit channel mask")
            mask |= 1 << (channel - 1)
        return mask

    def _resolve_channels(self, channels):
        """
        Normalize a variadic channel argument, defaulting to all channels.

        Accepts either separate channel arguments or a single iterable. When empty,
        uses ``max_channels`` or the device's declared count. Only legacy firmware
        falls back to the product table or 7.

        :param channels: The variadic channels tuple as received by a public method.

        :returns: A tuple of 1-based channel numbers.
        """
        if len(channels) == 1 and isinstance(channels[0], (list, tuple, set)):
            channels = tuple(channels[0])
        if not channels:
            n = self.max_channels
            if not isinstance(n, int) or n <= 0 or n == 0xFF:
                declared = (getattr(self, "_device_capabilities", None) or {}).get("channels")
                product_info = PRODUCT_CATALOG.get(self.product_type)
                if declared:
                    n = declared
                elif self.capabilities_source == "legacy":
                    n = product_info["channels"] if product_info else 7
                else:
                    raise RuntimeError("Device did not declare a channel count")
            channels = tuple(range(1, n + 1))
        return channels

    def get_channels(self):
        """
        Return all valid 1-based channel numbers for the connected product.

        Uses the cached count, then CMD_GET_MAX_CHANNELS or the device declaration.
        Only legacy firmware falls back to the product table.

        :returns: Tuple such as (1, 2, 3, 4).

        :raises RuntimeError: If the count cannot be resolved.
        """
        n = self.max_channels
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            n = self.get_max_channels()
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            declared_channels = (getattr(self, "_device_capabilities", None) or {}).get("channels")
            product_info = PRODUCT_CATALOG.get(self.product_type)
            n = declared_channels or (product_info["channels"] if product_info and self.capabilities_source == "legacy" else None)
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            raise RuntimeError(f"Cannot determine max channel count: {n!r}")
        return tuple(range(1, n + 1))

    def _filter_channel_dict(self, source, channels):
        """
        Build a result dict copy from a cached per-channel state dict.

        :param source: Source dict keyed by channel number.

        :param channels: Channels to include; empty means all keys in ``source.``

        :returns: A new dict containing only the requested, known channels.
        """
        if channels:
            return {ch: source[ch] for ch in channels if ch in source}
        return dict(source)

    def _measurement_snapshot(self, channels, valid_default, include_stream_meta=False):
        """
        Snapshot cached measurements for the given channels.

        :param channels: Channels to include.

        :param valid_default: Default for the "valid" flag when not yet known.

        :param include_stream_meta: Include sample_tick/sample_period_ms entries.

        :returns: Dict {channel: {voltage, current, power, fresh, stale, valid, ...}}.
        """
        result = {}
        for ch in channels:
            if ch not in self.channel_voltages and ch not in self.channel_currents:
                continue
            fresh = self.channel_measurement_fresh.get(ch, False)
            entry = {
                "voltage": self.channel_voltages.get(ch),
                "current": self.channel_currents.get(ch),
                "power": self.channel_powers.get(ch),
                "fresh": fresh,
                "stale": not fresh,
                "valid": self.channel_measurement_valid.get(ch, valid_default),
            }
            if include_stream_meta:
                entry["sample_tick"] = self.channel_measurement_sample_tick.get(ch)
                entry["sample_period_ms"] = self._measurement_stream_period_ms
            result[ch] = entry
        return result

    def _retry_get_info(self, get_func, info_name, max_retry_time=10.0):
        """
        Repeatedly call a getter until it returns non-None or the deadline passes.

        :param get_func: Zero-argument getter to retry.

        :param info_name: Label used in log messages.

        :param max_retry_time: Maximum total retry time in seconds.

        :returns: The retrieved value, or None on timeout.
        """
        start_time = time.time()
        retry_count = 0
        while True:
            result = get_func()
            if result is not None:
                logger.debug(f"{info_name} retrieved after {retry_count} retries, "
                             f"{time.time() - start_time:.2f}s")
                return result

            elapsed = time.time() - start_time
            if elapsed >= max_retry_time:
                logger.error(f"{info_name} failed after {retry_count} retries, "
                             f"{elapsed:.2f}s - giving up")
                return None

            retry_count += 1
            # Back off gradually: fast at first, then slower.
            if retry_count <= 3:
                time.sleep(0.05)
            elif retry_count <= 10:
                time.sleep(0.1)
            else:
                time.sleep(0.2)

    def _is_legacy_v1_firmware(self):
        """
        Return True when the firmware-version reply used the legacy V1 shape.

        V1 firmware reports only the minor version in the value byte and leaves
        the channel byte at zero. Newer firmware uses the channel byte as a
        major-version field, so this check does not need unsupported-command
        timeouts.
        """
        return (self.firmware_version_major == 1 and
                getattr(self, "_v3_header_len", V3_LEGACY_HEADER_LEN) != V3_HEADER_LEN)

    def _uses_legacy_measurement_queries(self):
        """Shipped USB2 four-port firmware uses V1 voltage/current queries."""
        return (getattr(self, "product_type", None) == 0x00
                and self.capabilities_source == "legacy")

    def get_protocol_info(self):
        """Return the protocol API version and firmware upgrade recommendation.

        Only known pre-declaration devices receive the SDK legacy baseline.
        Missing/invalid versions on current devices stay unknown.
        :returns: Protocol version, source and upgrade recommendation.
        :rtype: dict
        """
        document = getattr(self, "_device_capabilities", None) or {}
        declaration = document.get("protocol", {})
        value = declaration.get("version") if isinstance(declaration, dict) else None
        parts = value.split(".") if isinstance(value, str) else []
        valid = (len(parts) == 3 and all(p.isascii() and p.isdigit() and
                 (p == "0" or not p.startswith("0")) for p in parts))
        if valid:
            version, source = value, "device"
        elif self.capabilities_source == "legacy" and getattr(self, "product_type", None) in _LEGACY_PRODUCT_CAPABILITIES:
            version, source = "1.0.0", "legacy"
        else:
            version, source = None, "unavailable"
        recommended = "1.2.0"
        upgrade = version is not None and tuple(map(int, version.split("."))) < (1, 2, 0)
        message = ("当前固件使用兼容模式，基础控制和测量仍可使用，建议更新固件。\n请到此页面下载最新的Control Pannel：https://mixedsignallab.com/download\n下载安装完后会打开说明书，请按照说明书操作。"
                   if upgrade else "")
        return dict(version=version, source=source, recommended_version=recommended,
                    update_recommended=upgrade, message=message)

    def get_device_info(self):
        """
        Read and cache the hub's identity and configuration.

        Critical items (versions, operate mode, ...) are retried for up to ~10 s
        each to tolerate a device that is still initializing. Optional items not
        supported by older firmware are treated as unavailable.

        :returns: Dict describing the hub (id, address, versions, product, mode, ...).
        """
        logger.info("Reading device info (retrying up to 10s per critical item)...")

        self.hardware_version = self._retry_get_info(self.get_hardware_version, "hardware_version")
        self.firmware_version = self._retry_get_info(self.get_firmware_version, "firmware_version")
        self._negotiate_v3_protocol()
        self._query_device_capabilities()

        if self._is_legacy_v1_firmware():
            self.product_type = 0x00
            product_info = PRODUCT_CATALOG.get(self.product_type)
            self.max_channels = product_info["channels"] if product_info is not None else 4
            self.serial_no = "N/A"
            self.device_alias = ""
            logger.info("Legacy V1 firmware detected; using HBP_USB2_4CH defaults "
                        "without probing newer identity commands")
        else:
            self.product_type = self.get_product_type()
            if self.product_type is None and self.capabilities_source == "legacy":
                self.product_type = 0x00
                logger.info("CMD_GET_PRODUCT_TYPE unsupported; defaulting to HBP_USB2_4CH")

            product_info = PRODUCT_CATALOG.get(self.product_type)
            # Optional on old firmware: infer channel count from the product type.
            self.max_channels = self.get_max_channels()
            if self.max_channels is None or self.max_channels == 0xFF:
                declared_channels = (getattr(self, "_device_capabilities", None) or {}).get("channels")
                if declared_channels:
                    self.max_channels = declared_channels
                elif product_info is not None and self.capabilities_source == "legacy":
                    self.max_channels = product_info["channels"]
                    logger.info(f"CMD_GET_MAX_CHANNELS unsupported; inferring "
                                f"max_channels={self.max_channels} from {product_info['name']}")

            self.serial_no = self.get_serial_no()  # optional
            self.device_alias = self.get_device_alias() or ""

        product_info = PRODUCT_CATALOG.get(self.product_type)
        if self.capabilities_source != "legacy":
            self.com_timeout = 0.5
        elif product_info is not None:
            self.com_timeout = _LEGACY_PRODUCT_CAPABILITIES.get(self.product_type, {}).get("ack_timeout", 0.1)
            logger.info(f"ACK timeout set to {self.com_timeout}s for {product_info['name']}")

        self.operate_mode = self._retry_get_info(self.get_operate_mode, "operate_mode")
        caps = self._get_capabilities()
        diagnostics = caps.get("device", {}).get("diagnostics", {})
        if isinstance(diagnostics, dict) and type(diagnostics.get("reset_flags")) is int:
            logger.info("Device reset flags=0x%08X uptime_ms=%s",
                        diagnostics["reset_flags"], diagnostics.get("uptime_ms"))
        self.auto_restore_status = (self._retry_get_info(self.get_auto_restore_status, "auto_restore_status")
                                    if caps["auto_restore"]["supported"] is not False else None)
        self.button_control_status = (self._retry_get_info(self.get_button_control_status, "button_control_status")
                                      if caps["button_control"]["supported"] is not False else None)
        self.device_address = self._retry_get_info(self.get_device_address, "device_address")

        # Warm the default-state caches for every channel (best effort).
        n = self.max_channels
        channels = tuple(range(1, n + 1)) if isinstance(n, int) and 1 <= n <= 16 else ()
        if channels:
            self.get_default_power_status(*channels)
            if self._get_capabilities()["usb2_data_switch"].get("supported") is True:
                self.get_default_usb2_dataline_status(*channels)

        product_type_name = self._declared_model() or (product_info["name"] if product_info is not None
                             else (f"Unknown({self.product_type})" if self.product_type is not None else "N/A"))
        hub_info = {
            "id": self.port.split("/")[-1],
            "address": self.device_address,
            "hardware_version": self.hardware_version,
            "firmware_version": self.firmware_version,
            "firmware_version_major": self.firmware_version_major,
            "firmware_version_minor": self.firmware_version_minor,
            "product_type": product_type_name,
            "max_channels": self.max_channels if self.max_channels is not None else "N/A",
            "serial_no": self.serial_no if self.serial_no else "N/A",
            "device_alias": self.device_alias,
            "operate_mode": ("normal" if self.operate_mode == 0
                             else "interlock" if self.operate_mode == 1 else "N/A"),
            "auto_restore": "enabled" if self.auto_restore_status == 1 else "disabled",
            "button_control_status": "enabled" if self.button_control_status == 1 else "disabled",
        }

        protocol = self.get_protocol_info()
        hub_info.update(protocol_version=protocol["version"], protocol_version_source=protocol["source"],
                        firmware_update_recommended=protocol["update_recommended"],
                        firmware_update_message=protocol["message"])
        if protocol["update_recommended"] and not getattr(self, "_protocol_upgrade_warned", False):
            logger.warning("%s [%s, protocol %s, source=%s]", protocol["message"], self.port,
                           protocol["version"], protocol["source"])
            self._protocol_upgrade_warned = True
            warnings.warn(protocol["message"], FirmwareUpdateRecommendedWarning, stacklevel=3)
        if self.operate_mode is None:
            logger.error("Failed to get operate mode after retries - this is critical!")
        for name in ("hardware_version", "firmware_version", "product_type",
                     "max_channels", "serial_no"):
            if getattr(self, name) is None:
                logger.warning(f"Failed to get {name} after retries")
        return hub_info

    @synchronized
    def set_operate_mode(self, mode):
        """
        Set the device operating mode.

        :param mode: ``OPERATE_MODE_NORMAL`` (0) or ``OPERATE_MODE_INTERLOCK`` (1).

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_OPERATE_MODE].clear()
        self._send_packet(CMD_SET_OPERATE_MODE, None, mode)
        if self._wait_for_ack_with_recovery(CMD_SET_OPERATE_MODE):
            return True
        logger.error("set_operate_mode No ACK!")
        return False

    @synchronized
    def get_operate_mode(self):
        """
        Query the current operating mode.

        :returns: 0 (normal), 1 (interlock), or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_OPERATE_MODE]
        ack_event.clear()
        self._send_packet(CMD_GET_OPERATE_MODE, None, None)
        if ack_event.wait(self.com_timeout):
            return self.operate_mode
        self.operate_mode = None
        logger.warning("get_operate_mode No ACK!")
        return None

    @synchronized
    def set_channel_power(self, *channels, state):
        """
        Set the power state of one or more channels.

        :param channels: Channel numbers (1-based) to update.

        :param state: 1 to power on, 0 to power off.

        :returns: True if acknowledged, False otherwise.
        """
        if state not in (0, 1):
            raise ValueError("state must be 0 or 1")
        self._channel_mask(channels)  # Validate before any protection side effects.
        # A new explicit ON is the user's retry. Keep this handshake for older
        # alert firmware; the MCU still validates health and enforces protection.
        caps = getattr(self, '_device_capabilities', None) or {}
        alerts = caps.get('alerts', {})
        if state == 1 and isinstance(alerts, dict) and alerts.get('supported') is True:
            status = self.get_alert_status()
            if not status or not status['ready'] or status['io_fault']:
                return False
            selected = self._resolve_channels(channels)
            retry_mask = self._channel_mask(ch for ch in selected
                                            if status['channels'].get(ch, {}).get('trip'))
            if retry_mask and not self.reset_protection_trip(retry_mask):
                return False
        self.ack_events[CMD_SET_CHANNEL_POWER].clear()
        self._send_packet(CMD_SET_CHANNEL_POWER, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
            return True
        logger.error("set_channel_power No ACK!")
        return False

    @synchronized
    def get_channel_power_status(self, *channels):
        """
        Query the power status of one or more channels.

        :param channels: Channels to query.

        :returns: For a single channel, its power state; for multiple, a dict {channel: state}; or None on timeout.
        """
        result = self._get_channel_status(CMD_GET_CHANNEL_POWER_MASK, channels)
        resolved = self._resolve_channels(channels)
        if result is not None and len(resolved) == 1:
            return result.get(resolved[0])
        return result

    @synchronized
    def get_channel_oc_status(self):
        """
        Query per-channel overcurrent status.

        :returns: Dict {channel: {'active': bool, 'latch': bool}}, or None on timeout. 'active' is the OC pin/comparator state; 'latch' is OC history until cleared.

        :raises FeatureNotSupportedError: If overcurrent reporting is unavailable.
        """
        if not self._check_feature_support("overcurrent"):
            self._raise_overcurrent_unsupported()
        if self._get_capabilities()["overcurrent"].get("status_api") == "alerts":
            status = self.get_alert_status()
            if status is None:
                return None
            return {ch: {"active": bool(item["active"] & 1),
                         "latch": bool(item["history"] & 1)}
                    for ch, item in status["channels"].items()}
        ack_event = self.ack_events[CMD_GET_CHANNEL_OC_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_OC_STATUS, None, 0)
        if ack_event.wait(self.com_timeout):
            return {ch: {'active': self.channel_oc_active.get(ch, False),
                         'latch': self.channel_oc_latch.get(ch, False)}
                    for ch in sorted(self.channel_oc_active)}
        logger.error("get_channel_oc_status No ACK!")
        return None

    @synchronized
    def clear_channel_oc_latch(self, *channels):
        """
        Clear the sticky overcurrent latch for one or more channels.

        Devices with ``overcurrent.status_api == "alerts"`` use
        ``clear_alert_latch()`` for history and ``reset_protection_trip()``
        to unlock protection instead.

        :param channels: Channels to clear; no arguments clears all channels.

        :returns: True if acknowledged, False otherwise.

        :raises FeatureNotSupportedError: If overcurrent status is unsupported
            or the device uses the alerts interface.
        """
        if not self._check_feature_support("overcurrent"):
            self._raise_overcurrent_unsupported()
        if self._get_capabilities()["overcurrent"].get("status_api") == "alerts":
            raise FeatureNotSupportedError(
                "measurement hardware protection separates history from power locks; use "
                "clear_alert_latch() for history or reset_protection_trip() to unlock.")
        if not channels:
            n = self.max_channels if isinstance(self.max_channels, int) and 0 < self.max_channels <= 16 else 7
            channels = tuple(range(1, n + 1))
        ack_event = self.ack_events[CMD_CLEAR_CHANNEL_OC_LATCH]
        ack_event.clear()
        self._send_packet(CMD_CLEAR_CHANNEL_OC_LATCH, channels, 0)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("clear_channel_oc_latch No ACK!")
        return False

    @synchronized
    def set_channel_power_interlock(self, channel):
        """
        Select the only powered channel, or turn all channels off.

        This does not change the operating mode; use ``set_operate_mode()``
        to configure it.

        :param channel: Channel to power, or None to turn all channels off.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_CHANNEL_POWER_INTERLOCK].clear()
        if channel is None:
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, None, 0)
        else:
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, [channel], 1)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER_INTERLOCK):
            return True
        logger.error("set_channel_power_interlock No ACK!")
        return False

    def _raise_adc_unsupported(self):
        """Raise FeatureNotSupportedError when voltage/current monitoring is absent."""
        product_info = PRODUCT_CATALOG.get(self.product_type)
        product_name = product_info["name"] if product_info else f"Unknown({self.product_type!r})"
        raise FeatureNotSupportedError(
            f"Device {product_name} does not declare voltage/current monitoring support.")

    def _raise_usb2_data_switch_unsupported(self):
        """Raise a descriptive error when USB2 data-line control is absent."""
        product_info = PRODUCT_CATALOG.get(self.product_type)
        product_name = product_info["name"] if product_info else f"Unknown({self.product_type!r})"
        raise FeatureNotSupportedError(
            f"Device {product_name} does not declare USB2 data-line switching support.")

    def _raise_overcurrent_unsupported(self):
        """Raise FeatureNotSupportedError when overcurrent status is unsupported."""
        product_info = PRODUCT_CATALOG.get(self.product_type)
        product_name = product_info["name"] if product_info else f"Unknown({self.product_type!r})"
        raise FeatureNotSupportedError(
            f"Device {product_name} does not declare overcurrent status reporting support.")

    @synchronized
    def get_channel_voltage(self, channel):
        """
        Read the voltage of a single channel.

        :param channel: Channel to query.

        :returns: Voltage in mV, or None on timeout.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.

        :raises ValueError: If a list/tuple is passed instead of a single channel.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_voltage only supports a single channel")
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()

        ack_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [channel])
        if ack_event.wait(self.com_timeout):
            return self.channel_voltages.get(channel)
        logger.error("get_channel_voltage No ACK!")
        return None

    @synchronized
    def get_channel_current(self, channel):
        """
        Read the current of a single channel.

        :param channel: Channel to query.

        :returns: Current in mA, or None on timeout.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.

        :raises ValueError: If a list/tuple is passed instead of a single channel.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_current only supports a single channel")
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()

        ack_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_CURRENT, [channel])
        if ack_event.wait(self.com_timeout):
            return self.channel_currents.get(channel)
        logger.error("get_channel_current No ACK!")
        return None

    def get_channel_power(self, channel):
        """Query one channel's power in mW, or None if unavailable.

        Uses hardware power from the measurement frame when supplied. Legacy
        devices fall back to V*I/1000 using their sequential voltage/current
        queries; that estimate is not a simultaneous hardware power sample.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_power only supports a single channel")
        values = self.get_channel_measurements(channel)
        item = values.get(channel) if values else None
        if not item or not item.get("valid") or not item.get("fresh"):
            return None
        if item.get("power") is not None:
            return item["power"]
        v, i = item.get("voltage"), item.get("current")
        return v * i / 1000.0 if v is not None and i is not None else None

    @synchronized
    def get_channel_measurements(self, *channels):
        """
        Send a request and wait for voltage/current/power readings.

        This queries the device; unlike get_cached_measurements(), it does not
        simply return a cached value. It does not start streaming.

        :param channels: Channels to query; if omitted, all channels are queried.

        :returns: Dict {channel: {"voltage", "current", "power", "fresh", "stale", "valid"}}.
            Units are mV, mA and mW. ``power`` comes from the device when supplied,
            is estimated from sequential voltage/current queries on legacy firmware,
            or is None when unavailable. Returns None if no valid reply is obtained.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.
        """
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()
        channels = self._resolve_channels(channels)

        if self._is_legacy_v1_firmware() or self._uses_legacy_measurement_queries():
            result = {}
            for ch in channels:
                voltage_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
                voltage_event.clear()
                self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [ch])
                if not voltage_event.wait(self.com_timeout):
                    logger.error("get_channel_measurements legacy voltage No ACK!")
                    return None

                current_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
                current_event.clear()
                self._send_packet(CMD_GET_CHANNEL_CURRENT, [ch])
                if not current_event.wait(self.com_timeout):
                    logger.error("get_channel_measurements legacy current No ACK!")
                    return None

                result[ch] = {
                    "voltage": self.channel_voltages.get(ch),
                    "current": self.channel_currents.get(ch),
                    "power": (self.channel_voltages.get(ch) * self.channel_currents.get(ch) / 1000.0
                              if self.channel_voltages.get(ch) is not None and self.channel_currents.get(ch) is not None else None),
                    "fresh": True,
                    "stale": False,
                    "valid": True,
                }
            return result

        ack_event = self.ack_events[CMD_GET_CHANNEL_MEASUREMENTS]
        channel_mask = self._channel_mask(channels)
        for attempt in range(3):
            ack_event.clear()
            self._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, [channel_mask, 0x00])
            if ack_event.wait(self.com_timeout):
                if self._last_v3_status.get(CMD_GET_CHANNEL_MEASUREMENTS) == V3_STATUS_OK:
                    result = self._measurement_snapshot(channels, valid_default=True)
                    has_fresh = any(item["fresh"] for item in result.values())
                    if result and any(item["valid"] for item in result.values()) and has_fresh:
                        return result
                    if attempt < 2:
                        time.sleep(0.06)
                        continue
                    logger.warning("V3 measurement response contained no valid channel data")
                else:
                    logger.warning("V3 measurement command returned an error")
                break
            if attempt < 2:
                time.sleep(0.02)

        logger.error("get_channel_measurements No ACK!")
        return None

    def get_stream_channel_measurements(self, *channels, timeout=None, wait_new_sample=True):
        """
        Read the next measurements from an enabled V3 stream.

        Does not send a request; the device must already have streaming enabled via
        :meth:`set_channel_measurement_stream`.

        Batch capture consumes unread samples in order, waiting only when its
        queue is empty. Other streams wait for a new sample tick or frame.

        :param channels: Channels to include; if omitted, all channels.

        :param timeout: Wait timeout in seconds; defaults to ``self.com_timeout``.

        :param wait_new_sample: For non-capture streams, True waits for a new
            sample tick; False accepts the next frame even with the same tick.
            Batch capture always consumes its unread queue regardless of this flag.

        :returns: Dict of per-channel readings (with sample_tick/sample_period_ms), or None.
        """
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()
        channels = self._resolve_channels(channels)
        if timeout is None:
            timeout = self.com_timeout

        deadline = time.monotonic() + timeout
        with self._measurement_stream_condition:
            start_seq = self._measurement_stream_seq
            start_tick = self._measurement_stream_tick
            while True:
                if self._capture_stream_enabled and self._capture_queue:
                    sample = self._capture_queue.popleft()
                    return {ch: sample[ch] for ch in channels if ch in sample}
                has_channels = any(ch in self.channel_voltages or ch in self.channel_currents
                                   for ch in channels)
                got_new_frame = self._measurement_stream_seq != start_seq
                got_new_sample = (self._measurement_stream_tick is not None
                                  and (start_tick is None
                                       or self._measurement_stream_tick != start_tick))
                if has_channels and (got_new_sample if wait_new_sample else got_new_frame):
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._measurement_stream_condition.wait(remaining)

            return self._measurement_snapshot(channels, valid_default=False, include_stream_meta=True)

    def discard_measurement_backlog(self):
        """Advanced App integration: discard unread capture samples on resume."""
        with self._measurement_stream_condition:
            self._capture_queue.clear()

    def measurement_stream_counter(self):
        """Advanced App integration: sample count and host monotonic timestamp.

        Both belong to the same completed RX batch. Pairing a newer counter
        with an earlier application timestamp biases rate estimates upward.
        Empty health reports and capture-mode query replies do not count.
        """
        with self._measurement_stream_condition:
            return (self._measurement_stream_seq,
                    getattr(self, '_measurement_stream_received_at', None))

    @synchronized
    def set_channel_measurement_stream(self, *channels, enabled=True, wait_ack=True):
        """
        Enable or disable V3 measurement streaming.

        Stream frames are unsolicited V3 notifications and are not acknowledged by
        the host.

        :param channels: Channels to stream; if omitted, all channels.

        :param enabled: True to enable streaming, False to disable.

        :param wait_ack: If True, wait for the command ACK before returning.

        :returns: True on success (or when ``wait_ack`` is False), False on rejection or timeout.
        """
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()
        channels = self._resolve_channels(channels)
        if self._uses_legacy_measurement_queries():
            if enabled:
                raise FeatureNotSupportedError("旧固件支持逐通道测量，不支持V3测量流。" + self.get_protocol_info()["message"])
            return True
        if self.supports_measurement_capture():
            return self._capture_stream(enabled, wait_ack)
        channel_mask = self._channel_mask(channels)
        flags = V3_MEAS_FLAG_STREAM_ENABLE if enabled else V3_MEAS_FLAG_STREAM_DISABLE
        ack_event = self.ack_events[CMD_GET_CHANNEL_MEASUREMENTS]
        ack_event.clear()
        self._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, [channel_mask, flags])
        if not wait_ack:
            self._track_async_v3_request(CMD_GET_CHANNEL_MEASUREMENTS)
            return True
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("set_channel_measurement_stream No ACK!")
        return False

    def get_cached_measurements(self, *channels):
        """
        Return cached measurements without sending a command or waiting.

        This is not equivalent to a fresh voltage/current query. Cached data
        may predate this call; fresh/valid describe the last received frame,
        not an elapsed-time guarantee.

        Returns the latest cache populated by a measurement query or stream.
        Starting a stream is not required.

        :param channels: Channels to include; if omitted, all channels.

        :returns: Dict of per-channel readings, or None if nothing has been received.
        """
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()
        return self._cached_measurements(channels)

    def _cached_measurements(self, channels):
        channels = self._resolve_channels(channels)
        with self._measurement_stream_condition:
            result = self._measurement_snapshot(channels, valid_default=False, include_stream_meta=True)
        return result if result else None

    def get_latest_measurements(self, *channels):
        """Deprecated cache-only alias; use get_cached_measurements()."""
        _warn_legacy_api('get_latest_measurements()', 'get_cached_measurements()')
        # Published 1.2.1 also permits an empty cache on devices without ADC.
        return self._cached_measurements(channels)

    @synchronized
    def set_channel_usb3_dataline(self, *channels, state):
        """
        Set the USB3.0 data-line state of one or more channels.

        :param channels: Channels to update.

        :param state: 1 to connect the data line, 0 to disconnect.

        :returns: True if acknowledged, False otherwise.
        """
        if not self._check_feature_support("usb3_data_switch"):
            raise FeatureNotSupportedError("USB3 data switching is not supported by this product")
        channels = self._resolve_channels(channels)
        if state not in (0, 1):
            raise ValueError("state must be 0 or 1")
        self.ack_events[CMD_SET_CHANNEL_USB3_DATALINE].clear()
        self._send_packet(CMD_SET_CHANNEL_USB3_DATALINE, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_USB3_DATALINE):
            return True
        logger.error("set_channel_usb3_dataline No ACK!")
        return False

    @synchronized
    def get_channel_usb3_dataline_status(self, *channels):
        """
        Query the USB3.0 data-line status of one or more channels.

        :param channels: Channels to query; if omitted, returns all known channels.

        :returns: Dict {channel: state} for the requested channels, or None on timeout.
        """
        if not self._check_feature_support("usb3_data_switch"):
            raise FeatureNotSupportedError("USB3 data switching is not supported by this product")
        return self._get_channel_status(CMD_GET_CHANNEL_USB3_DATALINE_MASK, channels)

    @synchronized
    def set_channel_usb2_dataline(self, *channels, state):
        """
        Set the USB2.0 data-line state of one or more channels.

        :param channels: Channels to update.

        :param state: 1 to connect the data line, 0 to disconnect.

        :returns: True if acknowledged, False otherwise.
        """
        if not self._check_feature_support("usb2_data_switch"):
            self._raise_usb2_data_switch_unsupported()
        self.ack_events[CMD_SET_CHANNEL_DATALINE].clear()
        self._send_packet(CMD_SET_CHANNEL_DATALINE, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_DATALINE):
            return True
        logger.error("set_channel_usb2_dataline No ACK!")
        return False

    def set_channel_dataline(self, *channels, state):
        """Deprecated USB2-only alias; use ``set_channel_usb2_dataline()``."""
        _warn_legacy_api('set_channel_dataline()', 'set_channel_usb2_dataline()')
        return self.set_channel_usb2_dataline(*channels, state=state)

    @synchronized
    def get_channel_usb2_dataline_status(self, *channels):
        """
        Query the USB2.0 data-line status of one or more channels.

        :param channels: Channels to query; if omitted, returns all known channels.

        :returns: Dict {channel: state} for the requested channels, or None on timeout.
        """
        if not self._check_feature_support("usb2_data_switch"):
            self._raise_usb2_data_switch_unsupported()
        return self._get_channel_status(CMD_GET_CHANNEL_USB2_DATALINE_MASK, channels)

    def get_channel_dataline_status(self, *channels):
        """Deprecated USB2-only alias; use ``get_channel_usb2_dataline_status()``."""
        _warn_legacy_api('get_channel_dataline_status()', 'get_channel_usb2_dataline_status()')
        return self.get_channel_usb2_dataline_status(*channels)

    @synchronized
    def set_button_control(self, enable: bool):
        """
        Enable or disable the hub's physical buttons.

        :param enable: True to enable buttons, False to disable.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_BUTTON_CONTROL].clear()
        self._send_packet(CMD_SET_BUTTON_CONTROL, None, 1 if enable else 0)
        if self._wait_for_ack_with_recovery(CMD_SET_BUTTON_CONTROL):
            return True
        logger.error("set_button_control No ACK!")
        return False

    @synchronized
    def get_button_control_status(self):
        """
        Query whether the hub's physical buttons are enabled.

        :returns: 1 if enabled, 0 if disabled, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_BUTTON_CONTROL_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_BUTTON_CONTROL_STATUS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.button_control_status
        logger.error("get_button_control_status No ACK!")
        return None

    @synchronized
    def set_default_power_status(self, *channels, enable, status=None):
        """
        Set the power-on default power state for one or more channels.

        :param channels: Channels to configure.

        :param enable: 1 to apply a default power state, 0 to disable defaulting.

        :param status: Default state when enabled: 1 for ON, 0 for OFF (default 0).

        :returns: True if acknowledged, False otherwise.
        """
        if status is None:
            status = 0
        self.ack_events[CMD_SET_DEFAULT_POWER_STATUS].clear()
        self._send_packet(CMD_SET_DEFAULT_POWER_STATUS, channels, [enable, status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_POWER_STATUS):
            return True
        logger.error("set_default_power_status No ACK!")
        return False

    @synchronized
    def get_default_power_status(self, *channels):
        """
        Query the default power configuration for one or more channels.

        :param channels: Channels to query.

        :returns: Dict {channel: {"enabled", "value"}}, or None if no response.
        """
        return self._get_default_status(CMD_GET_DEFAULT_POWER_STATUS, channels,
                                        self.channel_default_power_flag,
                                        self.channel_default_power_status,
                                        CMD_GET_DEFAULT_POWER_MASK)

    @synchronized
    def set_default_usb2_dataline_status(self, *channels, enable, status=None):
        """
        Set the USB2 power-on default state; USB3 defaults are not changed.

        :param channels: Channels to configure.

        :param enable: 1 to apply a default data-line state, 0 to disable defaulting.

        :param status: Default state when enabled: 1 for connected, 0 for disconnected (default 0).

        :returns: True if acknowledged, False otherwise.
        """
        if not self._check_feature_support("usb2_data_switch"):
            self._raise_usb2_data_switch_unsupported()
        if status is None:
            status = 0
        self.ack_events[CMD_SET_DEFAULT_DATALINE_STATUS].clear()
        self._send_packet(CMD_SET_DEFAULT_DATALINE_STATUS, channels, [enable, status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_DATALINE_STATUS):
            return True
        logger.error("set_default_dataline_status No ACK!")
        return False

    @synchronized
    def get_default_usb2_dataline_status(self, *channels):
        """
        Query the USB2 default configuration; this does not report USB3 defaults.

        :param channels: Channels to query.

        :returns: Dict {channel: {"enabled", "value"}}, or None if no response.
        """
        if not self._check_feature_support("usb2_data_switch"):
            self._raise_usb2_data_switch_unsupported()
        return self._get_default_status(CMD_GET_DEFAULT_DATALINE_STATUS, channels,
                                        self.channel_default_dataline_flag,
                                        self.channel_default_dataline_status,
                                        CMD_GET_DEFAULT_USB2_DATALINE_MASK)

    def _handle_default_usb3_response(self, channel, value):
        if isinstance(value, dict) and value.get("v3") and not value.get("stream"):
            p = value.get("payload", b"")
            if len(p) == 3 and p[0] and not ((p[1] | p[2]) & ~p[0]):
                self._default_usb3_reply = bytes(p)

    def _default_usb3_exchange(self, cmd, channels, enable=None, status=None):
        document = self.get_capability()
        if not document or document.get("device", {}).get("default_usb3_data") is not True:
            raise FeatureNotSupportedError("Device does not declare USB3 default configuration")
        channels = self._resolve_channels(channels)
        if any(type(ch) is not int or ch < 1 or ch > self.max_channels for ch in channels):
            raise ValueError("Invalid channel number")
        mask = self._channel_mask(channels)
        payload = bytes([mask]) if enable is None else bytes([mask, enable, status])
        event = self.ack_events[cmd]
        event.clear()
        self._default_usb3_reply = None
        self._send_v3_packet(cmd, payload)
        if not event.wait(max(1.0, self.com_timeout)):
            return None
        p = self._default_usb3_reply
        if self._last_v3_status.get(cmd) != V3_STATUS_OK or not p or p[0] != mask:
            return None
        return {ch: {"enabled": int(bool(p[1] & (1 << (ch - 1)))),
                     "value": int(bool(p[2] & (1 << (ch - 1))))} for ch in channels}

    @synchronized
    def set_default_usb3_dataline_status(self, *channels, enable, status=None):
        """Persist USB3 boot defaults; does not change current data GPIO.

        enable/status accept 0/1 or bool. Disabled entries revert to normal
        default (value=1). USB2-off and VBUS-off take precedence on restoration.
        Returns True only after firmware verifies persistence and echoes values.
        """
        if type(enable) not in (int, bool) or enable not in (0, 1):
            raise ValueError("enable must be 0 or 1")
        status = 0 if status is None else status
        if type(status) not in (int, bool) or status not in (0, 1):
            raise ValueError("status must be 0 or 1")
        result = self._default_usb3_exchange(CMD_SET_DEFAULT_USB3_DATALINE_STATUS,
                                           channels, int(enable), int(status))
        return bool(result and all(v == {"enabled": int(enable), "value": int(status) if enable else 1}
                                   for v in result.values()))

    @synchronized
    def get_default_usb3_dataline_status(self, *channels):
        """Query USB3 boot defaults: {channel: {enabled, value}}, None on failure."""
        document = self.get_capability()
        if document and document.get("device", {}).get("default_status_mask") is True:
            if document.get("device", {}).get("default_usb3_data") is not True:
                raise FeatureNotSupportedError("Device does not declare USB3 default configuration")
            return self._get_default_status(CMD_GET_DEFAULT_USB3_DATALINE_STATUS, channels,
                                            self.channel_default_usb3_data_flag,
                                            self.channel_default_usb3_data_status,
                                            CMD_GET_DEFAULT_USB3_DATALINE_MASK)
        return self._default_usb3_exchange(CMD_GET_DEFAULT_USB3_DATALINE_STATUS, channels)

    def set_default_dataline_status(self, *channels, enable, status=None):
        """Deprecated USB2-only alias; this does not configure USB3 defaults."""
        _warn_legacy_api('set_default_dataline_status()', 'set_default_usb2_dataline_status()')
        return self.set_default_usb2_dataline_status(*channels, enable=enable, status=status)

    def get_default_dataline_status(self, *channels):
        """Deprecated USB2-only alias."""
        _warn_legacy_api('get_default_dataline_status()', 'get_default_usb2_dataline_status()')
        return self.get_default_usb2_dataline_status(*channels)

    @synchronized
    def set_auto_restore(self, enable: bool):
        """
        Enable or disable the auto-restore feature.

        :param enable: True to enable auto-restore, False to disable.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_AUTO_RESTORE].clear()
        self._send_packet(CMD_SET_AUTO_RESTORE, None, 1 if enable else 0)
        if self._wait_for_ack_with_recovery(CMD_SET_AUTO_RESTORE):
            return True
        logger.error("set_auto_restore No ACK!")
        return False

    @synchronized
    def get_auto_restore_status(self):
        """
        Query whether auto-restore is enabled.

        :returns: 1 if enabled, 0 if disabled, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_AUTO_RESTORE_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_AUTO_RESTORE_STATUS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.auto_restore_status
        logger.error("get_auto_restore_status No ACK!")
        return None

    def _require_upstream_host_switch(self):
        if not self._get_capabilities()["upstream_host_switch"].get("controllable"):
            raise FeatureNotSupportedError(
                "Device does not declare controllable upstream host selection")

    @synchronized
    def set_upstream_host(self, host: int):
        """Select Host1 or Host2. Current firmware persists selection in Flash.

        Requires the declared upstream-host capability. Unsupported devices raise
        FeatureNotSupportedError. Returns False on rejection or timeout.
        :param int host: Upstream host number, 1 or 2.
        :returns: Whether matching confirmation arrived.
        :rtype: bool
        :raises ValueError: Invalid host number.
        :raises FeatureNotSupportedError: Switching is unsupported.
        """
        if isinstance(host, bool) or not isinstance(host, int) or host not in (1, 2):
            raise ValueError("host must be 1 or 2")
        self._require_upstream_host_switch()
        self._upstream_host = None
        event = self.ack_events[CMD_SET_UPSTREAM_HOST]
        event.clear()
        self._send_packet(CMD_SET_UPSTREAM_HOST, None, host)
        return event.wait(self.com_timeout) and self._upstream_host == host

    @synchronized
    def get_upstream_host(self):
        """Return 0/1/2, or None on device rejection/communication failure.

        Unsupported products/firmware raise FeatureNotSupportedError.
        :returns: Firmware host value 0, 1 or 2, or None.
        :rtype: int or None
        :raises FeatureNotSupportedError: Switching is unsupported.
        """
        self._require_upstream_host_switch()
        self._upstream_host = None
        event = self.ack_events[CMD_GET_UPSTREAM_HOST]
        event.clear()
        self._send_packet(CMD_GET_UPSTREAM_HOST, None, 0)
        return self._upstream_host if event.wait(self.com_timeout) else None

    @synchronized
    def set_device_address(self, address: int):
        """
        Set the 16-bit device address.

        :param address: Address in the range 0x0000 - 0xFFFF.

        :returns: True if acknowledged, False otherwise.

        :raises ValueError: If the address is out of range.
        """
        if not (0 <= address <= 0xFFFF):
            raise ValueError("Address must be between 0x0000 and 0xFFFF")
        lsb = address & 0xFF
        msb = (address >> 8) & 0xFF
        ack_event = self.ack_events[CMD_SET_DEVICE_ADDRESS]
        ack_event.clear()
        self._device_address_reply = None
        self._send_packet(CMD_SET_DEVICE_ADDRESS, msb, lsb)
        if ack_event.wait(self.com_timeout) and self._device_address_reply == address:
            self.device_address = address
            return True
        logger.error("set_device_address No ACK!")
        return False

    @synchronized
    def get_device_address(self):
        """
        Query the current device address.

        :returns: The 16-bit device address, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_DEVICE_ADDRESS]
        ack_event.clear()
        self._send_packet(CMD_GET_DEVICE_ADDRESS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.device_address
        logger.error("get_device_address No ACK!")
        return None

    @synchronized
    def reset_hub(self):
        """Reset only the USB data Hub; attached USB devices disconnect.

        MCU/CMD and port power policies are not reset. Hub volatile chip
        configuration returns to reset/OTP defaults. Requires firmware declaring
        device.reset_hub=true; older firmware is never probed destructively.
        """
        document = self.get_capability()
        if not document or document.get("device", {}).get("reset_hub") is not True:
            raise FeatureNotSupportedError("Device does not declare Hub reset support")
        event = self.ack_events[CMD_RESET_HUB]
        event.clear()
        self._send_v3_packet(CMD_RESET_HUB)
        return bool(event.wait(max(2.0, self.com_timeout)) and
                    self._last_v3_status.get(CMD_RESET_HUB) == V3_STATUS_OK)

    @synchronized
    def reboot_mcu(self):
        """
        Reboot the device MCU.

        The MCU reboots ~100 ms after acknowledging, so the connection is lost and
        the device must typically be reconnected afterwards.

        :returns: True if the reboot command was acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_REBOOT_MCU]
        ack_event.clear()
        # Catch an ACK that may already be in flight.
        time.sleep(0.001)
        if ack_event.is_set():
            ack_event.clear()
            return True

        self._send_packet(CMD_REBOOT_MCU, None, None)
        # Longer timeout: the MCU delays ~100 ms after the ACK before rebooting.
        if ack_event.wait(0.2):
            return True
        logger.error("reboot_mcu No ACK!")
        return False

    @synchronized
    def factory_reset(self):
        """
        Reset the device to factory settings.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_FACTORY_RESET]
        ack_event.clear()
        self._send_packet(CMD_FACTORY_RESET, None, None)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("factory_reset No ACK!")
        return False

    @synchronized
    def identify_device(self):
        """
        Blink the device status LED quickly for a few seconds.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_IDENTIFY_DEVICE]
        ack_event.clear()
        self._send_packet(CMD_IDENTIFY_DEVICE, None, None)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("identify_device No ACK!")
        return False

    @staticmethod
    def _default_channel_name(channel):
        return f"CH{int(channel)}"

    @staticmethod
    def _encode_utf8_fit(text, max_bytes):
        data = str(text or "").strip().encode("utf-8")[:max_bytes]
        while True:
            try:
                data.decode("utf-8")
                return data
            except UnicodeDecodeError:
                data = data[:-1]

    @staticmethod
    def _encode_channel_name(name):
        return SmartUSBHub._encode_utf8_fit(name, 15)

    @staticmethod
    def _encode_device_alias(alias):
        return SmartUSBHub._encode_utf8_fit(alias, 15)

    @synchronized
    def set_device_alias(self, alias):
        """
        Store a custom device alias in the device.

        Empty aliases clear the custom alias. Alias is UTF-8, up to 15 bytes.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_SET_DEVICE_ALIAS]
        ack_event.clear()
        self._send_v3_packet(CMD_SET_DEVICE_ALIAS, self._encode_device_alias(alias))
        if ack_event.wait(max(0.2, self.com_timeout)):
            return True
        logger.error("set_device_alias No ACK!")
        return False

    @synchronized
    def get_device_alias(self):
        """
        Query the custom device alias.

        :returns: Alias string, or "" if unset or no response is received.
        """
        ack_event = self.ack_events[CMD_GET_DEVICE_ALIAS]
        ack_event.clear()
        self.device_alias = ""
        self._send_v3_packet(CMD_GET_DEVICE_ALIAS, b"")
        if ack_event.wait(max(0.2, self.com_timeout)):
            return self.device_alias or ""
        logger.debug("get_device_alias No ACK (may be old firmware)")
        return ""

    @synchronized
    def set_channel_name(self, channel, name):
        """
        Store a custom channel display name in the device.

        Empty names clear the custom name and make the device fall back to CHn.
        Names are stored as UTF-8, up to 15 bytes.

        :returns: True if acknowledged, False otherwise.
        """
        channel = int(channel)
        if channel < 1:
            raise ValueError("channel must be >= 1")
        ack_event = self.ack_events[CMD_SET_CHANNEL_NAME]
        ack_event.clear()
        payload = bytes([channel]) + self._encode_channel_name(name)
        self._send_v3_packet(CMD_SET_CHANNEL_NAME, payload)
        if ack_event.wait(max(0.2, self.com_timeout)):
            return True
        logger.error("set_channel_name No ACK!")
        return False

    @synchronized
    def get_channel_name(self, channel):
        """
        Query a channel display name from the device.

        :returns: Stored name, or default CHn if unset or no response is received.
        """
        channel = int(channel)
        if channel < 1:
            raise ValueError("channel must be >= 1")
        ack_event = self.ack_events[CMD_GET_CHANNEL_NAME]
        ack_event.clear()
        self.channel_names.pop(channel, None)
        self._send_v3_packet(CMD_GET_CHANNEL_NAME, [channel])
        if ack_event.wait(max(0.2, self.com_timeout)):
            return self.channel_names.get(channel, self._default_channel_name(channel))
        logger.debug("get_channel_name No ACK (may be old firmware)")
        return self._default_channel_name(channel)

    def get_channel_names(self, *channels):
        """Query display names for one or more channels."""
        resolved = self._resolve_channels(channels)
        return {ch: self.get_channel_name(ch) for ch in resolved}

    @staticmethod
    def _load_auth_issuer_public_key(key_material, ec, serialization):
        """Normalize a P-256 public-key object, PEM/DER, or SEC1 encoded point."""
        if hasattr(key_material, "verify") and hasattr(key_material, "curve"):
            key = key_material
        else:
            if isinstance(key_material, str):
                key_material = key_material.encode("ascii")
            if not isinstance(key_material, (bytes, bytearray)):
                raise AuthenticationTrustError("Trusted issuer key has an unsupported type.")
            encoded = bytes(key_material)
            try:
                if encoded.startswith(b"-----BEGIN"):
                    key = serialization.load_pem_public_key(encoded)
                elif len(encoded) in (33, 65) and encoded[:1] in (b"\x02", b"\x03", b"\x04"):
                    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), encoded)
                else:
                    key = serialization.load_der_public_key(encoded)
            except Exception as exc:
                raise AuthenticationTrustError("Trusted issuer public key is invalid.") from exc

        if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
            raise AuthenticationTrustError("Trusted issuer key must be a P-256 public key.")
        return key

    @staticmethod
    def _parse_auth_certificate(certificate):
        """Parse and structurally validate the canonical 125-byte certificate."""
        certificate = bytes(certificate)
        if len(certificate) != AUTH_CERTIFICATE_SIZE:
            raise DeviceAuthenticationCommunicationError(
                f"Certificate has {len(certificate)} bytes; expected {AUTH_CERTIFICATE_SIZE}.")
        if certificate[:4] != AUTH_CERT_MAGIC:
            raise DeviceAuthenticationRejectedError("Certificate magic is invalid.")
        if certificate[4] != AUTH_CERT_VERSION:
            raise DeviceAuthenticationRejectedError(
                f"Unsupported certificate format version {certificate[4]}.")
        if certificate[5] != AUTH_ALGORITHM_P256_SHA256:
            raise DeviceAuthenticationRejectedError(
                f"Unsupported certificate algorithm {certificate[5]}.")
        if certificate[15] != 0:
            raise DeviceAuthenticationRejectedError("Certificate reserved field is not canonical.")
        if certificate[28] not in (0x02, 0x03):
            raise DeviceAuthenticationRejectedError("Certificate public key is not compressed P-256.")

        return {
            "certificate": certificate,
            "issuer_id": int.from_bytes(certificate[6:8], "big"),
            "certificate_serial": int.from_bytes(certificate[8:12], "big"),
            "product_type": certificate[12],
            "hardware_major": certificate[13],
            "hardware_minor": certificate[14],
            "device_uid": certificate[16:28],
            "public_key_compressed": certificate[28:61],
            "issuer_signature": certificate[61:125],
        }

    @staticmethod
    def _raise_auth_status(status, operation):
        """Translate a firmware authentication status into a stable SDK exception."""
        if status == AUTH_STATUS_UNSUPPORTED:
            raise AuthenticationNotSupportedError(
                f"Device firmware does not support {operation} authentication.")
        labels = {
            AUTH_STATUS_INVALID_REQUEST: "invalid request",
            AUTH_STATUS_NOT_PROVISIONED: "device is not provisioned",
            AUTH_STATUS_INVALID_PROVISIONING: "device provisioning is invalid",
            AUTH_STATUS_SIGNING_FAILED: "device challenge signing failed",
        }
        label = labels.get(status, f"unknown status 0x{status:02X}")
        raise DeviceAuthenticationRejectedError(f"Authentication rejected: {label}.")

    @synchronized
    def authenticate_device(self, trusted_issuers, nonce=None, timeout=2.0):
        """
        Optionally verify the per-device certificate and a fresh P-256 challenge.

        This method is deliberately not called by the constructor. Open protocols,
        Python automation and user-developed software remain usable without any
        authentication policy; official applications can call this method after
        connecting and enforce their own policy.

        ``trusted_issuers`` maps the certificate's integer issuer ID to a P-256
        public key. Values may be cryptography public-key objects, PEM/DER bytes,
        PEM strings, or compressed/uncompressed SEC1 points.

        ``timeout`` controls the certificate exchange and is also used as the
        caller-requested lower bound for the challenge exchange.  The challenge
        always receives at least ``AUTH_CHALLENGE_TIMEOUT_MIN`` seconds because
        current HBL firmware performs P-256 signing in software on the MCU.

        :returns: A dict containing authenticated certificate metadata.

        :raises AuthenticationNotSupportedError: Firmware has no authentication commands.
        :raises DeviceAuthenticationCommunicationError: The exchange times out or is malformed.
        :raises AuthenticationTrustError: The issuer is absent from the supplied trust store.
        :raises DeviceAuthenticationRejectedError: A certificate or proof is invalid.
        :raises AuthenticationDependencyError: Install ``smartusbhub[auth]`` first.
        """
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec, utils
        except ImportError as exc:
            raise AuthenticationDependencyError(
                "Device authentication requires the optional 'cryptography' package; "
                "install smartusbhub[auth].") from exc

        if not isinstance(trusted_issuers, dict):
            raise AuthenticationTrustError("trusted_issuers must be a mapping keyed by issuer ID.")
        if nonce is None:
            nonce = os.urandom(AUTH_NONCE_SIZE)
        else:
            nonce = bytes(nonce)
        if len(nonce) != AUTH_NONCE_SIZE:
            raise ValueError(f"nonce must be exactly {AUTH_NONCE_SIZE} bytes")
        timeout = max(float(timeout), self.com_timeout)

        cert_event = self.ack_events[CMD_AUTH_GET_CERTIFICATE]
        cert_event.clear()
        self._auth_certificate_response = None
        self._send_v3_packet(CMD_AUTH_GET_CERTIFICATE, b"")
        if not self._wait_for_ack_with_recovery(CMD_AUTH_GET_CERTIFICATE, timeout):
            if self._auth_certificate_response and self._auth_certificate_response[0]:
                self._raise_auth_status(self._auth_certificate_response[0], "certificate")
            raise DeviceAuthenticationCommunicationError(
                "Timed out while reading the device certificate.")
        response = self._auth_certificate_response
        if not response:
            raise DeviceAuthenticationCommunicationError("Empty certificate response.")
        if response[0] != AUTH_STATUS_OK:
            self._raise_auth_status(response[0], "certificate")
        if len(response) != 1 + AUTH_CERTIFICATE_SIZE:
            raise DeviceAuthenticationCommunicationError(
                f"Certificate response has {len(response)} bytes; expected "
                f"{1 + AUTH_CERTIFICATE_SIZE}.")

        info = self._parse_auth_certificate(response[1:])
        if self.product_type is not None and info["product_type"] != self.product_type:
            raise DeviceAuthenticationRejectedError(
                "Certificate product type does not match the connected device.")
        if self.hardware_version is not None and info["hardware_major"] != self.hardware_version:
            raise DeviceAuthenticationRejectedError(
                "Certificate hardware version does not match the connected device.")

        issuer_material = trusted_issuers.get(info["issuer_id"])
        if issuer_material is None:
            issuer_material = trusted_issuers.get(str(info["issuer_id"]))
        if issuer_material is None:
            raise AuthenticationTrustError(
                f"No trusted public key for issuer ID {info['issuer_id']}.")
        issuer_key = self._load_auth_issuer_public_key(issuer_material, ec, serialization)

        issuer_raw_signature = info["issuer_signature"]
        issuer_der_signature = utils.encode_dss_signature(
            int.from_bytes(issuer_raw_signature[:32], "big"),
            int.from_bytes(issuer_raw_signature[32:], "big"),
        )
        try:
            issuer_key.verify(
                issuer_der_signature,
                info["certificate"][:61],
                ec.ECDSA(hashes.SHA256()),
            )
            device_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), info["public_key_compressed"])
        except (InvalidSignature, ValueError) as exc:
            raise DeviceAuthenticationRejectedError(
                "Device certificate signature is invalid.") from exc

        challenge_event = self.ack_events[CMD_AUTH_CHALLENGE]
        challenge_event.clear()
        self._auth_challenge_response = None
        self._send_v3_packet(CMD_AUTH_CHALLENGE, nonce)
        challenge_timeout = max(timeout, AUTH_CHALLENGE_TIMEOUT_MIN)
        if not self._wait_for_ack_with_recovery(CMD_AUTH_CHALLENGE, challenge_timeout):
            if self._auth_challenge_response and self._auth_challenge_response[0]:
                self._raise_auth_status(self._auth_challenge_response[0], "challenge")
            raise DeviceAuthenticationCommunicationError(
                "Timed out while waiting for the device challenge signature.")
        response = self._auth_challenge_response
        if not response:
            raise DeviceAuthenticationCommunicationError("Empty challenge response.")
        if response[0] != AUTH_STATUS_OK:
            self._raise_auth_status(response[0], "challenge")
        if len(response) != 1 + AUTH_SIGNATURE_SIZE:
            raise DeviceAuthenticationCommunicationError(
                f"Challenge response has {len(response)} bytes; expected "
                f"{1 + AUTH_SIGNATURE_SIZE}.")

        raw_signature = response[1:]
        der_signature = utils.encode_dss_signature(
            int.from_bytes(raw_signature[:32], "big"),
            int.from_bytes(raw_signature[32:], "big"),
        )
        challenge_hash = hashlib.sha256(
            AUTH_CHALLENGE_DOMAIN + nonce +
            hashlib.sha256(info["certificate"]).digest()
        ).digest()
        try:
            device_key.verify(
                der_signature,
                challenge_hash,
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )
        except InvalidSignature as exc:
            raise DeviceAuthenticationRejectedError(
                "Device challenge signature is invalid.") from exc

        info = dict(info)
        info.pop("issuer_signature", None)
        info["device_uid"] = info["device_uid"].hex()
        info["public_key_fingerprint"] = hashlib.sha256(
            info["public_key_compressed"]).hexdigest()
        info["authenticated"] = True
        self.authentication_info = info
        return info

    @synchronized
    def get_firmware_version(self):
        """
        Query the firmware version.

        :returns: The firmware version, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_FIRMWARE_VERSION]
        ack_event.clear()
        self._send_packet(CMD_GET_FIRMWARE_VERSION, None, None)
        if ack_event.wait(self.com_timeout):
            return self.firmware_version
        logger.error("get_firmware_version No ACK!")
        return None

    def get_firmware_version_major(self):
        """
        Return the cached firmware major version, querying the device if needed.

        Older firmware replies only with the minor version byte; those devices
        are treated as major version 1 for backward compatibility.
        """
        if self.firmware_version_major is None:
            self.get_firmware_version()
        return self.firmware_version_major

    def get_firmware_version_string(self):
        """Format the cached firmware version for display.

        Returns ``V<major>.<minor>`` without zero padding, or ``V1.0.0`` for
        the first public USB3 release. Returns "Unknown" when unavailable.
        """
        major = self.firmware_version_major if self.firmware_version_major is not None else 1
        minor = self.firmware_version_minor
        if minor is None:
            minor = self.firmware_version
        if minor is None:
            return "Unknown"
        # USB3 first public release: the existing wire header carries major/minor;
        # patch zero is implicit and does not change the DFU header layout.
        if self.product_type == 0x04 and major == 1 and minor == 0 and not self._is_legacy_v1_firmware():
            return "V1.0.0"
        return f"V{major}.{minor}"

    @synchronized
    def get_hardware_version(self):
        """
        Query the hardware version.

        :returns: The hardware version, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_HARDWARE_VERSION]
        ack_event.clear()
        self._send_packet(CMD_GET_HARDWARE_VERSION, None, None)
        if ack_event.wait(self.com_timeout):
            return self.hardware_version
        logger.error("get_hardware_version No ACK!")
        return None

    @synchronized
    def get_product_type(self):
        """
        Query the product-type ID.

        Optional command: older firmware does not respond, in which case None is
        returned (logged at debug level, not as an error).

        :returns: The product-type ID, or None if unsupported/no response.
        """
        ack_event = self.ack_events[CMD_GET_PRODUCT_TYPE]
        ack_event.clear()
        self._send_packet(CMD_GET_PRODUCT_TYPE, None, None)
        if ack_event.wait(self.com_timeout):
            return self.product_type
        logger.debug("get_product_type No ACK (may be old firmware)")
        return None

    def _declared_model(self):
        # BASIC/ADV share the USB3 firmware/authentication family ID 0x04.
        model = (getattr(self, "_device_capabilities", None) or {}).get("model")
        if self.product_type == 0x04 and model in ("HBP_USB3_4CH", "HBP_USB3_4CH_ADV"):
            return model
        return None

    @synchronized
    def get_product_name(self):
        """
        Get the product name for the connected device.

        :returns: The product name (e.g. "HBP_USB2_4CH"), an "Unknown(...)" string, or None if the product type is unavailable.
        """
        if self.product_type is None:
            self.product_type = self.get_product_type()
        if self.product_type is None:
            return None
        product_info = PRODUCT_CATALOG.get(self.product_type)
        return self._declared_model() or (product_info["name"] if product_info is not None else f"Unknown({self.product_type:#02x})")

    @synchronized
    def get_max_channels(self):
        """
        Query the maximum channel count.

        Optional command: older firmware does not respond, in which case None is
        returned (logged at debug level, not as an error).

        :returns: The maximum channel count, or None if unsupported/no response.
        """
        ack_event = self.ack_events[CMD_GET_MAX_CHANNELS]
        ack_event.clear()
        self._send_packet(CMD_GET_MAX_CHANNELS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.max_channels
        logger.debug("get_max_channels No ACK (may be old firmware)")
        return None

    @synchronized
    def get_serial_no(self):
        """
        Query the device serial number.

        :returns: The serial-number string ("N/A" if unavailable), or None if no response.
        """
        if self._is_legacy_v1_firmware():
            self.serial_no = self.serial_no or "N/A"
            return self.serial_no

        ack_event = self.ack_events[CMD_GET_SERIAL_NO]
        ack_event.clear()
        self.serial_no = None
        self._send_packet(CMD_GET_SERIAL_NO, None, None)
        if ack_event.wait(self.com_timeout):
            deadline = time.time() + max(0.2, self.com_timeout)
            while self.serial_no is None and time.time() < deadline:
                time.sleep(0.01)
            return self.serial_no
        logger.debug("get_serial_no No ACK (may be old firmware)")
        return None


def decode_usb3_capture_batch(payload):
    """Decode 0x28 measurement STREAM batches (not the one-byte command ACK).

    Timestamps bound the host-requested measurement hardware snapshot: ``refresh_us`` is the
    request time and ``read_us`` the completed read, NOT the ADC conversion
    instant or USB send time. Values use mV/mA. All counters wrap at 2**32.
    Conversion count identifies measurement hardware progress independently of MCU sequence.
    """
    import struct
    payload = bytes(payload)
    if len(payload) < 16:
        raise ValueError("Truncated capture header")
    version, count, record_size, mask, drops, errors, duplicates = struct.unpack_from(
        '<4B3I', payload)
    if (version not in (1, 2, 3) or not 0 <= count <= 7 or record_size != 48
            or (mask & 15) != 15 or mask not in (15, 31)
            or (version == 1 and mask != 15)):
        raise ValueError("Unsupported capture format")
    header = 20 if version >= 3 else 16
    if len(payload) != header + count * record_size:
        raise ValueError("Invalid capture length")
    rate = struct.unpack_from('<H', payload, 16)[0] if version >= 3 else 500
    if not 0 < rate <= 65535:
        raise ValueError('Invalid sample rate')
    records = []
    for offset in range(header, len(payload), record_size):
        values = struct.unpack_from('<4I8H', payload, offset)
        records.append(dict(sequence=values[0], refresh_us=values[1],
                            read_us=values[2], conversion_count=values[3],
                            voltage_mv=list(values[4:8]), current_ma=list(values[8:12])))
        records[-1]['power_uw'] = list(struct.unpack_from('<4I', payload, offset + 32))
    return dict(drops=drops, errors=errors, duplicates=duplicates, records=records,
                filter=(mask >> 4) & 1, sample_rate=rate)


# Disconnect every open instance on interpreter exit as a safety net for callers
# that forget to disconnect() or use the context-manager form.
atexit.register(SmartUSBHub._cleanup_all_instances)
