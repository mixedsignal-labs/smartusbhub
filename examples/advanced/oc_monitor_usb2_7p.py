"""
@file oc_monitor_usb2_7p.py
@brief OC (overcurrent) monitor demo for SmartUSBHub USB2 7P models only.
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/advanced/oc_monitor_usb2_7p.py
"""

import sys
import os
import time
import argparse
import threading

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, CMD_GET_CHANNEL_OC_STATUS

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

USB2_7P_PRODUCT_TYPES = {0x02, 0x03}
USB2_7P_CHANNELS = tuple(range(1, 8))


def ensure_usb2_7p(hub: SmartUSBHub):
    """Exit unless the connected device is a USB2 7-port model."""
    product_type = hub.product_type
    product_info = SmartUSBHub.get_product_info(product_type)
    if product_info:
        product_name = product_info["name"]
    elif product_type is None:
        product_name = "Unknown"
    else:
        product_name = f"Unknown(0x{product_type:02X})"

    if product_type not in USB2_7P_PRODUCT_TYPES:
        print(
            f"{YELLOW}oc_monitor_usb2_7p.py only supports SmartUSBHub USB2 7P models.{RESET}\n"
            f"Connected product: {product_name}"
        )
        hub.disconnect()
        sys.exit(1)

    return product_name


def validate_channels(channels):
    invalid = [ch for ch in channels if ch not in USB2_7P_CHANNELS]
    if invalid:
        raise ValueError(f"Invalid USB2 7P channel(s): {invalid}. Valid range is 1..7.")


def oc_callback(active_mask: int, latch_mask: int, channels):
    """Invoked from _uart_recv_task background thread on OC event."""
    ts = time.strftime('%H:%M:%S')
    print()
    print(f"[{ts}] {BOLD}OC EVENT{RESET}  active=0x{active_mask:02X}  latch=0x{latch_mask:02X}")
    for ch in channels:
        idx = ch - 1
        active = bool(active_mask & (1 << idx))
        latch  = bool(latch_mask  & (1 << idx))
        if active or latch:
            a_str = f"{RED}OVERCURRENT{RESET}" if active else f"{GREEN}clear{RESET}"
            l_str = f"{YELLOW}LATCHED{RESET}"  if latch  else "—"
            print(f"  CH{ch}  {a_str}  latch={l_str}")
    print()


def print_status(hub: SmartUSBHub):
    status = hub.get_channel_oc_status()
    if status is None:
        print(f"{RED}No response from device.{RESET}")
        return

    any_fault = any(v['active'] or v['latch'] for v in status.values())
    print(f"\n{'CH':>3}  {'Active':^10}  {'Latch':^8}")
    print(f"{'─'*3}  {'─'*10}  {'─'*8}")
    for ch in sorted(status):
        v = status[ch]
        a = f"{RED}OC{RESET}  " if v['active'] else f"{GREEN}OK{RESET}  "
        l = f"{YELLOW}LATCHED{RESET}" if v['latch'] else "—      "
        print(f"{ch:>3}  {a:^10}  {l}")
    print()
    if not any_fault:
        print(f"{GREEN}All channels normal.{RESET}\n")
    else:
        print(f"{YELLOW}Tip: press Enter to clear latches, Ctrl-C to exit.{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="SmartUSBHub OC monitor")
    parser.add_argument("--port", help="Serial port (auto-detect if omitted)")
    parser.add_argument("--clear", nargs='*', type=int, metavar='CH',
                        help="Clear OC latch for listed channels (all if no CH given) then exit")
    args = parser.parse_args()

    hub = SmartUSBHub(args.port) if args.port else SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found.")
        sys.exit(1)
    product_name = ensure_usb2_7p(hub)

    # ── one-shot clear mode ───────────────────────────────────────────────────
    if args.clear is not None:
        channels = args.clear if args.clear else []   # empty list = all
        if channels:
            validate_channels(channels)
            hub.clear_channel_oc_latch(*channels)
            print(f"OC latch cleared for channel(s): {channels}")
        else:
            hub.clear_channel_oc_latch()
            print("OC latch cleared for all channels.")
        print_status(hub)
        hub.disconnect()
        return

    # ── monitor mode ──────────────────────────────────────────────────────────
    print(f"\n{BOLD}SmartUSBHub OC Monitor{RESET}  {product_name}  (Ctrl-C to exit, Enter to clear latches)\n")

    # Power on all channels so FLAG# can assert on overcurrent
    channels = USB2_7P_CHANNELS
    print(f"Powering on channels {channels}...")
    hub.set_channel_power(*channels, state=1)
    time.sleep(0.1)

    # Register callback for unsolicited OC events
    # The callback receives (active_mask, latch_mask) extracted from the V1 frame.
    hub.register_callback(CMD_GET_CHANNEL_OC_STATUS,
                          lambda ch, val: oc_callback(ch, val, channels))

    print("Current OC status:")
    print_status(hub)

    stop = threading.Event()

    def stdin_reader():
        while not stop.is_set():
            try:
                input()          # blocks until Enter
                if stop.is_set():
                    break
                hub.clear_channel_oc_latch()
                print("[Latch cleared]")
                print_status(hub)
            except (EOFError, KeyboardInterrupt):
                break

    stdin_thread = threading.Thread(target=stdin_reader, daemon=True)
    stdin_thread.start()

    print("Polling OC status every 1s (callback also active)...\n")
    try:
        while True:
            time.sleep(1)
            # Active poll every second as backup (callback fires on unsolicited events)
            status = hub.get_channel_oc_status()
            if status:
                fault = {ch: v for ch, v in status.items() if v['active'] or v['latch']}
                if fault:
                    ts = time.strftime('%H:%M:%S')
                    print(f"[{ts}] Poll detected fault: {fault}")
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        hub.disconnect()
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
