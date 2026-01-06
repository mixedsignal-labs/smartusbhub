"""
SmartUSBHub client proxy
Provides the same API interface as SmartUSBHub, but calls service process through inter-process communication
"""
import sys
import os
import time
import uuid
from multiprocessing import Queue, Manager
from typing import Optional, Dict, Any

# Add parent directory to path to import smartusbhub (only for type hints)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class SmartUSBHubClient:
    """
    SmartUSBHub client proxy class
    Provides the same API interface as SmartUSBHub, but calls service process through inter-process communication
    """
    
    def __init__(self, request_queue: Queue, response_dict: Dict, timeout: float = 5.0):
        """
        Initialize client
        
        Args:
            request_queue: Request queue for sending requests to service process
            response_dict: Shared dictionary for receiving responses from service process
            timeout: Request timeout (seconds)
        """
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.timeout = timeout
        self._pending_requests = {}  # Track pending requests
        
    def _send_request(self, request_type: str, args: tuple = (), kwargs: dict = None) -> Any:
        """
        Send request to service process and wait for response
        
        Args:
            request_type: Request type
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Result returned by service process
            
        Raises:
            TimeoutError: If request times out
            RuntimeError: If service process returns error
        """
        if kwargs is None:
            kwargs = {}
            
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Construct request
        request = {
            'request_id': request_id,
            'type': request_type,
            'args': args,
            'kwargs': kwargs
        }
        
        # Send request
        self.request_queue.put(request)
        
        # Wait for response
        start_time = time.time()
        while True:
            if request_id in self.response_dict:
                # Response received
                response = self.response_dict.pop(request_id)
                if response['success']:
                    return response['result']
                else:
                    raise RuntimeError(f"Service process error: {response.get('error', 'Unknown error')} / 服务进程错误: {response.get('error', '未知错误')}")
            
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Request timeout: {request_type} / 请求超时: {request_type}")
            
            time.sleep(0.01)  # Avoid high CPU usage
    
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
    
    def set_channel_slow_charge(self, *channels):
        """
        设置通道慢充模式（限流）
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_slow_charge', args=channels)
        except Exception as e:
            print(f"[Client] set_channel_slow_charge 失败: {e}")
            return False
    
    def set_channel_fast_charge(self, *channels):
        """
        设置通道快充模式（全功率）
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            return self._send_request('set_channel_fast_charge', args=channels)
        except Exception as e:
            print(f"[Client] set_channel_fast_charge 失败: {e}")
            return False
    
    def get_channel_charge_mode(self, *channels):
        """
        获取通道充电模式状态
        
        Args:
            *channels: 通道编号（1-4）
            
        Returns:
            dict或None: 充电模式状态字典（0=off, 1=fast_charge, 2=slow_charge），或None（如果超时）
        """
        try:
            return self._send_request('get_channel_charge_mode', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_charge_mode 失败: {e}")
            return None
    
    def shutdown(self):
        """请求服务进程关闭"""
        try:
            self._send_request('shutdown')
        except Exception as e:
            print(f"[Client] shutdown 失败: {e}")









