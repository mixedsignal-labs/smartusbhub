# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Disconnects and reconnects the first channel's data line (USB2.0 on most
models; on USB3 models this also covers SuperSpeed pairs). Power stays on
the whole time - the device re-enumerates but never loses power.

Run:
    python examples/extras/dataline_control.py
"""

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
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channel = hub.get_channels()[0]
    print(f"Product: {hub.get_product_name()}  Channel under test: {channel}")

    hub.set_channel_power(channel, state=1)

    print("disconnect data line (power stays on)")
    hub.set_channel_dataline(channel, state=0)
    time.sleep(2)
    print(f"data line status: {hub.get_channel_dataline_status(channel)}")

    print("reconnect data line")
    hub.set_channel_dataline(channel, state=1)
    time.sleep(2)
    print(f"data line status: {hub.get_channel_dataline_status(channel)}")

    hub.disconnect()


if __name__ == "__main__":
    main()
