# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Monitor per-channel voltage/current using V2 request/response.

Continuously polls and prints every channel's voltage/current without changing
channel power states. Optional CSV logging. Press Ctrl-C to stop.

Run:
    python examples/power_measurement_oneshot.py
    python examples/power_measurement_oneshot.py --csv data.csv
"""

import argparse
import csv
import os
import sys
import time

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def main():
    parser = argparse.ArgumentParser(description="USB channel voltage/current monitor (V2 request/response)")
    parser.add_argument("--csv", metavar="FILE", help="log data to CSV file")
    parser.add_argument("--interval-ms", type=int, default=200, help="poll interval in ms (default 200)")
    args = parser.parse_args()

    hub = SmartUSBHub.scan_and_connect()
    # hub = SmartUSBHub("/dev/cu.usbmodem132301")  # Connect to a specific device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channels = list(hub.get_channels())
    print(f"Product: {hub.get_product_name()}  Channels: {channels}")
    print(f"Polling every {args.interval_ms} ms - Ctrl-C to stop\n")

    csv_file = open(args.csv, "w", newline="") if args.csv else None
    if csv_file:
        header = ["timestamp_s"] + [f"ch{c}_mV" for c in channels] + [f"ch{c}_mA" for c in channels]
        csv.writer(csv_file).writerow(header)

    try:
        while True:
            voltages = [hub.get_channel_voltage(ch) for ch in channels]
            currents = [hub.get_channel_current(ch) for ch in channels]
            for ch, voltage, current in zip(channels, voltages, currents):
                print(f"CH{ch}  {voltage:6d} mV  {current:6d} mA")
            print()

            if csv_file:
                row = [f"{time.time():.3f}"] + voltages + currents
                csv.writer(csv_file).writerow(row)
                csv_file.flush()

            time.sleep(args.interval_ms / 1000)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        if csv_file:
            csv_file.close()
        hub.disconnect()


if __name__ == "__main__":
    main()
