#!/usr/bin/env python3
"""
Periodic charge mode toggle demo.

Periodically toggles between fast charge and slow charge modes.
The toggle interval can be configured via command line arguments (default: 4 seconds).

Usage:
    python charge_mode_toggle_demo.py              # Use default 4 second interval
    python charge_mode_toggle_demo.py 2            # Toggle every 2 seconds
    python charge_mode_toggle_demo.py 10           # Toggle every 10 seconds

Press Ctrl+C to exit.
"""

import sys
import os
import time
import signal
import logging
import argparse

# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# Custom log handler to capture "No ACK" errors
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

# Global variables for signal handling
hub = None
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    global running
    print("\n\n收到退出信号，正在停止... / Received exit signal, stopping...")
    running = False
    if hub:
        try:
            hub.disconnect()
        except:
            pass
    sys.exit(0)

def main():
    global hub, running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Periodic charge mode toggle demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Use default 4 second interval
  %(prog)s 2            # Toggle every 2 seconds
  %(prog)s 10           # Toggle every 10 seconds
        """
    )
    parser.add_argument(
        'interval',
        type=float,
        nargs='?',
        default=4.0,
        help='Toggle interval in seconds (default: 4 seconds)'
    )
    args = parser.parse_args()
    
    toggle_interval = args.interval
    if toggle_interval <= 0:
        print("错误: 切换间隔必须大于0")
        sys.exit(1)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set up log handler to capture \"No ACK\" errors
    no_ack_counter = NoACKCounter()
    no_ack_counter.setLevel(logging.ERROR)  # 只捕获 ERROR 级别的日志
    logger = logging.getLogger('smartusbhub')
    # Ensure logger level is low enough so ERROR logs are handled
    if not logger.handlers:  # 避免重复添加处理器
        logger.addHandler(no_ack_counter)
    logger.setLevel(logging.ERROR)  # 设置 logger 级别为 ERROR
    
    print("=" * 60)
    print("Periodic charge mode toggle demo / 定时切换充电模式示例")
    print("=" * 60)
    print(f"Toggling between fast and slow charge every {toggle_interval} seconds / 每 {toggle_interval} 秒在快充和慢充之间切换一次")
    print("Press Ctrl+C to exit / 按 Ctrl+C 退出程序")
    print("=" * 60)
    print()
    
    # Scan and connect to device
    print("正在扫描设备... / Scanning for devices ...")
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("错误: 未找到 SmartUSBHub 设备 / Error: No SmartUSBHub device found")
        return
    
    print(f"已连接到设备 / Connected to device: {hub.name}")
    print(f"设备地址 / Device address: {hub.device_address:#04x}")
    print()
    
    # Get device information
    device_info = hub.get_device_info()
    print("Device info / 设备信息:", device_info)
    
    # Get and show hardware and firmware versions
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version / 硬件版本: V1.{hardware_version}" if hardware_version is not None else "Hardware Version / 硬件版本: Unknown")
    print(f"Firmware Version / 固件版本: V1.{firmware_version}" if firmware_version is not None else "Firmware Version / 固件版本: Unknown")
    print()
    
    # Initialize: set to fast charge mode
    current_mode = "FAST_CHARGE"
    print(f"[Initial] Set to {current_mode} mode / 设置为 {current_mode} 模式")
    hub.set_channel_fast_charge(1, disconnect_before_switch=False)
    time.sleep(0.5)  # 等待设置完成
    
    # Statistics
    cycle_count = 0
    success_count = 0
    error_count = 0
    fast_to_slow_errors = 0
    slow_to_fast_errors = 0
    
    try:
        while running:
            cycle_count += 1
            print(f"\n[循环 #{cycle_count}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Toggle mode
            if current_mode == "FAST_CHARGE":
                print(f"-> Switching to SLOW_CHARGE (current limited mode)")
                success = hub.set_channel_slow_charge(1, disconnect_before_switch=False)
                if success:
                    current_mode = "SLOW_CHARGE"
                    success_count += 1
                else:
                    error_count += 1
                    fast_to_slow_errors += 1
                    print("Warning: Failed to switch to slow charge mode")
            else:
                print(f"-> Switching to FAST_CHARGE (fast charge mode)")
                success = hub.set_channel_fast_charge(1, disconnect_before_switch=True)
                if success:
                    current_mode = "FAST_CHARGE"
                    success_count += 1
                else:
                    error_count += 1
                    slow_to_fast_errors += 1
                    print("Warning: Failed to switch to fast charge mode")
            
            # Wait a short time for MCU state to stabilize
            time.sleep(0.1)
            
            # Verify current mode
            charge_mode = hub.get_channel_charge_mode(1)
            if charge_mode:
                mode_value = charge_mode.get(1, 0)
                mode_str = "off" if mode_value == 0 else ("fast_charge" if mode_value == 1 else "slow_charge")
                expected_mode = 1 if current_mode == "FAST_CHARGE" else 2
                if mode_value != expected_mode:
                    print(f"[WARN] State mismatch: expected {current_mode} ({expected_mode}), actual {mode_str} ({mode_value})")
                    # Treat mismatch as an error as well
                    error_count += 1
                    if current_mode == "SLOW_CHARGE":
                        fast_to_slow_errors += 1
                    else:
                        slow_to_fast_errors += 1
                else:
                    print(f"[Current] Channel 1: {mode_str} ({mode_value})")
            else:
                print("[WARN] 无法获取充电模式状态 / Failed to get charge mode status")
                error_count += 1
            
            # Show statistics
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
            
            # Wait for the configured interval
            print(f"Waiting {toggle_interval} seconds before next toggle...")
            if toggle_interval >= 1:
                # If interval >= 1s, show countdown
                for i in range(int(toggle_interval), 0, -1):
                    if not running:
                        break
                    print(f"  {i}...", end='\r', flush=True)
                    time.sleep(1)
                # Handle fractional part
                remaining = toggle_interval - int(toggle_interval)
                if remaining > 0 and running:
                    time.sleep(remaining)
                print("     ", end='\r')  # Clear countdown
            else:
                # If interval < 1s, just sleep
                time.sleep(toggle_interval)
            
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received, exiting...")
    except Exception as e:
        print(f"\n\nError occurred: {e}")
    finally:
        # Show final statistics
        print("\n" + "=" * 60)
        print("Final statistics")
        print("=" * 60)
        print(f"总循环次数: {cycle_count}")
        print(f"成功次数: {success_count}")
        print(f"失败次数: {error_count}")
        if cycle_count > 0:
            success_rate = (success_count / cycle_count * 100)
            print(f"Success rate: {success_rate:.2f}%")
        if fast_to_slow_errors > 0 or slow_to_fast_errors > 0:
            print(f"快充→慢充失败: {fast_to_slow_errors} 次")
            print(f"慢充→快充失败: {slow_to_fast_errors} 次")
        
        # \"No ACK\" error statistics
        total_no_ack = sum(no_ack_counter.no_ack_errors.values())
        if total_no_ack > 0:
            print(f"\nNo ACK error statistics (total: {total_no_ack}):")
            if no_ack_counter.no_ack_errors['set_channel_slow_charge'] > 0:
                print(f"  - set_channel_slow_charge: {no_ack_counter.no_ack_errors['set_channel_slow_charge']}")
            if no_ack_counter.no_ack_errors['set_channel_fast_charge'] > 0:
                print(f"  - set_channel_fast_charge: {no_ack_counter.no_ack_errors['set_channel_fast_charge']}")
            if no_ack_counter.no_ack_errors['get_channel_charge_mode'] > 0:
                print(f"  - get_channel_charge_mode: {no_ack_counter.no_ack_errors['get_channel_charge_mode']}")
            if no_ack_counter.no_ack_errors['get_channel_power_status'] > 0:
                print(f"  - get_channel_power_status: {no_ack_counter.no_ack_errors['get_channel_power_status']}")
            if no_ack_counter.no_ack_errors['other'] > 0:
                print(f"  - other commands: {no_ack_counter.no_ack_errors['other']}")
        else:
            print("\nNo ACK errors: 0")
        
        print("=" * 60)
        
        if hub:
            try:
                print("\nDisconnecting...")
                hub.disconnect()
            except:
                pass
        print("Program exited")

if __name__ == "__main__":
    main()


