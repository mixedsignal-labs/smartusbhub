# Description: voltage monitor for each channel of the SmartUSBHub
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
from smartusbhub import SmartUSBHub

def main():
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found
    # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)


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