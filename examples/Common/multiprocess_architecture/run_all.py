"""
Main startup script
Start 1 SmartUSBHub service process and 4 business processes
"""
import sys
import os
import time
import signal
from multiprocessing import Process, Manager, Queue

# Add project root to path (from Common/multiprocess_architecture to project root)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Import modules from current directory
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_server import server_process_main
from business_process_1 import main as business_1_main
from business_process_2 import main as business_2_main
from business_process_3 import main as business_3_main
from business_process_4 import main as business_4_main


class ProcessManager:
    """Process manager"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        
    def signal_handler(self, sig, frame):
        """Signal handler function"""
        print("\nInterrupt signal received, closing all processes... / 收到中断信号，正在关闭所有进程...")
        self.running = False
        self.stop_all()
        
    def stop_all(self):
        """Stop all processes"""
        print("[ProcessManager] Stopping all processes... / 正在停止所有进程...")
        for process in self.processes:
            if process.is_alive():
                print(f"[ProcessManager] Terminating process: {process.name} / 终止进程: {process.name}")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    print(f"[ProcessManager] Force killing process: {process.name} / 强制终止进程: {process.name}")
                    process.kill()
                    process.join()
        print("[ProcessManager] All processes stopped / 所有进程已停止")


def main(sleep_after_on: float = 0.1, sleep_after_off: float = 0.1):
    """
    Main function
    
    Args:
        sleep_after_on: Wait time after turning on power (seconds), default 3.0 seconds
        sleep_after_off: Wait time after turning off power (seconds), default 2.0 seconds
    """
    print("=" * 60)
    print("SmartUSBHub Multiprocess Architecture Startup / SmartUSBHub 多进程架构启动")
    print("=" * 60)
    print("Architecture description / 架构说明:")
    print("  - 1 service process: handles all USB operations / 1个服务进程: 负责所有USB操作")
    print("  - 4 business processes: each controls one USB port / 4个业务进程: 每个进程控制一个USB端口")
    print(f"  - Execution interval: wait {sleep_after_on}s after ON, {sleep_after_off}s after OFF / 执行间隔: 开启后等待 {sleep_after_on}秒, 关闭后等待 {sleep_after_off}秒")
    print("=" * 60)
    
    # Create process manager
    manager = ProcessManager()
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # Create shared resources
    shared_manager = Manager()
    request_queue = Queue()
    response_dict = shared_manager.dict()
    
    # Start service process
    print("\n[Main] Starting SmartUSBHub service process... / 启动SmartUSBHub服务进程...")
    server_process = Process(
        target=server_process_main,
        args=(request_queue, response_dict, None),  # None means auto-scan ports
        name="SmartUSBHub-Server"
    )
    server_process.daemon = False
    server_process.start()
    manager.processes.append(server_process)
    
    # Wait for service process initialization
    print("[Main] Waiting for service process initialization... / 等待服务进程初始化...")
    time.sleep(3)
    
    if not server_process.is_alive():
        print("[Main] Error: Service process failed to start / 错误: 服务进程启动失败")
        return
    
    print("[Main] Service process started / 服务进程已启动")
    
    # Start 4 business processes
    print("\n[Main] Starting business processes... / 启动业务进程...")
    business_processes = [
        Process(target=business_1_main, args=(request_queue, response_dict, sleep_after_on, sleep_after_off), name="BusinessProcess-1"),
        Process(target=business_2_main, args=(request_queue, response_dict, sleep_after_on, sleep_after_off), name="BusinessProcess-2"),
        Process(target=business_3_main, args=(request_queue, response_dict, sleep_after_on, sleep_after_off), name="BusinessProcess-3"),
        Process(target=business_4_main, args=(request_queue, response_dict, sleep_after_on, sleep_after_off), name="BusinessProcess-4"),
    ]
    
    for bp in business_processes:
        bp.daemon = False
        bp.start()
        manager.processes.append(bp)
        print(f"[Main] {bp.name} started / {bp.name} 已启动")
        time.sleep(0.5)  # Slightly stagger startup time
    
    print("\n[Main] All processes started / 所有进程已启动")
    print("[Main] Press Ctrl+C to stop all processes / 按 Ctrl+C 停止所有进程\n")
    
    try:
        # Monitor process status
        while manager.running:
            time.sleep(1)
            
            # Check if service process is still running
            if not server_process.is_alive():
                print("[Main] Warning: Service process exited / 警告: 服务进程已退出")
                break
            
            # Check business process status
            dead_processes = [p for p in business_processes if not p.is_alive()]
            if dead_processes:
                for p in dead_processes:
                    print(f"[Main] Warning: {p.name} exited / 警告: {p.name} 已退出")
    
    except KeyboardInterrupt:
        print("\n[Main] Interrupt signal received / 收到中断信号")
    finally:
        # Stop all processes
        manager.stop_all()
        print("\n[Main] Program exited / 程序已退出")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartUSBHub multiprocess architecture startup script / SmartUSBHub 多进程架构启动脚本')
    parser.add_argument('--sleep-after-on', type=float, default=3.0,
                        help='Wait time after turning on power (seconds), default 3.0 seconds / 开启电源后的等待时间（秒），默认3.0秒')
    parser.add_argument('--sleep-after-off', type=float, default=2.0,
                        help='Wait time after turning off power (seconds), default 2.0 seconds / 关闭电源后的等待时间（秒），默认2.0秒')
    
    args = parser.parse_args()
    main(sleep_after_on=args.sleep_after_on, sleep_after_off=args.sleep_after_off)


