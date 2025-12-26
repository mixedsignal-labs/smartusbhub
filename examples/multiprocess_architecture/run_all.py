"""
主启动脚本
启动1个SmartUSBHub服务进程和4个业务进程
"""
import sys
import os
import time
import signal
from multiprocessing import Process, Manager, Queue

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# 导入当前目录的模块
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_server import server_process_main
from business_process_1 import main as business_1_main
from business_process_2 import main as business_2_main
from business_process_3 import main as business_3_main
from business_process_4 import main as business_4_main


class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        
    def signal_handler(self, sig, frame):
        """信号处理函数"""
        print("\n收到中断信号，正在关闭所有进程...")
        self.running = False
        self.stop_all()
        
    def stop_all(self):
        """停止所有进程"""
        print("[ProcessManager] 正在停止所有进程...")
        for process in self.processes:
            if process.is_alive():
                print(f"[ProcessManager] 终止进程: {process.name}")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    print(f"[ProcessManager] 强制终止进程: {process.name}")
                    process.kill()
                    process.join()
        print("[ProcessManager] 所有进程已停止")


def main(sleep_after_on: float = 0.1, sleep_after_off: float = 0.1):
    """
    主函数
    
    Args:
        sleep_after_on: 开启电源后的等待时间（秒），默认3.0秒
        sleep_after_off: 关闭电源后的等待时间（秒），默认2.0秒
    """
    print("=" * 60)
    print("SmartUSBHub 多进程架构启动")
    print("=" * 60)
    print("架构说明:")
    print("  - 1个服务进程: 负责所有USB操作")
    print("  - 4个业务进程: 每个进程控制一个USB端口")
    print(f"  - 执行间隔: 开启后等待 {sleep_after_on}秒, 关闭后等待 {sleep_after_off}秒")
    print("=" * 60)
    
    # 创建进程管理器
    manager = ProcessManager()
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # 创建共享资源
    shared_manager = Manager()
    request_queue = Queue()
    response_dict = shared_manager.dict()
    
    # 启动服务进程
    print("\n[Main] 启动SmartUSBHub服务进程...")
    server_process = Process(
        target=server_process_main,
        args=(request_queue, response_dict, None),  # None表示自动扫描端口
        name="SmartUSBHub-Server"
    )
    server_process.daemon = False
    server_process.start()
    manager.processes.append(server_process)
    
    # 等待服务进程初始化
    print("[Main] 等待服务进程初始化...")
    time.sleep(3)
    
    if not server_process.is_alive():
        print("[Main] 错误: 服务进程启动失败")
        return
    
    print("[Main] 服务进程已启动")
    
    # 启动4个业务进程
    print("\n[Main] 启动业务进程...")
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
        print(f"[Main] {bp.name} 已启动")
        time.sleep(0.5)  # 稍微错开启动时间
    
    print("\n[Main] 所有进程已启动")
    print("[Main] 按 Ctrl+C 停止所有进程\n")
    
    try:
        # 监控进程状态
        while manager.running:
            time.sleep(1)
            
            # 检查服务进程是否还在运行
            if not server_process.is_alive():
                print("[Main] 警告: 服务进程已退出")
                break
            
            # 检查业务进程状态
            dead_processes = [p for p in business_processes if not p.is_alive()]
            if dead_processes:
                for p in dead_processes:
                    print(f"[Main] 警告: {p.name} 已退出")
    
    except KeyboardInterrupt:
        print("\n[Main] 收到中断信号")
    finally:
        # 停止所有进程
        manager.stop_all()
        print("\n[Main] 程序已退出")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartUSBHub 多进程架构启动脚本')
    parser.add_argument('--sleep-after-on', type=float, default=3.0,
                        help='开启电源后的等待时间（秒），默认3.0秒')
    parser.add_argument('--sleep-after-off', type=float, default=2.0,
                        help='关闭电源后的等待时间（秒），默认2.0秒')
    
    args = parser.parse_args()
    main(sleep_after_on=args.sleep_after_on, sleep_after_off=args.sleep_after_off)

