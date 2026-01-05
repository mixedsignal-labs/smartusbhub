"""
SmartUSBHub服务进程
负责管理SmartUSBHub实例，接收来自业务进程的请求并执行USB操作
"""
import sys
import os
import time
import multiprocessing
from multiprocessing import Queue, Manager
import traceback

# 添加父目录到路径，以便导入smartusbhub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
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


class SmartUSBHubServer:
    """SmartUSBHub服务进程类"""
    
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
                    # 从队列获取请求（超时1秒，以便检查running状态）
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
        """
        处理单个请求
        
        Args:
            request: 请求字典，包含request_id, type, args, kwargs
        """
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
                result = self.hub.set_channel_slow_charge(*args)
                
            elif request_type == REQUEST_TYPE_SET_CHANNEL_FAST_CHARGE:
                result = self.hub.set_channel_fast_charge(*args)
                
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


if __name__ == "__main__":
    # 测试模式：直接运行服务进程
    manager = Manager()
    request_queue = Queue()
    response_dict = manager.dict()
    
    server = SmartUSBHubServer(request_queue, response_dict)
    server.start()







