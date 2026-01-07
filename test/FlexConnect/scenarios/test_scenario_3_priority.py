"""
测试三：优先级逻辑验证（关键测试）

验证上电恢复的优先级顺序是否正确：
  优先级1（最高）：默认电源标志 (channel_default_power_flag)
  优先级2（中等）：掉电恢复 (poweroff_recover + channel_power_status)
  优先级3（最低）：上电默认模式 (flexconnect_default_mode)

测试场景：
  3.1: 只有上电默认模式（最低优先级）
  3.2: 掉电恢复 > 上电默认模式
  3.3: 默认电源标志 > 掉电恢复（需要特殊设置，本脚本提供说明）
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
    hub = SmartUSBHub.scan_and_connect()
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


def test_scenario_3_1():
    """
    测试场景 3.1：只有上电默认模式（最低优先级）
    
    条件：
    - channel_default_power_flag = 0 (未设置)
    - poweroff_recover = 0 (禁用)
    - flexconnect_default_mode = UDISK2
    
    预期：断电重启后恢复到 UDISK2（使用默认模式）
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 3.1：只有上电默认模式（最低优先级）")
    
    print("\n测试说明：")
    print("  条件：")
    print("    - 默认电源标志: 未设置")
    print("    - 掉电恢复: 禁用")
    print("    - 上电默认模式: UDISK2")
    print("  预期：断电重启后使用上电默认模式 (UDISK2)")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：恢复出厂设置，清空所有配置
        print("\n[步骤1] 恢复出厂设置（清空所有配置）...")
        result = hub.factory_reset()
        if not result:
            print("✗ 恢复出厂设置失败")
            return False
        print("✓ 恢复出厂设置成功")
        time.sleep(0.5)
        
        # 步骤2：设置上电默认模式为 UDISK2
        print("\n[步骤2] 设置上电默认模式为 UDISK2...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
        if not result:
            print("✗ 设置失败")
            return False
        print("✓ 设置成功")
        time.sleep(0.2)
        
        # 验证设置
        default_mode = hub.get_flexconnect_default_mode()
        print(f"  当前默认模式: {default_mode} ({mode_names.get(default_mode, '未知')})")
        if default_mode != FLEXCONNECT_MODE_UDISK2:
            print(f"✗ 默认模式设置错误")
            return False
        
        # 步骤3：确认掉电恢复已禁用（出厂默认）
        print("\n[步骤3] 确认掉电恢复状态...")
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复状态: {auto_restore} (期望: 0 禁用)")
        if auto_restore != 0:
            print("  ⚠️  掉电恢复未禁用，手动禁用...")
            hub.set_auto_restore(False)
            time.sleep(0.2)
            auto_restore = hub.get_auto_restore_status()
            if auto_restore != 0:
                print("✗ 无法禁用掉电恢复")
                return False
        print("✓ 掉电恢复已禁用")
        
        hub.disconnect()
        
        # 步骤4：提示断电重启
        print("\n" + "⚠" * 35)
        print("⚠️  请断电重启设备")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 35)
        print("\n预期结果：断电重启后应该恢复到 UDISK2 模式")
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤5：重新连接并验证
        print("\n[步骤5] 重新连接并验证模式...")
        hub = connect_device()
        if hub is None:
            return False
        
        # 验证模式
        success = verify_mode(hub, FLEXCONNECT_MODE_UDISK2, mode_names, "验证结果")
        
        if success:
            print("\n✓✓✓ 测试场景 3.1 通过！")
            print("  结论：只有上电默认模式时，正确使用默认模式")
        else:
            print("\n✗✗✗ 测试场景 3.1 失败！")
            print("  问题：未使用上电默认模式")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_3_2():
    """
    测试场景 3.2：掉电恢复 > 上电默认模式
    
    条件：
    - channel_default_power_flag = 0 (未设置)
    - poweroff_recover = 1 (启用)
    - channel_power_status[1] = 1 (保存的是 UDISK1)
    - flexconnect_default_mode = PC
    
    预期：断电重启后恢复到 UDISK1（掉电恢复优先，不是默认模式PC）
    """
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 3.2：掉电恢复 > 上电默认模式")
    
    print("\n测试说明：")
    print("  条件：")
    print("    - 默认电源标志: 未设置")
    print("    - 掉电恢复: 启用")
    print("    - 保存的模式: UDISK1")
    print("    - 上电默认模式: PC")
    print("  预期：断电重启后使用掉电恢复的模式 (UDISK1)，不是默认模式 (PC)")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 步骤1：设置上电默认模式为 PC
        print("\n[步骤1] 设置上电默认模式为 PC...")
        result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
        if not result:
            print("✗ 设置失败")
            return False
        print("✓ 设置成功")
        time.sleep(0.2)
        
        # 验证设置
        default_mode = hub.get_flexconnect_default_mode()
        print(f"  当前默认模式: {default_mode} ({mode_names.get(default_mode, '未知')})")
        
        # 步骤2：启用掉电恢复
        print("\n[步骤2] 启用掉电恢复...")
        result = hub.set_auto_restore(True)
        if not result:
            print("✗ 启用失败")
            return False
        print("✓ 启用成功")
        time.sleep(0.2)
        
        # 验证设置
        auto_restore = hub.get_auto_restore_status()
        print(f"  掉电恢复状态: {auto_restore} (期望: 1 启用)")
        if auto_restore != 1:
            print("✗ 掉电恢复状态错误")
            return False
        
        # 步骤3：切换到 UDISK1（会保存）
        print("\n[步骤3] 切换到 UDISK1 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        if not result:
            print("✗ 切换失败")
            return False
        print("✓ 切换成功")
        time.sleep(0.3)
        
        # 验证当前模式
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names):
            return False
        
        hub.disconnect()
        
        # 步骤4：提示断电重启
        print("\n" + "⚠" * 35)
        print("⚠️  请断电重启设备")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 35)
        print("\n预期结果：断电重启后应该恢复到 UDISK1 模式（掉电恢复）")
        print("         而不是 PC 模式（默认模式）")
        input("\n按回车键继续（确认已重启设备）...")
        
        # 步骤5：重新连接并验证
        print("\n[步骤5] 重新连接并验证模式...")
        hub = connect_device()
        if hub is None:
            return False
        
        # 验证模式
        success = verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names, "验证结果")
        
        if success:
            print("\n✓✓✓ 测试场景 3.2 通过！")
            print("  结论：掉电恢复优先级高于上电默认模式")
        else:
            print("\n✗✗✗ 测试场景 3.2 失败！")
            current_mode = hub.get_flexconnect_mode()
            if current_mode == FLEXCONNECT_MODE_PC:
                print("  问题：错误使用了默认模式，而不是掉电恢复的模式")
                print("  分析：掉电恢复优先级逻辑有问题")
            else:
                print(f"  问题：恢复到意外的模式 {mode_names.get(current_mode, '未知')}")
        
        hub.disconnect()
        return success
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_3_3_instructions():
    """
    测试场景 3.3：默认电源标志 > 掉电恢复（最高优先级）
    
    注意：这个测试需要设置 channel_default_power_flag，
         目前 Python API 可能不支持这个功能。
         
    提供手动测试说明。
    """
    print_separator("测试场景 3.3：默认电源标志 > 掉电恢复（最高优先级）")
    
    print("\n⚠️  注意：此测试需要设置 channel_default_power_flag")
    print("⚠️  Python API 可能不支持此功能，需要通过其他方式设置")
    print("\n测试说明：")
    print("  条件：")
    print("    - channel_default_power_flag[2] = 1 (设置ch2为默认电源)")
    print("    - channel_default_power_status[2] = 1 (ch2默认开启 = UDISK2模式)")
    print("    - poweroff_recover = 1 (启用)")
    print("    - channel_power_status[1] = 1 (保存的是 UDISK1)")
    print("    - flexconnect_default_mode = PC")
    print("\n  预期：断电重启后使用默认电源标志 (UDISK2)")
    print("       而不是掉电恢复 (UDISK1) 或默认模式 (PC)")
    
    print("\n如果需要测试此场景，请：")
    print("  1. 检查 Python API 是否支持 set_default_power_status()")
    print("  2. 或通过固件调试工具设置 channel_default_power_flag")
    print("  3. 或修改固件代码直接设置此标志进行测试")
    
    print("\n⚠️  跳过此测试场景")
    return None


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          FlexConnect 优先级逻辑验证测试                           ║
║                                                                  ║
║  测试上电恢复的优先级顺序：                                        ║
║    1. 默认电源标志 (最高优先级)                                    ║
║    2. 掉电恢复 (中等优先级)                                       ║
║    3. 上电默认模式 (最低优先级)                                    ║
║                                                                  ║
║  本测试需要多次手动断电重启设备                                    ║
║  请准备好约10-15分钟的测试时间                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    input("按回车键开始测试...")
    
    results = {}
    
    try:
        # 测试场景 3.1
        print_separator()
        result = test_scenario_3_1()
        results["3.1"] = result
        
        if result:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        else:
            print("\n⚠️  测试场景 3.1 失败，是否继续？")
            choice = input("输入 y 继续，其他键退出: ").strip().lower()
            if choice != 'y':
                return
        
        # 测试场景 3.2
        print_separator()
        result = test_scenario_3_2()
        results["3.2"] = result
        
        if result:
            print("\n" + "▼" * 35)
            input("\n按回车键查看测试场景 3.3 说明...")
        else:
            print("\n⚠️  测试场景 3.2 失败，是否继续？")
            choice = input("输入 y 继续，其他键退出: ").strip().lower()
            if choice != 'y':
                return
        
        # 测试场景 3.3（仅说明）
        print_separator()
        test_scenario_3_3_instructions()
        results["3.3"] = None  # 未测试
        
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
            print("\n✓✓✓ 所有可测试场景通过！✓✓✓")
            print("\n结论：")
            print("  ✓ 上电默认模式逻辑正确（最低优先级）")
            print("  ✓ 掉电恢复逻辑正确（中等优先级）")
            print("  ✓ 优先级顺序正确")
        elif failed > 0:
            print("\n✗✗✗ 部分测试失败！")
            print("\n需要检查：")
            if not results.get("3.1"):
                print("  ✗ 上电默认模式逻辑")
            if not results.get("3.2"):
                print("  ✗ 掉电恢复优先级逻辑")
        
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



