#!/usr/bin/env python3
"""
多设备控制Demo

扫描并连接所有可用的SmartUSBHub设备，统一控制所有通道。
演示效果：流水灯效果，按照顺序依次打开每个通道。

按 Ctrl+C 退出程序。
"""

import sys
import os
import time
import signal

# 添加父目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# 全局变量，用于信号处理
hubs = []
running = True

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global running, hubs
    print("\n\n收到退出信号，正在停止...")
    running = False
    # 关闭所有通道
    for hub in hubs:
        if hub:
            try:
                # 关闭所有通道
                hub.set_channel_power(1, 2, 3, 4, state=0)
                hub.disconnect()
            except:
                pass
    sys.exit(0)

def scan_all_devices():
    """
    扫描并连接所有可用的SmartUSBHub设备
    
    Returns:
        list: SmartUSBHub实例列表
    """
    devices = []
    exclude_ports = set()
    
    print("正在扫描所有SmartUSBHub设备...")
    
    # 循环扫描，直到找不到新设备
    while True:
        hub = SmartUSBHub.scan_and_connect(exclude_ports=exclude_ports)
        if hub is None:
            break
        
        devices.append(hub)
        exclude_ports.add(hub.port)
        print(f"  设备 #{len(devices)}: {hub.name} (端口: {hub.port}, 地址: {hub.device_address:#04x})")
    
    return devices

def get_global_channel_info(device_index, local_channel, channels_per_device=4):
    """
    将设备索引和本地通道号转换为全局通道号
    
    Args:
        device_index (int): 设备索引（从0开始）
        local_channel (int): 设备内的通道号（1-4）
        channels_per_device (int): 每个设备的通道数，默认为4
    
    Returns:
        int: 全局通道号（从1开始）
    """
    return device_index * channels_per_device + local_channel

def get_device_and_local_channel(global_channel, channels_per_device=4):
    """
    将全局通道号转换为设备索引和本地通道号
    
    Args:
        global_channel (int): 全局通道号（从1开始）
        channels_per_device (int): 每个设备的通道数，默认为4
    
    Returns:
        tuple: (device_index, local_channel) 或 (None, None) 如果超出范围
    """
    global_channel -= 1  # 转换为从0开始
    device_index = global_channel // channels_per_device
    local_channel = global_channel % channels_per_device + 1
    return device_index, local_channel

def set_channel_power_and_verify(hub, channel, state, verify_delay=0.1, max_retries=2):
    """
    设置通道电源状态并验证是否真的执行成功
    
    Args:
        hub: SmartUSBHub实例
        channel (int): 通道号（1-4）
        state (int): 状态（0=关闭, 1=打开）
        verify_delay (float): 验证前的等待时间（秒）
        max_retries (int): 验证失败时的最大重试次数
    
    Returns:
        tuple: (设置成功, 验证成功) - 两个布尔值
    """
    # 执行设置命令
    set_success = hub.set_channel_power(channel, state=state)
    if not set_success:
        return (False, False)  # 设置失败
    
    # 等待状态稳定
    time.sleep(verify_delay)
    
    # 验证状态（带重试）
    verify_success = False
    for retry in range(max_retries + 1):
        actual_state = hub.get_channel_power_status(channel)
        if actual_state is not None:
            # 检查状态是否匹配
            if actual_state == state:
                verify_success = True
                break
            # 如果状态不匹配，等待一下再重试
            if retry < max_retries:
                time.sleep(verify_delay)
        else:
            # 获取状态超时，等待一下再重试
            if retry < max_retries:
                time.sleep(verify_delay)
    
    return (True, verify_success)  # 设置成功，验证可能成功或失败

def main():
    global hubs, running
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("多设备控制Demo")
    print("=" * 60)
    print("扫描并连接所有SmartUSBHub设备，统一控制所有通道")
    print("演示效果：流水灯效果，按顺序依次打开通道")
    print("按 Ctrl+C 退出程序")
    print("=" * 60)
    print()
    
    # 扫描并连接所有设备
    hubs = scan_all_devices()
    
    if len(hubs) == 0:
        print("错误: 未找到任何SmartUSBHub设备")
        return
    
    channels_per_device = 4  # 每个设备的通道数
    total_channels = len(hubs) * channels_per_device
    print(f"\n共找到 {len(hubs)} 个设备，总共 {total_channels} 个通道")
    print()
    
    # 显示设备信息
    for i, hub in enumerate(hubs):
        device_info = hub.get_device_info()
        if device_info:
            print(f"设备 #{i+1}:")
            print(f"  端口: {hub.port}")
            print(f"  地址: {hub.device_address:#04x}")
            print(f"  硬件版本: V1.{device_info.get('hardware_version', 'N/A')}")
            print(f"  固件版本: V1.{device_info.get('firmware_version', 'N/A')}")
            print()
    
    # 初始化：关闭所有通道
    print("初始化：关闭所有通道...")
    for hub in hubs:
        try:
            hub.set_channel_power(1, 2, 3, 4, state=0)
        except Exception as e:
            print(f"警告: 关闭设备 {hub.port} 的通道时出错: {e}")
    time.sleep(0.5)
    print("初始化完成\n")
    
    # 流水灯参数
    delay = 0.01  # 每个通道打开的时间间隔（秒）
    channels_per_device = 4  # 每个设备的通道数
    total_channels = len(hubs) * channels_per_device
    
    # 统计信息
    total_operations = 0
    success_count = 0
    error_count = 0
    
    try:
        cycle = 0
        while running:
            cycle += 1
            print(f"[循环 #{cycle}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 正向流水灯：从头到尾 (1 → total_channels)
            for global_ch in range(1, total_channels + 1):
                if not running:
                    break
                
                device_idx, local_ch = get_device_and_local_channel(global_ch, channels_per_device)
                
                if device_idx >= len(hubs):
                    continue
                
                hub = hubs[device_idx]
                
                # 关闭上一个通道
                if global_ch > 1:
                    prev_global_ch = global_ch - 1
                    prev_device_idx, prev_local_ch = get_device_and_local_channel(prev_global_ch, channels_per_device)
                    if prev_device_idx < len(hubs):
                        total_operations += 1
                        try:
                            set_success, verify_success = set_channel_power_and_verify(hubs[prev_device_idx], prev_local_ch, 0)
                            if set_success:
                                success_count += 1
                                if not verify_success:
                                    print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置成功但验证超时")
                            else:
                                error_count += 1
                                print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置失败")
                        except Exception as e:
                            error_count += 1
                            print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 时出错: {e}")
                
                # 打开当前通道
                total_operations += 1
                try:
                    set_success, verify_success = set_channel_power_and_verify(hub, local_ch, 1)
                    if set_success:
                        success_count += 1
                        verify_status = "✓" if verify_success else "? (验证超时)"
                        print(f"  通道 {global_ch:2d}/{total_channels} (设备{device_idx+1}, 通道{local_ch}) - 打开 [正向] {verify_status} | 成功:{success_count} 失败:{error_count}", end='\r', flush=True)
                        if not verify_success:
                            print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置成功但验证超时")
                    else:
                        error_count += 1
                        print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置失败")
                except Exception as e:
                    error_count += 1
                    print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 时出错: {e}")
                
                time.sleep(delay)
            
            # 反向流水灯：从尾到头 (total_channels → 1)
            for global_ch in range(total_channels, 0, -1):
                if not running:
                    break
                
                device_idx, local_ch = get_device_and_local_channel(global_ch, channels_per_device)
                
                if device_idx >= len(hubs):
                    continue
                
                hub = hubs[device_idx]
                
                # 关闭上一个通道（反向时，上一个通道是更大的编号）
                if global_ch < total_channels:
                    prev_global_ch = global_ch + 1
                    prev_device_idx, prev_local_ch = get_device_and_local_channel(prev_global_ch, channels_per_device)
                    if prev_device_idx < len(hubs):
                        total_operations += 1
                        try:
                            set_success, verify_success = set_channel_power_and_verify(hubs[prev_device_idx], prev_local_ch, 0)
                            if set_success:
                                success_count += 1
                                if not verify_success:
                                    print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置成功但验证超时")
                            else:
                                error_count += 1
                                print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 设置失败")
                        except Exception as e:
                            error_count += 1
                            print(f"\n警告: 关闭通道 {prev_global_ch} (设备{prev_device_idx+1}, 通道{prev_local_ch}) 时出错: {e}")
                
                # 打开当前通道
                total_operations += 1
                try:
                    set_success, verify_success = set_channel_power_and_verify(hub, local_ch, 1)
                    if set_success:
                        success_count += 1
                        verify_status = "✓" if verify_success else "? (验证超时)"
                        print(f"  通道 {global_ch:2d}/{total_channels} (设备{device_idx+1}, 通道{local_ch}) - 打开 [反向] {verify_status} | 成功:{success_count} 失败:{error_count}", end='\r', flush=True)
                        if not verify_success:
                            print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置成功但验证超时")
                    else:
                        error_count += 1
                        print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 设置失败")
                except Exception as e:
                    error_count += 1
                    print(f"\n警告: 打开通道 {global_ch} (设备{device_idx+1}, 通道{local_ch}) 时出错: {e}")
                
                time.sleep(delay)
            
            # 最后关闭通道1（如果还在运行）
            if running:
                device_idx, local_ch = get_device_and_local_channel(1, channels_per_device)
                if device_idx < len(hubs):
                    total_operations += 1
                    try:
                        set_success, verify_success = set_channel_power_and_verify(hubs[device_idx], local_ch, 0)
                        if set_success:
                            success_count += 1
                            if not verify_success:
                                print(f"\n警告: 关闭通道1设置成功但验证超时")
                        else:
                            error_count += 1
                            print(f"\n警告: 关闭通道1设置失败")
                    except Exception as e:
                        error_count += 1
                        print(f"\n警告: 关闭通道1时出错: {e}")
            
            # 显示统计信息
            success_rate = (success_count / total_operations * 100) if total_operations > 0 else 0
            print(f"\n[统计] 总操作: {total_operations}, 成功: {success_count}, 失败: {error_count}, 成功率: {success_rate:.1f}%")
            
    except KeyboardInterrupt:
        print("\n\n收到键盘中断，正在退出...")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 显示最终统计
        print("\n" + "=" * 60)
        print("最终统计结果")
        print("=" * 60)
        print(f"总操作次数: {total_operations}")
        print(f"成功次数: {success_count}")
        print(f"失败次数: {error_count}")
        if total_operations > 0:
            success_rate = (success_count / total_operations * 100)
            print(f"成功率: {success_rate:.2f}%")
        print("=" * 60)
        
        # 关闭所有通道
        print("\n关闭所有通道...")
        for hub in hubs:
            try:
                hub.set_channel_power(1, 2, 3, 4, state=0)
                hub.disconnect()
            except:
                pass
        print("程序已退出")

if __name__ == "__main__":
    main()

