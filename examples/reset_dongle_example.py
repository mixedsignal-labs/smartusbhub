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

    interval = 0.3
    test_count = 0

    while True:
        # reset dongle: turn off 300ms then turn on
        hub.set_channel_power(1, state=0) #turn off
        status = hub.get_channel_power_status(1)# get channel status
        voltage = hub.get_channel_voltage(1)#check channel is physically off

        if status != 0:
            raise RuntimeError(f"Expected channel 1 OFF, but got: {status}")
        if voltage > 1000:
            raise RuntimeError(f"Expected voltage near 0V after OFF, but got: {voltage:.2f}V")
        
        time.sleep(interval)

        hub.set_channel_power(1, state=1)
        status = hub.get_channel_power_status(1)
        voltage = hub.get_channel_voltage(1)#check channel is physically on

        if status != 1:
            raise RuntimeError(f"Expected channel 1 ON, but got: {status}")
        if voltage < 3000:
            raise RuntimeError(f"Expected voltage > 3.0V after ON, but got: {voltage:.2f}V")
        
        test_count += 1
        print("reset done, total time: ", test_count)
        time.sleep(1)

    hub.disconnect()
        
if __name__ == "__main__":
    main()
