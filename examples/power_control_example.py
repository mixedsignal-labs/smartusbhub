# Description: control the power of each channel of the SmartUSBHub
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
    hub_list = SmartUSBHub.scan_available_ports()# Scan all available ports
    print("available device:", hub_list)

    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found
    # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)
    
    # 获取并显示硬件和固件版本
    print(hub.get_product_name())
    print(f"Hardware Version: V1.{hub.get_hardware_version()}")
    print(f"Firmware Version: V1.{hub.get_firmware_version()}")
    print(f"设备最大通道数: {hub.get_max_channels()}")

    interval = 0.5
    
    print("\ncontrol channel power one by one:")

    print("turn on channels 1")
    hub.set_channel_power(1, state=1)
    time.sleep(interval)

    print("turn off channels 1")
    hub.set_channel_power(1, state=0)
    time.sleep(interval)


    print("\ncontrol multi channel power at once:")
    print("turn on channels 1,2,3,4")
    hub.set_channel_power(1,2,3,4, state=1)
    time.sleep(interval)

    print("turn off channels 1,2,3,4")
    hub.set_channel_power(1,2,3,4, state=0)
    time.sleep(interval)

    print("interlock power control")

    for i in range(1, 5):
        hub.set_channel_power_interlock(i)
        print("interlock control,turn on channel", i)
        time.sleep(interval)

    print("set back to normal mode")
    hub.set_channel_power_interlock(None)

    hub.disconnect()
        
if __name__ == "__main__":
    main()
