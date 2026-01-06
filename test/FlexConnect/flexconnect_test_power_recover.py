import sys
import os
import time

# 添加项目根目录到路径（从test/FlexConnect/到项目根目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2


def main():
    hub = None
    try:
        hub = SmartUSBHub.scan_and_connect()  # Scan and connect to the first SmartUSBHub found
        # hub = SmartUSBHub("/dev/cu.usbmodem132301") # Connect to a specific SmartUSBHub device
        if hub is None:
            print("No SmartUSBHub found")
            sys.exit(1)
        
        device_info = hub.get_device_info()
        print("device info:", device_info)
        
        hub.set_auto_restore(False)

        # hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保断开连接
        if hub is not None:
            try:
                hub.disconnect()
                print("已断开连接")
            except:
                pass

if __name__ == "__main__":
    main()

