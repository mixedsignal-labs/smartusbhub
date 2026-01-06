"""
测试五：按键功能与掉电保存联动

验证按键切换模式时，掉电恢复功能是否正确保存状态：
  - 启用掉电恢复 + 按键切换 → 模式应该被保存
  - 禁用掉电恢复 + 按键切换 → 模式不应该被保存，使用默认模式

测试场景：
  5.1: 启用掉电恢复 + 按键切换
  5.2: 禁用掉电恢复 + 按键切换

按键功能：
  - 按键1（短按）：切换到 PC 模式
  - 按键2（短按）：切换到 UDISK1 模式
  - 按键3（短按）：切换到 UDISK2 模式
  - 按键2（长按3秒）：切换掉电恢复开关
  - 按键1（长按6秒）：恢复出厂设置
"""

import sys
import os
import time

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)


def connect_device():
    """连接设备"""
    print("正在连接设备...")
    hub = SmartUSBHub.auto_connect(feature_filter="flexconnect")
    if hub is None:
        print("错误: 未找到设备")
        return None
    print(f"✓ 成功连接到设备: {hub.port}")
    time.sleep(0.2)
    return hub


def verify_mode(hub, expected_mode, mode_names, test_name=""):
    """验证当前模式"""
    current_mode = hub.get_flexconnect_mode()
    print(f"\n{'['+test_name+'] ' if test_name else ''}当前模式: {current_mode} ({mode_names.get(current_mode, '未知')})")
    
    if current_mode == expected_mode:
        print(f"✓ 模式正确: {mode_names.get(expected_mode, '未知')}")
        return True
    else:
        print(f"✗ 模式错误: 期望 {mode_names.get(expected_mode, '未知')} ({expected_mode}), 实际 {mode_names.get(current_mode, '未知')} ({current_mode})")
        return False


def display_button_layout():
    """显示按键布局"""
    print("\n" + "┌" + "─" * 68 + "┐")
    print("│" + " " * 24 + "按键布局图" + " " * 32 + "│")
    print("├" + "─" * 68 + "┤")
    print("│                                                                    │")
    print("│        ┌──────────┐    ┌──────────┐    ┌──────────┐              │")
    print("│        │  按键1   │    │  按键2   │    │  按键3   │              │")
    print("│        │          │    │          │    │          │              │")
    print("│        │   PC     │    │ UDISK1   │    │ UDISK2   │              │")
    print("│        └──────────┘    └──────────┘    └──────────┘              │")
    print("│                                                                    │")
    print("│  按键1：短按切换到PC模式，长按6秒恢复出厂设置                        │")
    print("│  按键2：短按切换到UDISK1模式，长按3秒切换掉电恢复开关                │")
    print("│  按键3：短按切换到UDISK2模式                                        │")
    print("│                                                                    │")
    print("└" + "─" * 68 + "┘")


def test_scenario_5_1():
    """
    测试场景 5.1：启用掉电恢复 + 按键切换
    
    测试步骤：
    1. 启用掉电恢复
    2. 使用协议切换到 PC 模式
    3. 使用按键2切换到 UDISK1 模式
    4. 断电重启
    5. 验证恢复到 UDISK1 模式（按键切换已保存）
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 5.1：启用掉电恢复 + 按键切换")
    
    print("\n测试说明：")
    print("  验证启用掉电恢复时，按键切换的模式是否能正确保存")
    print("  预期：按键切换后断电重启，应该恢复到按键切换的模式")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：启用掉电恢复
        print_separator("步骤1：启用掉电恢复")
        
        result = hub.set_auto_restore(True)
        if not result:
            print("✗ 启用掉电恢复失败")
            return False
        print("✓ 启用掉电恢复成功")
        time.sleep(0.2)
        
        # 验证状态
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复状态: {auto_restore} (期望: 1)")
        if auto_restore != 1:
            print("✗ 掉电恢复状态错误")
            return False
        
        # 步骤2：使用协议切换到 PC 模式
        print_separator("步骤2：使用协议切换到 PC 模式")
        
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        if not result:
            print("✗ 切换失败")
            return False
        print("✓ 切换成功")
        time.sleep(0.3)
        
        if not verify_mode(hub, FLEXCONNECT_MODE_PC, mode_names):
            return False
        
        hub.disconnect()
        
        # 步骤3：使用按键切换
        print_separator("步骤3：使用按键切换到 UDISK1")
        
        display_button_layout()
        
        print("\n" + "⚠" * 35)
        print("⚠️  请执行按键操作")
        print("⚠️  操作：短按按键2（中间的按键）")
        print("⚠️  功能：切换到 UDISK1 模式")
        print("⚠" * 35)
        print("\n注意：")
        print("  - 按键2是中间的按键")
        print("  - 短按即可（不要长按）")
        print("  - 等待约1秒让设备处理")
        
        input("\n按回车键继续（确认已完成按键操作）...")
        
        # 重新连接并验证
        print("\n[验证] 连接设备并验证按键切换结果...")
        time.sleep(1)  # 等待设备稳定
        
        hub = connect_device()
        if hub is None:
            print("⚠️  无法连接设备，跳过验证")
        else:
            if verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names, "按键切换后"):
                print("✓ 按键切换成功")
            else:
                print("⚠️  按键切换可能失败，但继续测试断电重启")
            hub.disconnect()
        
        # 步骤4：提示断电重启
        print("\n" + "⚠" * 35)
        print("⚠️  请断电重启设备")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 35)
        print("\n预期结果：断电重启后应该恢复到 UDISK1 模式")
        print("         （按键切换的模式应该被保存）")
        
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤5：重新连接并验证
        print_separator("步骤5：验证掉电恢复结果")
        
        hub = connect_device()
        if hub is None:
            return False
        
        success = verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names, "断电重启后")
        
        if success:
            print("\n✓✓✓ 测试场景 5.1 通过！")
            print("  结论：启用掉电恢复时，按键切换的模式被正确保存")
            print("       断电重启后能正确恢复到按键切换的模式")
        else:
            print("\n✗✗✗ 测试场景 5.1 失败！")
            current_mode = hub.get_flexconnect_mode()
            print(f"  问题：断电重启后恢复到 {mode_names.get(current_mode, '未知')}，而不是 UDISK1")
            print("  分析：")
            print("    1. 可能按键切换未保存状态")
            print("    2. 可能延迟保存机制未触发")
            print("    3. 可能 Flash 写入有问题")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_5_2():
    """
    测试场景 5.2：禁用掉电恢复 + 按键切换
    
    测试步骤：
    1. 设置默认模式为 PC
    2. 禁用掉电恢复
    3. 使用按键3切换到 UDISK2 模式
    4. 断电重启
    5. 验证恢复到 PC 模式（默认模式，不是 UDISK2）
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 5.2：禁用掉电恢复 + 按键切换")
    
    print("\n测试说明：")
    print("  验证禁用掉电恢复时，按键切换的模式是否不会被保存")
    print("  预期：按键切换后断电重启，应该恢复到默认模式，不是按键切换的模式")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：设置默认模式为 PC
        print_separator("步骤1：设置默认模式为 PC")
        
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
        if not result:
            print("✗ 设置失败")
            return False
        print("✓ 设置成功")
        time.sleep(0.2)
        
        # 验证默认模式
        default_mode = hub.get_flexconnect_default_mode()
        print(f"  默认模式: {default_mode} ({mode_names.get(default_mode, '未知')})")
        
        # 步骤2：禁用掉电恢复
        print_separator("步骤2：禁用掉电恢复")
        
        result = hub.set_auto_restore(False)
        if not result:
            print("✗ 禁用失败")
            return False
        print("✓ 禁用成功")
        time.sleep(0.2)
        
        # 验证状态
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复状态: {auto_restore} (期望: 0)")
        if auto_restore != 0:
            print("✗ 掉电恢复状态错误")
            return False
        
        hub.disconnect()
        
        # 步骤3：使用按键切换
        print_separator("步骤3：使用按键切换到 UDISK2")
        
        display_button_layout()
        
        print("\n" + "⚠" * 35)
        print("⚠️  请执行按键操作")
        print("⚠️  操作：短按按键3（右边的按键）")
        print("⚠️  功能：切换到 UDISK2 模式")
        print("⚠" * 35)
        print("\n注意：")
        print("  - 按键3是右边的按键")
        print("  - 短按即可（不要长按）")
        print("  - 等待约1秒让设备处理")
        
        input("\n按回车键继续（确认已完成按键操作）...")
        
        # 重新连接并验证
        print("\n[验证] 连接设备并验证按键切换结果...")
        time.sleep(1)  # 等待设备稳定
        
        hub = connect_device()
        if hub is None:
            print("⚠️  无法连接设备，跳过验证")
        else:
            if verify_mode(hub, FLEXCONNECT_MODE_UDISK2, mode_names, "按键切换后"):
                print("✓ 按键切换成功")
            else:
                print("⚠️  按键切换可能失败，但继续测试断电重启")
            hub.disconnect()
        
        # 步骤4：提示断电重启
        print("\n" + "⚠" * 35)
        print("⚠️  请断电重启设备")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 35)
        print("\n预期结果：断电重启后应该恢复到 PC 模式（默认模式）")
        print("         而不是 UDISK2 模式（按键切换的模式）")
        
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤5：重新连接并验证
        print_separator("步骤5：验证断电重启结果")
        
        hub = connect_device()
        if hub is None:
            return False
        
        success = verify_mode(hub, FLEXCONNECT_MODE_PC, mode_names, "断电重启后")
        
        if success:
            print("\n✓✓✓ 测试场景 5.2 通过！")
            print("  结论：禁用掉电恢复时，按键切换的模式不会被保存")
            print("       断电重启后正确使用默认模式")
        else:
            print("\n✗✗✗ 测试场景 5.2 失败！")
            current_mode = hub.get_flexconnect_mode()
            if current_mode == FLEXCONNECT_MODE_UDISK2:
                print(f"  问题：断电重启后恢复到 UDISK2，说明按键切换被错误保存了")
                print("  分析：")
                print("    1. 按键切换时没有检查 poweroff_recover 标志")
                print("    2. 或者延迟保存机制没有检查 poweroff_recover")
            else:
                print(f"  问题：断电重启后恢复到 {mode_names.get(current_mode, '未知')}，而不是默认模式 PC")
                print("  分析：")
                print("    1. 默认模式设置可能有问题")
                print("    2. 恢复逻辑可能有问题")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          FlexConnect 按键功能与掉电保存联动测试                    ║
║                                                                  ║
║  测试内容：                                                       ║
║    - 启用掉电恢复时，按键切换是否正确保存状态                       ║
║    - 禁用掉电恢复时，按键切换是否不保存状态                        ║
║                                                                  ║
║  本测试需要：                                                     ║
║    - 物理按键操作（短按按键）                                      ║
║    - 多次断电重启（共2次）                                         ║
║    - 约10-15分钟的测试时间                                         ║
║                                                                  ║
║  ⚠️  注意：测试过程中需要物理操作硬件按键                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    input("按回车键开始测试...")
    
    results = {}
    
    try:
        # 测试场景 5.1
        print_separator()
        result = test_scenario_5_1()
        results["5.1"] = result
        
        if result:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        else:
            print("\n⚠️  测试场景 5.1 失败，是否继续？")
            choice = input("输入 y 继续，其他键退出: ").strip().lower()
            if choice != 'y':
                return
        
        # 测试场景 5.2
        print_separator()
        result = test_scenario_5_2()
        results["5.2"] = result
        
        # 最终结果汇总
        print_separator("测试结果汇总")
        
        print("\n测试场景结果：")
        for scenario, result in results.items():
            if result is True:
                status = "✓ 通过"
            elif result is False:
                status = "✗ 失败"
            else:
                status = "⊘ 跳过"
            print(f"  场景 {scenario}: {status}")
        
        # 统计
        passed = sum(1 for r in results.values() if r is True)
        failed = sum(1 for r in results.values() if r is False)
        
        print(f"\n统计：")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        
        if failed == 0 and passed > 0:
            print("\n✓✓✓ 所有测试通过！✓✓✓")
            print("\n结论：")
            print("  ✓ 启用掉电恢复时，按键切换正确保存状态")
            print("  ✓ 禁用掉电恢复时，按键切换不保存状态")
            print("  ✓ 按键功能与掉电保存联动逻辑正确")
            print("\n这验证了：")
            print("  1. 按键切换时正确检查了 poweroff_recover 标志")
            print("  2. 延迟保存机制正确实现")
            print("  3. Flash 读写功能正常")
        elif failed > 0:
            print("\n✗✗✗ 部分测试失败！")
            print("\n需要检查：")
            if not results.get("5.1"):
                print("  ✗ 按键切换时的保存逻辑（启用掉电恢复时）")
                print("     检查：smart_switch_gpio.c 按键处理代码")
            if not results.get("5.2"):
                print("  ✗ 按键切换时的保存判断（禁用掉电恢复时）")
                print("     检查：按键代码是否检查了 poweroff_recover")
        
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


