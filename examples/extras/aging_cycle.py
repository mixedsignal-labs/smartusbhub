# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Cycles each channel's power on and off N times, one channel at a time.
Useful as a quick burn-in or factory test. Press Ctrl-C to stop early.

Run:
    python examples/extras/aging_cycle.py
    python examples/extras/aging_cycle.py --cycles 50 --on-ms 1000
"""

import argparse
import os
import sys
import time

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def main():
    parser = argparse.ArgumentParser(description="Power-cycle every channel N times")
    parser.add_argument("--cycles", type=int, default=10, help="cycles per channel (default 10)")
    parser.add_argument("--on-ms", type=int, default=500, help="power-on duration in ms (default 500)")
    parser.add_argument("--off-ms", type=int, default=500, help="power-off duration in ms (default 500)")
    args = parser.parse_args()

    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channels = list(hub.get_channels())
    print(f"Product: {hub.get_product_name()}  Channels: {channels}")
    print(f"{args.cycles} cycles x {len(channels)} channels - Ctrl-C to stop\n")

    try:
        for cycle in range(1, args.cycles + 1):
            for ch in channels:
                print(f"cycle {cycle}/{args.cycles}  CH{ch}  ON")
                hub.set_channel_power(ch, state=1)
                time.sleep(args.on_ms / 1000)
                hub.set_channel_power(ch, state=0)
                time.sleep(args.off_ms / 1000)
    except KeyboardInterrupt:
        print("\nStopped.")

    hub.set_channel_power(*channels, state=0)
    hub.disconnect()


if __name__ == "__main__":
    main()
