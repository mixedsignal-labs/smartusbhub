# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Sets an overcurrent rule (threshold in mA) on --channel (default 1), subscribes
to alert events, and polls status once per second. The power_off_lock action
turns off channel power, disconnects its data lines, and locks it against
power-on until unlocked. Current firmware saves the rule on the device;
stopping this script does not clear the rule or the protection lock.

Run:
    python examples/extras/alerts.py
    python examples/extras/alerts.py --threshold 200
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

from smartusbhub import CMD_ALERT_EVENT, SmartUSBHub


def on_alert(channel, event):
    print(f"ALERT on CH{channel}: {event}")


def main():
    parser = argparse.ArgumentParser(description="Overcurrent alert demo")
    parser.add_argument("--channel", type=int, default=1, help="channel to watch (default 1)")
    parser.add_argument("--threshold", type=int, default=500, help="overcurrent threshold in mA (default 500)")
    args = parser.parse_args()

    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    rule = hub.set_alert_config(args.channel, "overcurrent", args.threshold, action="power_off_lock")
    print(f"alert rule: {rule}")

    hub.register_callback(CMD_ALERT_EVENT, on_alert)
    hub.subscribe_alert_events(True)
    print(f"watching CH{args.channel} for overcurrent > {args.threshold} mA - Ctrl-C to stop\n")

    try:
        while True:
            print(f"alert status: {hub.get_alert_status()}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

    hub.subscribe_alert_events(False)
    hub.disconnect()


if __name__ == "__main__":
    main()
