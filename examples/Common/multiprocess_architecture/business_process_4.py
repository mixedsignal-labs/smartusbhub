"""
业务进程4 - 控制USB端口4
"""
import sys
import os
import time
from multiprocessing import Queue, Manager

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# 导入客户端代理
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_client import SmartUSBHubClient


def main(request_queue: Queue, response_dict: dict, sleep_after_on: float = 3.0, sleep_after_off: float = 2.0):
    """
    业务进程4主函数 - 控制通道4
    
    Args:
        request_queue: 请求队列（与服务进程共享）
        response_dict: 响应字典（与服务进程共享）
        sleep_after_on: 开启电源后的等待时间（秒），默认3.0秒
        sleep_after_off: 关闭电源后的等待时间（秒），默认2.0秒
    """
    process_name = "BusinessProcess-4"
    channel = 4
    
    print(f"[{process_name}] 业务进程启动，控制通道 {channel}")
    
    # 创建客户端代理
    client = SmartUSBHubClient(request_queue, response_dict)
    
    try:
        # 业务逻辑：循环开关电源并监控状态
        iteration = 0
        while True:
            iteration += 1
            print(f"[{process_name}] ===== 迭代 {iteration} =====")
            
            # 开启电源
            print(f"[{process_name}] 开启通道 {channel} 电源")
            success = client.set_channel_power(channel, state=1)
            if success:
                print(f"[{process_name}] ✓ 通道 {channel} 电源已开启")
            else:
                print(f"[{process_name}] ✗ 开启电源失败")
            
            # 获取电源状态
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] 通道 {channel} 电源状态: {status}")
            
            # 获取电压和电流
            voltage = client.get_channel_voltage(channel)
            current = client.get_channel_current(channel)
            if voltage is not None:
                print(f"[{process_name}] 通道 {channel} 电压: {voltage:.2f}V")
            if current is not None:
                print(f"[{process_name}] 通道 {channel} 电流: {current:.3f}A")
            
            time.sleep(sleep_after_on)
            
            # 关闭电源
            print(f"[{process_name}] 关闭通道 {channel} 电源")
            success = client.set_channel_power(channel, state=0)
            if success:
                print(f"[{process_name}] ✓ 通道 {channel} 电源已关闭")
            else:
                print(f"[{process_name}] ✗ 关闭电源失败")
            
            # 获取电源状态
            status = client.get_channel_power_status(channel)
            print(f"[{process_name}] 通道 {channel} 电源状态: {status}")
            
            time.sleep(sleep_after_off)
            
    except KeyboardInterrupt:
        print(f"\n[{process_name}] 收到中断信号，正在退出...")
    except Exception as e:
        print(f"[{process_name}] 业务进程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{process_name}] 业务进程已退出")


if __name__ == "__main__":
    # 测试模式：需要先启动服务进程
    print("请使用 run_all.py 来启动所有进程")


