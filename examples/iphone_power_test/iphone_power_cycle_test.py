# Description: iPhone功耗循环测试demo
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import time
import threading
from datetime import datetime
from collections import deque
import os

# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# 导入图表模块
from battery_plotter import BatteryPlotter

# 尝试导入蓝牙库
try:
    from bleak import BleakScanner, BleakClient
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False
    try:
        import bluepy.btle as btle
        HAS_BLUEPY = True
    except ImportError:
        HAS_BLUEPY = False

class iPhoneBatteryMonitor:
    """iPhone电量监控类"""
    
    # 蓝牙Battery Service UUID
    BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
    BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, channel=1, device_name=None, device_uuid=None):
        """
        初始化iPhone电量监控
        
        Args:
            channel: 连接的通道号（1-4）
            device_name: iPhone设备名称（用于蓝牙扫描，如果为None则自动扫描）
            device_uuid: iPhone蓝牙MAC地址/UUID（直接连接，优先级高于device_name）
        """
        self.channel = channel
        self.device_name = device_name
        self.device_uuid = device_uuid  # 蓝牙MAC地址/UUID
        
        # 蓝牙相关
        self.ble_client = None
        self.device_address = device_uuid  # 如果提供了UUID，直接使用
        self.cached_device_address = None  # 缓存已找到的设备地址，避免重复扫描
        self.last_scan_time = 0  # 上次扫描时间
        self.scan_cache_duration = 30  # 扫描缓存有效期（秒）
        
    def get_battery_level(self):
        """
        获取iPhone电量百分比
        
        Returns:
            int: 电量百分比（0-100），如果无法获取则返回None
        """
        # 通过蓝牙Battery Service获取电量
        try:
            # 使用bleak库（推荐，跨平台）
            if HAS_BLEAK:
                return self._get_battery_via_bleak()
            # 使用bluepy库（Linux）
            elif HAS_BLUEPY:
                return self._get_battery_via_bluepy()
            else:
                if not hasattr(self, '_no_ble_library_warning'):
                    print("\n[警告] 未安装蓝牙库")
                    print("  请安装以下任一库:")
                    print("  pip install bleak  # 推荐，跨平台")
                    print("  或")
                    print("  pip install bluepy  # Linux")
                    self._no_ble_library_warning = True
                return None
        except Exception as e:
            if not hasattr(self, '_ble_error_shown'):
                print(f"[错误] 蓝牙获取电量失败: {e}")
                self._ble_error_shown = True
            return None
    
    def _get_battery_via_bleak(self):
        """使用bleak库通过蓝牙获取电量，自动重试直到找到设备"""
        import asyncio
        import time
        
        async def _scan_and_connect():
            current_time = time.time()
            max_retries = 10  # 最大重试次数（实际上会一直重试）
            retry_count = 0
            
            while True:  # 持续重试直到找到设备
                # 如果已缓存设备地址且在有效期内，先尝试直接连接（避免重复扫描）
                if self.cached_device_address and (current_time - self.last_scan_time) < self.scan_cache_duration:
                    try:
                        # 静默尝试连接，不打印太多信息
                        client = BleakClient(self.cached_device_address)
                        await client.connect()
                        
                        try:
                            services = client.services
                            service_uuids = [str(s.uuid) for s in services]
                            
                            if self.BATTERY_SERVICE_UUID in service_uuids:
                                battery_data = await client.read_gatt_char(self.BATTERY_LEVEL_UUID)
                                battery_level = int(battery_data[0])
                                if 0 <= battery_level <= 100:
                                    # 连接成功，更新缓存时间
                                    self.last_scan_time = time.time()
                                    return battery_level
                        finally:
                            await client.disconnect()
                    except Exception:
                        # 连接失败，清除缓存，准备重新扫描
                        self.cached_device_address = None
                        self.last_scan_time = 0
                
                # 需要扫描设备（蓝牙广播有间隔，需要足够长的扫描时间）
                scan_timeout = 15.0  # 始终使用较长的扫描时间，确保能找到设备
                devices = await BleakScanner.discover(timeout=scan_timeout)
                retry_count += 1
                
                # 查找目标设备
                target_device = None
                
                if self.device_uuid:
                    # 如果提供了UUID，查找匹配的设备
                    uuid_lower = self.device_uuid.lower().replace('-', '').replace(':', '')
                    for device in devices:
                        device_addr = str(device.address).lower().replace('-', '').replace(':', '')
                        # 匹配UUID（支持完整UUID或部分匹配）
                        if uuid_lower in device_addr or device_addr in uuid_lower:
                            target_device = device
                            break
                    
                    if not target_device:
                        # 未找到设备，继续循环重试（不返回None）
                        continue
                elif self.device_name:
                    # 如果指定了设备名称，精确匹配
                    for device in devices:
                        if device.name and self.device_name.lower() in device.name.lower():
                            target_device = device
                            break
                    
                    if not target_device:
                        # 未找到设备，继续循环重试（不返回None）
                        continue
                else:
                    # 否则查找第一个包含"iPhone"或"iphone"的设备
                    for device in devices:
                        if device.name and ('iphone' in device.name.lower()):
                            target_device = device
                            break
                    
                    if not target_device:
                        # 未找到设备，继续循环重试（不返回None）
                        continue
                
                # 连接设备并读取电池电量
                # 使用设备地址连接（更稳定，避免事件循环问题）
                try:
                    # 使用设备地址创建客户端（避免事件循环问题）
                    client = BleakClient(target_device.address)
                    await client.connect()
                    
                    try:
                        # 获取服务（新版本bleak使用services属性）
                        services = client.services
                        service_uuids = [str(s.uuid) for s in services]
                        
                        if self.BATTERY_SERVICE_UUID in service_uuids:
                            battery_data = await client.read_gatt_char(self.BATTERY_LEVEL_UUID)
                            battery_level = int(battery_data[0])
                            if 0 <= battery_level <= 100:
                                # 清除警告标志
                                if hasattr(self, '_no_device_warning'):
                                    delattr(self, '_no_device_warning')
                                if hasattr(self, '_uuid_not_found_warning'):
                                    delattr(self, '_uuid_not_found_warning')
                                # 缓存设备地址和时间戳，避免下次重新扫描（蓝牙广播有间隔）
                                self.cached_device_address = target_device.address
                                self.last_scan_time = time.time()
                                return battery_level
                        else:
                            # 设备不支持Battery Service，静默处理
                            if not hasattr(self, '_no_battery_service_warning'):
                                self._no_battery_service_warning = True
                    finally:
                        await client.disconnect()
                except Exception as e:
                    # 连接失败，清除缓存，继续循环重试
                    self.cached_device_address = None
                    self.last_scan_time = 0
                    # 不返回None，继续循环重试
                    continue
        
        # 运行异步函数
        return asyncio.run(_scan_and_connect())
    
    def _get_battery_via_bluepy(self):
        """使用bluepy库通过蓝牙获取电量（Linux）"""
        target_addr = None
        
        # 如果提供了UUID，直接使用
        if self.device_uuid:
            target_addr = self.device_uuid
        else:
            # 否则扫描设备
            scanner = btle.Scanner()
            devices = scanner.scan(5.0)  # 扫描5秒
            
            # 查找iPhone设备
            if self.device_name:
                for device in devices:
                    if device.getValueText(9):  # Complete Local Name
                        name = device.getValueText(9)
                        if self.device_name.lower() in name.lower():
                            target_addr = device.addr
                            break
            else:
                for device in devices:
                    name = device.getValueText(9) or ""
                    if 'iphone' in name.lower():
                        target_addr = device.addr
                        break
            
            if not target_addr:
                # 未找到设备，静默返回None（会在主循环中继续重试）
                if not hasattr(self, '_no_device_warning'):
                    self._no_device_warning = True
                return None
        
        # 连接并读取
        try:
            client = btle.Peripheral(target_addr)
            battery_service = client.getServiceByUUID(self.BATTERY_SERVICE_UUID)
            battery_char = battery_service.getCharacteristics(self.BATTERY_LEVEL_UUID)[0]
            battery_level = int(battery_char.read()[0])
            client.disconnect()
            
            if 0 <= battery_level <= 100:
                if hasattr(self, '_no_device_warning'):
                    delattr(self, '_no_device_warning')
                return battery_level
        except Exception as e:
            # 连接失败，静默返回None（会在主循环中继续重试）
            if not hasattr(self, '_connection_error_shown'):
                self._connection_error_shown = True
            return None
        
        return None

def iphone_power_cycle_test(hub, channel=1, check_interval=5, device_name=None, device_uuid=None):
    """
    iPhone功耗循环测试
    
    Args:
        hub: SmartUSBHub实例
        channel: 连接的通道号（1-4）
        check_interval: 电量检查间隔（秒）
        device_name: iPhone设备名称（用于蓝牙扫描）
        device_uuid: iPhone蓝牙MAC地址/UUID（直接连接，优先级高于device_name）
    """
    monitor = iPhoneBatteryMonitor(channel=channel, device_name=device_name, device_uuid=device_uuid)
    
    # 充电模式状态
    # 初始化为慢充模式（因为main函数中初始设置为慢充）
    current_charge_mode = 'slow'  # 'fast', 'slow'
    low_battery_threshold = 10  # 低电量阈值（%）
    full_battery_threshold = 100  # 满电阈值（%）
    
    # 初始化时获取一次实际通道状态，确保current_charge_mode正确
    charge_mode_result = hub.get_channel_charge_mode(channel)
    if charge_mode_result and channel in charge_mode_result:
        actual_mode = charge_mode_result[channel]
        if actual_mode == 1:
            current_charge_mode = 'fast'
        elif actual_mode == 2:
            current_charge_mode = 'slow'
    
    # 数据存储（用于绘图）
    timestamps = deque(maxlen=1000)  # 最多保存1000个数据点
    battery_levels = deque(maxlen=1000)
    charge_modes = deque(maxlen=1000)  # 记录充电模式
    
    print("=" * 60)
    print("iPhone功耗循环测试")
    print("=" * 60)
    print(f"通道: {channel}")
    print(f"低电量阈值: {low_battery_threshold}%")
    print(f"满电阈值: {full_battery_threshold}%")
    print(f"检查间隔: {check_interval}秒")
    print("=" * 60)
    print("\n循环逻辑:")
    print(f"  - 电量 <= {low_battery_threshold}%: 切换到全速充电模式")
    print(f"  - 电量 >= {full_battery_threshold}%: 切换到保持连接模式")
    print("\n时间统计:")
    print(f"  - 记录从高电量到{low_battery_threshold}%的放电时间")
    print(f"  - 记录从{low_battery_threshold}%到{full_battery_threshold}%的充电时间")
    print("\n按 Ctrl+C 停止测试\n")
    
    # 初始化图表绘制器
    plotter = BatteryPlotter()
    plotter.setup_plot(timestamps, battery_levels, charge_modes)
    
    cycle_count = 0
    last_battery_level = None
    
    # 时间统计
    discharge_start_time = None  # 开始放电的时间（从100%或高电量开始）
    charge_start_time = None     # 开始充电的时间（从10%开始）
    last_charge_mode = None      # 上一次的充电模式，用于检测模式切换
    
    try:
        while True:
            # 获取当前电量（会自动重试直到找到设备）
            battery_level = monitor.get_battery_level()
            
            # 如果返回None，说明还在重试中，等待后继续（get_battery_level内部会自动重试直到找到设备）
            if battery_level is None:
                time.sleep(check_interval)
                continue
            
            # 记录数据点
            current_time = datetime.now()
            timestamps.append(current_time)
            battery_levels.append(battery_level)
            charge_modes.append(current_charge_mode or 'none')
            
            # 显示电量变化（带完整时间戳）
            timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            if last_battery_level is not None and battery_level != last_battery_level:
                change = battery_level - last_battery_level
                change_str = f"(+{change})" if change > 0 else f"({change})"
                print(f"[{timestamp_str}] 电量: {battery_level}% {change_str}", end="")
            else:
                print(f"[{timestamp_str}] 电量: {battery_level}%", end="")
            
            # 根据电量决定充电模式
            if battery_level <= low_battery_threshold:
                # 低电量（<=10%）：切换到快充
                if current_charge_mode != 'fast':
                    print(f" -> [{timestamp_str}] 切换到全速充电模式（电量达到{low_battery_threshold}%）")
                    success = hub.set_channel_fast_charge(channel, disconnect_before_switch=True)
                    if success:
                        current_charge_mode = 'fast'
                        cycle_count += 1
                        
                        # 记录开始充电的时间
                        if charge_start_time is None:
                            charge_start_time = current_time
                            print(f"  [{timestamp_str}] [循环 #{cycle_count}] 开始充电计时")
                        
                        # 如果之前正在放电，计算放电时间
                        if discharge_start_time is not None:
                            discharge_duration = current_time - discharge_start_time
                            hours = int(discharge_duration.total_seconds() // 3600)
                            minutes = int((discharge_duration.total_seconds() % 3600) // 60)
                            seconds = int(discharge_duration.total_seconds() % 60)
                            print(f"  [{timestamp_str}] ⏱️  放电时间: {hours:02d}:{minutes:02d}:{seconds:02d} (从高电量到{low_battery_threshold}%)")
                            discharge_start_time = None
                        
                        print(f"  [{timestamp_str}] [循环 #{cycle_count}] 全速充电模式已启用")
                    else:
                        print(f"  [{timestamp_str}] [错误] 切换到全速充电模式失败")
                else:
                    print(" [全速充电]")
                    
            elif battery_level >= full_battery_threshold:
                # 满电（>=100%）：切换到慢充
                if current_charge_mode != 'slow':
                    print(f" -> [{timestamp_str}] 切换到保持连接模式（电量达到{full_battery_threshold}%）")
                    success = hub.set_channel_slow_charge(channel, disconnect_before_switch=False)
                    if success:
                        current_charge_mode = 'slow'
                        
                        # 记录开始放电的时间
                        if discharge_start_time is None:
                            discharge_start_time = current_time
                            print(f"  [{timestamp_str}] [循环 #{cycle_count}] 开始放电计时")
                        
                        # 如果之前正在充电，计算充电时间
                        if charge_start_time is not None:
                            charge_duration = current_time - charge_start_time
                            hours = int(charge_duration.total_seconds() // 3600)
                            minutes = int((charge_duration.total_seconds() % 3600) // 60)
                            seconds = int(charge_duration.total_seconds() % 60)
                            print(f"  [{timestamp_str}] ⏱️  充电时间: {hours:02d}:{minutes:02d}:{seconds:02d} (从{low_battery_threshold}%到{full_battery_threshold}%)")
                            charge_start_time = None
                        
                        print(f"  [{timestamp_str}] [循环 #{cycle_count}] 保持连接模式已启用")
                    else:
                        print(f"  [{timestamp_str}] [错误] 切换到保持连接模式失败")
                else:
                    print(" [保持连接]")
            else:
                # 中等电量：保持当前模式，显示当前状态
                if current_charge_mode == 'fast':
                    print(" [全速充电]")
                elif current_charge_mode == 'slow':
                    print(" [保持连接]")
                else:
                    # 如果current_charge_mode意外为None，尝试获取实际通道状态
                    charge_mode_result = hub.get_channel_charge_mode(channel)
                    if charge_mode_result and channel in charge_mode_result:
                        actual_mode = charge_mode_result[channel]
                        if actual_mode == 1:
                            current_charge_mode = 'fast'
                            print(" [全速充电]")
                        elif actual_mode == 2:
                            current_charge_mode = 'slow'
                            print(" [保持连接]")
                        else:
                            # 如果状态为0（关闭），默认显示保持连接
                            current_charge_mode = 'slow'
                            print(" [保持连接]")
                    else:
                        # 如果获取失败，使用默认值（保持连接）
                        current_charge_mode = 'slow'
                        print(" [保持连接]")
            
            last_battery_level = battery_level
            last_charge_mode = current_charge_mode
            
            # 等待下次检查（分段sleep，期间处理Qt事件）
            elapsed = 0
            while elapsed < check_interval:
                sleep_time = min(0.1, check_interval - elapsed)  # 每次最多sleep 0.1秒
                time.sleep(sleep_time)
                elapsed += sleep_time
                # 在处理过程中也更新Qt事件，避免界面卡顿
                plotter.update()
            
    except KeyboardInterrupt:
        print("\n\n测试已停止")
        print(f"总共完成 {cycle_count} 个充电循环")
        
        # 保持图表窗口打开
        plotter.close(keep_open=True)
    except Exception as e:
        print(f"\n[错误] 发生异常: {e}")
        import traceback
        traceback.print_exc()
        plotter.close(keep_open=False)

def main():
    """主函数"""
    # 扫描可用设备
    hub_list = SmartUSBHub.scan_available_ports()
    print("可用设备:", hub_list)
    
    # 连接设备
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("未找到SmartUSBHub设备")
        sys.exit(1)
    
    # 显示设备信息
    device_info = hub.get_device_info()
    print("\n设备信息:", device_info)
    
    # 询问用户配置
    print("\n" + "=" * 60)
    print("配置测试参数")
    print("=" * 60)
    
    # 首先检查是否可以获取真实电量（通过蓝牙）
    print("\n正在检查iPhone蓝牙连接状态...")
    print("请确保iPhone蓝牙已开启并在附近")
    
    # 询问设备UUID或名称（UUID优先级更高）
    device_uuid_input = input("请输入iPhone蓝牙UUID/MAC地址（留空则使用设备名称扫描）: ").strip()
    device_uuid = device_uuid_input if device_uuid_input else None
    
    device_name_input = None
    if not device_uuid:
        device_name_input = input("请输入iPhone设备名称（留空自动扫描）: ").strip()
    device_name = device_name_input if device_name_input else None
    
    test_monitor = iPhoneBatteryMonitor(device_name=device_name, device_uuid=device_uuid)
    test_battery = test_monitor.get_battery_level()
    
    if test_battery is not None:
        print(f"✓ 成功通过蓝牙检测到iPhone，当前电量: {test_battery}%")
    else:
        print("✗ 无法通过蓝牙获取电量")
        print("\n可能的原因:")
        print("  1. iPhone蓝牙未开启")
        print("  2. iPhone不在蓝牙范围内")
        print("  3. 未安装蓝牙库（bleak或bluepy）")
        print("\n建议:")
        print("  - 确保iPhone蓝牙已开启")
        print("  - 确保iPhone在附近（蓝牙范围内）")
        print("  - 安装蓝牙库: pip install bleak")
        print("\n程序将继续运行，但会持续尝试连接设备...")
    
    # 选择通道
    try:
        channel_input = input("\n请输入通道号 (1-4，默认1): ").strip()
        channel = int(channel_input) if channel_input else 1
        if channel < 1 or channel > 4:
            print("无效的通道号，使用默认值1")
            channel = 1
    except ValueError:
        print("无效输入，使用默认值1")
        channel = 1
    
    # 检查间隔
    try:
        interval_input = input("电量检查间隔（秒，默认5）: ").strip()
        check_interval = float(interval_input) if interval_input else 5.0
        if check_interval < 1:
            check_interval = 1.0
    except ValueError:
        check_interval = 5.0
    
    # 首先用快充模式让电脑识别到设备
    print(f"\n正在开启通道 {channel}...")
    hub.set_channel_power(channel, state=1)
    time.sleep(1)

    # 初始设置为慢充模式
    print("初始设置为慢充模式...")
    hub.set_channel_slow_charge(channel, disconnect_before_switch=False)
    time.sleep(1)
    
    # 开始测试
    print("\n开始测试...\n")
    iphone_power_cycle_test(
        hub=hub,
        channel=channel,
        check_interval=check_interval,
        device_name=device_name,
        device_uuid=device_uuid
    )
    
    # 清理
    print("\n正在断开连接...")
    hub.disconnect()

if __name__ == "__main__":
    main()

