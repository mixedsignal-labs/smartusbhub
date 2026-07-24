"""
@file dataline_control_example.py
@brief Connect/disconnect a channel's USB2.0 data line while keeping power on.
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/advanced/dataline_control_example.py
"""

import os
import sys
import time

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def main():
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        return

    with hub:  # disconnects automatically on exit
        print("device info:", hub.get_device_info())

        # Make sure the channel is powered, then toggle only the data line.
        if hub.get_channel_power_status(1) == 0:
            print("channel 1 power is off, turning it on first")
            hub.set_channel_power(1, state=1)

        print("disconnecting channel 1 data line (power stays on)")
        hub.set_channel_usb2_dataline(1, state=0)
        time.sleep(3)

        print("reconnecting channel 1 data line")
        hub.set_channel_usb2_dataline(1, state=1)
        time.sleep(1)


if __name__ == "__main__":
    main()
