import threading

import pytest

from smartusbhub import CMD_GET_CHANNEL_MEASUREMENTS, SmartUSBHub, V3_STATUS_OK


def make_hub(max_channels=7):
    hub = object.__new__(SmartUSBHub)
    hub.max_channels = max_channels
    hub.product_type = None
    hub.channel_voltages = {}
    hub.channel_currents = {}
    hub.channel_measurement_fresh = {}
    hub.channel_measurement_valid = {}
    hub.channel_measurement_sample_tick = {}
    hub.channel_oc_active = {}
    hub.channel_oc_latch = {}
    hub._measurement_stream_condition = threading.Condition()
    hub._measurement_stream_seq = 0
    hub._measurement_stream_tick = None
    hub._measurement_stream_period_ms = None
    hub._last_v3_status = {}
    return hub


@pytest.mark.unit
def test_legacy_measurement_payload_with_fresh_mask():
    hub = make_hub()
    payload = bytes([
        0x03,  # channels 1 and 2
        0x01,  # only channel 1 is fresh
        0x13, 0x88, 0x00, 0x64,  # ch1: 5000 mV, 100 mA
        0x13, 0x56, 0x00, 0x2A,  # ch2: 4950 mV, 42 mA
    ])

    hub._handle_legacy_measurements(payload)

    assert hub.channel_voltages == {1: 5000, 2: 4950}
    assert hub.channel_currents == {1: 100, 2: 42}
    assert hub.channel_measurement_fresh == {1: True, 2: False}


@pytest.mark.unit
def test_v3_measurement_payload_updates_cache_and_stream_metadata():
    hub = make_hub()
    payload = bytes([
        0x03,  # channels 1 and 2
        0x03,  # fresh mask
        0x01,  # only channel 1 valid
        20,    # sample period ms
        0x78, 0x56, 0x34, 0x12,  # sample tick
        0x88, 0x13, 0x64, 0x00,  # ch1: 5000 mV, 100 mA, little endian
        0x56, 0x13, 0x2A, 0x00,  # ch2: 4950 mV, 42 mA
    ])

    hub._handle_v3_measurements(payload)

    assert hub._last_v3_status[CMD_GET_CHANNEL_MEASUREMENTS] == V3_STATUS_OK
    assert hub.channel_voltages == {1: 5000, 2: 4950}
    assert hub.channel_currents == {1: 100, 2: 42}
    assert hub.channel_measurement_fresh == {1: True, 2: True}
    assert hub.channel_measurement_valid == {1: True, 2: False}
    assert hub.channel_measurement_sample_tick == {1: 0x12345678, 2: 0x12345678}
    assert hub._measurement_stream_tick == 0x12345678
    assert hub._measurement_stream_period_ms == 20
    assert hub._measurement_stream_seq == 1


@pytest.mark.unit
def test_measurement_snapshot_can_include_stream_metadata():
    hub = make_hub()
    hub.channel_voltages[1] = 5000
    hub.channel_currents[1] = 100
    hub.channel_measurement_fresh[1] = True
    hub.channel_measurement_valid[1] = True
    hub.channel_measurement_sample_tick[1] = 123
    hub._measurement_stream_period_ms = 20

    snapshot = hub._measurement_snapshot((1, 2), valid_default=False, include_stream_meta=True)

    assert snapshot == {
        1: {
            "voltage": 5000,
            "current": 100,
            "fresh": True,
            "stale": False,
            "valid": True,
            "sample_tick": 123,
            "sample_period_ms": 20,
        }
    }


@pytest.mark.unit
def test_overcurrent_status_handler_updates_all_channels():
    hub = make_hub(max_channels=4)

    hub._handle_oc_status(0b0101, 0b0011)

    assert hub.channel_oc_active == {
        1: True,
        2: False,
        3: True,
        4: False,
    }
    assert hub.channel_oc_latch == {
        1: True,
        2: True,
        3: False,
        4: False,
    }
