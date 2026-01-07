"""
测试场景 2.4：掉电恢复状态持久化

测试步骤：
1. 启用掉电恢复，切换到 UDISK1
2. 多次断电重启（至少 3 次），每次都应该恢复到 UDISK1
3. 切换到 UDISK2，断电重启，应该恢复到 UDISK2
4. 验证掉电恢复的参数持久化是否正确

预期结果：
- 启用掉电恢复后，无论重启多少次，都能正确恢复到上次的模式
- 模式切换后，新模式也能正确持久化
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
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)


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


def verify_mode(hub, expected_mode, mode_names):
    """验证当前模式"""
    current_mode = hub.get_flexconnect_mode()
    print(f"\n当前模式: {current_mode} ({mode_names.get(current_mode, '未知')})")
    
    if current_mode == expected_mode:
        print(f"✓ 模式正确: {mode_names.get(expected_mode, '未知')}")
        return True
    else:
        print(f"✗ 模式错误: 期望 {mode_names.get(expected_mode, '未知')} ({expected_mode}), 实际 {mode_names.get(current_mode, '未知')} ({current_mode})")
        return False


def main():
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC",
        FLEXCONNECT_MODE_UDISK1: "UDISK1",
        FLEXCONNECT_MODE_UDISK2: "UDISK2"
    }
    
    print_separator("测试场景 2.4：掉电恢复状态持久化")
    
    try:
        # ========== 阶段1：启用掉电恢复并切换到 UDISK1 ==========
        print_separator("阶段1：启用掉电恢复并切换到 UDISK1")
        
        hub = connect_device()
        if hub is None:
            return
        
        print("\n[步骤1.1] 启用掉电恢复...")
        result = hub.set_auto_restore(True)
        if not result:
            print("✗ 启用掉电恢复失败")
            return
        print("✓ 启用掉电恢复成功")
        time.sleep(0.2)
        
        # 验证掉电恢复状态
        auto_restore = hub.get_auto_restore_status()
        if auto_restore != 1:
            print(f"✗ 掉电恢复状态错误: {auto_restore} (期望: 1)")
            return
        print(f"✓ 掉电恢复状态: {auto_restore} (已启用)")
        
        print("\n[步骤1.2] 切换到 UDISK1 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        if not result:
            print("✗ 切换模式失败")
            return
        print("✓ 切换到 UDISK1 成功")
        time.sleep(0.3)
        
        # 验证当前模式
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names):
            return
        
        hub.disconnect()
        print("\n✓ 阶段1 完成")
        print("\n" + "⚠" * 30)
        print("⚠️  请断电重启设备（第1次）")
        print("⚠️  操作：拔掉电源 → 等待5秒 → 重新上电")
        print("⚠" * 30)
        input("\n按回车键继续（确认已重启设备）...")
        
        # ========== 阶段2：第1次重启验证 ==========
        print_separator("阶段2：第1次重启验证 - 应该恢复到 UDISK1")
        
        hub = connect_device()
        if hub is None:
            return
        
        # 验证掉电恢复状态是否保持
        auto_restore = hub.get_auto_restore_status()
        print(f"\n掉电恢复状态: {auto_restore} (期望: 1)")
        if auto_restore != 1:
            print(f"✗ 掉电恢复状态丢失！")
            return
        
        # 验证模式
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names):
            print("\n✗ 测试失败：第1次重启后模式不正确")
            return
        
        print("\n✓ 第1次重启验证通过")
        hub.disconnect()
        
        print("\n" + "⚠" * 30)
        print("⚠️  请断电重启设备（第2次）")
        print("⚠" * 30)
        input("\n按回车键继续（确认已重启设备）...")
        
        # ========== 阶段3：第2次重启验证 ==========
        print_separator("阶段3：第2次重启验证 - 应该恢复到 UDISK1")
        
        hub = connect_device()
        if hub is None:
            return
        
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names):
            print("\n✗ 测试失败：第2次重启后模式不正确")
            return
        
        print("\n✓ 第2次重启验证通过")
        hub.disconnect()
        
        print("\n" + "⚠" * 30)
        print("⚠️  请断电重启设备（第3次）")
        print("⚠" * 30)
        input("\n按回车键继续（确认已重启设备）...")
        
        # ========== 阶段4：第3次重启验证 ==========
        print_separator("阶段4：第3次重启验证 - 应该恢复到 UDISK1")
        
        hub = connect_device()
        if hub is None:
            return
        
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK1, mode_names):
            print("\n✗ 测试失败：第3次重启后模式不正确")
            return
        
        print("\n✓ 第3次重启验证通过")
        print("✓ UDISK1 模式持久化测试通过（3次重启）")
        
        # ========== 阶段5：切换到 UDISK2 并验证 ==========
        print_separator("阶段5：切换到 UDISK2 并验证持久化")
        
        print("\n[步骤5.1] 切换到 UDISK2 模式...")
        result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
        if not result:
            print("✗ 切换模式失败")
            return
        print("✓ 切换到 UDISK2 成功")
        time.sleep(0.3)
        
        # 验证当前模式
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK2, mode_names):
            return
        
        hub.disconnect()
        
        print("\n" + "⚠" * 30)
        print("⚠️  请断电重启设备（第4次）")
        print("⚠️  验证是否能恢复到 UDISK2")
        print("⚠" * 30)
        input("\n按回车键继续（确认已重启设备）...")
        
        # ========== 阶段6：验证 UDISK2 持久化 ==========
        print_separator("阶段6：验证 UDISK2 持久化")
        
        hub = connect_device()
        if hub is None:
            return
        
        if not verify_mode(hub, FLEXCONNECT_MODE_UDISK2, mode_names):
            print("\n✗ 测试失败：切换到 UDISK2 后重启，模式不正确")
            return
        
        print("\n✓ UDISK2 模式持久化验证通过")
        
        # ========== 最终结果 ==========
        print_separator("测试结果")
        
        print("\n✓✓✓ 测试场景 2.4 全部通过！✓✓✓")
        print("\n测试摘要：")
        print("  1. ✓ 启用掉电恢复功能")
        print("  2. ✓ 切换到 UDISK1 模式")
        print("  3. ✓ 第1次重启：恢复到 UDISK1")
        print("  4. ✓ 第2次重启：恢复到 UDISK1")
        print("  5. ✓ 第3次重启：恢复到 UDISK1")
        print("  6. ✓ 切换到 UDISK2 模式")
        print("  7. ✓ 第4次重启：恢复到 UDISK2")
        print("\n结论：")
        print("  掉电恢复功能正常工作！")
        print("  参数持久化功能正常工作！")
        print("  Flash 读写功能正常工作！")
        
        # 清理：恢复默认状态
        print("\n" + "=" * 60)
        print("清理：恢复到默认状态")
        print("=" * 60)
        
        print("\n[清理] 切换回 PC 模式...")
        hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        time.sleep(0.3)
        print("✓ 已切换回 PC 模式")
        
        hub.disconnect()
        print("\n已断开连接")
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pass


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          FlexConnect 掉电恢复状态持久化测试                  ║
║                                                            ║
║  本测试需要多次手动断电重启设备（共4次）                       ║
║  请准备好：                                                 ║
║    - 可控电源开关（方便断电重启）                            ║
║    - 约5-10分钟的测试时间                                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
    
    input("按回车键开始测试...")
    main()



