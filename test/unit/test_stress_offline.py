"""
Bounded offline stress tests — a permanent race/regression guard for the refactored
dispatch path (codec, port lock, dispatch seam, deterministic multi-channel
completion, and the clear-before-send ACK discipline).

These drive the real SDK against the in-process simulator at volume, including
concurrent access from several threads. Marked ``slow`` so they can be excluded
with ``-m "not slow"`` for a fast unit run.
"""
import threading

import pytest

from fake_device import make_live_hub


@pytest.mark.unit
@pytest.mark.slow
def test_offline_stress_single_thread(monkeypatch):
    hub, device, fake = make_live_hub(
        monkeypatch, product_type=0x00, max_channels=4, com_timeout=0.2)
    try:
        chans = (1, 2, 3, 4)
        for i in range(120):
            st = i & 1
            assert hub.set_channel_power(*chans, state=st) is True
            assert hub.get_channel_power_status(*chans) == {c: st for c in chans}
            assert hub.set_channel_usb2_dataline(*chans, state=st) is True
            assert hub.get_channel_usb2_dataline_status(*chans) == {c: st for c in chans}
        # Consecutive same-command SETs must each be independently acknowledged
        # (the #1 ACK-leak regression, exercised at scale).
        assert all(hub.set_channel_power(1, state=i & 1) for i in range(500))
    finally:
        hub.disconnect()


@pytest.mark.unit
@pytest.mark.slow
def test_offline_stress_concurrent_distinct_channels(monkeypatch):
    hub, device, fake = make_live_hub(
        monkeypatch, product_type=0x00, max_channels=4, com_timeout=0.3)
    errors = []

    def worker(ch):
        for i in range(60):
            st = i & 1
            try:
                if not hub.set_channel_power(ch, state=st):
                    errors.append(f"ch{ch} i{i} set no-ack")
                elif hub.get_channel_power_status(ch) != st:
                    errors.append(f"ch{ch} i{i} readback mismatch")
            except Exception as e:  # pragma: no cover - failure path
                errors.append(f"ch{ch} i{i} exc {e!r}")

    try:
        workers = [threading.Thread(target=worker, args=(c,)) for c in (1, 2, 3, 4)]
        for t in workers:
            t.start()
        for t in workers:
            t.join()
        assert errors == [], errors[:10]
    finally:
        hub.disconnect()
