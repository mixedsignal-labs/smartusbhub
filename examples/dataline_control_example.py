# Description: control the dataline of each channel of the SmartUSBHub
# copyright: (c) 2026 MixedSignalLab
# license: Apache-2.0
# version: 1.0
# author: zhang <mixedsignallab@outlook.com>
# email: mixedsignallab@outlook.com
# website: https://www.mixedsignallab.com

import sys
import os
import time
# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def main():
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found
    # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)

    # Get and display hardware and firmware versions
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version: V1.{hardware_version}" if hardware_version is not None else "Hardware Version: Unknown")
    print(f"Firmware Version: V1.{firmware_version}" if firmware_version is not None else "Firmware Version: Unknown")
    print()

    while True:
        # control channel data line
        print("disconnect channel's data but keep power on:\n")

        if hub.get_channel_power_status(1) == 0:
            print("channel 1 power is off,turn on first")
            hub.set_channel_power(1, state=1)

        hub.set_channel_usb2_dataline(1,state=0)
        print("now channel 1 power is on but data is disconnected\n")

        time.sleep(60)

        print("connect channel 1 data again\n")
        hub.set_channel_usb2_dataline(1,state=1)
        print("channel 1 data connected\n")
        time.sleep(60)

        # # control multi channel data line
        # print("disconnect multi channel's data but keep power on:")
        # if hub.get_channel_power_status(1,3) == 0:
        #     print("channel 1,3 power is off,turn on first")
        #     hub.set_channel_power(1,3, state=1)
        #     if(hub.get_channel_power_status(1,3) == 0):
        #         print("channel 1,3 power is still off")
        #         sys.exit(1)

        # result = hub.set_channel_usb2_dataline(1,3,state=0)
        # if result:
        #     print("now channel 1,3 power is on and data is disconnected")
        # else:
        #     print("channel 1,3 dataline disconnect failed")

        # time.sleep(3)
        # print("connect channel 1,3's data again")
        # result = hub.set_channel_usb2_dataline(1,3,state=1)
        # if result:
        #     print("channel 1,3 dataline connected")
        # else:
        #     print("channel 1,3 dataline connect failed")


if __name__ == "__main__":
    main()
