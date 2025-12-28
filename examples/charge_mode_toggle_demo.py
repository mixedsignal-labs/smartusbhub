#!/usr/bin/env python3
"""
定时切换充电模式Demo

每4秒在快充和慢充模式之间切换一次。
按 Ctrl+C 退出程序。
"""

import sys
import os
import time
import signal
import logging

# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# 自定义日志处理器，用于捕获 "No ACK" 错误
class NoACKCounter(logging.Handler):
    def __init__(self):
        super().__init__()
        self.no_ack_errors = {
            'set_channel_slow_charge': 0,
            'set_channel_fast_charge': 0,
            'get_channel_charge_mode': 0,
            'get_channel_power_status': 0,
            'other': 0
        }
    
    def emit(self, record):
        if 'No ACK' in record.getMessage():
            msg = record.getMessage()
            if 'set_channel_slow_charge' in msg:
                self.no_ack_errors['set_channel_slow_charge'] += 1
            elif 'set_channel_fast_charge' in msg:
                self.no_ack_errors['set_channel_fast_charge'] += 1
            elif 'get_channel_charge_mode' in msg:
                self.no_ack_errors['get_channel_charge_mode'] += 1
            elif 'get_channel_power_status' in msg:
                self.no_ack_errors['get_channel_power_status'] += 1
            else:
                self.no_ack_errors['other'] += 1

# 全局变量，用于信号处理
hub = None
running = True

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global running
    print("\n\n收到退出信号，正在停止...")
    running = False
    if hub:
        try:
            hub.disconnect()
        except:
            pass
    sys.exit(0)

def main():
    global hub, running
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 设置日志处理器来捕获 No ACK 错误
    no_ack_counter = NoACKCounter()
    no_ack_counter.setLevel(logging.ERROR)  # 只捕获 ERROR 级别的日志
    logger = logging.getLogger('smartusbhub')
    # 确保 logger 的级别足够低，以便 ERROR 级别的日志能够被处理
    if not logger.handlers:  # 避免重复添加处理器
        logger.addHandler(no_ack_counter)
    logger.setLevel(logging.ERROR)  # 设置 logger 级别为 ERROR
    
    print("=" * 60)
    print("定时切换充电模式Demo")
    print("=" * 60)
    print("每4秒在快充和慢充模式之间切换一次")
    print("按 Ctrl+C 退出程序")
    print("=" * 60)
    print()
    
    # 扫描并连接设备
    print("正在扫描设备...")
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("错误: 未找到SmartUSBHub设备")
        return
    
    print(f"已连接到设备: {hub.name}")
    print(f"设备地址: {hub.device_address:#04x}")
    print()
    
    # 获取设备信息
    device_info = hub.get_device_info()
    if device_info:
        print(f"硬件版本: V1.{device_info.get('hardware_version', 'N/A')}")
        print(f"固件版本: V1.{device_info.get('firmware_version', 'N/A')}")
        print()
    
    # 初始化：设置为快充模式
    current_mode = "FAST_CHARGE"
    print(f"[初始状态] 设置为 {current_mode} 模式")
    hub.set_channel_fast_charge(1, disconnect_before_switch=False)
    time.sleep(0.5)  # 等待设置完成
    
    # 统计信息
    cycle_count = 0
    success_count = 0
    error_count = 0
    fast_to_slow_errors = 0
    slow_to_fast_errors = 0
    
    try:
        while running:
            cycle_count += 1
            print(f"\n[循环 #{cycle_count}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 切换模式
            if current_mode == "FAST_CHARGE":
                print(f"-> 切换到 SLOW_CHARGE (慢充模式)")
                success = hub.set_channel_slow_charge(1, disconnect_before_switch=False)
                if success:
                    current_mode = "SLOW_CHARGE"
                    success_count += 1
                else:
                    error_count += 1
                    fast_to_slow_errors += 1
                    print("警告: 切换到慢充模式失败")
            else:
                print(f"-> 切换到 FAST_CHARGE (快充模式)")
                success = hub.set_channel_fast_charge(1, disconnect_before_switch=False)
                if success:
                    current_mode = "FAST_CHARGE"
                    success_count += 1
                else:
                    error_count += 1
                    slow_to_fast_errors += 1
                    print("警告: 切换到快充模式失败")
            
            # 等待一小段时间，让MCU状态稳定
            time.sleep(0.1)
            
            # 验证当前模式
            charge_mode = hub.get_channel_charge_mode(1)
            if charge_mode:
                mode_value = charge_mode.get(1, 0)
                mode_str = "off" if mode_value == 0 else ("fast_charge" if mode_value == 1 else "slow_charge")
                expected_mode = 1 if current_mode == "FAST_CHARGE" else 2
                if mode_value != expected_mode:
                    print(f"⚠️  状态不匹配: 期望 {current_mode} ({expected_mode}), 实际 {mode_str} ({mode_value})")
                    # 状态不匹配也算作错误
                    error_count += 1
                    if current_mode == "SLOW_CHARGE":
                        fast_to_slow_errors += 1
                    else:
                        slow_to_fast_errors += 1
                else:
                    print(f"[当前状态] 通道1: {mode_str} ({mode_value})")
            else:
                print("⚠️  无法获取充电模式状态")
                error_count += 1
            
            # 显示统计信息
            success_rate = (success_count / cycle_count * 100) if cycle_count > 0 else 0
            total_no_ack = sum(no_ack_counter.no_ack_errors.values())
            print(f"[统计] 总循环: {cycle_count}, 成功: {success_count}, 失败: {error_count}, 成功率: {success_rate:.1f}%")
            if fast_to_slow_errors > 0 or slow_to_fast_errors > 0:
                print(f"      快充→慢充失败: {fast_to_slow_errors}, 慢充→快充失败: {slow_to_fast_errors}")
            if total_no_ack > 0:
                print(f"      No ACK 错误: 总计 {total_no_ack} 次")
                if no_ack_counter.no_ack_errors['set_channel_slow_charge'] > 0:
                    print(f"        - set_channel_slow_charge: {no_ack_counter.no_ack_errors['set_channel_slow_charge']} 次")
                if no_ack_counter.no_ack_errors['set_channel_fast_charge'] > 0:
                    print(f"        - set_channel_fast_charge: {no_ack_counter.no_ack_errors['set_channel_fast_charge']} 次")
                if no_ack_counter.no_ack_errors['get_channel_charge_mode'] > 0:
                    print(f"        - get_channel_charge_mode: {no_ack_counter.no_ack_errors['get_channel_charge_mode']} 次")
                if no_ack_counter.no_ack_errors['get_channel_power_status'] > 0:
                    print(f"        - get_channel_power_status: {no_ack_counter.no_ack_errors['get_channel_power_status']} 次")
                if no_ack_counter.no_ack_errors['other'] > 0:
                    print(f"        - 其他命令: {no_ack_counter.no_ack_errors['other']} 次")
            
            # 等待4秒
            print(f"等待4秒后切换...")
            for i in range(4, 0, -1):
                if not running:
                    break
                print(f"  {i}...", end='\r', flush=True)
                time.sleep(1)
            print("     ", end='\r')  # 清除倒计时
            
    except KeyboardInterrupt:
        print("\n\n收到键盘中断，正在退出...")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
    finally:
        # 显示最终统计
        print("\n" + "=" * 60)
        print("最终统计结果")
        print("=" * 60)
        print(f"总循环次数: {cycle_count}")
        print(f"成功次数: {success_count}")
        print(f"失败次数: {error_count}")
        if cycle_count > 0:
            success_rate = (success_count / cycle_count * 100)
            print(f"成功率: {success_rate:.2f}%")
        if fast_to_slow_errors > 0 or slow_to_fast_errors > 0:
            print(f"快充→慢充失败: {fast_to_slow_errors} 次")
            print(f"慢充→快充失败: {slow_to_fast_errors} 次")
        
        # No ACK 错误统计
        total_no_ack = sum(no_ack_counter.no_ack_errors.values())
        if total_no_ack > 0:
            print(f"\nNo ACK 错误统计 (总计: {total_no_ack} 次):")
            if no_ack_counter.no_ack_errors['set_channel_slow_charge'] > 0:
                print(f"  - set_channel_slow_charge: {no_ack_counter.no_ack_errors['set_channel_slow_charge']} 次")
            if no_ack_counter.no_ack_errors['set_channel_fast_charge'] > 0:
                print(f"  - set_channel_fast_charge: {no_ack_counter.no_ack_errors['set_channel_fast_charge']} 次")
            if no_ack_counter.no_ack_errors['get_channel_charge_mode'] > 0:
                print(f"  - get_channel_charge_mode: {no_ack_counter.no_ack_errors['get_channel_charge_mode']} 次")
            if no_ack_counter.no_ack_errors['get_channel_power_status'] > 0:
                print(f"  - get_channel_power_status: {no_ack_counter.no_ack_errors['get_channel_power_status']} 次")
            if no_ack_counter.no_ack_errors['other'] > 0:
                print(f"  - 其他命令: {no_ack_counter.no_ack_errors['other']} 次")
        else:
            print("\nNo ACK 错误: 0 次")
        
        print("=" * 60)
        
        if hub:
            try:
                print("\n断开连接...")
                hub.disconnect()
            except:
                pass
        print("程序已退出")

if __name__ == "__main__":
    main()

