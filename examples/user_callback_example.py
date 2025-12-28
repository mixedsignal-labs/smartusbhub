# Description: user callback example of the SmartUSBHub
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import os
import time
# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import *

def button_press_callback(channel, status):
    print("Button press detected on channel", channel, "with power status", status)

def main():
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found
    # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)
    
    # 获取并显示硬件和固件版本
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version: V1.{hardware_version}" if hardware_version is not None else "Hardware Version: Unknown")
    print(f"Firmware Version: V1.{firmware_version}" if firmware_version is not None else "Firmware Version: Unknown")
    print()

    #register a callback function to handle the button press event
    hub.register_callback(CMD_GET_CHANNEL_POWER_STATUS, button_press_callback)
    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    main()

