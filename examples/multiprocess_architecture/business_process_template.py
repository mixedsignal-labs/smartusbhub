"""
业务进程模板
每个业务进程应该控制一个USB端口，执行自己的测试业务
"""
import sys
import os
import time
from multiprocessing import Queue, Manager, Process

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# 导入客户端代理和服务进程
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_client import SmartUSBHubClient
from smartusbhub_server import server_process_main


def business_process(channel: int, request_queue: Queue, response_dict: dict, process_name: str = None):
    """
    业务进程主函数
    
    Args:
        channel: 控制的USB通道编号（1-4）
        request_queue: 请求队列（与服务进程共享）
        response_dict: 响应字典（与服务进程共享）
        process_name: 进程名称（用于日志）
    """
    if process_name is None:
        process_name = f"BusinessProcess-{channel}"
    
    print(f"[{process_name}] 业务进程启动，控制通道 {channel}")
    
    # 创建客户端代理
    client = SmartUSBHubClient(request_queue, response_dict)
    
    try:
        # 业务逻辑示例：循环开关电源
        iteration = 0
        while True:
            iteration += 1
            print(f"[{process_name}] 迭代 {iteration}: 开启通道 {channel} 电源")
            
            # 开启电源
            success = client.set_channel_power(channel, state=1)
            if not success:
                print(f"[{process_name}] 警告: 开启电源失败")
            else:
                print(f"[{process_name}] 通道 {channel} 电源已开启")
            
            # 获取电源状态
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] 通道 {channel} 电源状态: {status}")
            
            # 等待一段时间
            time.sleep(2)
            
            # 关闭电源
            print(f"[{process_name}] 关闭通道 {channel} 电源")
            success = client.set_channel_power(channel, state=0)
            if not success:
                print(f"[{process_name}] 警告: 关闭电源失败")
            else:
                print(f"[{process_name}] 通道 {channel} 电源已关闭")
            
            # 获取电源状态
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] 通道 {channel} 电源状态: {status}")
            
            # 等待一段时间
            time.sleep(2)
            
            # 示例：只运行10次迭代（可以根据需要修改）
            if iteration >= 10:
                print(f"[{process_name}] 完成 {iteration} 次迭代，退出")
                break
                
    except KeyboardInterrupt:
        print(f"\n[{process_name}] 收到中断信号，正在退出...")
    except Exception as e:
        print(f"[{process_name}] 业务进程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{process_name}] 业务进程已退出")


if __name__ == "__main__":
    # 测试模式：单独运行一个业务进程
    manager = Manager()
    request_queue = Queue()
    response_dict = manager.dict()
    
    # 启动服务进程
    server_process = Process(
        target=server_process_main,
        args=(request_queue, response_dict, None),
        daemon=True
    )
    server_process.start()
    
    # 等待服务进程初始化
    time.sleep(2)
    
    # 运行业务进程
    business_process(1, request_queue, response_dict, "TestBusinessProcess")

