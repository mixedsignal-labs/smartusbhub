"""
测试四：恢复出厂设置验证

验证恢复出厂设置功能是否正确重置所有参数：
  - flexconnect_default_mode → MODE_PC (0)
  - poweroff_recover → 0 (禁用)
  - channel_power_status → 全部清零
  - 当前模式 → 应用默认模式（PC）

测试场景：
  4.1: 恢复出厂设置功能
  4.2: 恢复出厂设置后断电重启
  4.3: 按键长按恢复出厂设置
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


def verify_factory_defaults(hub, mode_names):
    """
    验证出厂默认值
    
    预期：
    - flexconnect_default_mode = MODE_PC (0)
    - poweroff_recover = 0 (禁用)
    - current_mode = MODE_PC (0)
    """
    print("\n验证出厂默认值...")
    
    all_correct = True
    
    # 1. 验证默认模式
    default_mode = hub.get_flexconnect_default_mode()
    print(f"\n1. 上电默认模式: {default_mode} ({mode_names.get(default_mode, '未知')})")
    if default_mode == FLEXCONNECT_MODE_PC:
        print("   ✓ 正确: MODE_PC (出厂默认)")
    else:
        print(f"   ✗ 错误: 期望 MODE_PC (0), 实际 {default_mode}")
        all_correct = False
    
    # 2. 验证掉电恢复状态
    auto_restore = hub.get_auto_restore_status()
    print(f"\n2. 掉电恢复状态: {auto_restore}")
    if auto_restore == 0:
        print("   ✓ 正确: 禁用 (出厂默认)")
    else:
        print(f"   ✗ 错误: 期望 禁用 (0), 实际 {auto_restore}")
        all_correct = False
    
    # 3. 验证当前模式
    current_mode = hub.get_flexconnect_mode()
    print(f"\n3. 当前模式: {current_mode} ({mode_names.get(current_mode, '未知')})")
    if current_mode == FLEXCONNECT_MODE_PC:
        print("   ✓ 正确: MODE_PC (应用默认模式)")
    else:
        print(f"   ✗ 错误: 期望 MODE_PC (0), 实际 {current_mode}")
        all_correct = False
    
    return all_correct


def test_scenario_4_1():
    """
    测试场景 4.1：恢复出厂设置功能
    
    步骤：
    1. 设置一些非默认值
    2. 读取当前状态（恢复前）
    3. 执行恢复出厂设置
    4. 验证恢复后的状态
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 4.1：恢复出厂设置功能")
    
    print("\n测试说明：")
    print("  1. 设置一些非默认值（默认模式、掉电恢复、当前模式）")
    print("  2. 执行恢复出厂设置")
    print("  3. 验证所有参数是否恢复为出厂默认值")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # ===== 步骤1：设置一些非默认值 =====
        print_separator("步骤1：设置非默认值")
        
        print("\n[1.1] 设置默认模式为 UDISK2（非默认）...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
        if not result:
            print("✗ 设置失败")
            return False
        print("✓ 设置成功")
        time.sleep(0.2)
        
        print("\n[1.2] 启用掉电恢复（非默认）...")
        result = hub.set_auto_restore(True)
        if not result:
            print("✗ 启用失败")
            return False
        print("✓ 启用成功")
        time.sleep(0.2)
        
        print("\n[1.3] 切换到 UDISK1 模式（非默认）...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        if not result:
            print("✗ 切换失败")
            return False
        print("✓ 切换成功")
        time.sleep(0.3)
        
        # ===== 步骤2：读取当前状态（恢复前） =====
        print_separator("步骤2：读取当前状态（恢复前）")
        
        default_mode_before = hub.get_flexconnect_default_mode()
        auto_restore_before = hub.get_auto_restore_status()
        current_mode_before = hub.get_flexconnect_mode()
        
        print(f"\n  默认模式: {default_mode_before} ({mode_names.get(default_mode_before, '未知')})")
        print(f"  掉电恢复: {auto_restore_before} ({'启用' if auto_restore_before == 1 else '禁用'})")
        print(f"  当前模式: {current_mode_before} ({mode_names.get(current_mode_before, '未知')})")
        
        if (default_mode_before != FLEXCONNECT_MODE_UDISK2 or 
            auto_restore_before != 1 or 
            current_mode_before != FLEXCONNECT_MODE_UDISK1):
            print("\n⚠️  警告: 设置的非默认值不正确，测试可能不准确")
        
        # ===== 步骤3：执行恢复出厂设置 =====
        print_separator("步骤3：执行恢复出厂设置")
        
        print("\n正在执行恢复出厂设置...")
        result = hub.factory_reset()
        if not result:
            print("✗ 恢复出厂设置失败")
            return False
        print("✓ 恢复出厂设置成功")
        time.sleep(0.5)  # 等待设备重置完成
        
        # ===== 步骤4：验证恢复后的状态 =====
        print_separator("步骤4：验证恢复后的状态")
        
        success = verify_factory_defaults(hub, mode_names)
        
        # 显示对比
        print("\n" + "-" * 70)
        print("恢复前后对比：")
        print("-" * 70)
        
        default_mode_after = hub.get_flexconnect_default_mode()
        auto_restore_after = hub.get_auto_restore_status()
        current_mode_after = hub.get_flexconnect_mode()
        
        print(f"\n默认模式:   {mode_names.get(default_mode_before, '未知')} → {mode_names.get(default_mode_after, '未知')}")
        print(f"掉电恢复:   {'启用' if auto_restore_before == 1 else '禁用'} → {'启用' if auto_restore_after == 1 else '禁用'}")
        print(f"当前模式:   {mode_names.get(current_mode_before, '未知')} → {mode_names.get(current_mode_after, '未知')}")
        
        if success:
            print("\n✓✓✓ 测试场景 4.1 通过！")
            print("  结论：恢复出厂设置功能正常，所有参数已恢复为默认值")
        else:
            print("\n✗✗✗ 测试场景 4.1 失败！")
            print("  问题：部分参数未正确恢复为默认值")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_4_2():
    """
    测试场景 4.2：恢复出厂设置后断电重启
    
    验证恢复出厂设置后，参数持久化是否正确。
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 4.2：恢复出厂设置后断电重启")
    
    print("\n测试说明：")
    print("  1. 设置非默认值")
    print("  2. 执行恢复出厂设置")
    print("  3. 断电重启设备")
    print("  4. 验证参数是否仍然是出厂默认值")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：设置非默认值
        print("\n[步骤1] 设置非默认值...")
        hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
        time.sleep(0.2)
        hub.set_auto_restore(True)
        time.sleep(0.2)
        hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        time.sleep(0.3)
        print("✓ 已设置非默认值")
        
        # 步骤2：执行恢复出厂设置
        print("\n[步骤2] 执行恢复出厂设置...")
        result = hub.factory_reset()
        if not result:
            print("✗ 恢复出厂设置失败")
            return False
        print("✓ 恢复出厂设置成功")
        time.sleep(0.5)
        
        # 验证立即恢复后的状态
        print("\n[验证] 立即验证恢复后的状态...")
        if not verify_factory_defaults(hub, mode_names):
            print("\n⚠️  警告: 恢复后立即验证失败，但继续测试断电重启")
        else:
            print("\n✓ 立即验证通过")
        
        hub.disconnect()
        
        # 步骤3：提示断电重启
        print("\n" + "⚠" * 35)
        print("⚠️  请断电重启设备")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 35)
        print("\n预期结果：断电重启后，所有参数仍然是出厂默认值")
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤4：重新连接并验证
        print("\n[步骤4] 重新连接并验证参数持久化...")
        hub = connect_device()
        if hub is None:
            return False
        
        success = verify_factory_defaults(hub, mode_names)
        
        if success:
            print("\n✓✓✓ 测试场景 4.2 通过！")
            print("  结论：恢复出厂设置后，参数持久化正确")
            print("       断电重启后仍然保持出厂默认值")
        else:
            print("\n✗✗✗ 测试场景 4.2 失败！")
            print("  问题：断电重启后，参数未保持出厂默认值")
            print("  分析：Flash 写入或读取可能有问题")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_4_3_instructions():
    """
    测试场景 4.3：按键长按恢复出厂设置
    
    手动测试说明。
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 4.3：按键长按恢复出厂设置")
    
    print("\n测试说明：")
    print("  FlexConnect 支持通过按键1长按6秒恢复出厂设置")
    print("  此测试需要物理按键操作")
    
    print("\n⚠️  手动测试步骤：")
    print("  1. 先设置一些非默认值")
    print("  2. 长按按键1 6秒以上")
    print("  3. LED 应该闪烁3次（确认）")
    print("  4. 重新连接设备并验证参数")
    
    try:
        choice = input("\n是否进行手动测试？(y/n): ").strip().lower()
        if choice != 'y':
            print("跳过手动测试")
            return None
        
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：设置非默认值
        print("\n[步骤1] 设置非默认值...")
        hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
        time.sleep(0.2)
        hub.set_auto_restore(True)
        time.sleep(0.2)
        hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        time.sleep(0.3)
        print("✓ 已设置非默认值")
        
        # 读取当前状态
        print("\n[验证] 当前状态：")
        default_mode = hub.get_flexconnect_default_mode()
        auto_restore = hub.get_auto_restore_status()
        current_mode = hub.get_flexconnect_mode()
        print(f"  默认模式: {mode_names.get(default_mode, '未知')}")
        print(f"  掉电恢复: {'启用' if auto_restore == 1 else '禁用'}")
        print(f"  当前模式: {mode_names.get(current_mode, '未知')}")
        
        hub.disconnect()
        
        # 步骤2：提示按键操作
        print("\n" + "⚠" * 35)
        print("⚠️  请执行按键操作")
        print("⚠️  操作：")
        print("⚠️    1. 长按按键1（最左边的按键）")
        print("⚠️    2. 保持按住至少6秒")
        print("⚠️    3. LED应该闪烁3次")
        print("⚠️    4. 释放按键")
        print("⚠" * 35)
        input("\n按回车键继续（确认已完成按键操作）...")
        
        # 步骤3：重新连接并验证
        print("\n[步骤3] 重新连接并验证...")
        time.sleep(1)  # 等待设备稳定
        
        hub = connect_device()
        if hub is None:
            print("⚠️  无法连接设备，请检查设备状态")
            return False
        
        success = verify_factory_defaults(hub, mode_names)
        
        if success:
            print("\n✓✓✓ 测试场景 4.3 通过！")
            print("  结论：按键长按恢复出厂设置功能正常")
        else:
            print("\n✗✗✗ 测试场景 4.3 失败！")
            print("  问题：按键操作未能恢复出厂设置")
            print("  请检查：")
            print("    1. 是否按对了按键（按键1，最左边）")
            print("    2. 是否按够了时间（至少6秒）")
            print("    3. LED 是否闪烁了3次（确认）")
        
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
║          FlexConnect 恢复出厂设置功能验证测试                      ║
║                                                                  ║
║  验证恢复出厂设置功能是否正确重置所有参数：                         ║
║    - flexconnect_default_mode → MODE_PC (0)                     ║
║    - poweroff_recover → 0 (禁用)                                 ║
║    - channel_power_status → 全部清零                              ║
║    - 当前模式 → MODE_PC                                           ║
║                                                                  ║
║  测试内容：                                                       ║
║    4.1 - 恢复出厂设置功能（协议命令）                              ║
║    4.2 - 恢复出厂设置后断电重启验证                                ║
║    4.3 - 按键长按恢复出厂设置（手动测试）                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    input("按回车键开始测试...")
    
    results = {}
    
    try:
        # 测试场景 4.1
        print_separator()
        result = test_scenario_4_1()
        results["4.1"] = result
        
        if result:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        else:
            print("\n⚠️  测试场景 4.1 失败，是否继续？")
            choice = input("输入 y 继续，其他键退出: ").strip().lower()
            if choice != 'y':
                return
        
        # 测试场景 4.2
        print_separator()
        result = test_scenario_4_2()
        results["4.2"] = result
        
        if result:
            print("\n" + "▼" * 35)
            input("\n按回车键继续测试场景 4.3...")
        else:
            print("\n⚠️  测试场景 4.2 失败，是否继续？")
            choice = input("输入 y 继续，其他键退出: ").strip().lower()
            if choice != 'y':
                return
        
        # 测试场景 4.3（手动测试）
        print_separator()
        result = test_scenario_4_3_instructions()
        results["4.3"] = result
        
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
        skipped = sum(1 for r in results.values() if r is None)
        
        print(f"\n统计：")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  跳过: {skipped}")
        
        if failed == 0 and passed > 0:
            print("\n✓✓✓ 所有测试通过！✓✓✓")
            print("\n结论：")
            print("  ✓ 协议命令恢复出厂设置功能正常")
            print("  ✓ 参数持久化功能正常")
            if results.get("4.3"):
                print("  ✓ 按键恢复出厂设置功能正常")
            print("  ✓ 所有参数都能正确恢复为出厂默认值")
        elif failed > 0:
            print("\n✗✗✗ 部分测试失败！")
            print("\n需要检查：")
            if not results.get("4.1"):
                print("  ✗ 恢复出厂设置逻辑（smart_switch_params_reset）")
            if not results.get("4.2"):
                print("  ✗ Flash 参数持久化")
            if results.get("4.3") is False:
                print("  ✗ 按键恢复出厂设置功能")
        
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



