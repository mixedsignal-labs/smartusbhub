"""
Demo 01: FlexConnect 基础使用示例

演示内容：
1. 连接设备
2. 获取设备信息
3. 切换模式
4. 查询当前模式

适用场景：
- 快速入门
- 验证设备连接
- 基本功能测试
"""

import sys
import os
import time

# Add project root to sys.path (from examples/FlexConnect/ to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入 SmartUSBHub SDK
from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def main():
    print("=" * 60)
    print("FlexConnect 基础使用示例")
    print("=" * 60)
    
    # ========== 步骤1: 连接设备 ==========
    print("\n[步骤1] 扫描并连接设备...")
    hub = SmartUSBHub.scan_and_connect()
    
    if hub is None:
        print("✗ 错误: 未找到设备")
        print("\n请检查:")
        print("  1. 设备是否已连接")
        print("  2. 驱动是否已安装")
        print("  3. 串口是否被其他程序占用")
        return 1
    
    print("✓ 成功连接到设备")
    
    try:
        # ========== 步骤2: 获取设备信息 ==========
        print("\n[步骤2] 获取设备信息...")
        device_info = hub.get_device_info()
        
        print("\n设备信息:")
        print(f"  产品名称: {device_info['product_type']}")
        if hub.product_type is not None:
            print(f"  产品类型ID: 0x{hub.product_type:02X}")
        else:
            print("  产品类型ID: N/A")
        print(f"  硬件版本: V1.{device_info['hardware_version']}")
        print(f"  固件版本: V1.{device_info['firmware_version']}")
        print(f"  序列号: {device_info['serial_no']}")
        
        # ========== 步骤3: 获取当前状态 ==========
        print("\n[步骤3] 获取当前状态...")
        
        current_mode = hub.get_flexconnect_mode()
        mode_names = {
            FLEXCONNECT_MODE_PC: "PC 模式（ADB 调试）",
            FLEXCONNECT_MODE_UDISK1: "U 盘1 模式",
            FLEXCONNECT_MODE_UDISK2: "U 盘2 模式"
        }
        
        print(f"  当前模式: {mode_names.get(current_mode, '未知')}")
        
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复: {'已启用' if auto_restore == 1 else '已禁用'}")
        
        button_status = hub.get_button_control_status()
        print(f"  按键控制: {'已启用' if button_status == 1 else '已禁用'}")
        
        # ========== 步骤4: 模式切换演示 ==========
        print("\n[步骤4] 模式切换演示...")
        
        # 切换到 PC 模式
        print("\n  → 切换到 PC 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        if result:
            print("  ✓ 切换成功")
            time.sleep(0.5)
            
            # 验证模式
            current_mode = hub.get_flexconnect_mode()
            if current_mode == FLEXCONNECT_MODE_PC:
                print("  ✓ 验证成功: 当前为 PC 模式")
            else:
                print("  ✗ 验证失败")
        else:
            print("  ✗ 切换失败")
        
        # 切换到 U 盘1 模式
        print("\n  → 切换到 U 盘1 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        if result:
            print("  ✓ 切换成功")
            time.sleep(0.5)
            
            # 验证模式
            current_mode = hub.get_flexconnect_mode()
            if current_mode == FLEXCONNECT_MODE_UDISK1:
                print("  ✓ 验证成功: 当前为 U 盘1 模式")
            else:
                print("  ✗ 验证失败")
        else:
            print("  ✗ 切换失败")
        
        # 切换回 PC 模式
        print("\n  → 切换回 PC 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        if result:
            print("  ✓ 切换成功")
        else:
            print("  ✗ 切换失败")
        
        # ========== 完成 ==========
        print("\n" + "=" * 60)
        print("✓ 基础功能测试完成！")
        print("=" * 60)
        
        print("\n提示:")
        print("  - 使用 set_flexconnect_mode() 切换模式")
        print("  - 使用 get_flexconnect_mode() 查询当前模式")
        print("  - 切换模式后建议等待 0.3~1 秒让设备稳定")
        
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # 断开连接
        hub.disconnect()
        print("\n已断开连接")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

