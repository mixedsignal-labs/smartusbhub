"""
Offline discovery/connection tests. The serial-port enumeration and the device
handshake are faked, so ``scan_available_ports`` / ``scan_and_connect`` /
``auto_connect`` / ``scan_and_connect_by_address`` are exercised with no hardware.
"""
import pytest

import smartusbhub as m
from smartusbhub import SmartUSBHub
from fake_device import FakeHubDevice, FakeHubSerial


class FakePortInfo:
    def __init__(self, device, vid=0x1A86, pid=0xfe0c):
        self.device = device
        self.vid = vid
        self.pid = pid


def install_fake_environment(monkeypatch, ports, device=None, address=0x0000):
    """Fake comports() plus a serial layer + handshake for one hub device."""
    device = device or FakeHubDevice()
    device.address = address
    fake_serial = FakeHubSerial(device)

    monkeypatch.setattr(m.serial.tools.list_ports, "comports",
                        lambda: [FakePortInfo(p) for p in ports])
    monkeypatch.setattr(m.serial, "Serial", lambda *a, **k: fake_serial)
    monkeypatch.setattr(SmartUSBHub, "_acquire_port_lock",
                        classmethod(lambda cls, port: True))
    monkeypatch.setattr(SmartUSBHub, "_release_port_lock",
                        classmethod(lambda cls, port: None))

    def fake_device_info(self):
        self.product_type = device.product_type
        self.max_channels = device.max_channels
        self.operate_mode = device.operate_mode
        self.firmware_version = device.firmware_version
        self.hardware_version = device.hardware_version
        self.button_control_status = device.button_control
        self.auto_restore_status = device.auto_restore
        self.device_address = device.address
        self.serial_no = "N/A"
        return {}

    monkeypatch.setattr(SmartUSBHub, "get_device_info", fake_device_info)
    return device


@pytest.fixture(autouse=True)
def _clean_connection_registry():
    SmartUSBHub._connected_ports.clear()
    SmartUSBHub._connected_addresses.clear()
    yield
    SmartUSBHub._connected_ports.clear()
    SmartUSBHub._connected_addresses.clear()


@pytest.mark.unit
def test_scan_available_ports_filters_by_vid_pid(monkeypatch):
    monkeypatch.setattr(m.serial.tools.list_ports, "comports", lambda: [
        FakePortInfo("/dev/cu.hub1"),
        FakePortInfo("/dev/cu.other", vid=0x1234, pid=0x5678),
        FakePortInfo("/dev/cu.hub2"),
    ])
    assert SmartUSBHub.scan_available_ports() == ["/dev/cu.hub1", "/dev/cu.hub2"]


@pytest.mark.unit
def test_scan_and_connect_returns_first_matching_device(monkeypatch):
    install_fake_environment(monkeypatch, ["/dev/cu.hubA"])

    hub = SmartUSBHub.scan_and_connect()
    try:
        assert hub is not None
        assert hub.port == "/dev/cu.hubA"
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_scan_and_connect_skips_excluded_ports(monkeypatch):
    install_fake_environment(monkeypatch, ["/dev/cu.busy"])

    hub = SmartUSBHub.scan_and_connect(exclude_ports={"/dev/cu.busy"})
    assert hub is None


@pytest.mark.unit
def test_scan_and_connect_returns_none_when_no_hub_present(monkeypatch):
    monkeypatch.setattr(m.serial.tools.list_ports, "comports", lambda: [
        FakePortInfo("/dev/cu.other", vid=0x0001, pid=0x0002),
    ])
    assert SmartUSBHub.scan_and_connect() is None


@pytest.mark.unit
def test_scan_and_connect_by_address_match_and_mismatch(monkeypatch):
    install_fake_environment(monkeypatch, ["/dev/cu.addr"], address=0x00AB)

    hub = SmartUSBHub.scan_and_connect_by_address(0x00AB)
    try:
        assert hub is not None
        assert hub.device_address == 0x00AB
    finally:
        hub.disconnect()

    SmartUSBHub._connected_ports.clear()
    assert SmartUSBHub.scan_and_connect_by_address(0x0099) is None


@pytest.mark.unit
def test_auto_connect_returns_device(monkeypatch):
    install_fake_environment(monkeypatch, ["/dev/cu.auto"])

    hub = SmartUSBHub.auto_connect()
    try:
        assert hub is not None
        assert hub.port == "/dev/cu.auto"
    finally:
        hub.disconnect()


@pytest.mark.unit
def test_auto_connect_feature_filter_skips_unsupported(monkeypatch):
    # 2CH model lacks ADC; the feature filter must reject it.
    device = FakeHubDevice(product_type=0x01, max_channels=2)
    install_fake_environment(monkeypatch, ["/dev/cu.basic"], device=device)

    hub = SmartUSBHub.auto_connect(feature_filter="adc")
    assert hub is None


@pytest.mark.unit
def test_auto_connect_returns_none_when_no_ports(monkeypatch):
    monkeypatch.setattr(SmartUSBHub, "scan_available_ports",
                        classmethod(lambda cls: []))
    assert SmartUSBHub.auto_connect() is None
