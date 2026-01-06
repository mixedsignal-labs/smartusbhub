# Description: 
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import os
import time
# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def main():
    hub_list = SmartUSBHub.scan_available_ports()# Scan all available ports
    print("Available devices / 可用设备:", hub_list)
    ch_count = 5 #todo change to get channel count
    
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found

    if hub is None:
        print("No SmartUSBHub found / 未找到 SmartUSBHub 设备")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("Device info / 设备信息:", device_info)
    
    # Get and display hardware and firmware version
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version / 硬件版本: V1.{hardware_version}" if hardware_version is not None else "Hardware Version / 硬件版本: Unknown")
    print(f"Firmware Version / 固件版本: V1.{firmware_version}" if firmware_version is not None else "Firmware Version / 固件版本: Unknown")
    print()
    
    # Press Enter to toggle between fast charge and slow charge mode.
    mode = "FAST_CHARGE"  # or "SLOW_CHARGE"

    print("\nInteractive battery test demo / 交互式电池测试示例")
    print("- Press Enter to toggle mode / 按回车键切换模式")
    print("- Type 'q' then Enter to quit / 输入 'q' 然后回车退出\n")

    try:
        while True:
            cmd = input(f"Current mode / 当前模式: {mode}. Press Enter to toggle (q to quit) / 回车切换，q 退出: ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                print("Exiting... / 正在退出...")
                break

            # Toggle mode
            if mode == "FAST_CHARGE":
                mode = "SLOW_CHARGE"
                print("-> Switching to SLOW_CHARGE (ilim mode) / 切换到慢充模式 (限流模式)")

                # Enable slow charge mode (limits charging current)
                hub.set_channel_slow_charge(1,2,3,4, disconnect_before_switch=False)
            else:
                mode = "FAST_CHARGE"
                print("-> Switching to FAST_CHARGE (full-speed charging) / 切换到快充模式")

                # Enable fast charge mode (full power)
                hub.set_channel_fast_charge(1,2,3,4)

            print(f"[STATE] mode / 模式 = {mode}")
            
            # Get and display charge mode status
            charge_modes = hub.get_channel_charge_mode(1)
            if charge_modes:
                for ch, mode_val in charge_modes.items():
                    mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                    print(f"  Channel {ch} / 通道 {ch}: {mode_str} ({mode_val})")

    except KeyboardInterrupt:
        print("\nInterrupted by user / 用户中断")
    finally:
        hub.disconnect()
        
if __name__ == "__main__":
    main()

