# Description: basic settings and info of the SmartUSBHub
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
    
    print("Starting setting example...")

    default_power_status = hub.get_default_power_status(1,2,3,4)
    if default_power_status:
        for ch, info in default_power_status.items():
            print(f"Channel {ch} default power status is {'enable' if info['enabled'] else 'disable'}, default power is {'ON' if info['value'] else 'OFF'}")
    else:
        print("Failed to get default power status")

    default_dataline_status = hub.get_default_dataline_status(1,2,3,4)
    if default_dataline_status:
        for ch, info in default_dataline_status.items():
            print(f"Channel {ch} default dataline status is {'enable' if info['enabled'] else 'disable'}, default dataline is {'Connect' if info['value'] else 'Disconnect'}")
    else:
        print("Failed to get default dataline status")

    print("Set device address to 0x0000")
    hub.set_device_address(0x0000)
    #read back address
    device_address = hub.get_device_address()
    print("device address: 0x%04X" % device_address)

    print("\r\nEnabling default power status on specified channels with default power set to ON.")
    hub.set_default_power_status(1,2,3,4,enable=1,status=1)
    default_power_status = hub.get_default_power_status(1,2,3,4)
    if default_power_status:
        for ch, info in default_power_status.items():
            print(f"Channel {ch} default power status is {'enable' if info['enabled'] else 'disable'}, default power is {'ON' if info['value'] else 'OFF'}")
    else:
        print("Failed to get default power status")

    print("\r\nDisabling default power status on specified channels.")
    hub.set_default_power_status(1,2,3,4,enable=0)
    default_power_status = hub.get_default_power_status(1,2,3,4)
    if default_power_status:
        for ch, info in default_power_status.items():
            print(f"Channel {ch} default power status is {'enable' if info['enabled'] else 'disable'}, default power is {'ON' if info['value'] else 'OFF'}")
    else:
        print("Failed to get default power status")

    print("\r\nEnabling default dataline status on specified channels with default state set to Disconnect.")
    hub.set_default_dataline_status(1,2,3,4,enable=1,status=0)
    default_dataline_status = hub.get_default_dataline_status(1,2,3,4)
    if default_dataline_status:
        for ch, info in default_dataline_status.items():
            print(f"Channel {ch} default dataline status is {'enable' if info['enabled'] else 'disable'}, default dataline is {'Connect' if info['value'] else 'Disconnect'}")
    else:
        print("Failed to get default dataline status")

    print("\r\nDisabling default dataline status on specified channels.")
    hub.set_default_dataline_status(1,2,3,4,enable=0)
    default_dataline_status = hub.get_default_dataline_status(1,2,3,4)
    if default_dataline_status:
        for ch, info in default_dataline_status.items():
            print(f"Channel {ch} default dataline status is {'enable' if info['enabled'] else 'disable'}, default dataline is {'Connect' if info['value'] else 'Disconnect'}")
    else:
        print("Failed to get default dataline status")
    
    print("\r\nEnabling auto-restore feature.")
    hub.set_auto_restore(1)
    auto_restore_status = hub.get_auto_restore_status()
    if auto_restore_status:
        print("Auto restore is enabled.")
    else:
        print("Failed to get auto restore status")
    time.sleep(1)
    print("\r\nDisabling auto-restore feature.")
    hub.set_auto_restore(0)
    auto_restore_status = hub.get_auto_restore_status()
    if auto_restore_status is 0:
        print("Auto restore is disabled.")
    else:
        print("Failed to get auto restore status")

    print("\r\nSetting operate mode to interlock mode.")
    hub.set_operate_mode(1)
    mode = hub.get_operate_mode()
    if mode!=1 :
        print("Set operate mode to interlock mode failed.")
    print("Operate mode is interlock mode.")
    time.sleep(1)
    print("\r\nChanging operate mode to normal mode.")
    hub.set_operate_mode(0)
    mode = hub.get_operate_mode()
    if mode!=0 :
        print("Set operate mode to normal mode failed.")
    print("Operate mode is normal mode.")
    time.sleep(1)

    print("\r\nDisabling button control.")
    hub.set_button_control(0)
    button_control_status = hub.get_button_control_status()
    if button_control_status is 0:
        print("Button control disabled. Manual button input is now inactive.")
    else:
        print("Failed to get button control status")

    time.sleep(1)
    print("\r\nRe-enabling button control.")
    hub.set_button_control(1)
    button_control_status = hub.get_button_control_status()
    if button_control_status is 1:
        print("Button control enabled. Manual button input is now active.")
    else:
        print("Failed to get button control status")

    print("\r\nFactory reset.")
    result = hub.factory_reset()
    if result:
        print("Factory reset successful.")
    else:
        print("Factory reset failed.")

    print("\r\nSetting example completed.")

    hub.disconnect()
    
    sys.exit(0)
    

if __name__ == "__main__":
    main()
