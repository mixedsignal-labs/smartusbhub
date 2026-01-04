# Description: 
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
    ch_count = 5 #todo change to get channel count
    
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found

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
    
    # Press Enter to toggle between fast charge and slow charge mode.
    mode = "FAST_CHARGE"  # or "SLOW_CHARGE"

    print("\nInteractive battery test demo")
    print("- Press Enter to toggle mode")
    print("- Type 'q' then Enter to quit\n")

    try:
        while True:
            cmd = input(f"Current mode: {mode}. Press Enter to toggle (q to quit): ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                print("Exiting...")
                break

            # Toggle mode
            if mode == "FAST_CHARGE":
                mode = "SLOW_CHARGE"
                print("-> Switching to SLOW_CHARGE (ilim mode)")

                # Enable slow charge mode (limits charging current)
                hub.set_channel_slow_charge(1,2,3,4, disconnect_before_switch=False)
            else:
                mode = "FAST_CHARGE"
                print("-> Switching to FAST_CHARGE (full-speed charging)")

                # Enable fast charge mode (full power)
                hub.set_channel_fast_charge(1,2,3,4)

            print(f"[STATE] mode={mode}")
            
            # Get and display charge mode status
            charge_modes = hub.get_channel_charge_mode(1)
            if charge_modes:
                for ch, mode_val in charge_modes.items():
                    mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                    print(f"  Channel {ch}: {mode_str} ({mode_val})")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        hub.disconnect()
        
if __name__ == "__main__":
    main()
