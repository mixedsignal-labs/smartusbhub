# Description: control the dataline of each channel of the SmartUSBHub
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

        #only for usb3 model
        print("disconnect channel 1 usb3 data but keep usb2 data and power on:\n")
        hub.set_channel_usb3_dataline(1,state=0) 
        time.sleep(60)
        
        print("connect channel 1 usb3 data again\n")
        #for re enumeration, we need to turn off and turn on the channel
        hub.set_channel_power(1, state=0)
        time.sleep(1)
        hub.set_channel_power(1, state=1)
        hub.set_channel_usb3_dataline(1,state=1) 

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