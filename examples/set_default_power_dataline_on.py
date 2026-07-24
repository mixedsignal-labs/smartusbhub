"""
@file set_default_power_dataline_on.py
@brief set power-on defaults to power ON and USB2 dataline connected
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/set_default_power_dataline_on.py
"""

import argparse
import os
import sys

# Add the repository root to sys.path so we can import
# smartusbhub from a source checkout without installing it.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def parse_args():
    parser = argparse.ArgumentParser(
        description="Set all controllable channels to power ON and USB2 dataline connected on power-up."
    )
    parser.add_argument(
        "--port",
        help="Serial port to open. If omitted, the first detected SmartUSBHub is used.",
    )
    parser.add_argument(
        "--apply-now",
        action="store_true",
        help="Also turn on power and USB2 dataline immediately after changing defaults.",
    )
    return parser.parse_args()


def connect_hub(port):
    if port:
        return SmartUSBHub(port)
    return SmartUSBHub.scan_and_connect()


def verify_status(name, status, channels):
    if not status:
        print(f"{name}: readback failed")
        return False

    ok = True
    for channel in channels:
        item = status.get(channel)
        enabled = item.get("enabled") if item else None
        value = item.get("value") if item else None
        passed = enabled == 1 and value == 1
        ok = ok and passed
        print(
            f"{name} CH{channel}: "
            f"enabled={enabled}, value={value}, {'OK' if passed else 'FAIL'}"
        )
    return ok


def main():
    args = parse_args()
    hub = connect_hub(args.port)
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    try:
        channels = list(hub.get_channels())
        print(f"Product: {hub.get_product_name() or 'N/A'}")
        print(f"Max channels: {len(channels)}")
        print("Setting default power: enabled, ON")
        power_ok = hub.set_default_power_status(*channels, enable=1, status=1)

        print("Setting default USB2 dataline: enabled, connected")
        dataline_ok = hub.set_default_dataline_status(*channels, enable=1, status=1)

        if args.apply_now:
            print("Applying current power and USB2 dataline state now")
            hub.set_channel_power(*channels, state=1)
            hub.set_channel_usb2_dataline(*channels, state=1)

        print("Reading back default settings")
        power_status = hub.get_default_power_status(*channels)
        dataline_status = hub.get_default_dataline_status(*channels)

        power_verify_ok = verify_status("Default power", power_status, channels)
        dataline_verify_ok = verify_status("Default dataline", dataline_status, channels)

        if power_ok and dataline_ok and power_verify_ok and dataline_verify_ok:
            print("Default power and dataline settings are ON for all channels.")
            sys.exit(0)

        print("Failed to set or verify one or more default settings.")
        sys.exit(2)
    finally:
        hub.disconnect()


if __name__ == "__main__":
    main()
