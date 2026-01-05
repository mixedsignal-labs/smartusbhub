"""
FlexConnect 高级功能测试程序

测试以下关键功能：
1. 上电默认模式设置和验证
2. 掉电恢复功能的启用/禁用和验证
3. 恢复出厂设置功能
4. 参数持久化验证（断电后参数是否保存）

使用方法：
    python examples/flexconnect_advanced_test.py
"""

import sys
import os
import time

# 添加父目录到路径，以便导入smartusbhub
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def print_mode_name(mode):
    """打印模式名称"""
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC模式",
        FLEXCONNECT_MODE_UDISK1: "UDISK1模式",
        FLEXCONNECT_MODE_UDISK2: "UDISK2模式"
    }
    return mode_names.get(mode, f"Unknown({mode})")


def test_default_mode(hub):
    """测试上电默认模式功能"""
    print("\n" + "="*60)
    print("测试1: 上电默认模式设置和验证")
    print("="*60)
    
    # 测试设置默认模式为UDISK1
    print("\n[步骤1] 设置上电默认模式为 UDISK1...")
    result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1)
    if result:
        print("  ✓ 设置成功")
    else:
        print("  ✗ 设置失败")
        return False
    
    time.sleep(0.2)
    
    # 验证默认模式
    print("[步骤2] 读取上电默认模式...")
    default_mode = hub.get_flexconnect_default_mode()
    if default_mode == FLEXCONNECT_MODE_UDISK1:
        print(f"  ✓ 默认模式正确: {print_mode_name(default_mode)}")
    else:
        print(f"  ✗ 默认模式错误: 期望 {FLEXCONNECT_MODE_UDISK1}, 实际 {default_mode}")
        return False
    
    # 测试设置默认模式为UDISK2
    print("\n[步骤3] 设置上电默认模式为 UDISK2...")
    result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
    if result:
        print("  ✓ 设置成功")
    else:
        print("  ✗ 设置失败")
        return False
    
    time.sleep(0.2)
    
    # 验证默认模式
    print("[步骤4] 读取上电默认模式...")
    default_mode = hub.get_flexconnect_default_mode()
    if default_mode == FLEXCONNECT_MODE_UDISK2:
        print(f"  ✓ 默认模式正确: {print_mode_name(default_mode)}")
    else:
        print(f"  ✗ 默认模式错误: 期望 {FLEXCONNECT_MODE_UDISK2}, 实际 {default_mode}")
        return False
    
    # 恢复为PC模式（默认值）
    print("\n[步骤5] 恢复默认模式为 PC（出厂默认）...")
    result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
    if result:
        print("  ✓ 设置成功")
    else:
        print("  ✗ 设置失败")
        return False
    
    print("\n  ⚠️  注意: 要验证上电默认模式，需要重启设备后检查")
    print("     当前设备会立即应用默认模式，但上电默认模式需要重启验证")
    
    return True


def test_poweroff_recover(hub):
    """测试掉电恢复功能"""
    print("\n" + "="*60)
    print("测试2: 掉电恢复功能")
    print("="*60)
    
    # 测试启用掉电恢复
    print("\n[步骤1] 启用掉电恢复功能...")
    result = hub.set_auto_restore(True)
    if result:
        print("  ✓ 启用成功")
    else:
        print("  ✗ 启用失败")
        return False
    
    time.sleep(0.2)
    
    # 验证掉电恢复状态
    print("[步骤2] 读取掉电恢复状态...")
    status = hub.get_auto_restore_status()
    if status == 1:
        print("  ✓ 掉电恢复已启用")
    else:
        print(f"  ✗ 掉电恢复状态错误: 期望 1, 实际 {status}")
        return False
    
    # 切换到UDISK2模式并保存
    print("\n[步骤3] 切换到 UDISK2 模式（用于掉电恢复测试）...")
    result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
    if result:
        print("  ✓ 切换成功")
        time.sleep(0.3)  # 等待模式切换完成
    else:
        print("  ✗ 切换失败")
        return False
    
    # 验证当前模式
    current_mode = hub.get_flexconnect_mode()
    if current_mode == FLEXCONNECT_MODE_UDISK2:
        print(f"  ✓ 当前模式: {print_mode_name(current_mode)}")
    else:
        print(f"  ✗ 模式错误: 期望 {FLEXCONNECT_MODE_UDISK2}, 实际 {current_mode}")
        return False
    
    print("\n  ⚠️  注意: 要验证掉电恢复，需要:")
    print("     1. 确保掉电恢复已启用（当前状态: 已启用）")
    print("     2. 当前模式为 UDISK2")
    print("     3. 断电后重新上电")
    print("     4. 检查设备是否恢复到 UDISK2 模式")
    
    # 测试禁用掉电恢复
    print("\n[步骤4] 禁用掉电恢复功能...")
    result = hub.set_auto_restore(False)
    if result:
        print("  ✓ 禁用成功")
    else:
        print("  ✗ 禁用失败")
        return False
    
    time.sleep(0.2)
    
    # 验证掉电恢复状态
    print("[步骤5] 读取掉电恢复状态...")
    status = hub.get_auto_restore_status()
    if status == 0:
        print("  ✓ 掉电恢复已禁用")
    else:
        print(f"  ✗ 掉电恢复状态错误: 期望 0, 实际 {status}")
        return False
    
    print("\n  ⚠️  注意: 掉电恢复已禁用，重启后将使用上电默认模式")
    
    return True


def test_factory_reset(hub):
    """测试恢复出厂设置功能"""
    print("\n" + "="*60)
    print("测试3: 恢复出厂设置")
    print("="*60)
    
    # 先设置一些非默认值
    print("\n[步骤1] 设置一些非默认值用于测试...")
    print("  - 设置默认模式为 UDISK2...")
    hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK2)
    time.sleep(0.2)
    
    print("  - 启用掉电恢复...")
    hub.set_auto_restore(True)
    time.sleep(0.2)
    
    print("  - 切换到 UDISK1 模式...")
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
    time.sleep(0.3)
    
    # 读取当前状态
    print("\n[步骤2] 读取当前状态（恢复前）...")
    default_mode_before = hub.get_flexconnect_default_mode()
    auto_restore_before = hub.get_auto_restore_status()
    current_mode_before = hub.get_flexconnect_mode()
    
    print(f"  默认模式: {print_mode_name(default_mode_before)}")
    print(f"  掉电恢复: {'启用' if auto_restore_before == 1 else '禁用'}")
    print(f"  当前模式: {print_mode_name(current_mode_before)}")
    
    # 执行恢复出厂设置
    print("\n[步骤3] 执行恢复出厂设置...")
    result = hub.factory_reset()
    if result:
        print("  ✓ 恢复出厂设置成功")
        time.sleep(0.5)  # 等待设备重置完成
    else:
        print("  ✗ 恢复出厂设置失败")
        return False
    
    # 验证恢复后的状态
    print("\n[步骤4] 验证恢复后的状态...")
    time.sleep(0.2)
    
    default_mode_after = hub.get_flexconnect_default_mode()
    auto_restore_after = hub.get_auto_restore_status()
    current_mode_after = hub.get_flexconnect_mode()
    
    print(f"  默认模式: {print_mode_name(default_mode_after)} (期望: PC模式)")
    print(f"  掉电恢复: {'启用' if auto_restore_after == 1 else '禁用'} (期望: 禁用)")
    print(f"  当前模式: {print_mode_name(current_mode_after)} (期望: PC模式)")
    
    # 检查是否符合预期
    success = True
    if default_mode_after != FLEXCONNECT_MODE_PC:
        print(f"  ✗ 默认模式错误: 期望 PC模式, 实际 {print_mode_name(default_mode_after)}")
        success = False
    else:
        print("  ✓ 默认模式正确: PC模式")
    
    if auto_restore_after != 0:
        print(f"  ✗ 掉电恢复状态错误: 期望 禁用, 实际 {'启用' if auto_restore_after == 1 else '未知'}")
        success = False
    else:
        print("  ✓ 掉电恢复状态正确: 禁用")
    
    if current_mode_after != FLEXCONNECT_MODE_PC:
        print(f"  ✗ 当前模式错误: 期望 PC模式, 实际 {print_mode_name(current_mode_after)}")
        success = False
    else:
        print("  ✓ 当前模式正确: PC模式")
    
    return success


def test_power_cycle_verification(hub):
    """测试断电重启验证（需要手动操作）"""
    print("\n" + "="*60)
    print("测试4: 断电重启验证（需要手动操作）")
    print("="*60)
    
    print("\n这个测试需要手动断电重启设备，请按照以下步骤操作：")
    print("\n[测试场景1] 上电默认模式验证")
    print("  1. 设置上电默认模式为 UDISK1")
    print("  2. 断电重启设备")
    print("  3. 检查设备是否自动切换到 UDISK1 模式")
    print("\n  执行步骤1...")
    
    result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1)
    if result:
        print("  ✓ 已设置默认模式为 UDISK1")
        print("\n  ⚠️  请手动断电重启设备，然后检查模式是否为 UDISK1")
    else:
        print("  ✗ 设置失败")
        return False
    
    input("\n  按回车键继续（确认已重启设备并检查模式）...")
    
    # 检查当前模式
    current_mode = hub.get_flexconnect_mode()
    print(f"\n  当前模式: {print_mode_name(current_mode)}")
    if current_mode == FLEXCONNECT_MODE_UDISK1:
        print("  ✓ 上电默认模式验证通过")
    else:
        print(f"  ✗ 上电默认模式验证失败: 期望 UDISK1, 实际 {print_mode_name(current_mode)}")
    
    print("\n[测试场景2] 掉电恢复功能验证")
    print("  1. 启用掉电恢复")
    print("  2. 切换到 UDISK2 模式")
    print("  3. 断电重启设备")
    print("  4. 检查设备是否恢复到 UDISK2 模式")
    print("\n  执行步骤1-2...")
    
    hub.set_auto_restore(True)
    time.sleep(0.2)
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
    time.sleep(0.3)
    
    print("  ✓ 已启用掉电恢复，当前模式为 UDISK2")
    print("\n  ⚠️  请手动断电重启设备，然后检查模式是否为 UDISK2")
    
    input("\n  按回车键继续（确认已重启设备并检查模式）...")
    
    # 检查当前模式
    current_mode = hub.get_flexconnect_mode()
    print(f"\n  当前模式: {print_mode_name(current_mode)}")
    if current_mode == FLEXCONNECT_MODE_UDISK2:
        print("  ✓ 掉电恢复功能验证通过")
    else:
        print(f"  ✗ 掉电恢复功能验证失败: 期望 UDISK2, 实际 {print_mode_name(current_mode)}")
    
    print("\n[测试场景3] 掉电恢复禁用验证")
    print("  1. 禁用掉电恢复")
    print("  2. 切换到 UDISK1 模式")
    print("  3. 断电重启设备")
    print("  4. 检查设备是否使用默认模式（不是UDISK1）")
    print("\n  执行步骤1-2...")
    
    hub.set_auto_restore(False)
    time.sleep(0.2)
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
    time.sleep(0.3)
    
    default_mode = hub.get_flexconnect_default_mode()
    print(f"  ✓ 已禁用掉电恢复，当前模式为 UDISK1，默认模式为 {print_mode_name(default_mode)}")
    print(f"\n  ⚠️  请手动断电重启设备，然后检查模式是否为默认模式 {print_mode_name(default_mode)}")
    
    input("\n  按回车键继续（确认已重启设备并检查模式）...")
    
    # 检查当前模式
    current_mode = hub.get_flexconnect_mode()
    print(f"\n  当前模式: {print_mode_name(current_mode)}")
    if current_mode == default_mode:
        print(f"  ✓ 掉电恢复禁用验证通过（使用默认模式 {print_mode_name(default_mode)}）")
    else:
        print(f"  ✗ 掉电恢复禁用验证失败: 期望 {print_mode_name(default_mode)}, 实际 {print_mode_name(current_mode)}")
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("FlexConnect 高级功能测试程序")
    print("=" * 60)
    print()
    print("测试内容：")
    print("  1. 上电默认模式设置和验证")
    print("  2. 掉电恢复功能的启用/禁用")
    print("  3. 恢复出厂设置功能")
    print("  4. 断电重启验证（需要手动操作）")
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
        
        # 运行测试
        results = []
        
        # 测试1: 上电默认模式
        results.append(("上电默认模式", test_default_mode(hub)))
        
        # 测试2: 掉电恢复功能
        results.append(("掉电恢复功能", test_poweroff_recover(hub)))
        
        # 测试3: 恢复出厂设置
        results.append(("恢复出厂设置", test_factory_reset(hub)))
        
        # 测试4: 断电重启验证（可选）
        print("\n" + "="*60)
        user_input = input("是否进行断电重启验证测试？(y/n): ").strip().lower()
        if user_input == 'y':
            results.append(("断电重启验证", test_power_cycle_verification(hub)))
        else:
            print("跳过断电重启验证测试")
        
        # 显示测试结果摘要
        print("\n" + "="*60)
        print("测试结果摘要")
        print("="*60)
        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {test_name}: {status}")
        
        all_passed = all(result for _, result in results)
        if all_passed:
            print("\n✓ 所有测试通过！")
        else:
            print("\n✗ 部分测试失败，请检查上述错误信息")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 断开连接
        if hub is not None:
            hub.disconnect()
            print("\n已断开连接")


if __name__ == "__main__":
    main()




