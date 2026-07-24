"""
Offline tests for callback registration, product-info lookup, and the receive
loop's frame dispatch (including byte-stream splitting/concatenation and the
rule that unsolicited stream frames must not satisfy a pending ACK).
"""
import time

import pytest

import smartusbhub as m
from smartusbhub import PRODUCT_TYPE_TABLE, SmartUSBHub
from fake_device import make_live_hub, frame_v1


@pytest.fixture
def live(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch)
    try:
        yield hub, device, fake
    finally:
        hub.disconnect()


# -- get_product_info (pure static lookup) --------------------------------
@pytest.mark.unit
def test_get_product_info_known_and_unknown():
    info = SmartUSBHub.get_product_info(0x03)
    assert info is PRODUCT_TYPE_TABLE[0x03]
    assert info["name"] == "HBP_USB2_7CH_ADV"
    assert SmartUSBHub.get_product_info(0x99) is None


# -- register_callback -----------------------------------------------------
@pytest.mark.unit
def test_register_callback_fires_on_ack(live):
    hub, device, _ = live
    received = []
    hub.register_callback(m.CMD_GET_CHANNEL_POWER_STATUS,
                          lambda channel, value: received.append((channel, value)))
    device.power[1] = 1

    hub.get_channel_power_status(1)
    time.sleep(0.02)

    assert received, "callback was not invoked on ACK"
    assert received[-1][1] == 1


@pytest.mark.unit
def test_register_callback_ignores_unknown_command(live):
    hub, _, _ = live
    # 0xEE is not an ACK command; registration must be a no-op, not an error.
    hub.register_callback(0xEE, lambda c, v: None)
    assert 0xEE not in hub.callbacks


@pytest.mark.unit
def test_callback_exception_does_not_break_receiver(live):
    hub, device, _ = live

    def boom(channel, value):
        raise RuntimeError("callback failure")

    hub.register_callback(m.CMD_GET_CHANNEL_POWER_STATUS, boom)
    device.power[1] = 1

    # The receive thread must survive a throwing callback and still return data.
    assert hub.get_channel_power_status(1) == 1


# -- register_disconnect_callback -----------------------------------------
@pytest.mark.unit
def test_disconnect_callback_fires_on_serial_error(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch)
    fired = []
    hub.register_disconnect_callback(lambda: fired.append(True))

    # Simulate an unexpected serial failure inside the receive loop.
    def raise_error(size=1):
        raise OSError("simulated unplug")

    fake.feed(b"\x55\x5A")          # ensure in_waiting > 0 so read() is called
    fake.read = raise_error
    time.sleep(0.1)

    assert fired == [True]
    hub.disconnect()


# -- receive-loop framing --------------------------------------------------
@pytest.mark.unit
def test_split_frame_across_reads_is_reassembled(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        frame = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x01, 1)
        ack = hub.ack_events[m.CMD_GET_CHANNEL_POWER_STATUS]
        ack.clear()

        # Feed the frame in two halves with a gap; the loop must reassemble it.
        fake.feed(frame[:3])
        time.sleep(0.03)
        fake.feed(frame[3:])

        assert ack.wait(0.5)
        assert hub.channel_power_status.get(1) == 1
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_two_frames_in_one_read_are_both_dispatched(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        f1 = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x01, 1)
        f2 = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x02, 0)
        fake.feed(f1 + f2)
        time.sleep(0.1)

        assert hub.channel_power_status.get(1) == 1
        assert hub.channel_power_status.get(2) == 0
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_leading_garbage_before_frame_is_skipped(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        frame = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x04, 1)
        fake.feed(b"\x00\xFF\x12" + frame)
        time.sleep(0.1)

        assert hub.channel_power_status.get(3) == 1
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_oversized_v3_header_does_not_block_following_frame(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        oversized = bytes([
            0x55, 0xAB, 0xCD, 0xEF,
            0x7E,
            m.V3_FLAG_STREAM,
            0xFF, 0xFF,
            0x00, 0x00,
        ])
        valid = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x01, 1)
        fake.feed(oversized + valid)

        deadline = time.monotonic() + 0.5
        while hub.channel_power_status.get(1) != 1 and time.monotonic() < deadline:
            time.sleep(0.01)

        assert hub.channel_power_status.get(1) == 1
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_invalid_v3_magic_does_not_block_following_frame(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        invalid_magic = bytes([
            0x55, 0xAB, 0x00, 0x00,
            0x7E,
            m.V3_FLAG_STREAM,
            m.V3_MAX_DATA_LEN, 0x00,
            0x00, 0x00,
        ])
        valid = frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 0x01, 1)
        fake.feed(invalid_magic + valid)

        deadline = time.monotonic() + 0.5
        while hub.channel_power_status.get(1) != 1 and time.monotonic() < deadline:
            time.sleep(0.01)

        assert hub.channel_power_status.get(1) == 1
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_stream_frame_does_not_satisfy_pending_ack(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        ack = hub.ack_events[m.CMD_GET_CHANNEL_MEASUREMENTS]
        ack.clear()
        # An unsolicited stream notification must update caches but NOT set the ACK.
        device.voltage[1] = 4200
        stream = device.build_measurement_frame(0x01, flags=m.V3_FLAG_STREAM)
        fake.feed(stream)
        time.sleep(0.1)

        assert ack.is_set() is False
        assert hub.channel_voltages.get(1) == 4200
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_stream_measurements_delivered_to_blocking_reader(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False)
    try:
        device.voltage[1] = 5000
        device.current[1] = 120

        # Deliver a stream frame shortly after the reader starts blocking.
        def deliver():
            time.sleep(0.03)
            fake.feed(device.build_measurement_frame(0x01, tick=0x1000,
                                                     flags=m.V3_FLAG_STREAM))

        import threading
        threading.Thread(target=deliver, daemon=True).start()

        result = hub.get_stream_channel_measurements(1, timeout=1.0)
        assert result is not None
        assert result[1]["voltage"] == 5000
        assert result[1]["current"] == 120
        assert result[1]["sample_period_ms"] == 20
    finally:
        hub.disconnect()
