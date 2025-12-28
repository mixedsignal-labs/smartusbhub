"""
SmartUSBHub 多进程支持模块（可选）

提供多进程架构支持，解决多进程访问串口时的ACK错误问题。

使用方式：
    from smartusbhub import SmartUSBHub
    from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient, SmartUSBHubServer
    
    # 或者
    from smartusbhub.smartusbhub_multiprocess import *
"""

import time
import uuid
import traceback
from multiprocessing import Queue, Manager
from typing import Optional, Dict, Any

# 导入主模块
from smartusbhub import SmartUSBHub

# 请求类型定义
REQUEST_TYPE_SET_CHANNEL_POWER = 'set_channel_power'
REQUEST_TYPE_GET_CHANNEL_POWER_STATUS = 'get_channel_power_status'
REQUEST_TYPE_SET_CHANNEL_USB2_DATALINE = 'set_channel_usb2_dataline'
REQUEST_TYPE_GET_CHANNEL_USB2_DATALINE_STATUS = 'get_channel_usb2_dataline_status'
REQUEST_TYPE_SET_CHANNEL_USB3_DATALINE = 'set_channel_usb3_dataline'
REQUEST_TYPE_GET_CHANNEL_USB3_DATALINE_STATUS = 'get_channel_usb3_dataline_status'
REQUEST_TYPE_GET_CHANNEL_VOLTAGE = 'get_channel_voltage'
REQUEST_TYPE_GET_CHANNEL_CURRENT = 'get_channel_current'
REQUEST_TYPE_SET_CHANNEL_SLOW_CHARGE = 'set_channel_slow_charge'
REQUEST_TYPE_SET_CHANNEL_FAST_CHARGE = 'set_channel_fast_charge'
REQUEST_TYPE_GET_CHANNEL_CHARGE_MODE = 'get_channel_charge_mode'
REQUEST_TYPE_SHUTDOWN = 'shutdown'


class SmartUSBHubClient:
    """
    SmartUSBHub客户端代理类
    
    提供与SmartUSBHub相同的API接口，但通过进程间通信调用服务进程。
    适用于多进程场景，避免多进程直接访问串口导致的ACK错误。
    
    示例：
        from multiprocessing import Queue, Manager
        from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient
        
        request_queue = Queue()
        response_dict = Manager().dict()
        
        client = SmartUSBHubClient(request_queue, response_dict)
        client.set_channel_power(1, state=1)
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
        self._pending_requests = {}
        
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
        """设置USB通道的电源状态"""
        try:
            return self._send_request('set_channel_power', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_power 失败: {e}")
            return False
    
    def get_channel_power_status(self, *channels):
        """获取USB通道的电源状态"""
        try:
            return self._send_request('get_channel_power_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_power_status 失败: {e}")
            return None
    
    def set_channel_usb2_dataline(self, *channels, state):
        """设置USB2数据线状态"""
        try:
            return self._send_request('set_channel_usb2_dataline', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_usb2_dataline 失败: {e}")
            return False
    
    def get_channel_usb2_dataline_status(self, *channels):
        """获取USB2数据线状态"""
        try:
            return self._send_request('get_channel_usb2_dataline_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_usb2_dataline_status 失败: {e}")
            return None
    
    def set_channel_usb3_dataline(self, *channels, state):
        """设置USB3数据线状态"""
        try:
            return self._send_request('set_channel_usb3_dataline', args=channels, kwargs={'state': state})
        except Exception as e:
            print(f"[Client] set_channel_usb3_dataline 失败: {e}")
            return False
    
    def get_channel_usb3_dataline_status(self, *channels):
        """获取USB3数据线状态"""
        try:
            return self._send_request('get_channel_usb3_dataline_status', args=channels)
        except Exception as e:
            print(f"[Client] get_channel_usb3_dataline_status 失败: {e}")
            return None
    
    def get_channel_voltage(self, channel):
        """获取通道电压"""
        try:
            return self._send_request('get_channel_voltage', args=(channel,))
        except Exception as e:
            print(f"[Client] get_channel_voltage 失败: {e}")
            return None
    
    def get_channel_current(self, channel):
        """获取通道电流"""
        try:
            return self._send_request('get_channel_current', args=(channel,))
        except Exception as e:
            print(f"[Client] get_channel_current 失败: {e}")
            return None
    
    def set_channel_slow_charge(self, *channels, disconnect_before_switch=False):
        """
        设置通道慢充模式（限流）
        
        Args:
            *channels: 通道号
            disconnect_before_switch: 如果为True，在启用慢充前断开通道3秒。默认为True。
        """
        try:
            return self._send_request('set_channel_slow_charge', args=channels, kwargs={'disconnect_before_switch': disconnect_before_switch})
        except Exception as e:
            print(f"[Client] set_channel_slow_charge 失败: {e}")
            return False
    
    def set_channel_fast_charge(self, *channels, disconnect_before_switch=True):
        """
        设置通道快充模式（全功率）
        
        Args:
            *channels: 通道号
            disconnect_before_switch: 如果为True，在启用快充前断开通道1秒。默认为True。
        """
        try:
            return self._send_request('set_channel_fast_charge', args=channels, kwargs={'disconnect_before_switch': disconnect_before_switch})
        except Exception as e:
            print(f"[Client] set_channel_fast_charge 失败: {e}")
            return False
    
    def get_channel_charge_mode(self, *channels):
        """获取通道充电模式状态"""
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


class SmartUSBHubServer:
    """
    SmartUSBHub服务进程类
    
    负责管理SmartUSBHub实例，接收来自业务进程的请求并执行USB操作。
    所有USB操作都在此进程中串行执行，避免多进程竞争导致的ACK错误。
    
    示例：
        from multiprocessing import Queue, Manager, Process
        from smartusbhub.smartusbhub_multiprocess import SmartUSBHubServer
        
        request_queue = Queue()
        response_dict = Manager().dict()
        
        server = SmartUSBHubServer(request_queue, response_dict)
        server_process = Process(target=server.start)
        server_process.start()
    """
    
    def __init__(self, request_queue, response_dict, port=None):
        """
        初始化服务进程
        
        Args:
            request_queue: 请求队列，用于接收业务进程的请求
            response_dict: 共享字典，用于返回响应结果
            port: 串口名称，如果为None则自动扫描
        """
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.port = port
        self.hub = None
        self.running = True
        
    def start(self):
        """启动服务进程"""
        print("[Server] 正在初始化SmartUSBHub...")
        
        try:
            # 连接SmartUSBHub
            if self.port:
                self.hub = SmartUSBHub(self.port)
            else:
                self.hub = SmartUSBHub.scan_and_connect()
            
            if self.hub is None:
                print("[Server] 错误: 无法找到或连接SmartUSBHub设备")
                return False
                
            print(f"[Server] SmartUSBHub已连接: {self.hub.port}")
            print(f"[Server] 硬件版本: V1.{self.hub.hardware_version}")
            print(f"[Server] 固件版本: V1.{self.hub.firmware_version}")
            print("[Server] 服务进程已启动，等待请求...")
            
            # 主循环：处理请求
            while self.running:
                try:
                    # 从队列获取请求
                    if not self.request_queue.empty():
                        request = self.request_queue.get(timeout=0.1)
                        self._handle_request(request)
                    else:
                        time.sleep(0.01)  # 避免CPU占用过高
                        
                except Exception as e:
                    print(f"[Server] 处理请求时出错: {e}")
                    traceback.print_exc()
                    
        except KeyboardInterrupt:
            print("\n[Server] 收到中断信号，正在关闭...")
        except Exception as e:
            print(f"[Server] 服务进程出错: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()
            
        return True
    
    def _handle_request(self, request):
        """处理单个请求"""
        request_id = request.get('request_id')
        request_type = request.get('type')
        args = request.get('args', ())
        kwargs = request.get('kwargs', {})
        
        if request_id is None or request_type is None:
            print(f"[Server] 无效的请求: {request}")
            return
        
        try:
            result = None
            error = None
            
            # 根据请求类型执行相应的操作
            if request_type == REQUEST_TYPE_SET_CHANNEL_POWER:
                result = self.hub.set_channel_power(*args, **kwargs)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_POWER_STATUS:
                result = self.hub.get_channel_power_status(*args)
            elif request_type == REQUEST_TYPE_SET_CHANNEL_USB2_DATALINE:
                result = self.hub.set_channel_usb2_dataline(*args, **kwargs)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_USB2_DATALINE_STATUS:
                result = self.hub.get_channel_usb2_dataline_status(*args)
            elif request_type == REQUEST_TYPE_SET_CHANNEL_USB3_DATALINE:
                result = self.hub.set_channel_usb3_dataline(*args, **kwargs)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_USB3_DATALINE_STATUS:
                result = self.hub.get_channel_usb3_dataline_status(*args)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_VOLTAGE:
                result = self.hub.get_channel_voltage(*args)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_CURRENT:
                result = self.hub.get_channel_current(*args)
            elif request_type == REQUEST_TYPE_SET_CHANNEL_SLOW_CHARGE:
                result = self.hub.set_channel_slow_charge(*args, **kwargs)
            elif request_type == REQUEST_TYPE_SET_CHANNEL_FAST_CHARGE:
                result = self.hub.set_channel_fast_charge(*args, **kwargs)
            elif request_type == REQUEST_TYPE_GET_CHANNEL_CHARGE_MODE:
                result = self.hub.get_channel_charge_mode(*args)
            elif request_type == REQUEST_TYPE_SHUTDOWN:
                self.running = False
                result = True
            else:
                error = f"未知的请求类型: {request_type}"
                print(f"[Server] {error}")
            
            # 将结果写入共享字典
            self.response_dict[request_id] = {
                'success': error is None,
                'result': result,
                'error': error
            }
            
        except Exception as e:
            error_msg = f"执行请求时出错: {str(e)}"
            print(f"[Server] {error_msg}")
            traceback.print_exc()
            self.response_dict[request_id] = {
                'success': False,
                'result': None,
                'error': error_msg
            }
    
    def cleanup(self):
        """清理资源"""
        print("[Server] 正在清理资源...")
        if self.hub:
            try:
                self.hub.disconnect()
            except:
                pass
        print("[Server] 服务进程已退出")


def server_process_main(request_queue, response_dict, port=None):
    """
    服务进程主函数（用于multiprocessing.Process）
    
    Args:
        request_queue: 请求队列
        response_dict: 响应字典
        port: 串口名称
    """
    server = SmartUSBHubServer(request_queue, response_dict, port)
    server.start()


# 导出主要类和函数
__all__ = [
    'SmartUSBHubClient',
    'SmartUSBHubServer',
    'server_process_main',
    'REQUEST_TYPE_SET_CHANNEL_POWER',
    'REQUEST_TYPE_GET_CHANNEL_POWER_STATUS',
    'REQUEST_TYPE_SET_CHANNEL_USB2_DATALINE',
    'REQUEST_TYPE_GET_CHANNEL_USB2_DATALINE_STATUS',
    'REQUEST_TYPE_SET_CHANNEL_USB3_DATALINE',
    'REQUEST_TYPE_GET_CHANNEL_USB3_DATALINE_STATUS',
    'REQUEST_TYPE_GET_CHANNEL_VOLTAGE',
    'REQUEST_TYPE_GET_CHANNEL_CURRENT',
    'REQUEST_TYPE_SET_CHANNEL_SLOW_CHARGE',
    'REQUEST_TYPE_SET_CHANNEL_FAST_CHARGE',
    'REQUEST_TYPE_GET_CHANNEL_CHARGE_MODE',
    'REQUEST_TYPE_SHUTDOWN',
]

