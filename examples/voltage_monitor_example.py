# Description: voltage monitor for each channel of the SmartUSBHub
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
        voltages = []
        for i in range(1, 5):
            voltage = hub.get_channel_voltage(i)
            if voltage is not None:
                voltages.append(f"{voltage / 1000.0:.2f} V")
            else:
                voltages.append("N/A")
        print(" | ".join([f"Channel {i}: {v}" for i, v in enumerate(voltages, start=1)]))
        time.sleep(0.01)


if __name__ == "__main__":
    main()
