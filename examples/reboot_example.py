# Description: Reboot MCU repeatedly to test reboot functionality
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import os
import time
# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

def main():
    """
    反复重启 MCU 的示例程序
    
    功能：
    1. 扫描并连接设备
    2. 循环执行重启操作
    3. 每次重启后等待设备恢复并重新连接
    4. 显示重启次数和状态
    """
    print("=" * 60)
    print("SmartUSBHub MCU Reboot Test")
    print("=" * 60)
    
    # 扫描并连接设备
    print("\n[1/4] Scanning for SmartUSBHub devices...")
    hub = SmartUSBHub.scan_and_connect()
    # hub = SmartUSBHub("/dev/cu.usbmodem132301")  # 或者直接指定设备路径
    
    if hub is None:
        print("❌ No SmartUSBHub found")
        sys.exit(1)
    
    print("✅ Device connected successfully")
    
    # 获取设备信息
    device_info = hub.get_device_info()
    print(f"📱 Device Info: {device_info}")
    
    # 获取固件版本
    firmware_version = hub.get_firmware_version()
    hardware_version = hub.get_hardware_version()
    print(f"🔧 Firmware Version: {firmware_version}")
    print(f"🔧 Hardware Version: {hardware_version}")
    
    # 配置参数
    reboot_count = 0
    max_reboots = 0  # 最大重启次数，设置为 0 表示无限循环
    reboot_interval = 3.0  # 每次重启后的等待时间（秒）
    reconnect_timeout = 5.0  # 重新连接的超时时间（秒）
    
    print(f"\n[2/4] Configuration:")
    print(f"   - Max reboots: {max_reboots if max_reboots > 0 else 'Infinite'}")
    print(f"   - Reboot interval: {reboot_interval}s")
    print(f"   - Reconnect timeout: {reconnect_timeout}s")
    
    print(f"\n[3/4] Starting reboot test...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            reboot_count += 1
            print(f"\n{'='*60}")
            print(f"Reboot #{reboot_count}")
            print(f"{'='*60}")
            
            # 显示重启前的状态（可选，失败时静默处理）
            print(f"[{time.strftime('%H:%M:%S')}] Before reboot:")
            status = hub.get_channel_power_status(1)
            if status is not None:
                print(f"   Channel 1 power status: {'ON' if status else 'OFF'}")
            # 如果获取失败（返回 None），静默处理，不打印错误
            
            # 执行重启
            print(f"[{time.strftime('%H:%M:%S')}] Sending reboot command...")
            if hub.reboot_mcu():
                print("   ✅ Reboot command sent successfully")
            else:
                print("   ❌ Failed to send reboot command")
                print("   ⚠️  Retrying in 1 second...")
                time.sleep(1)
                continue
            
            # 等待设备重启（MCU 会在约 100ms 后重启）
            print(f"[{time.strftime('%H:%M:%S')}] Waiting for MCU to reboot...")
            time.sleep(0.2)  # 等待 200ms 让 MCU 完成重启
            
            # 断开当前连接
            print(f"[{time.strftime('%H:%M:%S')}] Disconnecting...")
            try:
                hub.disconnect()
            except Exception:
                # 设备可能已经断开，忽略错误
                pass
            
            # 等待设备重新枚举（USB设备重启后需要时间重新枚举）
            print(f"[{time.strftime('%H:%M:%S')}] Waiting for device to re-enumerate...")
            time.sleep(2.0)  # USB设备通常需要1-2秒重新枚举
            
            # 重新创建 hub 实例并连接
            print(f"[{time.strftime('%H:%M:%S')}] Reconnecting to device...")
            hub = None
            
            # 使用 scan_and_connect 重新扫描并连接
            reconnect_start = time.time()
            while time.time() - reconnect_start < reconnect_timeout:
                try:
                    hub = SmartUSBHub.scan_and_connect()
                    if hub is not None:
                        # 验证连接是否正常
                        test_version = hub.get_firmware_version()
                        if test_version is not None:
                            print(f"   ✅ Reconnected successfully")
                            print(f"   🔧 Port: {hub.port}")
                            print(f"   🔧 Firmware version: {test_version}")
                            break
                        else:
                            hub.disconnect()
                            hub = None
                except Exception:
                    pass
                
                time.sleep(0.5)  # 等待 500ms 后重试
            
            if hub is None:
                print(f"   ❌ Failed to reconnect within {reconnect_timeout}s")
                print(f"   💡 Tip: Device may need more time to re-enumerate")
                sys.exit(1)
            
            # 显示重启后的状态（等待设备完全就绪后再获取）
            print(f"[{time.strftime('%H:%M:%S')}] After reboot:")
            # 等待设备完全就绪（给设备一些时间稳定）
            time.sleep(0.3)
            # 尝试获取状态，失败时静默处理
            status = hub.get_channel_power_status(1)
            if status is not None:
                print(f"   Channel 1 power status: {'ON' if status else 'OFF'}")
            # 如果获取失败（返回 None），静默处理，不打印错误
            
            # 检查是否达到最大重启次数
            if max_reboots > 0 and reboot_count >= max_reboots:
                print(f"\n✅ Completed {reboot_count} reboots. Test finished.")
                break
            
            # 等待间隔
            if reboot_count < max_reboots or max_reboots == 0:
                print(f"\n⏳ Waiting {reboot_interval}s before next reboot...")
                time.sleep(reboot_interval)
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user")
        print(f"✅ Total reboots completed: {reboot_count}")
    
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        print(f"\n[4/4] Cleaning up...")
        if hub is not None:
            try:
                hub.disconnect()
                print("✅ Disconnected successfully")
            except (OSError, AttributeError, Exception) as e:
                # 设备可能已经断开，忽略错误
                pass
        
        print(f"\n{'='*60}")
        print(f"Test Summary:")
        print(f"   Total reboots: {reboot_count}")
        print(f"   Status: {'✅ Completed' if reboot_count > 0 else '❌ Failed'}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

