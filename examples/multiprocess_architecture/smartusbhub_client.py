"""
SmartUSBHub客户端代理
提供与SmartUSBHub相同的API接口，但通过进程间通信调用服务进程
"""
import sys
import os
import time
import uuid
from multiprocessing import Queue, Manager
from typing import Optional, Dict, Any

# 添加父目录到路径，以便导入smartusbhub（仅用于类型提示）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class SmartUSBHubClient:
    """
    SmartUSBHub客户端代理类
    提供与SmartUSBHub相同的API接口，但通过进程间通信调用服务进程
    """
    
    def __init__(self, request_queue: Queue, response_dict: Dict, timeout: float = 5.0):
        """
        初始化客户端
        
        Args:
            request_queue: 请求队列，用于发送请求到服务进程
            response_dict: 共享字典，用于接收服务进程的响应
            timeout: 请求超时时间（秒）
        """
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.timeout = timeout
        self._pending_requests = {}  # 用于跟踪待处理的请求
        
    def _send_request(self, request_type: str, args: tuple = (), kwargs: dict = None) -> Any:
        """
        发送请求到服务进程并等待响应
        
        Args:
            request_type: 请求类型
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            服务进程返回的结果
            
        Raises:
            TimeoutError: 如果请求超时
            RuntimeError: 如果服务进程返回错误
        """
        if kwargs is None:
            kwargs = {}
            
        # 生成唯一的请求ID
        request_id = str(uuid.uuid4())
        
        # 构造请求
        request = {
            'request_id': request_id,
            'type': request_type,
            'args': args,
            'kwargs': kwargs
        }
        
        # 发送请求
        self.request_queue.put(request)
        
        # 等待响应
        start_time = time.time()
        while True:
            if request_id in self.response_dict:
                # 收到响应
                response = self.response_dict.pop(request_id)
                if response['success']:
                    return response['result']
                else:
                    raise RuntimeError(f"服务进程错误: {response.get('error', '未知错误')}")
            
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"请求超时: {request_type}")
            
            time.sleep(0.01)  # 避免CPU占用过高
    
    def set_channel_power(self, *channels, state):
        """
        设置USB通道的电源状态
        
        Args:
            *channels: 通道编号（1-4）
            state: 1表示开启，0表示关闭
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_power', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_power 失败: {e}")
            return False
    
    def get_channel_power_status(self, *channels):
        """
        获取USB通道的电源状态
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            dict或int或None: 通道状态字典，或单个通道的状态值，或None（如果超时）
        """
        try:
            return self._send_request('get_channel_power_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_power_status 失败: {e}")
            return None
    
    def set_channel_usb2_dataline(self, *channels, state):
        """
        设置USB2数据线状态
        
        Args:
            *channels: 通道编号（1-4）
            state: 1表示启用，0表示禁用
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_usb2_dataline', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_usb2_dataline 失败: {e}")
            return False
    
    def get_channel_usb2_dataline_status(self, *channels):
        """
        获取USB2数据线状态
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            dict或None: 数据线状态字典，或None（如果超时）
        """
        try:
            return self._send_request('get_channel_usb2_dataline_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_usb2_dataline_status 失败: {e}")
            return None
    
    def set_channel_usb3_dataline(self, *channels, state):
        """
        设置USB3数据线状态
        
        Args:
            *channels: 通道编号（1-4）
            state: 1表示启用，0表示禁用
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_usb3_dataline', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_usb3_dataline 失败: {e}")
            return False
    
    def get_channel_usb3_dataline_status(self, *channels):
        """
        获取USB3数据线状态
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            dict或None: USB3数据线状态字典，或None（如果超时）
        """
        try:
            return self._send_request('get_channel_usb3_dataline_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_usb3_dataline_status 失败: {e}")
            return None
    
    def get_channel_voltage(self, channel):
        """
        获取通道电压
        
        Args:
            channel: 通道编号（1-4）
            
        Returns:
            float或None: 电压值（V），或None（如果超时）
        """
        try:
            return self._send_request('get_channel_voltage', args=(channel,))
        except Exception as e:
            print(f"[Client] get_channel_voltage 失败: {e}")
            return None
    
    def get_channel_current(self, channel):
        """
        获取通道电流
        
        Args:
            channel: 通道编号（1-4）
            
        Returns:
            float或None: 电流值（A），或None（如果超时）
        """
        try:
            return self._send_request('get_channel_current', args=(channel,))
        except Exception as e:
            print(f"[Client] get_channel_current 失败: {e}")
            return None
    
    def set_channel_low_current(self, *channels, state):
        """
        设置通道低电流模式
        
        Args:
            *channels: 通道编号（1-4）
            state: 1表示启用，0表示禁用
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_low_current', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_low_current 失败: {e}")
            return False
    
    def get_channel_low_current_status(self, *channels):
        """
        获取通道低电流模式状态
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            dict或None: 低电流模式状态字典，或None（如果超时）
        """
        try:
            return self._send_request('get_channel_low_current_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_low_current_status 失败: {e}")
            return None
    
    def shutdown(self):
        """请求服务进程关闭"""
        try:
            self._send_request('shutdown')
        except Exception as e:
            print(f"[Client] shutdown 失败: {e}")


