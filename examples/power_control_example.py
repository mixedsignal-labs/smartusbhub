"""
@file power_control_example.py
@brief control the power of each channel of the SmartUSBHub
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/power_control_example.py
"""

import sys
import os
import time
# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def main():
    hub_list = SmartUSBHub.scan_available_ports()# Scan all available ports
    print("available device:", hub_list)

    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found
    # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)

    # Get and display hardware and firmware versions
    print(hub.get_product_name())
    print(f"Hardware Version: V1.{hub.get_hardware_version()}")
    print(f"Firmware Version: V1.{hub.get_firmware_version()}")
    channels = hub.get_channels()
    print(f"Product: {hub.get_product_name() or 'N/A'}")
    print(f"Channels: {list(channels)}")
    first_channel = channels[0]

    interval = 0.5

    print("\ncontrol channel power one by one:")

    print(f"turn on channel {first_channel}")
    hub.set_channel_power(first_channel, state=1)
    time.sleep(interval)

    print(f"turn off channel {first_channel}")
    hub.set_channel_power(first_channel, state=0)
    time.sleep(interval)


    print("\ncontrol multi channel power at once:")
    print(f"turn on channels {list(channels)}")
    hub.set_channel_power(*channels, state=1)
    time.sleep(interval)

    print(f"turn off channels {list(channels)}")
    hub.set_channel_power(*channels, state=0)
    time.sleep(interval)

    print("interlock power control")

    for channel in channels:
        hub.set_channel_power_interlock(channel)
        print("interlock control,turn on channel", channel)
        time.sleep(interval)

    print("set back to normal mode")
    hub.set_channel_power_interlock(None)

    hub.disconnect()

if __name__ == "__main__":
    main()
