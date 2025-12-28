import threading
import time
import sys
import os
import signal

# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# 命令间隔延迟时间（秒），用于避免命令发送过快导致MCU状态机混乱
# 可以根据测试需要调整此值，例如：0.001 (1ms), 0.010 (10ms), 0.020 (20ms) 等
# 注意：当 ENABLE_SYNC_LOCK = False 时，建议使用 20ms 或更大的延迟
COMMAND_DELAY = 0.020  # 默认20ms延迟，确保MCU有足够时间处理命令和发送ACK响应

# 全局变量，用于信号处理
hubs = []
running = True

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global running, hubs
    print("\n\n收到退出信号，正在停止...")
    running = False
    # 关闭所有通道并断开所有设备
    for hub in hubs:
        if hub:
            try:
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
        
        # 获取硬件和软件版本
        hardware_version = hub.get_hardware_version()
        firmware_version = hub.get_firmware_version()
        
        print(f"  设备 #{len(devices)}: {hub.name}")
        print(f"    端口: {hub.port}")
        print(f"    地址: {hub.device_address:#04x}")
        print(f"    硬件版本: V1.{hardware_version}" if hardware_version is not None else "    硬件版本: 未知")
        print(f"    固件版本: V1.{firmware_version}" if firmware_version is not None else "    固件版本: 未知")
    
    return devices

def stress_test(total_iterations: int = 10_000_000, channels_per_device=(1, 2, 3, 4)) -> None:
    """Run a concurrent stress test on multiple SmartUSBHub devices.

    This function scans and connects to all available SmartUSBHub devices and spawns one thread
    per channel per device. Each thread repeatedly toggles the power on its assigned channel on
    and off, counting cycles. The test stops once the total number of cycles across all channels
    reaches ``total_iterations``.

    For example, if 4 devices are connected, each with 4 channels, there will be 16 threads
    running concurrently.

    During the test, a progress printer thread outputs the current number of completed cycles and
    success/failure counts every second.

    Note: When ENABLE_SYNC_LOCK = False, this test can cause MCU state machine issues due to
    concurrent command sending. The test includes small delays to mitigate this, but for production
    use, ENABLE_SYNC_LOCK should be set to True.

    Args:
        total_iterations: Total number of on/off toggle cycles to perform across all channels.
        channels_per_device: A tuple of channel numbers to test per device (default: 1, 2, 3, 4).
    """
    global hubs, running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # 扫描并连接所有设备
    hubs = scan_all_devices()
    if not hubs:
        print("No Smart USB Hub found. Exiting stress test.")
        return
    
    num_devices = len(hubs)
    num_channels_per_device = len(channels_per_device)
    total_channels = num_devices * num_channels_per_device
    
    print(f"\n找到 {num_devices} 个设备，每个设备 {num_channels_per_device} 个通道")
    print(f"总共 {total_channels} 个通道，将创建 {total_channels} 个线程\n")

    # Shared counters
    # 使用 (device_index, channel) 作为键
    iteration_counts = {}
    for device_idx in range(num_devices):
        for ch in channels_per_device:
            iteration_counts[(device_idx, ch)] = 0
    
    success_count = 0
    failure_count = 0
    global_count = 0
    count_lock = threading.Lock()

    def worker(device_idx: int, ch: int) -> None:
        """工作线程：控制指定设备的指定通道"""
        nonlocal global_count, success_count, failure_count
        hub = hubs[device_idx]
        
        while running:
            with count_lock:
                if global_count >= total_iterations:
                    break
                global_count += 1
            
            # Turn the channel on and check status
            ok_on = hub.set_channel_power(ch, state=1)
            time.sleep(COMMAND_DELAY)
            hub.get_channel_power_status(ch)
            time.sleep(COMMAND_DELAY)
            # Turn the channel off and check status
            ok_off = hub.set_channel_power(ch, state=0)
            time.sleep(COMMAND_DELAY)
            hub.get_channel_power_status(ch)
            time.sleep(COMMAND_DELAY)
            with count_lock:
                iteration_counts[(device_idx, ch)] += 1
                # Record a success only if both on and off operations were acknowledged
                if ok_on and ok_off:
                    success_count += 1
                else:
                    failure_count += 1

    def progress_printer() -> None:
        """Print progress and success/failure counts once per second."""
        while running:
            time.sleep(1)
            with count_lock:
                current = global_count
                succ = success_count
                fail = failure_count
            print(f"Progress: {current}/{total_iterations} cycles, Success: {succ}, Failure: {fail}")
            if current >= total_iterations:
                break

    # Start worker threads for each channel of each device
    worker_threads = []
    for device_idx in range(num_devices):
        for ch in channels_per_device:
            t = threading.Thread(target=worker, args=(device_idx, ch), daemon=True)
            worker_threads.append(t)
            t.start()

    # Start the progress printer thread
    printer_thread = threading.Thread(target=progress_printer, daemon=True)
    printer_thread.start()

    try:
        # Wait for all worker threads to complete
        for t in worker_threads:
            t.join()
        # Ensure the progress printer has finished
        printer_thread.join()
    except KeyboardInterrupt:
        signal_handler(None, None)

    # Final report
    print(f"\nStress test completed.")
    print(f"Total cycles: {global_count}, Success: {success_count}, Failure: {failure_count}")
    
    # Print per-channel statistics
    print("\nPer-channel statistics:")
    for device_idx in range(num_devices):
        print(f"  Device {device_idx + 1} ({hubs[device_idx].name}):")
        for ch in channels_per_device:
            count = iteration_counts.get((device_idx, ch), 0)
            print(f"    Channel {ch}: {count} cycles")
    
    # Cleanup: turn off all channels
    print("\nTurning off all channels...")
    for hub in hubs:
        try:
            hub.set_channel_power(1, 2, 3, 4, state=0)
        except:
            pass


if __name__ == "__main__":
    # By default run a 10 million cycle stress test
    stress_test()

