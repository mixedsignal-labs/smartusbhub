"""
Business process template
Each business process should control one USB port and execute its own test business
"""
import sys
import os
import time
from multiprocessing import Queue, Manager, Process

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# Import client proxy and service process
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_client import SmartUSBHubClient
from smartusbhub_server import server_process_main


def business_process(channel: int, request_queue: Queue, response_dict: dict, process_name: str = None):
    """
    Business process main function
    
    Args:
        channel: USB channel number to control (1-4)
        request_queue: Request queue (shared with service process)
        response_dict: Response dictionary (shared with service process)
        process_name: Process name (for logging)
    """
    if process_name is None:
        process_name = f"BusinessProcess-{channel}"
    
    print(f"[{process_name}] Business process started, controlling channel {channel} / 业务进程启动，控制通道 {channel}")
    
    # Create client proxy
    client = SmartUSBHubClient(request_queue, response_dict)
    
    try:
        # Business logic example: cycle power on/off
        iteration = 0
        while True:
            iteration += 1
            print(f"[{process_name}] Iteration {iteration}: Turn on channel {channel} power / 迭代 {iteration}: 开启通道 {channel} 电源")
            
            # Turn on power
            success = client.set_channel_power(channel, state=1)
            if not success:
                print(f"[{process_name}] Warning: Failed to turn on power / 警告: 开启电源失败")
            else:
                print(f"[{process_name}] Channel {channel} power turned on / 通道 {channel} 电源已开启")
            
            # Get power status
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] Channel {channel} power status: {status} / 通道 {channel} 电源状态: {status}")
            
            # Wait for a while
            time.sleep(2)
            
            # Turn off power
            print(f"[{process_name}] Turn off channel {channel} power / 关闭通道 {channel} 电源")
            success = client.set_channel_power(channel, state=0)
            if not success:
                print(f"[{process_name}] Warning: Failed to turn off power / 警告: 关闭电源失败")
            else:
                print(f"[{process_name}] Channel {channel} power turned off / 通道 {channel} 电源已关闭")
            
            # Get power status
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] Channel {channel} power status: {status} / 通道 {channel} 电源状态: {status}")
            
            # Wait for a while
            time.sleep(2)
            
            # Example: only run 10 iterations (can be modified as needed)
            if iteration >= 10:
                print(f"[{process_name}] Completed {iteration} iterations, exiting / 完成 {iteration} 次迭代，退出")
                break
                
    except KeyboardInterrupt:
        print(f"\n[{process_name}] Interrupt signal received, exiting... / 收到中断信号，正在退出...")
    except Exception as e:
        print(f"[{process_name}] Business process error: {e} / 业务进程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{process_name}] Business process exited / 业务进程已退出")


if __name__ == "__main__":
    # Test mode: run a single business process
    manager = Manager()
    request_queue = Queue()
    response_dict = manager.dict()
    
    # Start service process
    server_process = Process(
        target=server_process_main,
        args=(request_queue, response_dict, None),
        daemon=True
    )
    server_process.start()
    
    # Wait for service process initialization
    time.sleep(2)
    
    # Run business process
    business_process(1, request_queue, response_dict, "TestBusinessProcess")


