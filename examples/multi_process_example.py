#!/usr/bin/env python3
"""
多进程压力测试Demo

扫描并连接所有可用的SmartUSBHub设备，使用多进程架构进行压力测试。
每个设备有一个服务进程，每个通道有一个业务进程。

例如：如果有4个设备，每个设备4个通道，将创建：
- 4个服务进程（每个设备一个）
- 16个业务进程（每个通道一个）

按 Ctrl+C 退出程序。
"""

import sys
import os
import time
import signal
from multiprocessing import Process, Manager, Queue
from typing import List, Dict, Tuple

# 添加项目根目录到路径，以便导入smartusbhub模块
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub
from smartusbhub_multiprocess import SmartUSBHubClient, server_process_main

# 命令间隔延迟时间（秒）
COMMAND_DELAY = 0.020  # 默认20ms延迟

# 全局变量，用于信号处理
server_processes: List[Process] = []
worker_processes: List[Process] = []
running = True

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global running, server_processes, worker_processes
    print("\n\n收到退出信号，正在停止所有进程...")
    running = False
    
    # 停止所有业务进程
    for p in worker_processes:
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)
    
    # 停止所有服务进程
    for p in server_processes:
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)
    
    print("所有进程已停止")
    sys.exit(0)

def scan_all_devices():
    """
    扫描并连接所有可用的SmartUSBHub设备
    
    Returns:
        list: (port, device_address, hardware_version, firmware_version) 元组列表
    """
    devices = []
    exclude_ports = set()
    
    print("正在扫描所有SmartUSBHub设备...")
    
    # 循环扫描，直到找不到新设备
    while True:
        hub = SmartUSBHub.scan_and_connect(exclude_ports=exclude_ports)
        if hub is None:
            break
        
        port = hub.port
        device_address = hub.device_address
        # 获取硬件和软件版本
        hardware_version = hub.get_hardware_version()
        firmware_version = hub.get_firmware_version()
        
        devices.append((port, device_address, hardware_version, firmware_version))
        exclude_ports.add(port)
        
        print(f"  设备 #{len(devices)}: {hub.name}")
        print(f"    端口: {port}")
        print(f"    地址: {device_address:#04x}")
        print(f"    硬件版本: V1.{hardware_version}" if hardware_version is not None else "    硬件版本: 未知")
        print(f"    固件版本: V1.{firmware_version}" if firmware_version is not None else "    固件版本: 未知")
        
        hub.disconnect()  # 断开连接，服务进程会重新连接
    
    return devices

def worker_process(device_idx: int, channel: int, request_queue: Queue, 
                   response_dict: Dict, total_iterations: int,
                   iteration_counts: Dict, success_count: Dict, 
                   failure_count: Dict, global_count: Dict, count_lock):
    """
    业务进程：控制指定设备的指定通道
    
    Args:
        device_idx: 设备索引
        channel: 通道号
        request_queue: 请求队列
        response_dict: 响应字典
        total_iterations: 总迭代次数
        iteration_counts: 迭代计数字典
        success_count: 成功计数字典
        failure_count: 失败计数字典
        global_count: 全局计数字典
        count_lock: 计数锁
    """
    process_name = f"Worker-Device{device_idx+1}-Ch{channel}"
    
    try:
        # 创建客户端
        client = SmartUSBHubClient(request_queue, response_dict, timeout=5.0)
        
        # 等待客户端初始化
        time.sleep(0.1)
        
        while running:
            with count_lock:
                if global_count['value'] >= total_iterations:
                    break
                global_count['value'] += 1
                current_count = global_count['value']
            
            # Turn the channel on and check status
            ok_on = client.set_channel_power(channel, state=1)
            time.sleep(COMMAND_DELAY)
            client.get_channel_power_status(channel)
            time.sleep(COMMAND_DELAY)
            
            # Turn the channel off and check status
            ok_off = client.set_channel_power(channel, state=0)
            time.sleep(COMMAND_DELAY)
            client.get_channel_power_status(channel)
            time.sleep(COMMAND_DELAY)
            
            with count_lock:
                key = (device_idx, channel)
                iteration_counts[key] = iteration_counts.get(key, 0) + 1
                # Record a success only if both on and off operations were acknowledged
                if ok_on and ok_off:
                    success_count['value'] = success_count.get('value', 0) + 1
                else:
                    failure_count['value'] = failure_count.get('value', 0) + 1
                    
    except KeyboardInterrupt:
        print(f"[{process_name}] 收到中断信号")
    except Exception as e:
        print(f"[{process_name}] 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{process_name}] 进程已退出")

def progress_printer(global_count: Dict, success_count: Dict, 
                     failure_count: Dict, count_lock, total_iterations: int):
    """打印进度和成功/失败计数"""
    while running:
        time.sleep(1)
        with count_lock:
            current = global_count.get('value', 0)
            succ = success_count.get('value', 0)
            fail = failure_count.get('value', 0)
        print(f"Progress: {current}/{total_iterations} cycles, Success: {succ}, Failure: {fail}")
        if current >= total_iterations:
            break

def stress_test(total_iterations: int = 10_000_000, channels_per_device=(1, 2, 3, 4)) -> None:
    """
    使用多进程架构进行压力测试
    
    Args:
        total_iterations: 总迭代次数
        channels_per_device: 每个设备的通道号元组
    """
    global server_processes, worker_processes, running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 扫描所有设备
    devices = scan_all_devices()
    if not devices:
        print("No Smart USB Hub found. Exiting stress test.")
        return
    
    num_devices = len(devices)
    num_channels_per_device = len(channels_per_device)
    total_channels = num_devices * num_channels_per_device
    
    print(f"\n找到 {num_devices} 个设备，每个设备 {num_channels_per_device} 个通道")
    print(f"总共 {total_channels} 个通道")
    print(f"将创建 {num_devices} 个服务进程和 {total_channels} 个业务进程\n")
    
    # 创建共享资源管理器
    manager = Manager()
    
    # 为每个设备创建服务进程和对应的共享资源
    device_queues = []
    device_response_dicts = []
    
    for device_idx, (port, device_address, hardware_version, firmware_version) in enumerate(devices):
        # 为每个设备创建独立的请求队列和响应字典
        request_queue = Queue()
        response_dict = manager.dict()
        device_queues.append(request_queue)
        device_response_dicts.append(response_dict)
        
        # 启动服务进程
        print(f"[Main] 启动设备 {device_idx + 1} 的服务进程 (端口: {port})...")
        server_process = Process(
            target=server_process_main,
            args=(request_queue, response_dict, port),
            name=f"Server-Device{device_idx+1}"
        )
        server_process.daemon = False
        server_process.start()
        server_processes.append(server_process)
    
    # 等待服务进程初始化
    print("\n[Main] 等待服务进程初始化...")
    time.sleep(3)
    
    # 检查服务进程是否都正常运行
    for i, p in enumerate(server_processes):
        if not p.is_alive():
            print(f"[Main] 错误: 设备 {i + 1} 的服务进程启动失败")
            signal_handler(None, None)
            return
    
    print("[Main] 所有服务进程已启动\n")
    
    # 创建共享计数器
    iteration_counts = manager.dict()
    success_count = manager.dict({'value': 0})
    failure_count = manager.dict({'value': 0})
    global_count = manager.dict({'value': 0})
    count_lock = manager.Lock()
    
    # 启动业务进程（每个设备的每个通道一个进程）
    print("[Main] 启动业务进程...")
    for device_idx in range(num_devices):
        for ch in channels_per_device:
            p = Process(
                target=worker_process,
                args=(
                    device_idx, ch,
                    device_queues[device_idx],
                    device_response_dicts[device_idx],
                    total_iterations,
                    iteration_counts,
                    success_count,
                    failure_count,
                    global_count,
                    count_lock
                ),
                name=f"Worker-Device{device_idx+1}-Ch{ch}"
            )
            p.daemon = False
            p.start()
            worker_processes.append(p)
    
    print(f"[Main] 已启动 {len(worker_processes)} 个业务进程\n")
    
    # 启动进度打印进程
    printer_process = Process(
        target=progress_printer,
        args=(global_count, success_count, failure_count, count_lock, total_iterations),
        name="ProgressPrinter"
    )
    printer_process.daemon = False
    printer_process.start()
    
    try:
        # 等待所有业务进程完成
        for p in worker_processes:
            p.join()
        
        # 等待进度打印进程完成
        printer_process.join()
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    # 最终报告
    print(f"\n{'='*60}")
    print("Stress test completed.")
    print(f"{'='*60}")
    print(f"Total cycles: {global_count.get('value', 0)}")
    print(f"Success: {success_count.get('value', 0)}")
    print(f"Failure: {failure_count.get('value', 0)}")
    
    # 打印每个通道的统计信息
    print(f"\n{'='*60}")
    print("Per-channel statistics:")
    print(f"{'='*60}")
    for device_idx in range(num_devices):
        port, device_address, hardware_version, firmware_version = devices[device_idx]
        print(f"\nDevice {device_idx + 1} (端口: {port}, 地址: {device_address:#04x})")
        print(f"  硬件版本: V1.{hardware_version}" if hardware_version is not None else "  硬件版本: 未知")
        print(f"  固件版本: V1.{firmware_version}" if firmware_version is not None else "  固件版本: 未知")
        for ch in channels_per_device:
            key = (device_idx, ch)
            count = iteration_counts.get(key, 0)
            print(f"  Channel {ch}: {count} cycles")
    
    # 清理：关闭所有通道
    print(f"\n{'='*60}")
    print("Turning off all channels...")
    for device_idx in range(num_devices):
        try:
            client = SmartUSBHubClient(device_queues[device_idx], device_response_dicts[device_idx])
            client.set_channel_power(1, 2, 3, 4, state=0)
        except:
            pass
    
    # 停止所有服务进程
    print("\nStopping all server processes...")
    for device_idx, p in enumerate(server_processes):
        if p.is_alive():
            try:
                # 发送关闭请求
                request_queue = device_queues[device_idx]
                response_dict = device_response_dicts[device_idx]
                client = SmartUSBHubClient(request_queue, response_dict)
                client.shutdown()
                time.sleep(0.5)  # 等待服务进程处理关闭请求
            except:
                pass
            p.join(timeout=2)
    
    print("All processes stopped.")


if __name__ == "__main__":
    # 默认运行 1000 万次循环的压力测试
    stress_test()

