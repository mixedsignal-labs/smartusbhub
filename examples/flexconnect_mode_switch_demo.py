"""
FlexConnect模式切换演示程序

功能：
- 按回车键循环切换FlexConnect模式：PC -> UDISK1 -> UDISK2 -> PC -> ...
- 显示当前模式和故障状态
- 输入 'q' 退出程序

使用方法：
    python examples/flexconnect_mode_switch_demo.py
"""

import sys
import os
import time

# 添加父目录到路径，以便导入smartusbhub
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def print_mode_info(hub, mode):
    """打印模式信息"""
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC (ADB调试模式)",
        FLEXCONNECT_MODE_UDISK1: "UDISK1 (U盘1模式)",
        FLEXCONNECT_MODE_UDISK2: "UDISK2 (U盘2模式)"
    }
    return mode_names.get(mode, f"Unknown({mode})")


def print_fault_info(fault):
    """打印故障信息"""
    if fault is None:
        return "无法获取"
    
    if fault == 0:
        return "无故障"
    
    fault_desc = []
    if fault & 0x01:
        fault_desc.append("DUT_VBUS故障")
    if fault & 0x02:
        fault_desc.append("UDISK1_VBUS故障")
    if fault & 0x04:
        fault_desc.append("UDISK2_VBUS故障")
    
    return f"故障: 0x{fault:02X} ({', '.join(fault_desc)})"


def main():
    """主函数"""
    print("=" * 60)
    print("FlexConnect 模式切换演示程序")
    print("=" * 60)
    print()
    
    # 自动连接FlexConnect设备
    print("正在扫描并连接FlexConnect设备...")
    hub = SmartUSBHub.auto_connect(feature_filter="flexconnect")
    
    if hub is None:
        print("错误: 未找到可用的FlexConnect设备")
        return
    
    print(f"✓ 成功连接到设备: {hub.port}")
    print()
    
    try:
        
        # 获取设备信息
        print("设备信息:")
        info = hub.get_device_info()
        print(f"  端口: {hub.port}")
        print(f"  产品类型: {info.get('product_type')}")
        print(f"  硬件版本: V1.{info.get('hardware_version')}")
        print(f"  固件版本: V1.{info.get('firmware_version')}")
        print()
        
        # 获取当前模式
        current_mode = hub.get_flexconnect_mode()
        if current_mode is None:
            print("错误: 无法获取当前模式")
            hub.disconnect()
            return
        
        # 模式循环顺序
        mode_sequence = [
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_UDISK2
        ]
        
        # 找到当前模式在序列中的位置
        try:
            current_index = mode_sequence.index(current_mode)
        except ValueError:
            # 如果当前模式不在序列中，从PC模式开始
            current_index = 0
            current_mode = FLEXCONNECT_MODE_PC
        
        print("=" * 60)
        print("操作说明:")
        print("  - 按回车键切换到下一个模式")
        print("  - 输入 'q' 或 'quit' 退出程序")
        print("=" * 60)
        print()
        
        # 显示初始状态
        print(f"当前模式: {print_mode_info(hub, current_mode)}")
        fault = hub.get_flexconnect_fault()
        print(f"故障状态: {print_fault_info(fault)}")
        print()
        
        # 主循环
        while True:
            try:
                # 等待用户输入
                user_input = input("按回车键切换模式 (输入 'q' 退出): ").strip().lower()
                
                # 检查是否退出
                if user_input in ['q', 'quit', 'exit']:
                    print("\n退出程序...")
                    break
                
                # 切换到下一个模式
                current_index = (current_index + 1) % len(mode_sequence)
                next_mode = mode_sequence[current_index]
                
                print(f"\n正在切换到: {print_mode_info(hub, next_mode)}...")
                
                # 设置模式
                result = hub.set_flexconnect_mode(next_mode)
                if not result:
                    print("错误: 模式切换失败")
                    continue
                
                # 等待模式切换完成
                time.sleep(0.2)
                
                # 验证模式
                actual_mode = hub.get_flexconnect_mode()
                if actual_mode == next_mode:
                    print(f"✓ 成功切换到: {print_mode_info(hub, next_mode)}")
                    current_mode = next_mode
                else:
                    print(f"警告: 模式切换可能未完成 (期望: {next_mode}, 实际: {actual_mode})")
                    current_mode = actual_mode if actual_mode is not None else current_mode
                
                # 获取故障状态
                fault = hub.get_flexconnect_fault()
                print(f"故障状态: {print_fault_info(fault)}")
                print()
                
            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C，退出程序...")
                break
            except Exception as e:
                print(f"\n错误: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # 断开连接
        if hub is not None:
            hub.disconnect()
            print("已断开连接")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        # 确保在异常情况下也断开连接
        if hub is not None:
            try:
                hub.disconnect()
            except:
                pass


if __name__ == "__main__":
    main()

