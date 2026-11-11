# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Scans and connects every SmartUSBHub found, then turns channels on one by
one across all devices - a "chasing light" driven by the channel indicator
LEDs. Press Ctrl-C to stop.

Run:
    python examples/multi_device_channel_control.py
"""

import os
import sys
import time

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def scan_all_hubs():
    """Connect to every SmartUSBHub found, one scan per port."""
    hubs = []
    exclude_ports = set()
    while True:
        hub = SmartUSBHub.scan_and_connect(exclude_ports=exclude_ports)
        if hub is None:
            return hubs
        hubs.append(hub)
        exclude_ports.add(hub.port)
        print(f"Device {len(hubs)}: {hub.name} (port: {hub.port})")


def main():
    hubs = scan_all_hubs()
    if not hubs:
        print("No SmartUSBHub found")
        sys.exit(1)

    total = sum(len(hub.get_channels()) for hub in hubs)
    print(f"Found {len(hubs)} device(s), {total} channels total. Ctrl-C to stop.\n")

    try:
        while True:
            for hub in hubs:
                for channel in hub.get_channels():
                    hub.set_channel_power(channel, state=1)
                    time.sleep(0.1)
                    hub.set_channel_power(channel, state=0)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        for hub in hubs:
            hub.set_channel_power(*hub.get_channels(), state=0)
            hub.disconnect()


if __name__ == "__main__":
    main()
