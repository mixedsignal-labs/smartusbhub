"""
Diagnostic script: read and display all related FlexConnect parameters.

Used to troubleshoot power-off recovery behavior.
"""

import sys
import os
import time

# Add project root to sys.path (from examples/FlexConnect/ to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def main():
    hub = None
    try:
        print("=" * 60)
        print("FlexConnect 参数诊断 / FlexConnect Parameter Diagnostics")
        print("=" * 60)
        
        hub = SmartUSBHub.scan_and_connect()
        if hub is None:
            print("错误: 未找到设备 / Error: No device found")
            sys.exit(1)
        
        print(f"✓ 成功连接到设备 / Connected to device: {hub.port}\n")
        
        # 读取所有相关参数
        print("读取设备参数 / Reading device parameters ...")
        time.sleep(0.2)
        
        # 当前模式
        current_mode = hub.get_flexconnect_mode()
        print(f"\n1. 当前 FlexConnect 模式 / Current FlexConnect mode: {current_mode}")
        mode_names = {0: "PC", 1: "UDISK1", 2: "UDISK2", 3: "DISCONNECT"}
        print(f"   ({mode_names.get(current_mode, '未知')})")
        
        # 默认模式
        default_mode = hub.get_flexconnect_default_mode()
        print(f"\n2. 上电默认模式 / Power-on default mode: {default_mode}")
        print(f"   ({mode_names.get(default_mode, '未知')})")
        print(f"   [NOTE] 断电重启时，如果没有其他优先级更高的设置，将使用此模式 /")
        print(f"          On power cycle, this mode is used if no higher-priority setting is present.")
        
        # 掉电恢复状态
        auto_restore = hub.get_auto_restore_status()
        print(f"\n3. 掉电恢复功能 / Power-off recovery: {auto_restore}")
        print(f"   ({'启用 / Enabled' if auto_restore == 1 else '禁用 / Disabled'})")
        print(f"   [NOTE] 如果启用，断电重启时将恢复到上次的模式 /")
        print(f"          If enabled, device restores to last mode after power cycle.")
        
        # 设备信息
        info = hub.get_device_info()
        print(f"\n4. 设备信息 / Device information:")
        print(f"   产品类型 / Product type: {info.get('product_type')}")
        print(f"   硬件版本 / HW version: V1.{info.get('hardware_version')}")
        print(f"   固件版本 / FW version: V1.{info.get('firmware_version')}")
        print(f"   序列号 / Serial number: {info.get('serial_no')}")
        
        # 分析恢复优先级
        print("\n" + "=" * 60)
        print("断电重启恢复逻辑分析 / Power-cycle recovery logic analysis")
        print("=" * 60)
        print("\n优先级顺序（从高到低）/ Priority order (high to low):")
        print("  1. 默认电源标志 / Default power flag (channel_default_power_flag)")
        print("     → 目前无法通过 Python API 读取 / Not readable via Python API")
        print("\n  2. 掉电恢复 / Power-off recovery (poweroff_recover + channel_power_status)")
        print(f"     → poweroff_recover = {auto_restore}")
        if auto_restore == 1:
            print(f"     → 如果启用，将从 channel_power_status 恢复 /")
            print(f"        If enabled, restores from channel_power_status.")
            print(f"     → 注意：无法通过 Python API 读取 channel_power_status /")
            print(f"        Note: channel_power_status is not readable from Python.")
            print(f"     → 上次切换的模式会被保存到 channel_power_status /")
            print(f"        Last switched mode is saved into channel_power_status.")
        else:
            print(f"     → 已禁用，不会从 channel_power_status 恢复 /")
            print(f"        Disabled, will not restore from channel_power_status.")
        
        print(f"\n  3. 上电默认模式 / Power-on default mode (flexconnect_default_mode)")
        print(f"     → flexconnect_default_mode = {default_mode} ({mode_names.get(default_mode, '未知')})")
        print(f"     → 如果前两项都没有，使用此模式 /")
        print(f"        Used when previous two mechanisms are not applied.")
        
        # 预测断电重启行为
        print("\n" + "=" * 60)
        print("断电重启预测 / Power-cycle behavior prediction")
        print("=" * 60)
        
        if auto_restore == 1:
            print(f"\n由于掉电恢复已启用，断电重启时 / Since power-off recovery is enabled, on power cycle:")
            print(f"  → 将尝试从 channel_power_status 恢复到上次的模式 /")
            print(f"    Will try to restore last mode from channel_power_status.")
            print(f"  → 如果 channel_power_status 无效，则使用默认模式: {mode_names.get(default_mode, '未知')} /")
            print(f"    If channel_power_status is invalid, default mode will be used.")
        else:
            print(f"\n由于掉电恢复已禁用，断电重启时 / Since power-off recovery is disabled, on power cycle:")
            print(f"  → 将直接使用默认模式: {mode_names.get(default_mode, '未知')} /")
            print(f"    Device will directly use the default mode.")
            print(f"  → 如果实际恢复到其他模式，说明实际行为与当前配置不一致，请检查固件实现和参数设置 /")
            print(f"    If the restored mode is different, the behavior is inconsistent with current settings; please review firmware implementation and parameters.")
        
        print("\n" + "=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C) / User interrupted (Ctrl+C)")
    except Exception as e:
        print(f"\n错误 / Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hub is not None:
            try:
                hub.disconnect()
                print("\n已断开连接 / Disconnected")
            except:
                pass


if __name__ == "__main__":
    main()


