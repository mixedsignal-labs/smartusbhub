#!/usr/bin/env python3
"""
@file multi_device_channel_control.py
@brief SmartUSBHub example.
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/advanced/multi_device_channel_control.py
"""

"""
Multi-device channel control demo

Scan and connect all available SmartUSBHub devices, control all channels uniformly.
This demo demonstrates multi-device port control - sequentially activating channels
across multiple devices. The visual "chasing light" effect is a side effect of
indicator lights on each channel, not the main purpose of this demo.

Press Ctrl+C to exit.
"""

import sys
import os
import time
import signal

# Add project root to sys.path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__)); project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# Global variables for signal handling
hubs = []
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C signal"""
    global running, hubs
    print("\n\nReceived exit signal, stopping...")
    running = False
    # Turn off all channels
    for hub in hubs:
        if hub:
            try:
                # Turn off all channels
                hub.set_channel_power(*hub.get_channels(), state=0)
                hub.disconnect()
            except:
                pass
    sys.exit(0)

def scan_all_devices():
    """
    Scan and connect all available SmartUSBHub devices

    Returns:
        list: List of SmartUSBHub instances
    """
    devices = []
    exclude_ports = set()

    print("Scanning for all SmartUSBHub devices...")

    # Loop scan until no new devices found
    while True:
        hub = SmartUSBHub.scan_and_connect(exclude_ports=exclude_ports)
        if hub is None:
            break

        devices.append(hub)
        exclude_ports.add(hub.port)
        print(f"  Device #{len(devices)}: {hub.name} (Port: {hub.port}, Address: {hub.device_address:#04x})")

    return devices

def get_global_channel_info(device_index, local_channel, channel_counts):
    """
    Convert device index and local channel number to global channel number

    Args:
        device_index (int): Device index (starting from 0)
        local_channel (int): Channel number within device
        channel_counts (list[int]): Number of channels for each device

    Returns:
        int: Global channel number (starting from 1)
    """
    return sum(channel_counts[:device_index]) + local_channel

def get_device_and_local_channel(global_channel, channel_counts):
    """
    Convert global channel number to device index and local channel number

    Args:
        global_channel (int): Global channel number (starting from 1)
        channel_counts (list[int]): Number of channels for each device

    Returns:
        tuple: (device_index, local_channel) or (None, None) if out of range
    """
    remaining = global_channel
    for device_index, count in enumerate(channel_counts):
        if remaining <= count:
            return device_index, remaining
        remaining -= count
    return None, None

def set_channel_power_and_verify(hub, channel, state):
    """
    Set channel power state and verify if it was actually executed successfully

    Args:
        hub: SmartUSBHub instance
        channel (int): Channel number (1-4)
        state (int): State (0=off, 1=on)

    Returns:
        tuple: (set_success, verify_success) - two boolean values
    """
    # Execute set command (already waits for ACK, state should have switched)
    set_success = hub.set_channel_power(channel, state=state)
    if not set_success:
        return (False, False)  # Set failed

    # Verify state directly (no extra delay needed, set_channel_power already waited for ACK)
    verify_success = False
    actual_state = hub.get_channel_power_status(channel)
    if actual_state is not None and actual_state == state:
        verify_success = True

    return (True, verify_success)  # Set succeeded, verification may succeed or fail

def main():
    global hubs, running

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("Multi-device channel control demo / 多设备通道控制演示")
    print("=" * 60)
    print("Scan and connect all SmartUSBHub devices, control all channels uniformly / 扫描并连接所有SmartUSBHub设备，统一控制所有通道")
    print("This demo demonstrates multi-device port control / 本演示展示多设备端口控制功能")
    print("Note: The visual effect is due to indicator lights on each channel / 注意：视觉效果是因为每个通道有指示灯")
    print("Press Ctrl+C to exit / 按 Ctrl+C 退出程序")
    print("=" * 60)
    print()

    # Scan and connect all devices
    hubs = scan_all_devices()

    if len(hubs) == 0:
        print("Error: No SmartUSBHub devices found / 错误: 未找到任何SmartUSBHub设备")
        return

    channel_counts = [len(hub.get_channels()) for hub in hubs]
    total_channels = sum(channel_counts)
    print(f"\nFound {len(hubs)} device(s), total {total_channels} channels / 共找到 {len(hubs)} 个设备，总共 {total_channels} 个通道")
    print()

    # Display device information
    for i, hub in enumerate(hubs):
        device_info = hub.get_device_info()
        if device_info:
            print(f"Device #{i+1} / 设备 #{i+1}:")
            print(f"  Port / 端口: {hub.port}")
            print(f"  Address / 地址: {hub.device_address:#04x}")
            print(f"  Hardware version / 硬件版本: V1.{device_info.get('hardware_version', 'N/A')}")
            print(f"  Firmware version / 固件版本: V1.{device_info.get('firmware_version', 'N/A')}")
            print(f"  Channels / 通道数: {channel_counts[i]}")
            print()

    # Initialize: turn off all channels
    print("Initializing: turning off all channels... / 初始化：关闭所有通道...")
    for hub in hubs:
        try:
            hub.set_channel_power(*hub.get_channels(), state=0)
        except Exception as e:
            print(f"Warning: Error turning off channels on device {hub.port} / 警告: 关闭设备 {hub.port} 的通道时出错: {e}")
    time.sleep(0.5)
    print("Initialization complete\n / 初始化完成\n")

    # Sequential channel activation parameters
    delay = 0.01  # Time interval between each channel turn-on (seconds)
    # Statistics
    total_operations = 0
    success_count = 0
    error_count = 0

    try:
        cycle = 0
        while running:
            cycle += 1
            print(f"[Cycle #{cycle} / 循环 #{cycle}] {time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Forward sequential activation: from start to end (1 → total_channels)
            for global_ch in range(1, total_channels + 1):
                if not running:
                    break

                device_idx, local_ch = get_device_and_local_channel(global_ch, channel_counts)

                if device_idx is None or device_idx >= len(hubs):
                    continue

                hub = hubs[device_idx]

                # Turn off previous channel
                if global_ch > 1:
                    prev_global_ch = global_ch - 1
                    prev_device_idx, prev_local_ch = get_device_and_local_channel(prev_global_ch, channel_counts)
                    if prev_device_idx < len(hubs):
                        total_operations += 1
                        try:
                            set_success, verify_success = set_channel_power_and_verify(hubs[prev_device_idx], prev_local_ch, 0)
                            if set_success:
                                success_count += 1
                                if not verify_success:
                                    print(f"\nWarning: Turn off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}) succeeded but verification timeout / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置成功但验证超时")
                            else:
                                error_count += 1
                                print(f"\nWarning: Failed to turn off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}) / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置失败")
                        except Exception as e:
                            error_count += 1
                            print(f"\nWarning: Error turning off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}): {e} / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 时出错: {e}")

                # Turn on current channel
                total_operations += 1
                try:
                    set_success, verify_success = set_channel_power_and_verify(hub, local_ch, 1)
                    if set_success:
                        success_count += 1
                        verify_status = "OK" if verify_success else "? (verify timeout)"
                        print(f"  Channel {global_ch:2d}/{total_channels} (device{device_idx+1}, ch{local_ch}) - ON [Forward] {verify_status} | Success:{success_count} Fail:{error_count} / 通道 {global_ch:2d}/{total_channels} (设备{device_idx+1}, 通道{local_ch}) - 打开 [正向] {verify_status} | 成功:{success_count} 失败:{error_count}", end='\r', flush=True)
                        if not verify_success:
                            print(f"\nWarning: Turn on channel {global_ch} (device{device_idx+1}, channel{local_ch}) succeeded but verification timeout / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置成功但验证超时")
                    else:
                        error_count += 1
                        print(f"\nWarning: Failed to turn on channel {global_ch} (device{device_idx+1}, channel{local_ch}) / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置失败")
                except Exception as e:
                    error_count += 1
                    print(f"\nWarning: Error turning on channel {global_ch} (device{device_idx+1}, channel{local_ch}): {e} / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 时出错: {e}")

                time.sleep(delay)

            # Reverse sequential activation: from end to start (total_channels → 1)
            for global_ch in range(total_channels, 0, -1):
                if not running:
                    break

                device_idx, local_ch = get_device_and_local_channel(global_ch, channel_counts)

                if device_idx is None or device_idx >= len(hubs):
                    continue

                hub = hubs[device_idx]

                # Turn off previous channel (when reversing, previous channel has larger number)
                if global_ch < total_channels:
                    prev_global_ch = global_ch + 1
                    prev_device_idx, prev_local_ch = get_device_and_local_channel(prev_global_ch, channel_counts)
                    if prev_device_idx < len(hubs):
                        total_operations += 1
                        try:
                            set_success, verify_success = set_channel_power_and_verify(hubs[prev_device_idx], prev_local_ch, 0)
                            if set_success:
                                success_count += 1
                                if not verify_success:
                                    print(f"\nWarning: Turn off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}) succeeded but verification timeout / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置成功但验证超时")
                            else:
                                error_count += 1
                                print(f"\nWarning: Failed to turn off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}) / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置失败")
                        except Exception as e:
                            error_count += 1
                            print(f"\nWarning: Error turning off channel {prev_global_ch} (device{prev_device_idx+1}, channel{prev_local_ch}): {e} / 警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 时出错: {e}")

                # Turn on current channel
                total_operations += 1
                try:
                    set_success, verify_success = set_channel_power_and_verify(hub, local_ch, 1)
                    if set_success:
                        success_count += 1
                        verify_status = "OK" if verify_success else "? (verify timeout)"
                        print(f"  Channel {global_ch:2d}/{total_channels} (device{device_idx+1}, ch{local_ch}) - ON [Reverse] {verify_status} | Success:{success_count} Fail:{error_count} / 通道 {global_ch:2d}/{total_channels} (设备{device_idx+1}, 通道{local_ch}) - 打开 [反向] {verify_status} | 成功:{success_count} 失败:{error_count}", end='\r', flush=True)
                        if not verify_success:
                            print(f"\nWarning: Turn on channel {global_ch} (device{device_idx+1}, channel{local_ch}) succeeded but verification timeout / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置成功但验证超时")
                    else:
                        error_count += 1
                        print(f"\nWarning: Failed to turn on channel {global_ch} (device{device_idx+1}, channel{local_ch}) / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置失败")
                except Exception as e:
                    error_count += 1
                    print(f"\nWarning: Error turning on channel {global_ch} (device{device_idx+1}, channel{local_ch}): {e} / 警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 时出错: {e}")

                time.sleep(delay)

            # Finally turn off channel 1 (if still running)
            if running:
                device_idx, local_ch = get_device_and_local_channel(1, channel_counts)
                if device_idx < len(hubs):
                    total_operations += 1
                    try:
                        set_success, verify_success = set_channel_power_and_verify(hubs[device_idx], local_ch, 0)
                        if set_success:
                            success_count += 1
                            if not verify_success:
                                print(f"\nWarning: Turn off channel 1 succeeded but verification timeout / 警告: 关闭通道1设置成功但验证超时")
                        else:
                            error_count += 1
                            print(f"\nWarning: Failed to turn off channel 1 / 警告: 关闭通道1设置失败")
                    except Exception as e:
                        error_count += 1
                        print(f"\nWarning: Error turning off channel 1: {e} / 警告: 关闭通道1时出错: {e}")

            # Display statistics
            success_rate = (success_count / total_operations * 100) if total_operations > 0 else 0
            print(f"\n[Statistics / 统计] Total ops: {total_operations}, Success: {success_count}, Fail: {error_count}, Success rate: {success_rate:.1f}% / 总操作: {total_operations}, 成功: {success_count}, 失败: {error_count}, 成功率: {success_rate:.1f}%")

    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received, exiting... / 收到键盘中断，正在退出...")
    except Exception as e:
        print(f"\n\nError occurred: {e} / 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Display final statistics
        print("\n" + "=" * 60)
        print("Final statistics / 最终统计结果")
        print("=" * 60)
        print(f"Total operations / 总操作次数: {total_operations}")
        print(f"Success count / 成功次数: {success_count}")
        print(f"Error count / 失败次数: {error_count}")
        if total_operations > 0:
            success_rate = (success_count / total_operations * 100)
            print(f"Success rate / 成功率: {success_rate:.2f}%")
        print("=" * 60)

        # Turn off all channels
        print("\nTurning off all channels... / 关闭所有通道...")
        for hub in hubs:
            try:
                hub.set_channel_power(*hub.get_channels(), state=0)
                hub.disconnect()
            except:
                pass
        print("Program exited / 程序已退出")

if __name__ == "__main__":
    main()
