"""
测试六：边界条件和异常测试

验证系统在各种边界条件和异常情况下的行为：
  - 无效参数处理
  - 快速连续切换
  - 重复设置相同值
  - 多次断电重启
  - 参数一致性验证

测试场景：
  6.1: 无效参数测试
  6.2: 快速连续模式切换
  6.3: 重复设置相同值
  6.4: 多次断电重启持久化验证
  6.5: 参数读取一致性验证
"""

import sys
import os
import time
import logging

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2, FLEXCONNECT_MODE_DISCONNECT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


def test_scenario_6_1():
    """
    测试场景 6.1：无效参数测试
    
    测试内容：
    - 设置无效的 FlexConnect 模式值
    - 设置无效的默认模式值
    - 验证设备能正确拒绝无效参数
    """
    print_separator("测试场景 6.1：无效参数测试")
    
    print("\n测试说明：")
    print("  验证设备对无效参数的处理能力")
    print("  预期：设备应该拒绝无效参数，不改变当前状态")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 记录初始状态
        print("\n[初始状态]")
        initial_mode = hub.get_flexconnect_mode()
        initial_default_mode = hub.get_flexconnect_default_mode()
        print(f"  当前模式: {initial_mode}")
        print(f"  默认模式: {initial_default_mode}")
        
        all_passed = True
        
        # 测试1：无效的 FlexConnect 模式（DISCONNECT 作为默认模式）
        print("\n[测试1] 尝试设置无效的默认模式: FLEXCONNECT_MODE_DISCONNECT (0x03)")
        try:
            result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_DISCONNECT)
            print(f"✗ 错误：应该拒绝 DISCONNECT 作为默认模式，但返回了: {result}")
            all_passed = False
        except ValueError as e:
            print(f"✓ 正确拒绝: {e}")
        except Exception as e:
            print(f"⚠ 异常: {e}")
        
        time.sleep(0.2)
        
        # 测试2：无效的模式值 (> 3)
        print("\n[测试2] 尝试设置超出范围的默认模式: 0x04")
        try:
            result = hub.set_flexconnect_default_mode(0x04)
            print(f"✗ 错误：应该拒绝无效模式，但返回了: {result}")
            all_passed = False
        except (ValueError, Exception) as e:
            print(f"✓ 正确拒绝: {e}")
        
        time.sleep(0.2)
        
        # 测试3：负数模式值
        print("\n[测试3] 尝试设置负数模式值: -1")
        try:
            result = hub.set_flexconnect_default_mode(-1)
            print(f"✗ 错误：应该拒绝负数模式，但返回了: {result}")
            all_passed = False
        except (ValueError, Exception) as e:
            print(f"✓ 正确拒绝: {e}")
        
        time.sleep(0.2)
        
        # 测试4：超大值
        print("\n[测试4] 尝试设置超大值: 0xFF")
        try:
            result = hub.set_flexconnect_default_mode(0xFF)
            print(f"✗ 错误：应该拒绝超大值，但返回了: {result}")
            all_passed = False
        except (ValueError, Exception) as e:
            print(f"✓ 正确拒绝: {e}")
        
        time.sleep(0.2)
        
        # 验证状态未改变
        print("\n[验证] 检查状态是否未改变...")
        final_mode = hub.get_flexconnect_mode()
        final_default_mode = hub.get_flexconnect_default_mode()
        print(f"  当前模式: {final_mode} (初始: {initial_mode})")
        print(f"  默认模式: {final_default_mode} (初始: {initial_default_mode})")
        
        if final_mode == initial_mode and final_default_mode == initial_default_mode:
            print("✓ 状态未改变，无效参数被正确拒绝")
        else:
            print("✗ 状态发生了改变，无效参数可能被接受了")
            all_passed = False
        
        hub.disconnect()
        
        if all_passed:
            print("\n✓✓✓ 测试场景 6.1 通过！")
            print("  结论：设备能正确拒绝所有无效参数")
            return True
        else:
            print("\n✗✗✗ 测试场景 6.1 失败！")
            print("  问题：部分无效参数未被正确拒绝")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False


def test_scenario_6_2():
    """
    测试场景 6.2：快速连续模式切换
    
    测试内容：
    - 快速连续切换模式（10次）
    - 验证每次切换都成功
    - 验证最终状态正确
    """
    print_separator("测试场景 6.2：快速连续模式切换")
    
    print("\n测试说明：")
    print("  验证设备在快速连续切换模式时的稳定性")
    print("  预期：所有切换都应该成功，最终状态正确")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 先禁用掉电恢复，避免频繁写Flash
        print("\n[准备] 禁用掉电恢复（避免频繁写Flash）...")
        hub.set_auto_restore(False)
        time.sleep(0.2)
        
        # 定义测试序列
        test_sequence = [
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_UDISK2,
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK2,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_UDISK2,
            FLEXCONNECT_MODE_PC,
        ]
        
        mode_names = {
            FLEXCONNECT_MODE_PC: "PC",
            FLEXCONNECT_MODE_UDISK1: "UDISK1",
            FLEXCONNECT_MODE_UDISK2: "UDISK2"
        }
        
        print(f"\n[测试] 执行 {len(test_sequence)} 次快速模式切换...")
        print(f"  序列: {' → '.join([mode_names[m] for m in test_sequence])}")
        
        success_count = 0
        fail_count = 0
        
        start_time = time.time()
        
        for i, target_mode in enumerate(test_sequence, 1):
            result = hub.set_flexconnect_mode(target_mode)
            time.sleep(0.05)  # 很短的延迟
            
            # 验证切换结果
            current_mode = hub.get_flexconnect_mode()
            
            if current_mode == target_mode:
                success_count += 1
                print(f"  [{i}/{len(test_sequence)}] ✓ {mode_names[target_mode]}")
            else:
                fail_count += 1
                print(f"  [{i}/{len(test_sequence)}] ✗ 目标: {mode_names[target_mode]}, 实际: {mode_names.get(current_mode, '未知')}")
            
            time.sleep(0.05)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[结果]")
        print(f"  成功: {success_count}/{len(test_sequence)}")
        print(f"  失败: {fail_count}/{len(test_sequence)}")
        print(f"  耗时: {elapsed_time:.2f}秒")
        print(f"  平均切换时间: {elapsed_time/len(test_sequence):.3f}秒")
        
        # 验证最终状态
        final_mode = hub.get_flexconnect_mode()
        expected_final_mode = test_sequence[-1]
        
        print(f"\n[验证] 最终模式: {mode_names.get(final_mode, '未知')} (期望: {mode_names[expected_final_mode]})")
        
        hub.disconnect()
        
        if fail_count == 0 and final_mode == expected_final_mode:
            print("\n✓✓✓ 测试场景 6.2 通过！")
            print("  结论：设备能正确处理快速连续模式切换")
            return True
        else:
            print("\n✗✗✗ 测试场景 6.2 失败！")
            print(f"  问题：{fail_count} 次切换失败")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False


def test_scenario_6_3():
    """
    测试场景 6.3：重复设置相同值
    
    测试内容：
    - 多次设置相同的模式
    - 多次设置相同的默认模式
    - 多次设置相同的掉电恢复状态
    - 验证设备能正确处理，不产生异常
    """
    print_separator("测试场景 6.3：重复设置相同值")
    
    print("\n测试说明：")
    print("  验证重复设置相同值时设备的行为")
    print("  预期：设备应该正常处理，不产生异常")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        all_passed = True
        
        # 测试1：重复设置相同模式
        print("\n[测试1] 重复设置相同模式 (PC) 5次...")
        for i in range(5):
            result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
            time.sleep(0.1)
            if not result:
                print(f"  ✗ 第 {i+1} 次设置失败")
                all_passed = False
            else:
                print(f"  ✓ 第 {i+1} 次设置成功")
        
        current_mode = hub.get_flexconnect_mode()
        if current_mode == FLEXCONNECT_MODE_PC:
            print("✓ 最终模式正确")
        else:
            print(f"✗ 最终模式错误: {current_mode}")
            all_passed = False
        
        # 测试2：重复设置相同默认模式
        print("\n[测试2] 重复设置相同默认模式 (UDISK1) 5次...")
        for i in range(5):
            result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1)
            time.sleep(0.1)
            if not result:
                print(f"  ✗ 第 {i+1} 次设置失败")
                all_passed = False
            else:
                print(f"  ✓ 第 {i+1} 次设置成功")
        
        default_mode = hub.get_flexconnect_default_mode()
        if default_mode == FLEXCONNECT_MODE_UDISK1:
            print("✓ 最终默认模式正确")
        else:
            print(f"✗ 最终默认模式错误: {default_mode}")
            all_passed = False
        
        # 测试3：重复设置相同掉电恢复状态
        print("\n[测试3] 重复设置相同掉电恢复状态 (启用) 5次...")
        for i in range(5):
            result = hub.set_auto_restore(True)
            time.sleep(0.1)
            if not result:
                print(f"  ✗ 第 {i+1} 次设置失败")
                all_passed = False
            else:
                print(f"  ✓ 第 {i+1} 次设置成功")
        
        auto_restore = hub.get_auto_restore_status()
        if auto_restore == 1:
            print("✓ 最终掉电恢复状态正确")
        else:
            print(f"✗ 最终掉电恢复状态错误: {auto_restore}")
            all_passed = False
        
        hub.disconnect()
        
        if all_passed:
            print("\n✓✓✓ 测试场景 6.3 通过！")
            print("  结论：设备能正确处理重复设置相同值的情况")
            print("  注意：重复写入可能触发Flash写入，应优化避免不必要的写入")
            return True
        else:
            print("\n✗✗✗ 测试场景 6.3 失败！")
            print("  问题：重复设置时出现异常")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False


def test_scenario_6_4():
    """
    测试场景 6.4：多次断电重启持久化验证
    
    测试内容：
    - 设置特定配置
    - 进行多次断电重启（5次）
    - 每次重启后验证配置是否保持不变
    """
    print_separator("测试场景 6.4：多次断电重启持久化验证")
    
    print("\n测试说明：")
    print("  验证参数在多次断电重启后的持久化能力")
    print("  预期：配置在多次重启后保持不变")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        # 设置测试配置
        print("\n[准备] 设置测试配置...")
        hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
        time.sleep(0.2)
        hub.set_auto_restore(True)
        time.sleep(0.2)
        hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        time.sleep(0.2)
        
        print("  默认模式: UDISK2")
        print("  掉电恢复: 启用")
        print("  当前模式: UDISK1")
        print("  预期：每次重启后应该恢复到 UDISK1")
        
        hub.disconnect()
        
        # 进行多次重启测试
        reboot_count = 5
        all_passed = True
        
        for i in range(1, reboot_count + 1):
            print(f"\n{'='*70}")
            print(f"  第 {i}/{reboot_count} 次重启测试")
            print(f"{'='*70}")
            
            print("\n⚠️  请断电重启设备...")
            input("  (断电 → 等待5秒 → 上电) 然后按回车键继续...\n")
            
            # 重新连接
            hub = connect_device()
            if hub is None:
                print(f"✗ 第 {i} 次重启后无法连接设备")
                all_passed = False
                break
            
            # 验证配置
            default_mode = hub.get_flexconnect_default_mode()
            auto_restore = hub.get_auto_restore_status()
            current_mode = hub.get_flexconnect_mode()
            
            print(f"\n[验证] 第 {i} 次重启后的状态:")
            print(f"  默认模式: {default_mode} (期望: {FLEXCONNECT_MODE_UDISK2})")
            print(f"  掉电恢复: {auto_restore} (期望: 1)")
            print(f"  当前模式: {current_mode} (期望: {FLEXCONNECT_MODE_UDISK1})")
            
            if (default_mode == FLEXCONNECT_MODE_UDISK2 and 
                auto_restore == 1 and 
                current_mode == FLEXCONNECT_MODE_UDISK1):
                print(f"✓ 第 {i} 次验证通过")
            else:
                print(f"✗ 第 {i} 次验证失败")
                all_passed = False
                break
            
            hub.disconnect()
        
        # 恢复到干净状态
        print("\n[清理] 恢复到初始配置...")
        hub = connect_device()
        if hub:
            hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
            hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
            hub.set_auto_restore(False)
            hub.disconnect()
        
        if all_passed:
            print("\n✓✓✓ 测试场景 6.4 通过！")
            print(f"  结论：配置在 {reboot_count} 次断电重启后保持不变")
            print("  验证：Flash 持久化功能可靠")
            return True
        else:
            print("\n✗✗✗ 测试场景 6.4 失败！")
            print("  问题：某次重启后配置丢失或错误")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False


def test_scenario_6_5():
    """
    测试场景 6.5：参数读取一致性验证
    
    测试内容：
    - 重复读取同一参数多次
    - 验证每次读取的结果是否一致
    - 设置新值后立即读取验证
    """
    print_separator("测试场景 6.5：参数读取一致性验证")
    
    print("\n测试说明：")
    print("  验证参数读取的一致性和可靠性")
    print("  预期：多次读取应返回相同的值")
    
    try:
        hub = connect_device()
        if hub is None:
            return False
        
        all_passed = True
        
        # 测试1：重复读取当前模式
        print("\n[测试1] 重复读取当前模式 10次...")
        mode_readings = []
        for i in range(10):
            mode = hub.get_flexconnect_mode()
            mode_readings.append(mode)
            time.sleep(0.05)
        
        if len(set(mode_readings)) == 1:
            print(f"✓ 所有读取一致: {mode_readings[0]}")
        else:
            print(f"✗ 读取不一致: {set(mode_readings)}")
            all_passed = False
        
        # 测试2：重复读取默认模式
        print("\n[测试2] 重复读取默认模式 10次...")
        default_readings = []
        for i in range(10):
            default_mode = hub.get_flexconnect_default_mode()
            default_readings.append(default_mode)
            time.sleep(0.05)
        
        if len(set(default_readings)) == 1:
            print(f"✓ 所有读取一致: {default_readings[0]}")
        else:
            print(f"✗ 读取不一致: {set(default_readings)}")
            all_passed = False
        
        # 测试3：重复读取掉电恢复状态
        print("\n[测试3] 重复读取掉电恢复状态 10次...")
        restore_readings = []
        for i in range(10):
            auto_restore = hub.get_auto_restore_status()
            restore_readings.append(auto_restore)
            time.sleep(0.05)
        
        if len(set(restore_readings)) == 1:
            print(f"✓ 所有读取一致: {restore_readings[0]}")
        else:
            print(f"✗ 读取不一致: {set(restore_readings)}")
            all_passed = False
        
        # 测试4：写入后立即读取验证
        print("\n[测试4] 写入后立即读取验证...")
        test_cases = [
            ("当前模式", lambda: hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2), 
             lambda: hub.get_flexconnect_mode(), FLEXCONNECT_MODE_UDISK2),
            ("默认模式", lambda: hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1), 
             lambda: hub.get_flexconnect_default_mode(), FLEXCONNECT_MODE_UDISK1),
            ("掉电恢复", lambda: hub.set_auto_restore(True), 
             lambda: hub.get_auto_restore_status(), 1),
        ]
        
        for name, set_func, get_func, expected in test_cases:
            print(f"\n  测试 {name}:")
            set_func()
            time.sleep(0.1)
            
            # 立即读取5次
            for i in range(5):
                value = get_func()
                if value == expected:
                    print(f"    读取 {i+1}: ✓ {value}")
                else:
                    print(f"    读取 {i+1}: ✗ 期望 {expected}, 实际 {value}")
                    all_passed = False
                time.sleep(0.05)
        
        hub.disconnect()
        
        if all_passed:
            print("\n✓✓✓ 测试场景 6.5 通过！")
            print("  结论：参数读取一致性良好，写入后立即可读")
            return True
        else:
            print("\n✗✗✗ 测试场景 6.5 失败！")
            print("  问题：参数读取存在不一致或延迟")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║            FlexConnect 边界条件和异常测试                         ║
║                                                                  ║
║  测试内容：                                                       ║
║    - 无效参数处理                                                 ║
║    - 快速连续模式切换                                             ║
║    - 重复设置相同值                                               ║
║    - 多次断电重启持久化                                           ║
║    - 参数读取一致性                                               ║
║                                                                  ║
║  本测试需要：                                                     ║
║    - 场景 6.4 需要多次断电重启（5次）                             ║
║    - 其他场景可以自动完成                                         ║
║    - 约20-30分钟的测试时间                                         ║
║                                                                  ║
║  ⚠️  注意：场景 6.4 需要物理断电重启操作                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # 询问用户是否运行场景 6.4
    print("\n场景 6.4 需要 5 次断电重启，比较耗时。")
    run_6_4 = input("是否运行场景 6.4？(y/n，默认 n): ").strip().lower()
    
    input("\n按回车键开始测试...")
    
    results = {}
    
    try:
        # 测试场景 6.1
        print_separator()
        results["6.1"] = test_scenario_6_1()
        
        if results["6.1"]:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        
        # 测试场景 6.2
        print_separator()
        results["6.2"] = test_scenario_6_2()
        
        if results["6.2"]:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        
        # 测试场景 6.3
        print_separator()
        results["6.3"] = test_scenario_6_3()
        
        if results["6.3"]:
            print("\n" + "▼" * 35)
            input("\n按回车键继续下一个测试场景...")
        
        # 测试场景 6.4（可选）
        if run_6_4 == 'y':
            print_separator()
            results["6.4"] = test_scenario_6_4()
            
            if results["6.4"]:
                print("\n" + "▼" * 35)
                input("\n按回车键继续下一个测试场景...")
        else:
            results["6.4"] = None  # 跳过
            print("\n[跳过] 场景 6.4")
        
        # 测试场景 6.5
        print_separator()
        results["6.5"] = test_scenario_6_5()
        
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
            print("  ✓ 设备能正确处理无效参数")
            print("  ✓ 快速连续切换稳定可靠")
            print("  ✓ 重复设置处理正常")
            if results.get("6.4"):
                print("  ✓ 多次重启持久化可靠")
            print("  ✓ 参数读取一致性良好")
            print("\n这验证了：")
            print("  1. 输入验证逻辑完善")
            print("  2. 状态机稳定性良好")
            print("  3. Flash 读写可靠")
            print("  4. 协议通信稳定")
        elif failed > 0:
            print("\n✗✗✗ 部分测试失败！")
            print("\n需要检查：")
            if not results.get("6.1"):
                print("  ✗ 输入验证逻辑")
            if not results.get("6.2"):
                print("  ✗ 快速切换处理能力")
            if not results.get("6.3"):
                print("  ✗ 重复操作处理")
            if results.get("6.4") is False:
                print("  ✗ Flash 持久化可靠性")
            if not results.get("6.5"):
                print("  ✗ 参数读取一致性")
        
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


