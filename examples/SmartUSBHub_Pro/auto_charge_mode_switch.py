# Description: Auto switch between fast charge and slow charge modes at specified intervals
# copyright: (c) 2026 makerlabtools
# license: Apache-2.0
# version: 1.0
# author: makerlabtools
# email: makerlabtools@outlook.com

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def format_time(seconds):
    """Format seconds into a human readable time string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def main():
    parser = argparse.ArgumentParser(
        description='Auto switch between fast charge and slow charge modes at specified intervals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Switch every hour (default)
  python auto_charge_mode_switch.py
  
  # Switch every 30 minutes
  python auto_charge_mode_switch.py --interval 1800
  
  # Switch every 10 minutes
  python auto_charge_mode_switch.py --interval 600
  
  # Switch every 2 hours
  python auto_charge_mode_switch.py --interval 7200
        """
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Time interval in seconds between mode switches (default: 3600 = 1 hour)'
    )
    parser.add_argument(
        '--channels',
        type=int,
        nargs='+',
        default=[1, 2, 3, 4],
        help='Channels to control (default: 1 2 3 4)'
    )
    
    args = parser.parse_args()
    
    if args.interval <= 0:
        print("Error: Interval must be greater than 0 / 错误：间隔必须大于 0")
        sys.exit(1)
    
    # Scan and connect to device
    hub_list = SmartUSBHub.scan_available_ports()
    print("Available devices / 可用设备:", hub_list)
    
    hub = SmartUSBHub.scan_and_connect()
    
    if hub is None:
        print("No SmartUSBHub found / 未找到 SmartUSBHub 设备")
        sys.exit(1)
    
    # Get device info
    device_info = hub.get_device_info()
    print("Device info / 设备信息:", device_info)
    
    # Get and display hardware and firmware version
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version / 硬件版本: V1.{hardware_version}" if hardware_version is not None else "Hardware Version / 硬件版本: Unknown")
    print(f"Firmware Version / 固件版本: V1.{firmware_version}" if firmware_version is not None else "Firmware Version / 固件版本: Unknown")
    print()
    
    # Display configuration
    print("=" * 60)
    print("Auto Charge Mode Switch Configuration / 自动充电模式切换配置")
    print("=" * 60)
    print(f"Channels / 通道: {args.channels}")
    print(f"Switch interval / 切换间隔: {format_time(args.interval)} ({args.interval} seconds)")
    print("=" * 60)
    print()
    
    # Start with fast charge mode
    current_mode = "FAST_CHARGE"
    switch_count = 0
    
    # Statistics tracking
    program_start_time = time.time()
    mode_start_time = time.time()
    fast_charge_total_time = 0.0
    slow_charge_total_time = 0.0
    fast_charge_count = 0
    slow_charge_count = 0
    switch_history = []  # Store switch timestamps and modes
    
    print(f"\nStarting auto-switch mode... / 开始自动切换充电模式...")
    print(f"Initial mode / 初始模式: {current_mode}")
    print(f"Press Ctrl+C to stop / 按 Ctrl+C 结束\n")
    
    try:
        # Set initial mode (fast charge)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Setting initial mode / 设置初始模式: {current_mode}")
        hub.set_channel_fast_charge(*args.channels, disconnect_before_switch=True)
        fast_charge_count = 1
        mode_start_time = time.time()
        switch_history.append({
            'timestamp': datetime.now(),
            'switch_num': 0,
            'mode': 'FAST_CHARGE',
            'action': 'Initial'
        })
        
        # Get and display charge mode status
        charge_modes = hub.get_channel_charge_mode(*args.channels)
        if charge_modes:
            for ch, mode_val in charge_modes.items():
                if ch in args.channels:
                    mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                    print(f"  Channel {ch} / 通道 {ch}: {mode_str} ({mode_val})")
        print()
        
        while True:
            # Calculate next switch time
            next_switch_time = datetime.now() + timedelta(seconds=args.interval)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Next switch at / 下次切换时间: {next_switch_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Current mode / 当前模式: {current_mode}")
            print("Countdown / 倒计时:")
            
            # Wait for the interval with second-by-second countdown
            start_time = time.time()
            last_remaining = args.interval
            
            while True:
                elapsed = time.time() - start_time
                remaining = args.interval - elapsed
                
                if remaining <= 0:
                    break
                
                # Update display every second
                remaining_int = int(remaining)
                if remaining_int != int(last_remaining):
                    # Calculate statistics
                    total_runtime = time.time() - program_start_time
                    current_mode_runtime = time.time() - mode_start_time
                    
                    # Clear the line and print updated countdown with statistics
                    remaining_str = format_time(remaining)
                    remaining_seconds = f"({remaining_int}s)"
                    stats_info = f"Switches / 切换次数: {switch_count} | Total / 总时长: {format_time(total_runtime)}"
                    print(f"  Remaining / 剩余: {remaining_str:>12} {remaining_seconds:>8} | Mode / 模式: {current_mode:12} | {stats_info}", end='\r')
                    last_remaining = remaining
                
                time.sleep(0.1)  # Check every 100ms for more accurate timing
            
            print()  # New line after countdown
            
            # Calculate time spent in previous mode
            mode_duration = time.time() - mode_start_time
            if current_mode == "FAST_CHARGE":
                fast_charge_total_time += mode_duration
            else:
                slow_charge_total_time += mode_duration
            
            # Switch mode
            switch_count += 1
            switch_timestamp = datetime.now()
            
            if current_mode == "FAST_CHARGE":
                current_mode = "SLOW_CHARGE"
                slow_charge_count += 1
                print(f"[{switch_timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Switch #{switch_count}: Switching to SLOW_CHARGE (ilim mode) / 切换到慢充模式 (限流模式)")
                print(f"  Previous FAST_CHARGE duration / 上一次快充持续时间: {format_time(mode_duration)}")
                hub.set_channel_slow_charge(*args.channels, disconnect_before_switch=False)
            else:
                current_mode = "FAST_CHARGE"
                fast_charge_count += 1
                print(f"[{switch_timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Switch #{switch_count}: Switching to FAST_CHARGE (full-speed charging) / 切换到快充模式")
                print(f"  Previous SLOW_CHARGE duration / 上一次慢充持续时间: {format_time(mode_duration)}")
                hub.set_channel_fast_charge(*args.channels, disconnect_before_switch=True)
            
            # Record switch history
            switch_history.append({
                'timestamp': switch_timestamp,
                'switch_num': switch_count,
                'mode': current_mode,
                'previous_duration': mode_duration
            })
            
            # Reset mode start time for new mode
            mode_start_time = time.time()
            
            # Get and display charge mode status
            charge_modes = hub.get_channel_charge_mode(*args.channels)
            if charge_modes:
                for ch, mode_val in charge_modes.items():
                    if ch in args.channels:
                        mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                        print(f"  Channel {ch} / 通道 {ch}: {mode_str} ({mode_val})")
            print()
            
    except KeyboardInterrupt:
        print(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Interrupted by user / 用户中断")
    except Exception as e:
        print(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error occurred / 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Calculate final statistics
        total_runtime = time.time() - program_start_time
        current_mode_duration = time.time() - mode_start_time
        
        # Add current mode duration to totals
        if current_mode == "FAST_CHARGE":
            fast_charge_total_time += current_mode_duration
        else:
            slow_charge_total_time += current_mode_duration
        
        # Print statistics report
        print("\n" + "=" * 70)
        print("TEST STATISTICS REPORT / 测试统计报告")
        print("=" * 70)
        print(f"Program start time / 程序开始时间: {datetime.fromtimestamp(program_start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Program end time   / 程序结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total runtime      / 总运行时间:   {format_time(total_runtime)} ({total_runtime:.1f} seconds)")
        print()
        print("Mode Statistics / 模式统计:")
        print(f"  Total switches / 总切换次数:           {switch_count}")
        print(f"  FAST_CHARGE sessions / 快充次数:        {fast_charge_count}")
        print(f"  SLOW_CHARGE sessions / 慢充次数:        {slow_charge_count}")
        print(f"  FAST_CHARGE total time / 快充总时长:    {format_time(fast_charge_total_time)} ({fast_charge_total_time:.1f}s)")
        print(f"  SLOW_CHARGE total time / 慢充总时长:    {format_time(slow_charge_total_time)} ({slow_charge_total_time:.1f}s)")
        if total_runtime > 0:
            fast_charge_percent = (fast_charge_total_time / total_runtime) * 100
            slow_charge_percent = (slow_charge_total_time / total_runtime) * 100
            print(f"  FAST_CHARGE percentage / 快充占比:      {fast_charge_percent:.1f}%")
            print(f"  SLOW_CHARGE percentage / 慢充占比:      {slow_charge_percent:.1f}%")
        print()
        print(f"Current mode / 当前模式:               {current_mode}")
        print(f"Current mode duration / 当前模式持续时间: {format_time(current_mode_duration)}")
        print()
        
        # Print switch history
        if switch_history:
            print("Switch History / 切换历史:")
            print("-" * 70)
            for i, switch in enumerate(switch_history):
                if i == 0:
                    print(f"  #{switch['switch_num']:3d} [{switch['timestamp'].strftime('%H:%M:%S')}] {switch['action']:8s} -> {switch['mode']:12s}")
                else:
                    prev_dur = switch.get('previous_duration', 0)
                    print(f"  #{switch['switch_num']:3d} [{switch['timestamp'].strftime('%H:%M:%S')}] Switch / 切换 -> {switch['mode']:12s} (previous / 上一次: {format_time(prev_dur)})")
            print("-" * 70)
        
        print("=" * 70)
        print("\nDisconnecting... / 正在断开连接...")
        hub.disconnect()
        print("Disconnected / 已断开连接")

if __name__ == "__main__":
    main()


