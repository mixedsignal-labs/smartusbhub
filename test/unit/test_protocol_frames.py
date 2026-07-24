import threading

import pytest

from smartusbhub import (
    CMD_GET_CHANNEL_MEASUREMENTS,
    CMD_GET_CHANNEL_VOLTAGE,
    CMD_SET_CHANNEL_POWER,
    SmartUSBHub,
    V3_FLAG_STREAM,
    V3_HEADER_LEN,
)


def make_hub():
    hub = object.__new__(SmartUSBHub)
    hub.lock = threading.Lock()
    return hub


def build_v3_frame(hub, cmd, payload=b"", flags=0):
    payload = bytes(payload)
    frame = bytearray([
        0x55,
        0xAB,
        0xCD,
        0xEF,
        cmd & 0xFF,
        flags & 0xFF,
        len(payload) & 0xFF,
        (len(payload) >> 8) & 0xFF,
        0x00,
        0x00,
    ]) + payload
    crc = hub._cal_crc16(frame)
    frame[8] = crc & 0xFF
    frame[9] = (crc >> 8) & 0xFF
    return frame


@pytest.mark.protocol
def test_parse_v1_frame():
    hub = make_hub()
    channel_mask = 0x03
    value = 0x01
    checksum = (CMD_SET_CHANNEL_POWER + channel_mask + value) & 0xFF
    frame = bytes([0x55, 0x5A, CMD_SET_CHANNEL_POWER, channel_mask, value, checksum])

    assert hub._parse_protocol_frame(frame) == (
        CMD_SET_CHANNEL_POWER,
        channel_mask,
        value,
        6,
    )


@pytest.mark.protocol
def test_parse_v1_frame_rejects_bad_checksum():
    hub = make_hub()
    frame = bytes([0x55, 0x5A, CMD_SET_CHANNEL_POWER, 0x01, 0x01, 0x00])

    assert hub._parse_protocol_frame(frame) is None

@pytest.mark.protocol
def test_parse_v2_frame():
    hub = make_hub()
    channel_mask = 0x01
    value_0 = 0x13
    value_1 = 0x56
    checksum = (CMD_GET_CHANNEL_VOLTAGE + channel_mask + value_0 + value_1) & 0xFF
    frame = bytes([
        0x55,
        0x5A,
        CMD_GET_CHANNEL_VOLTAGE,
        channel_mask,
        value_0,
        value_1,
        checksum,
    ])

    assert hub._parse_protocol_frame(frame) == (
        CMD_GET_CHANNEL_VOLTAGE,
        channel_mask,
        [value_0, value_1],
        7,
    )


@pytest.mark.protocol
def test_parse_v3_frame():
    hub = make_hub()
    payload = bytes([0x03, 0x03, 0x03, 20, 1, 0, 0, 0])
    frame = build_v3_frame(hub, CMD_GET_CHANNEL_MEASUREMENTS, payload)

    cmd, channel, value, length = hub._parse_protocol_frame(frame)

    assert cmd == CMD_GET_CHANNEL_MEASUREMENTS
    assert channel == 0
    assert value == {"v3": True, "stream": False, "payload": payload}
    assert length == V3_HEADER_LEN + len(payload)


@pytest.mark.protocol
def test_parse_v3_stream_frame_sets_stream_flag():
    hub = make_hub()
    payload = bytes([0x01, 0x01, 0x01, 20, 1, 0, 0, 0, 0x34, 0x12, 0x78, 0x56])
    frame = build_v3_frame(hub, CMD_GET_CHANNEL_MEASUREMENTS, payload, flags=V3_FLAG_STREAM)

    _, _, value, _ = hub._parse_protocol_frame(frame)

    assert value["stream"] is True


@pytest.mark.protocol
def test_parse_v3_frame_rejects_bad_crc():
    hub = make_hub()
    frame = build_v3_frame(hub, CMD_GET_CHANNEL_MEASUREMENTS, b"\x01\x02")
    frame[-1] ^= 0xFF

    assert hub._parse_protocol_frame(frame) is None
