# Description: Auto switch between fast charge and slow charge modes at specified intervals
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def format_time(seconds):
    """将秒数格式化为可读的时间字符串"""
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
        print("Error: Interval must be greater than 0")
        sys.exit(1)
    
    # Scan and connect to device
    hub_list = SmartUSBHub.scan_available_ports()
    print("Available devices:", hub_list)
    
    hub = SmartUSBHub.scan_and_connect()
    
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)
    
    # Get device info
    device_info = hub.get_device_info()
    print("Device info:", device_info)
    
    # Get and display hardware and firmware version
    hardware_version = hub.get_hardware_version()
    firmware_version = hub.get_firmware_version()
    print(f"Hardware Version: V1.{hardware_version}" if hardware_version is not None else "Hardware Version: Unknown")
    print(f"Firmware Version: V1.{firmware_version}" if firmware_version is not None else "Firmware Version: Unknown")
    print()
    
    # Display configuration
    print("=" * 60)
    print("Auto Charge Mode Switch Configuration")
    print("=" * 60)
    print(f"Channels: {args.channels}")
    print(f"Switch interval: {format_time(args.interval)} ({args.interval} seconds)")
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
    
    print(f"\nStarting auto-switch mode...")
    print(f"Initial mode: {current_mode}")
    print(f"Press Ctrl+C to stop\n")
    
    try:
        # Set initial mode (fast charge)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Setting initial mode: {current_mode}")
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
        charge_modes = hub.get_channel_charge_mode(args.channels[0])
        if charge_modes:
            for ch, mode_val in charge_modes.items():
                if ch in args.channels:
                    mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                    print(f"  Channel {ch}: {mode_str} ({mode_val})")
        print()
        
        while True:
            # Calculate next switch time
            next_switch_time = datetime.now() + timedelta(seconds=args.interval)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Next switch at: {next_switch_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Current mode: {current_mode}")
            print("Countdown:")
            
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
                    stats_info = f"Switches: {switch_count} | Total: {format_time(total_runtime)}"
                    print(f"  Remaining: {remaining_str:>12} {remaining_seconds:>8} | Mode: {current_mode:12} | {stats_info}", end='\r')
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
                print(f"[{switch_timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Switch #{switch_count}: Switching to SLOW_CHARGE (ilim mode)")
                print(f"  Previous FAST_CHARGE duration: {format_time(mode_duration)}")
                hub.set_channel_slow_charge(*args.channels, disconnect_before_switch=False)
            else:
                current_mode = "FAST_CHARGE"
                fast_charge_count += 1
                print(f"[{switch_timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Switch #{switch_count}: Switching to FAST_CHARGE (full-speed charging)")
                print(f"  Previous SLOW_CHARGE duration: {format_time(mode_duration)}")
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
            charge_modes = hub.get_channel_charge_mode(args.channels[0])
            if charge_modes:
                for ch, mode_val in charge_modes.items():
                    if ch in args.channels:
                        mode_str = "off" if mode_val == 0 else ("fast_charge" if mode_val == 1 else "slow_charge")
                        print(f"  Channel {ch}: {mode_str} ({mode_val})")
            print()
            
    except KeyboardInterrupt:
        print(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Interrupted by user")
    except Exception as e:
        print(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error occurred: {e}")
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
        print("TEST STATISTICS REPORT")
        print("=" * 70)
        print(f"Program start time: {datetime.fromtimestamp(program_start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Program end time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total runtime:      {format_time(total_runtime)} ({total_runtime:.1f} seconds)")
        print()
        print("Mode Statistics:")
        print(f"  Total switches:           {switch_count}")
        print(f"  FAST_CHARGE sessions:      {fast_charge_count}")
        print(f"  SLOW_CHARGE sessions:      {slow_charge_count}")
        print(f"  FAST_CHARGE total time:    {format_time(fast_charge_total_time)} ({fast_charge_total_time:.1f}s)")
        print(f"  SLOW_CHARGE total time:    {format_time(slow_charge_total_time)} ({slow_charge_total_time:.1f}s)")
        if total_runtime > 0:
            fast_charge_percent = (fast_charge_total_time / total_runtime) * 100
            slow_charge_percent = (slow_charge_total_time / total_runtime) * 100
            print(f"  FAST_CHARGE percentage:    {fast_charge_percent:.1f}%")
            print(f"  SLOW_CHARGE percentage:    {slow_charge_percent:.1f}%")
        print()
        print(f"Current mode:               {current_mode}")
        print(f"Current mode duration:       {format_time(current_mode_duration)}")
        print()
        
        # Print switch history
        if switch_history:
            print("Switch History:")
            print("-" * 70)
            for i, switch in enumerate(switch_history):
                if i == 0:
                    print(f"  #{switch['switch_num']:3d} [{switch['timestamp'].strftime('%H:%M:%S')}] {switch['action']:8s} -> {switch['mode']:12s}")
                else:
                    prev_dur = switch.get('previous_duration', 0)
                    print(f"  #{switch['switch_num']:3d} [{switch['timestamp'].strftime('%H:%M:%S')}] Switch -> {switch['mode']:12s} (previous: {format_time(prev_dur)})")
            print("-" * 70)
        
        print("=" * 70)
        print("\nDisconnecting...")
        hub.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    main()

