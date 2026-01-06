"""
SmartUSBHub service process
Manages SmartUSBHub instances, receives requests from business processes and executes USB operations
"""
import sys
import os
import time
import multiprocessing
from multiprocessing import Queue, Manager
import traceback

# Add parent directory to path to import smartusbhub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from smartusbhub import SmartUSBHub

# Request type definitions
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
    """SmartUSBHub service process class"""
    
    def __init__(self, request_queue, response_dict, port=None):
        """
        Initialize service process
        
        Args:
            request_queue: Request queue for receiving requests from business processes
            response_dict: Shared dictionary for returning response results
            port: Serial port name, if None then auto-scan
        """
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.port = port
        self.hub = None
        self.running = True
        
    def start(self):
        """Start service process"""
        print("[Server] Initializing SmartUSBHub... / 正在初始化SmartUSBHub...")
        
        try:
            # Connect SmartUSBHub
            if self.port:
                self.hub = SmartUSBHub(self.port)
            else:
                self.hub = SmartUSBHub.scan_and_connect()
            
            if self.hub is None:
                print("[Server] Error: Unable to find or connect SmartUSBHub device / 错误: 无法找到或连接SmartUSBHub设备")
                return False
                
            print(f"[Server] SmartUSBHub connected: {self.hub.port} / SmartUSBHub已连接: {self.hub.port}")
            print(f"[Server] Hardware version: V1.{self.hub.hardware_version} / 硬件版本: V1.{self.hub.hardware_version}")
            print(f"[Server] Firmware version: V1.{self.hub.firmware_version} / 固件版本: V1.{self.hub.firmware_version}")
            print("[Server] Service process started, waiting for requests... / 服务进程已启动，等待请求...")
            
            # Main loop: process requests
            while self.running:
                try:
                    # Get request from queue (timeout 1 second to check running status)
                    if not self.request_queue.empty():
                        request = self.request_queue.get(timeout=0.1)
                        self._handle_request(request)
                    else:
                        time.sleep(0.01)  # Avoid high CPU usage
                        
                except Exception as e:
                    print(f"[Server] Error processing request: {e} / 处理请求时出错: {e}")
                    traceback.print_exc()
                    
        except KeyboardInterrupt:
            print("\n[Server] Interrupt signal received, closing... / 收到中断信号，正在关闭...")
        except Exception as e:
            print(f"[Server] Service process error: {e} / 服务进程出错: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()
            
        return True
    
    def _handle_request(self, request):
        """
        Handle a single request
        
        Args:
            request: Request dictionary containing request_id, type, args, kwargs
        """
        request_id = request.get('request_id')
        request_type = request.get('type')
        args = request.get('args', ())
        kwargs = request.get('kwargs', {})
        
        if request_id is None or request_type is None:
            print(f"[Server] Invalid request: {request} / 无效的请求: {request}")
            return
        
        try:
            result = None
            error = None
            
            # Execute corresponding operation based on request type
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
                error = f"Unknown request type: {request_type} / 未知的请求类型: {request_type}"
                print(f"[Server] {error}")
            
            # Write result to shared dictionary
            self.response_dict[request_id] = {
                'success': error is None,
                'result': result,
                'error': error
            }
            
        except Exception as e:
            error_msg = f"Error executing request: {str(e)} / 执行请求时出错: {str(e)}"
            print(f"[Server] {error_msg}")
            traceback.print_exc()
            self.response_dict[request_id] = {
                'success': False,
                'result': None,
                'error': error_msg
            }
    
    def cleanup(self):
        """Clean up resources"""
        print("[Server] Cleaning up resources... / 正在清理资源...")
        if self.hub:
            try:
                self.hub.disconnect()
            except:
                pass
        print("[Server] Service process exited / 服务进程已退出")


def server_process_main(request_queue, response_dict, port=None):
    """
    Service process main function (for multiprocessing.Process)
    
    Args:
        request_queue: Request queue
        response_dict: Response dictionary
        port: Serial port name
    """
    server = SmartUSBHubServer(request_queue, response_dict, port)
    server.start()


if __name__ == "__main__":
    # Test mode: run service process directly
    manager = Manager()
    request_queue = Queue()
    response_dict = manager.dict()
    
    server = SmartUSBHubServer(request_queue, response_dict)
    server.start()









