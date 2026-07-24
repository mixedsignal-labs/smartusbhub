import threading

import pytest

from smartusbhub import FeatureNotSupportedError, PRODUCT_TYPE_TABLE, SmartUSBHub


def make_hub(**attrs):
    hub = object.__new__(SmartUSBHub)
    hub.max_channels = attrs.pop("max_channels", None)
    hub.product_type = attrs.pop("product_type", None)
    for name, value in attrs.items():
        setattr(hub, name, value)
    return hub


@pytest.mark.unit
def test_product_capability_table_contains_supported_models():
    assert PRODUCT_TYPE_TABLE[0x00]["name"] == "HBP_USB2_4CH"
    assert PRODUCT_TYPE_TABLE[0x00]["channels"] == 4
    assert PRODUCT_TYPE_TABLE[0x00]["enable_adc"] is True

    assert PRODUCT_TYPE_TABLE[0x01]["name"] == "HBP_USB2_2CH"
    assert PRODUCT_TYPE_TABLE[0x01]["channels"] == 2
    assert PRODUCT_TYPE_TABLE[0x01]["enable_adc"] is False
    assert PRODUCT_TYPE_TABLE[0x01]["enable_usb2_data_switch"] is False

    assert PRODUCT_TYPE_TABLE[0x02]["name"] == "HBP_USB2_7CH"
    assert PRODUCT_TYPE_TABLE[0x02]["channels"] == 7
    assert PRODUCT_TYPE_TABLE[0x02]["enable_usb2_data_switch"] is True

    assert PRODUCT_TYPE_TABLE[0x03]["name"] == "HBP_USB2_7CH_ADV"
    assert PRODUCT_TYPE_TABLE[0x03]["channels"] == 7
    assert PRODUCT_TYPE_TABLE[0x03]["enable_adc"] is True

    assert PRODUCT_TYPE_TABLE[0x04]["name"] == "HBP_USB3_4CH"
    assert PRODUCT_TYPE_TABLE[0x04]["channels"] == 4
    assert PRODUCT_TYPE_TABLE[0x04]["enable_adc"] is False
    assert PRODUCT_TYPE_TABLE[0x04]["enable_usb3_data_switch"] is True
    assert PRODUCT_TYPE_TABLE[0x04]["enable_ilim_switch"] is True

    assert PRODUCT_TYPE_TABLE[0x05]["name"] == "HBL_USB2_4CH"
    assert PRODUCT_TYPE_TABLE[0x05]["channels"] == 4
    assert PRODUCT_TYPE_TABLE[0x05]["enable_adc"] is False
    assert PRODUCT_TYPE_TABLE[0x05]["enable_usb2_data_switch"] is False
    assert PRODUCT_TYPE_TABLE[0x05]["enable_overcurrent"] is True


@pytest.mark.unit
def test_get_channels_uses_cached_max_channels():
    hub = make_hub(max_channels=4, product_type=0x02)

    assert hub.get_channels() == (1, 2, 3, 4)


@pytest.mark.unit
def test_usb3_4ch_rejects_adc_measurement_apis():
    hub = make_hub(max_channels=4, product_type=0x04)
    hub.lock = threading.Lock()

    with pytest.raises(FeatureNotSupportedError):
        hub.get_channel_voltage(1)
    with pytest.raises(FeatureNotSupportedError):
        hub.get_channel_current(1)
    with pytest.raises(FeatureNotSupportedError):
        hub.get_channel_measurements(1)


@pytest.mark.unit
def test_get_channels_falls_back_to_product_type_table():
    hub = make_hub(max_channels=0xFF, product_type=0x02)
    hub.get_max_channels = lambda: None

    assert hub.get_channels() == (1, 2, 3, 4, 5, 6, 7)


@pytest.mark.unit
def test_get_channels_raises_when_count_is_unknown():
    hub = make_hub(max_channels=0xFF, product_type=0x99)
    hub.get_max_channels = lambda: None

    with pytest.raises(RuntimeError):
        hub.get_channels()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("channel_mask", "channels"),
    [
        (0x00, []),
        (0x01, [1]),
        (0x03, [1, 2]),
        (0x55, [1, 3, 5, 7]),
    ],
)
def test_convert_channel_mask_to_channel_list(channel_mask, channels):
    hub = make_hub()

    assert hub._convert_channel(channel_mask) == channels


@pytest.mark.unit
def test_resolve_channels_accepts_iterables_and_defaults_to_all_channels():
    hub = make_hub(max_channels=4)

    assert hub._resolve_channels(([1, 3],)) == (1, 3)
    assert hub._resolve_channels((2, 4)) == (2, 4)
    assert hub._resolve_channels(()) == (1, 2, 3, 4)
