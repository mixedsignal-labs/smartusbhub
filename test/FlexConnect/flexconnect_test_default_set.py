import sys
import os
import time

# 添加项目根目录到路径（从test/FlexConnect/到项目根目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def main():
    hub = None
    try:
        hub = SmartUSBHub.scan_and_connect()  # Scan and connect to the first SmartUSBHub found
        # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
        if hub is None:
            print("No SmartUSBHub found")
            sys.exit(1)
        
        device_info = hub.get_device_info()
        print("device info:", device_info)
        
        # 测试设置和读取默认模式
        print("\n测试设置默认模式为 UDISK1...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1)
        print(f"设置结果: {result}")
        
        time.sleep(0.2)  # 等待命令完成

        print("\n测试读取默认模式...")
        default_mode = hub.get_flexconnect_default_mode()
        print(f"默认模式: {default_mode} (0x{default_mode:02X})")
        
        # 验证读取的值
        if default_mode == FLEXCONNECT_MODE_UDISK1:
            print("✓ 默认模式设置成功！")
        else:
            print(f"✗ 默认模式不匹配，期望 {FLEXCONNECT_MODE_UDISK1}，实际 {default_mode}")
        
        # 测试设置为 PC 模式
        print("\n测试设置默认模式为 PC...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
        print(f"设置结果: {result}")
        
        time.sleep(0.2)
        
        default_mode = hub.get_flexconnect_default_mode()
        print(f"默认模式: {default_mode} (0x{default_mode:02X})")
        
        if default_mode == FLEXCONNECT_MODE_PC:
            print("✓ 默认模式恢复为 PC 成功！")
        else:
            print(f"✗ 默认模式不匹配，期望 {FLEXCONNECT_MODE_PC}，实际 {default_mode}")
        
        print("\n测试完成！")
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保断开连接
        if hub is not None:
            try:
                hub.disconnect()
                print("已断开连接")
            except:
                pass

if __name__ == "__main__":
    main()

