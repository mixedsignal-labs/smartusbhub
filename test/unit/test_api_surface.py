import threading

import pytest

from smartusbhub import (
    CMD_CLEAR_CHANNEL_OC_LATCH,
    CMD_SET_DEVICE_ADDRESS,
    FeatureNotSupportedError,
    SmartUSBHub,
)


def make_hub(max_channels=7, product_type=0x03):
    hub = object.__new__(SmartUSBHub)
    hub.lock = threading.Lock()
    hub.max_channels = max_channels
    hub.product_type = product_type
    hub.com_timeout = 0.01
    hub.ack_events = {
        CMD_CLEAR_CHANNEL_OC_LATCH: threading.Event(),
        CMD_SET_DEVICE_ADDRESS: threading.Event(),
    }
    return hub


@pytest.mark.unit
def test_clear_channel_oc_latch_sends_requested_channels():
    hub = make_hub()
    sent = []

    def fake_send_packet(cmd, channels, data=None):
        sent.append((cmd, channels, data))
        hub.ack_events[cmd].set()

    hub._send_packet = fake_send_packet

    assert hub.clear_channel_oc_latch(1, 3, 5)
    assert sent == [(CMD_CLEAR_CHANNEL_OC_LATCH, (1, 3, 5), 0)]


@pytest.mark.unit
def test_clear_channel_oc_latch_without_channels_defaults_to_all_channels():
    hub = make_hub(max_channels=4)
    sent = []

    def fake_send_packet(cmd, channels, data=None):
        sent.append((cmd, channels, data))
        hub.ack_events[cmd].set()

    hub._send_packet = fake_send_packet

    assert hub.clear_channel_oc_latch()
    assert sent == [(CMD_CLEAR_CHANNEL_OC_LATCH, (1, 2, 3, 4), 0)]


@pytest.mark.unit
@pytest.mark.parametrize("address", [-1, 0x10000])
def test_set_device_address_rejects_out_of_range_values(address):
    hub = make_hub()

    with pytest.raises(ValueError):
        hub.set_device_address(address)


@pytest.mark.unit
def test_single_channel_measurement_apis_reject_channel_lists():
    hub = make_hub()

    with pytest.raises(ValueError):
        hub.get_channel_voltage([1])

    with pytest.raises(ValueError):
        hub.get_channel_current((1,))


@pytest.mark.unit
def test_unknown_feature_name_is_rejected():
    hub = make_hub()

    with pytest.raises(FeatureNotSupportedError):
        hub._check_feature_support("not_a_feature")
