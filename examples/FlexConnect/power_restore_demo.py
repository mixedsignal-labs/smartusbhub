"""
Demo 02: 掉电恢复功能演示

演示内容：
1. 启用/禁用掉电恢复
2. 设置上电默认模式
3. 验证掉电恢复逻辑
4. 理解掉电恢复优先级

适用场景：
- 需要断电后自动恢复状态
- 自动化测试环境
- 无人值守场景
"""

import sys
import time

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    else:
        print("=" * 60)


def get_current_state(hub):
    """获取并打印当前状态"""
    mode_names = {
        FLEXCONNECT_MODE_PC: "PC 模式",
        FLEXCONNECT_MODE_UDISK1: "U 盘1 模式",
        FLEXCONNECT_MODE_UDISK2: "U 盘2 模式"
    }
    
    current_mode = hub.get_flexconnect_mode()
    default_mode = hub.get_flexconnect_default_mode()
    auto_restore = hub.get_auto_restore_status()
    
    print("\n当前状态:")
    print(f"  当前模式: {mode_names.get(current_mode, '未知')} (0x{current_mode:02X})")
    print(f"  默认模式: {mode_names.get(default_mode, '未知')} (0x{default_mode:02X})")
    print(f"  掉电恢复: {'已启用' if auto_restore == 1 else '已禁用'}")
    
    return current_mode, default_mode, auto_restore


def demo_enable_auto_restore(hub):
    """演示：启用掉电恢复"""
    print_separator("演示1: 启用掉电恢复")
    
    print("\n掉电恢复启用后：")
    print("  - 断电重启会恢复到上次的工作模式")
    print("  - 适用于需要保持状态的场景")
    
    # 启用掉电恢复
    print("\n[操作] 启用掉电恢复...")
    result = hub.set_auto_restore(True)
    if not result:
        print("✗ 启用失败")
        return False
    
    time.sleep(0.2)
    
    # 验证
    status = hub.get_auto_restore_status()
    if status == 1:
        print("✓ 掉电恢复已启用")
    else:
        print("✗ 验证失败")
        return False
    
    # 切换到 UDISK1 模式
    print("\n[操作] 切换到 U 盘1 模式...")
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
    time.sleep(0.3)
    
    get_current_state(hub)
    
    print("\n说明:")
    print("  现在如果断电重启，设备会自动恢复到 U 盘1 模式")
    print("  因为掉电恢复已启用，且当前模式为 U 盘1")
    
    return True


def demo_disable_auto_restore(hub):
    """演示：禁用掉电恢复"""
    print_separator("演示2: 禁用掉电恢复 + 设置默认模式")
    
    print("\n掉电恢复禁用后：")
    print("  - 断电重启会使用上电默认模式")
    print("  - 适用于需要固定启动模式的场景")
    
    # 设置默认模式为 PC
    print("\n[操作] 设置上电默认模式为 PC...")
    result = hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
    if not result:
        print("✗ 设置失败")
        return False
    
    time.sleep(0.2)
    
    # 验证默认模式
    default_mode = hub.get_flexconnect_default_mode()
    if default_mode == FLEXCONNECT_MODE_PC:
        print("✓ 默认模式设置为 PC")
    else:
        print("✗ 验证失败")
        return False
    
    # 禁用掉电恢复
    print("\n[操作] 禁用掉电恢复...")
    result = hub.set_auto_restore(False)
    if not result:
        print("✗ 禁用失败")
        return False
    
    time.sleep(0.2)
    
    # 验证
    status = hub.get_auto_restore_status()
    if status == 0:
        print("✓ 掉电恢复已禁用")
    else:
        print("✗ 验证失败")
        return False
    
    # 切换到 UDISK2 模式
    print("\n[操作] 切换到 U 盘2 模式...")
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
    time.sleep(0.3)
    
    get_current_state(hub)
    
    print("\n说明:")
    print("  现在如果断电重启，设备会恢复到 PC 模式（默认模式）")
    print("  而不是当前的 U 盘2 模式，因为掉电恢复已禁用")
    
    return True


def demo_priority_logic(hub):
    """演示：掉电恢复优先级"""
    print_separator("演示3: 掉电恢复优先级")
    
    print("\n掉电恢复优先级（从高到低）：")
    print("  1. [最高] 默认电源标志（特殊场景，需要额外设置）")
    print("  2. [中等] 掉电恢复（保存上次状态）")
    print("  3. [最低] 上电默认模式（兜底机制）")
    
    print("\n实际应用:")
    print("  - 如果启用掉电恢复 → 使用上次的模式")
    print("  - 如果禁用掉电恢复 → 使用默认模式")
    
    # 测试场景1: 禁用掉电恢复，应该使用默认模式
    print("\n[场景1] 禁用掉电恢复 + 设置默认为 UDISK1")
    
    hub.set_auto_restore(False)
    time.sleep(0.2)
    
    hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_UDISK1)
    time.sleep(0.2)
    
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
    time.sleep(0.3)
    
    get_current_state(hub)
    
    print("\n  → 断电重启后会恢复到: U 盘1 模式（默认模式）")
    print("  → 而不是当前的 U 盘2 模式")
    
    # 测试场景2: 启用掉电恢复，应该使用上次模式
    print("\n[场景2] 启用掉电恢复")
    
    hub.set_auto_restore(True)
    time.sleep(0.2)
    
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
    time.sleep(0.3)
    
    get_current_state(hub)
    
    print("\n  → 断电重启后会恢复到: PC 模式（上次模式）")
    print("  → 忽略默认模式（U 盘1），因为掉电恢复优先级更高")
    
    return True


def main():
    print_separator("FlexConnect 掉电恢复功能演示")
    
    # 连接设备
    print("\n正在连接设备...")
    hub = SmartUSBHub.scan_and_connect()
    
    if hub is None:
        print("✗ 未找到设备")
        return 1
    
    print("✓ 设备已连接")
    
    try:
        # 显示初始状态
        print_separator("初始状态")
        get_current_state(hub)
        
        # 演示1: 启用掉电恢复
        if not demo_enable_auto_restore(hub):
            return 1
        
        time.sleep(1)
        
        # 演示2: 禁用掉电恢复
        if not demo_disable_auto_restore(hub):
            return 1
        
        time.sleep(1)
        
        # 演示3: 优先级逻辑
        if not demo_priority_logic(hub):
            return 1
        
        # 恢复默认状态
        print_separator("恢复默认状态")
        print("\n[清理] 恢复到默认配置...")
        
        hub.set_auto_restore(False)
        hub.set_flexconnect_default_mode(FLEXCONNECT_MODE_PC)
        hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        time.sleep(0.3)
        
        print("✓ 已恢复到默认状态")
        
        # 完成
        print_separator("演示完成")
        
        print("\n关键要点:")
        print("  1. 掉电恢复启用后，断电重启会恢复上次模式")
        print("  2. 掉电恢复禁用后，断电重启会使用默认模式")
        print("  3. 掉电恢复优先级 > 上电默认模式")
        print("  4. 模式切换后等待至少 3 秒再断电（Flash 写入延迟）")
        
        print("\n实际应用建议:")
        print("  - 开发调试: 禁用掉电恢复，固定默认为 PC 模式")
        print("  - 自动化测试: 启用掉电恢复，保持测试状态")
        print("  - 生产环境: 根据需求选择合适的配置")
        
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        hub.disconnect()
        print("\n已断开连接")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

