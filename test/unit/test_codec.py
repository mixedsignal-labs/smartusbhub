"""
Direct unit tests for the pure ``_Codec`` wire-protocol codec.

These exercise framing in isolation — no ``SmartUSBHub`` instance, no serial, no
threads — which is the whole point of extracting the codec: framing is now a pure,
independently testable unit and a single source of truth for the send path, the
receive loop's sizing and the parser.
"""
import pytest

import smartusbhub as m
from smartusbhub import (
    _Codec,
    SmartUSBHub,
    CMD_SET_CHANNEL_POWER,
    CMD_GET_CHANNEL_VOLTAGE,
    CMD_GET_CHANNEL_MEASUREMENTS,
    V3_HEADER_LEN,
    V3_MAX_DATA_LEN,
    V3_FLAG_STREAM,
)
from fake_device import cal_crc16


@pytest.mark.unit
def test_single_source_of_v2_framing_table():
    """The class alias and the codec table are literally the same object."""
    assert SmartUSBHub._V2_REPLY_COMMANDS is _Codec.V2_REPLY_COMMANDS


@pytest.mark.unit
def test_crc16_matches_reference():
    for data in (b"", b"\x00", b"\x55\xAB\xCD\xEF", bytes(range(32))):
        assert _Codec.crc16(data) == cal_crc16(data)


@pytest.mark.unit
def test_encode_v1v2_builds_v1_frame_with_checksum():
    packet = _Codec.encode_v1v2(CMD_SET_CHANNEL_POWER, 0x05, [0x01])
    assert packet[:5] == bytes([0x55, 0x5A, CMD_SET_CHANNEL_POWER, 0x05, 0x01])
    assert packet[5] == (CMD_SET_CHANNEL_POWER + 0x05 + 0x01) & 0xFF


@pytest.mark.unit
def test_encode_v3_has_valid_crc_and_length():
    payload = [0x7F, 0x02]
    packet = _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, payload)
    assert packet[:4] == bytes([0x55, 0xAB, 0xCD, 0xEF])
    assert packet[6] | (packet[7] << 8) == len(payload)
    crc_data = bytearray(packet)
    crc_data[8] = crc_data[9] = 0
    assert packet[8] | (packet[9] << 8) == cal_crc16(crc_data)
    assert packet[V3_HEADER_LEN:] == bytes(payload)


@pytest.mark.unit
def test_encode_v3_rejects_oversized_payload():
    with pytest.raises(ValueError):
        _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, b"\x00" * (V3_MAX_DATA_LEN + 1))


@pytest.mark.unit
def test_parse_v3_rejects_oversized_declared_payload():
    packet = bytearray([
        0x55, 0xAB, 0xCD, 0xEF,
        CMD_GET_CHANNEL_MEASUREMENTS,
        0x00,
        (V3_MAX_DATA_LEN + 1) & 0xFF,
        ((V3_MAX_DATA_LEN + 1) >> 8) & 0xFF,
        0x00, 0x00,
    ])

    assert _Codec.parse_frame(packet) is None


@pytest.mark.unit
def test_encode_v3_accepts_int_list_and_none():
    assert _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, 0x05)[V3_HEADER_LEN:] == b"\x05"
    assert _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, [1, 2])[V3_HEADER_LEN:] == b"\x01\x02"
    assert _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, None)[V3_HEADER_LEN:] == b""


@pytest.mark.unit
def test_parse_v1_roundtrip():
    packet = _Codec.encode_v1v2(CMD_SET_CHANNEL_POWER, 0x03, [0x01])
    assert _Codec.parse_frame(bytes(packet)) == (CMD_SET_CHANNEL_POWER, 0x03, 0x01, 6)


@pytest.mark.unit
def test_parse_v2_frame_two_payload_bytes():
    # CMD_GET_CHANNEL_VOLTAGE is in the V2 table -> 7-byte frame, value is [hi, lo].
    packet = _Codec.encode_v1v2(CMD_GET_CHANNEL_VOLTAGE, 0x01, [0x12, 0x34])
    assert _Codec.parse_frame(bytes(packet)) == (CMD_GET_CHANNEL_VOLTAGE, 0x01, [0x12, 0x34], 7)


@pytest.mark.unit
def test_parse_v3_roundtrip_and_stream_flag():
    packet = _Codec.encode_v3(CMD_GET_CHANNEL_MEASUREMENTS, [0x0A, 0x0B])
    cmd, channel, value, length = _Codec.parse_frame(bytes(packet))
    assert cmd == CMD_GET_CHANNEL_MEASUREMENTS
    assert channel == 0
    assert value["v3"] is True and value["stream"] is False
    assert value["payload"] == b"\x0A\x0B"
    assert length == len(packet)

    # A frame whose flags carry the stream bit is reported as a notification.
    streamed = bytearray(packet)
    streamed[5] = V3_FLAG_STREAM
    crc = _Codec.crc16(bytes(streamed[:8]) + b"\x00\x00" + bytes(streamed[V3_HEADER_LEN:]))
    streamed[8] = crc & 0xFF
    streamed[9] = (crc >> 8) & 0xFF
    assert _Codec.parse_frame(bytes(streamed))[2]["stream"] is True


@pytest.mark.unit
def test_parse_rejects_bad_checksum_and_partial():
    good = _Codec.encode_v1v2(CMD_SET_CHANNEL_POWER, 0x03, [0x01])
    bad = bytearray(good)
    bad[-1] ^= 0xFF
    assert _Codec.parse_frame(bytes(bad)) is None        # corrupt checksum
    assert _Codec.parse_frame(bytes(good[:4])) is None   # partial frame -> need more
