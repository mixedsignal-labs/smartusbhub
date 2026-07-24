"""
Direct unit tests for ``_PortLock`` — the cross-process serial-port file lock.

This OS-specific logic (stale-lock reaping, PID liveness probing, the acquire/
release lifecycle) was previously untested: every other test monkeypatches the
lock away. Extracting it into its own unit makes it testable on its own.
"""
import os

import pytest

import smartusbhub as m
from smartusbhub import _PortLock, SmartUSBHub


@pytest.fixture
def clean_lock():
    """Isolate ``_PortLock`` state and remove any lock files a test creates."""
    saved = dict(_PortLock._locks)
    _PortLock._locks.clear()
    try:
        yield
    finally:
        for handle in _PortLock._locks.values():
            try:
                handle.close()
            except Exception:
                pass
        _PortLock._locks.clear()
        _PortLock._locks.update(saved)


@pytest.mark.unit
def test_acquire_then_release_roundtrip(clean_lock):
    port = "/dev/cu.test-portlock-roundtrip"
    assert _PortLock.acquire(port) is True
    assert port in _PortLock._locks
    _PortLock.release(port)
    assert port not in _PortLock._locks


@pytest.mark.unit
def test_acquire_is_idempotent_within_process(clean_lock):
    port = "/dev/cu.test-portlock-idem"
    assert _PortLock.acquire(port) is True
    handle = _PortLock._locks[port]
    assert _PortLock.acquire(port) is True          # fast path, same handle
    assert _PortLock._locks[port] is handle
    _PortLock.release(port)


@pytest.mark.unit
def test_release_of_unheld_port_is_noop(clean_lock):
    assert _PortLock.release("/dev/cu.never-held") is None


@pytest.mark.unit
def test_check_process_exists_live_and_dead():
    assert _PortLock._check_process_exists(os.getpid()) is True
    # Above the platform's max PID -> ESRCH -> reported as not existing.
    assert _PortLock._check_process_exists(2_000_000) is False


@pytest.mark.unit
def test_clear_stale_lock_removes_dead_owner_keeps_live(tmp_path, monkeypatch):
    dead = tmp_path / "dead.lock"
    dead.write_text("12345")
    monkeypatch.setattr(_PortLock, "_check_process_exists",
                        classmethod(lambda cls, pid: False))
    _PortLock._clear_stale_lock(str(dead))
    assert not dead.exists()              # owner dead -> reaped

    live = tmp_path / "live.lock"
    live.write_text(str(os.getpid()))
    monkeypatch.setattr(_PortLock, "_check_process_exists",
                        classmethod(lambda cls, pid: True))
    _PortLock._clear_stale_lock(str(live))
    assert live.exists()                  # owner alive -> kept


@pytest.mark.unit
def test_acquire_degrades_to_success_without_os_locking(clean_lock, monkeypatch):
    monkeypatch.setattr(m, "HAS_FCNTL", False)
    monkeypatch.setattr(m, "HAS_MSVCRT", False)
    port = "/dev/cu.test-portlock-nolock"
    assert _PortLock.acquire(port) is True   # graceful fallback
    assert port not in _PortLock._locks      # no OS handle held in this mode


@pytest.mark.unit
def test_hub_delegators_route_to_portlock(clean_lock, monkeypatch):
    calls = []
    monkeypatch.setattr(_PortLock, "acquire",
                        classmethod(lambda cls, port: calls.append(("acq", port)) or True))
    monkeypatch.setattr(_PortLock, "release",
                        classmethod(lambda cls, port: calls.append(("rel", port))))
    assert SmartUSBHub._acquire_port_lock("/dev/cu.x") is True
    SmartUSBHub._release_port_lock("/dev/cu.x")
    assert calls == [("acq", "/dev/cu.x"), ("rel", "/dev/cu.x")]
