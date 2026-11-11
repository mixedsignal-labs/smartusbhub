# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Connects to the first SmartUSBHub found, prints a full device report
(identity, capabilities, runtime status) and then demonstrates channel
power control (single channel, all channels at once, interlock mode) and
device address get/set.

Run:
    python examples/quick_start.py
"""

import os
import sys
import time
from pprint import pprint

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def print_report(hub):
    """Print device identity, capabilities and runtime status."""
    print("\n=== Device Info ===")
    print(f"  Product name      : {hub.get_product_name() or 'N/A'}")
    print(f"  Hardware version  : V1.{hub.get_hardware_version()}")
    print(f"  Firmware version  : V1.{hub.get_firmware_version()}")
    print(f"  Device info       : {hub.get_device_info()}")

    channels = tuple(hub.get_channels())
    print(f"  Channels          : {list(channels)}")

    print("\n=== Capabilities ===")
    pprint(hub.get_capability(), sort_dicts=False)

    print("\n=== Runtime status ===")
    pprint(hub.get_channel_power_status(*channels), sort_dicts=False)
    pprint(hub.get_channel_usb2_dataline_status(*channels), sort_dicts=False)
    return channels


def demo_power_control(hub, channels):
    """Demonstrate single-channel, all-channel and interlock power control."""
    first_channel = channels[0]
    interval = 0.5

    print("\n=== Power control ===")

    print(f"turn on channel {first_channel}")
    hub.set_channel_power(first_channel, state=1)
    time.sleep(interval)

    print(f"turn off channel {first_channel}")
    hub.set_channel_power(first_channel, state=0)
    time.sleep(interval)

    print(f"\nturn on all channels {list(channels)} at once")
    hub.set_channel_power(*channels, state=1)
    time.sleep(interval)

    print(f"turn off all channels {list(channels)} at once")
    hub.set_channel_power(*channels, state=0)
    time.sleep(interval)

    print("\ninterlock power control (only one channel on at a time):")
    for channel in channels:
        hub.set_channel_power_interlock(channel)
        print("interlock control, turn on channel", channel)
        time.sleep(interval)

    print("set back to normal mode")
    hub.set_channel_power_interlock(None)


def demo_device_address(hub):
    """Demonstrate reading and setting the device address."""
    print("\n=== Device address ===")
    address = hub.get_device_address()
    print(f"current device address: {address}")

    hub.set_device_address(address)
    print(f"device address set to: {address}")


def main():
    hub = SmartUSBHub.scan_and_connect()
    # hub = SmartUSBHub("/dev/cu.usbmodem132301")  # Connect to a specific device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channels = print_report(hub)
    demo_power_control(hub, channels)
    demo_device_address(hub)
    hub.disconnect()


if __name__ == "__main__":
    main()
