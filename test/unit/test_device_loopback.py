"""
Offline loopback tests: drive the real SDK against an in-process device
simulator so the full send/parse/dispatch/ACK path is exercised with no
hardware. See ``fake_device.py`` for the simulator.
"""
import threading
import time

import pytest

import smartusbhub as m
from fake_device import FakeHubDevice, frame_v1, make_live_hub


@pytest.fixture
def live(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch)
    try:
        yield hub, device, fake
    finally:
        hub.disconnect()


# -- power -----------------------------------------------------------------
@pytest.mark.unit
def test_set_channel_power_acknowledged_and_applied(live):
    hub, device, _ = live

    assert hub.set_channel_power(1, 3, state=1) is True
    assert device.power[1] == 1
    assert device.power[3] == 1
    assert device.power[2] == 0


@pytest.mark.unit
def test_get_channel_power_status_single_and_multi(live):
    hub, device, _ = live
    device.power.update({1: 1, 2: 0, 3: 1})

    assert hub.get_channel_power_status(1) == 1
    assert hub.get_channel_power_status(1, 2, 3) == {1: 1, 2: 0, 3: 1}


@pytest.mark.unit
def test_multichannel_read_waits_for_all_frames_and_uses_fresh_values(monkeypatch):
    """
    A multi-channel read must collect every per-channel reply, even when the frames
    trickle in across multiple receive passes, and must return this request's fresh
    values rather than stale cache.

    The frames arrive ~80 ms apart — well beyond the fixed 50 ms settle the old code
    used — so this fails with that approach and passes with content-based completion.
    """
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False, com_timeout=0.6)
    try:
        # Stale cache that must be discarded (proves the drop-before-send freshness).
        hub.channel_power_status.update({1: 9, 2: 9, 3: 9})

        def trickle():
            for ch, val in ((1, 1), (2, 0), (3, 1)):
                time.sleep(0.08)
                fake.feed(frame_v1(m.CMD_GET_CHANNEL_POWER_STATUS, 1 << (ch - 1), val))

        worker = threading.Thread(target=trickle)
        worker.start()
        try:
            assert hub.get_channel_power_status(1, 2, 3) == {1: 1, 2: 0, 3: 1}
        finally:
            worker.join()
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_power_roundtrip_off(live):
    hub, device, _ = live
    hub.set_channel_power(2, state=1)
    assert hub.get_channel_power_status(2) == 1
    hub.set_channel_power(2, state=0)
    assert hub.get_channel_power_status(2) == 0


@pytest.mark.unit
def test_set_channel_power_interlock_powers_one_and_clears_rest(live):
    hub, device, _ = live
    device.power.update({1: 1, 2: 1, 3: 1})

    assert hub.set_channel_power_interlock(2) is True
    assert device.power[2] == 1

    assert hub.set_channel_power_interlock(None) is True
    assert all(state == 0 for state in device.power.values())


# -- USB2 data line --------------------------------------------------------
@pytest.mark.unit
def test_set_and_get_usb2_dataline(live):
    hub, device, _ = live

    assert hub.set_channel_usb2_dataline(1, 2, state=1) is True
    assert device.dataline[1] == 1 and device.dataline[2] == 1
    assert hub.get_channel_usb2_dataline_status(1, 2) == {1: 1, 2: 1}


@pytest.mark.unit
def test_usb2_dataline_roundtrip_off(live):
    hub, device, _ = live
    hub.set_channel_usb2_dataline(1, state=1)
    assert hub.get_channel_usb2_dataline_status(1) == {1: 1}
    hub.set_channel_usb2_dataline(1, state=0)
    assert hub.get_channel_usb2_dataline_status(1) == {1: 0}


@pytest.mark.unit
def test_v1_dataline_aliases(live):
    hub, device, _ = live

    assert hub.set_channel_dataline(1, 3, state=1) is True
    assert device.dataline[1] == 1 and device.dataline[3] == 1
    assert hub.get_channel_dataline_status(1, 3) == {1: 1, 3: 1}


# -- voltage / current -----------------------------------------------------
@pytest.mark.unit
def test_get_channel_voltage_and_current(live):
    hub, device, _ = live
    device.voltage[1] = 5000
    device.current[1] = 250

    assert hub.get_channel_voltage(1) == 5000
    assert hub.get_channel_current(1) == 250


@pytest.mark.unit
def test_get_channel_measurements_batch(live):
    hub, device, _ = live
    device.voltage.update({1: 5000, 2: 4900})
    device.current.update({1: 100, 2: 80})

    result = hub.get_channel_measurements(1, 2)
    assert result[1]["voltage"] == 5000
    assert result[1]["current"] == 100
    assert result[2]["voltage"] == 4900
    assert result[1]["valid"] is True
    assert result[1]["fresh"] is True


# -- overcurrent -----------------------------------------------------------
@pytest.mark.unit
def test_get_channel_oc_status(live):
    hub, device, _ = live
    device.oc_active_mask = 0b0001  # channel 1 actively over current
    device.oc_latch_mask = 0b0011   # channels 1 and 2 latched

    status = hub.get_channel_oc_status()
    assert status[1] == {"active": True, "latch": True}
    assert status[2] == {"active": False, "latch": True}
    assert status[3] == {"active": False, "latch": False}


@pytest.mark.unit
def test_clear_channel_oc_latch_clears_device_latch(live):
    hub, device, _ = live
    device.oc_latch_mask = 0b0111

    assert hub.clear_channel_oc_latch(1, 2) is True
    assert device.oc_latch_mask == 0b0100  # only channel 3 still latched


# -- default power / data line --------------------------------------------
@pytest.mark.unit
def test_set_and_get_default_power_status(live):
    hub, device, _ = live

    assert hub.set_default_power_status(1, 2, enable=1, status=1) is True
    assert device.default_power[1] == (1, 1)

    result = hub.get_default_power_status(1, 2)
    assert result[1] == {"enabled": 1, "value": 1}
    assert result[2] == {"enabled": 1, "value": 1}


@pytest.mark.unit
def test_set_and_get_default_dataline_status(live):
    hub, device, _ = live

    assert hub.set_default_dataline_status(3, enable=1, status=0) is True
    result = hub.get_default_dataline_status(3)
    assert result[3] == {"enabled": 1, "value": 0}


# -- operate mode / button / auto-restore ---------------------------------
@pytest.mark.unit
def test_operate_mode_roundtrip(live):
    hub, device, _ = live

    assert hub.set_operate_mode(1) is True
    assert hub.get_operate_mode() == 1
    assert hub.set_operate_mode(0) is True
    assert hub.get_operate_mode() == 0


@pytest.mark.unit
def test_button_control_roundtrip(live):
    hub, device, _ = live

    assert hub.set_button_control(False) is True
    assert hub.get_button_control_status() == 0
    assert hub.set_button_control(True) is True
    assert hub.get_button_control_status() == 1


@pytest.mark.unit
def test_auto_restore_roundtrip(live):
    hub, device, _ = live

    assert hub.set_auto_restore(True) is True
    assert hub.get_auto_restore_status() == 1


# -- device address --------------------------------------------------------
@pytest.mark.unit
def test_device_address_roundtrip(live):
    hub, device, _ = live

    assert hub.set_device_address(0x1234) is True
    assert device.address == 0x1234
    assert hub.get_device_address() == 0x1234


# -- identity / maintenance ------------------------------------------------
@pytest.mark.unit
def test_identity_queries(live):
    hub, device, _ = live

    assert hub.get_firmware_version() == device.firmware_version
    assert hub.get_hardware_version() == device.hardware_version
    assert hub.get_product_type() == 0x03
    assert hub.get_product_name() == "HBP_USB2_7CH_ADV"
    assert hub.get_max_channels() == 7
    assert hub.get_serial_no() == "N/A"


@pytest.mark.unit
def test_factory_reset_and_reboot_acknowledged(live):
    hub, device, _ = live

    assert hub.factory_reset() is True
    assert hub.reboot_mcu() is True


# -- full identity handshake (real get_device_info) -----------------------
@pytest.mark.unit
def test_real_get_device_info_handshake(monkeypatch):
    hub, device, _ = make_live_hub(monkeypatch, real_device_info=True)
    try:
        info = hub.get_device_info()
        assert info["product_type"] == "HBP_USB2_7CH_ADV"
        assert info["max_channels"] == 7
        assert info["firmware_version"] == device.firmware_version
        assert info["operate_mode"] == "normal"
        assert hub.product_type == 0x03
        assert hub.max_channels == 7
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_legacy_v1_get_device_info_skips_new_identity_probes(monkeypatch):
    device = FakeHubDevice(product_type=0x03, max_channels=7, firmware_major=1)
    hub, _, fake = make_live_hub(monkeypatch, device=device, real_device_info=True)
    try:
        assert hub.firmware_version_major == 1
        assert hub.product_type == 0x00
        assert hub.max_channels == 4
        assert hub.serial_no == "N/A"
        assert hub.device_alias == ""

        written_cmds = []
        for packet in fake.written:
            if packet[:2] == b"\x55\x5A":
                written_cmds.append(packet[2])
            elif packet[:4] == bytes(m.V3_MAGIC):
                written_cmds.append(packet[4])

        assert m.CMD_GET_PRODUCT_TYPE not in written_cmds
        assert m.CMD_GET_MAX_CHANNELS not in written_cmds
        assert m.CMD_GET_SERIAL_NO not in written_cmds
        assert m.CMD_GET_DEVICE_ALIAS not in written_cmds
    finally:
        hub.disconnect()


# -- timeout path (device silent) -----------------------------------------
@pytest.mark.unit
def test_get_returns_none_when_device_does_not_respond(monkeypatch):
    hub, device, fake = make_live_hub(monkeypatch, auto_respond=False, com_timeout=0.05)
    try:
        assert hub.get_channel_power_status(1) is None
        assert hub.set_channel_power(1, state=1) is False
    finally:
        hub.disconnect()


# -- ACK correlation: a satisfied ACK must not leak into the next command --
@pytest.mark.unit
def test_set_does_not_report_false_ack_after_a_prior_success(monkeypatch):
    """
    Regression: a SET whose ACK is never received must return False even when the
    *previous* SET (same command) was acknowledged.

    The per-command ACK ``Event`` is shared across calls; if a satisfied wait left
    the flag set, the next SET's wait would short-circuit on the stale flag and
    report success for a command the device never acknowledged. This was timing
    dependent, so repeat to defeat the scheduling race.
    """
    hub, device, fake = make_live_hub(monkeypatch, com_timeout=0.1)
    try:
        for _ in range(15):
            fake.auto_respond = True
            assert hub.set_channel_power(1, state=1) is True   # device ACKs
            fake.auto_respond = False                          # device goes silent
            assert hub.set_channel_power(1, state=0) is False  # no ACK -> must be False
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_successful_set_clears_its_ack_event(monkeypatch):
    """A satisfied ACK leaves the shared event cleared, ready for the next reuse."""
    hub, device, fake = make_live_hub(monkeypatch, com_timeout=0.1)
    try:
        assert hub.set_channel_power(1, state=1) is True
        assert hub.ack_events[m.CMD_SET_CHANNEL_POWER].is_set() is False
    finally:
        hub.disconnect()
