"""
测试场景 2.3：禁用掉电恢复 - 使用默认模式

测试步骤：
1. 设置默认模式为 PC
2. 禁用掉电恢复
3. 切换到 UDISK2 模式（当前模式）
4. 断电重启设备
5. 验证设备应该使用默认模式（PC），而不是 UDISK2

预期结果：断电重启后，设备应该恢复到 PC 模式（默认模式）
实际结果：如果恢复到 UDISK2，说明逻辑有问题
"""

import sys
import os
import time

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def main():
    hub = None
    try:
        print("=" * 60)
        print("测试场景 2.3：禁用掉电恢复 - 使用默认模式")
        print("=" * 60)
        
        hub = SmartUSBHub.scan_and_connect()
        if hub is None:
            print("错误: 未找到设备")
            sys.exit(1)
        
        print(f"✓ 成功连接到设备: {hub.port}\n")
        
        # 步骤1：设置默认模式为 PC
        print("[步骤1] 设置默认模式为 PC...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
        if result:
            print("  ✓ 设置成功")
        else:
            print("  ✗ 设置失败")
            return
        
        time.sleep(0.2)
        
        # 验证默认模式
        default_mode = hub.get_flexconnect_default_mode()
        print(f"  当前默认模式: {default_mode} (0=PC, 1=UDISK1, 2=UDISK2)")
        if default_mode != FLEXCONNECT_MODE_PC:
            print(f"  ⚠️  警告: 默认模式不是 PC，而是 {default_mode}")
        
        # 步骤2：禁用掉电恢复
        print("\n[步骤2] 禁用掉电恢复...")
        result = hub.set_auto_restore(False)
        if result:
            print("  ✓ 禁用成功")
        else:
            print("  ✗ 禁用失败")
            return
        
        time.sleep(0.2)
        
        # 验证掉电恢复状态
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复状态: {auto_restore} (0=禁用, 1=启用)")
        if auto_restore != 0:
            print(f"  ⚠️  警告: 掉电恢复未禁用，状态为 {auto_restore}")
        
        # 步骤3：切换到 UDISK2 模式
        print("\n[步骤3] 切换到 UDISK2 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
        if result:
            print("  ✓ 切换成功")
            time.sleep(0.3)
        else:
            print("  ✗ 切换失败")
            return
        
        # 验证当前模式
        current_mode = hub.get_flexconnect_mode()
        print(f"  当前模式: {current_mode} (0=PC, 1=UDISK1, 2=UDISK2)")
        if current_mode != FLEXCONNECT_MODE_UDISK2:
            print(f"  ⚠️  警告: 当前模式不是 UDISK2，而是 {current_mode}")
        
        # 步骤4：提示断电重启
        print("\n" + "=" * 60)
        print("[步骤4] 请断电重启设备")
        print("=" * 60)
        print("  操作步骤：")
        print("  1. 拔掉设备电源（USB线）")
        print("  2. 等待 5 秒")
        print("  3. 重新插上电源")
        print("  4. 按回车键继续测试...")
        print()
        print("  重要：")
        print("  - 默认模式：PC (0)")
        print("  - 掉电恢复：禁用 (0)")
        print("  - 切换前模式：UDISK2 (2)")
        print("  ⚠️  预期结果：断电重启后应该恢复到 PC 模式（默认模式）")
        print("  ⚠️  如果恢复到 UDISK2，说明掉电恢复逻辑有 BUG！")
        print("=" * 60)
        
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤5：重新连接并验证模式
        print("\n[步骤5] 重新连接设备并验证模式...")
        hub.disconnect()
        time.sleep(1)
        
        hub = SmartUSBHub.scan_and_connect()
        if hub is None:
            print("错误: 重新连接失败")
            return
        
        print("  ✓ 重新连接成功")
        time.sleep(0.5)
        
        # 读取当前模式
        current_mode = hub.get_flexconnect_mode()
        print(f"\n  断电重启后的模式: {current_mode}")
        
        # 读取默认模式和掉电恢复状态（验证参数是否保存）
        default_mode = hub.get_flexconnect_default_mode()
        auto_restore = hub.get_auto_restore_status()
        
        print(f"  默认模式: {default_mode} (0=PC, 1=UDISK1, 2=UDISK2)")
        print(f"  掉电恢复: {auto_restore} (0=禁用, 1=启用)")
        
        # 验证结果
        print("\n" + "=" * 60)
        print("测试结果")
        print("=" * 60)
        
        if current_mode == FLEXCONNECT_MODE_PC:
            print("✓ 测试通过：设备恢复到 PC 模式（默认模式）")
            print("  掉电恢复逻辑正确！")
        elif current_mode == FLEXCONNECT_MODE_UDISK2:
            print("✗ 测试失败：设备恢复到 UDISK2 模式")
            print("  ⚠️  BUG：禁用掉电恢复后，仍然从保存的状态恢复！")
            print("\n  问题分析：")
            print("  1. 可能原因：channel_power_status 没有在禁用掉电恢复时清除")
            print("  2. 可能原因：恢复逻辑没有正确检查 poweroff_recover 标志")
            print("  3. 可能原因：按键切换时立即写入了 channel_power_status")
        else:
            print(f"? 意外结果：设备恢复到模式 {current_mode}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hub is not None:
            try:
                hub.disconnect()
                print("\n已断开连接")
            except:
                pass


if __name__ == "__main__":
    main()


