"""
FlexConnect mode switch demo

Features:
- Press Enter to cycle FlexConnect mode: PC -> UDISK1 -> UDISK2 -> PC -> ...
- Show current mode and fault status
- Type 'q' to quit

Usage:
    python examples/FlexConnect/flexconnect_mode_switch_demo.py
"""

import sys
import os
import time

# Add project root to sys.path (from examples/FlexConnect/ to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def print_mode_info(hub, mode):
    """Return human readable mode name (Chinese + English)."""
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC (ADB 调试模式 / ADB debug mode)",
        FLEXCONNECT_MODE_UDISK1: "UDISK1 (U盘1 模式 / U-disk 1 mode)",
        FLEXCONNECT_MODE_UDISK2: "UDISK2 (U盘2 模式 / U-disk 2 mode)"
    }
    return mode_names.get(mode, f"Unknown({mode})")


def print_fault_info(fault):
    """Return human readable fault description (Chinese + English)."""
    if fault is None:
        return "无法获取 / Not available"
    
    # Some firmware versions use 0xFF to indicate that fault detection is disabled.
    # In this case we treat it as "no fault" to avoid confusing users.
    if fault == 0xFF:
        return "无故障（故障检测已禁用） / No fault (fault detection disabled)"
    
    if fault == 0:
        return "无故障 / No fault"
    
    fault_desc = []
    if fault & 0x01:
        fault_desc.append("DUT_VBUS 故障 / DUT_VBUS fault")
    if fault & 0x02:
        fault_desc.append("UDISK1_VBUS 故障 / UDISK1_VBUS fault")
    if fault & 0x04:
        fault_desc.append("UDISK2_VBUS 故障 / UDISK2_VBUS fault")
    
    return f"故障 / Fault: 0x{fault:02X} ({', '.join(fault_desc)})"


def main():
    """Main entry point."""
    print("=" * 60)
    print("FlexConnect 模式切换演示程序 / FlexConnect mode switch demo")
    print("=" * 60)
    print()
    
    # Automatically connect to FlexConnect device
    print("正在扫描并连接 FlexConnect 设备... / Scanning and connecting to FlexConnect device ...")
    hub = SmartUSBHub.auto_connect(feature_filter="flexconnect")
    
    if hub is None:
        print("错误: 未找到可用的 FlexConnect 设备 / Error: No available FlexConnect device found")
        return
    
    print(f"✓ 成功连接到设备 / Connected to device: {hub.port}")
    print()
    
    try:
        
        # Get device information
        print("设备信息 / Device information:")
        info = hub.get_device_info()
        print(f"  端口 / Port: {hub.port}")
        print(f"  产品类型 / Product type: {info.get('product_type')}")
        print(f"  硬件版本 / HW version: V1.{info.get('hardware_version')}")
        print(f"  固件版本 / FW version: V1.{info.get('firmware_version')}")
        print()
        
        # Get current mode
        current_mode = hub.get_flexconnect_mode()
        if current_mode is None:
            print("错误: 无法获取当前模式 / Error: Failed to get current mode")
            hub.disconnect()
            return
        
        # Mode sequence for cycling
        mode_sequence = [
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_UDISK2
        ]
        
        # Find current mode index in sequence
        try:
            current_index = mode_sequence.index(current_mode)
        except ValueError:
            # 如果当前模式不在序列中，从PC模式开始
            current_index = 0
            current_mode = FLEXCONNECT_MODE_PC
        
        print("=" * 60)
        print("操作说明 / Instructions:")
        print("  - 按回车键切换到下一个模式 / Press Enter to switch to next mode")
        print("  - 输入 'q' 或 'quit' 退出程序 / Type 'q' or 'quit' to exit")
        print("=" * 60)
        print()
        
        # Show initial status
        print(f"当前模式 / Current mode: {print_mode_info(hub, current_mode)}")
        fault = hub.get_flexconnect_fault()
        print(f"故障状态 / Fault status: {print_fault_info(fault)}")
        print()
        
        # Main loop
        while True:
            try:
                # Wait for user input
                user_input = input("按回车键切换模式 (输入 'q' 退出) / Press Enter to switch mode ('q' to quit): ").strip().lower()
                
                # Check for exit
                if user_input in ['q', 'quit', 'exit']:
                    print("\n退出程序 / Exiting program ...")
                    break
                
                # Switch to next mode in sequence
                current_index = (current_index + 1) % len(mode_sequence)
                next_mode = mode_sequence[current_index]
                
                print(f"\n正在切换到 / Switching to: {print_mode_info(hub, next_mode)} ...")
                
                # Set mode
                result = hub.set_flexconnect_mode(next_mode)
                if not result:
                    print("错误: 模式切换失败 / Error: Mode switch failed")
                    continue
                
                # Wait for mode switch to take effect
                time.sleep(0.2)
                
                # Verify mode
                actual_mode = hub.get_flexconnect_mode()
                if actual_mode == next_mode:
                    print(f"✓ 成功切换到 / Switched to: {print_mode_info(hub, next_mode)}")
                    current_mode = next_mode
                else:
                    print(f"警告: 模式切换可能未完成 (期望: {next_mode}, 实际: {actual_mode}) /")
                    print(f"Warning: Mode switch may not have completed (expected: {next_mode}, actual: {actual_mode})")
                    current_mode = actual_mode if actual_mode is not None else current_mode
                
                # Read fault status
                fault = hub.get_flexconnect_fault()
                print(f"故障状态 / Fault status: {print_fault_info(fault)}")
                print()
                
            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C，退出程序 / Ctrl+C detected, exiting program ...")
                break
            except Exception as e:
                print(f"\n错误 / Error: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # Disconnect device
        if hub is not None:
            hub.disconnect()
            print("已断开连接 / Disconnected")
        
    except Exception as e:
        print(f"错误 / Error: {e}")
        import traceback
        traceback.print_exc()
        # Ensure device is disconnected on exception
        if hub is not None:
            try:
                hub.disconnect()
            except:
                pass


if __name__ == "__main__":
    main()


