import pytest

import smartusbhub as smartusbhub_module
from smartusbhub import DeviceConnectionError, SmartUSBHub


class FakeSerial:
    def __init__(self):
        self.is_open = True
        self.closed = False

    def flush(self):
        pass

    def close(self):
        self.is_open = False
        self.closed = True


@pytest.mark.unit
def test_init_releases_port_lock_when_device_does_not_respond(monkeypatch):
    port = "/dev/cu.fake-smartusbhub"
    fake_serial = FakeSerial()
    released_ports = []

    monkeypatch.setattr(
        smartusbhub_module.serial,
        "Serial",
        lambda *args, **kwargs: fake_serial,
    )
    monkeypatch.setattr(
        SmartUSBHub,
        "_acquire_port_lock",
        classmethod(lambda cls, locked_port: True),
    )
    monkeypatch.setattr(
        SmartUSBHub,
        "_release_port_lock",
        classmethod(lambda cls, released_port: released_ports.append(released_port)),
    )
    monkeypatch.setattr(SmartUSBHub, "_start", lambda self: None)
    monkeypatch.setattr(SmartUSBHub, "get_device_info", lambda self: None)

    SmartUSBHub._connected_ports.discard(port)
    SmartUSBHub._connected_addresses.pop(port, None)

    with pytest.raises(DeviceConnectionError):
        SmartUSBHub(port)

    assert fake_serial.closed is True
    assert released_ports == [port]
    assert port not in SmartUSBHub._connected_ports
    assert port not in SmartUSBHub._connected_addresses
