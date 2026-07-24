"""
@file cycle_all_channels.py
@brief cycle power on every controllable channel of the SmartUSBHub
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/cycle_all_channels.py
"""

import argparse
import os
import sys
import time

# Add the repository root to sys.path so we can import
# smartusbhub from a source checkout without installing it.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cycle power on every controllable SmartUSBHub channel."
    )
    parser.add_argument(
        "--port",
        help="Serial port to open. If omitted, the first detected SmartUSBHub is used.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Number of full cycles. 0 means run forever.",
    )
    parser.add_argument(
        "--on-time",
        type=float,
        default=0.01,
        help="Seconds to keep each channel on.",
    )
    parser.add_argument(
        "--off-time",
        type=float,
        default=0.01,
        help="Seconds to wait after turning a channel off.",
    )
    parser.add_argument(
        "--all-off-between",
        action="store_true",
        help="Turn all channels off before enabling the next channel.",
    )
    return parser.parse_args()


def cycle_channels(hub, channels, cycles, on_time, off_time, all_off_between):
    completed = 0
    while cycles == 0 or completed < cycles:
        completed += 1
        print(f"Cycle {completed}" if cycles else f"Cycle {completed} (press Ctrl+C to stop)")

        for channel in channels:
            if all_off_between:
                hub.set_channel_power(*channels, state=0)
                time.sleep(off_time)

            print(f"  CH{channel}: ON")
            hub.set_channel_power(channel, state=1)
            time.sleep(on_time)

            print(f"  CH{channel}: OFF")
            hub.set_channel_power(channel, state=0)
            time.sleep(off_time)


def main():
    args = parse_args()
    hub = SmartUSBHub(args.port) if args.port else SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channels = []
    try:
        channels = list(hub.get_channels())
        print(f"Product: {hub.get_product_name() or 'N/A'}")
        print(f"Max channels: {len(channels)}")
        hub.set_channel_power(*channels, state=0)
        cycle_channels(
            hub,
            channels,
            args.cycles,
            args.on_time,
            args.off_time,
            args.all_off_between,
        )
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        try:
            if channels:
                hub.set_channel_power(*channels, state=0)
        except Exception:
            pass
        hub.disconnect()


if __name__ == "__main__":
    main()
