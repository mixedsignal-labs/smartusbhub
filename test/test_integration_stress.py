"""
简化压力测试 - 只测试核心功能

测试内容：
1. 多通道设置电源
2. 获取电源状态
3. 设置数据线
4. 获取数据线状态

使用方法:
    # 运行压力测试
    pytest test/test_integration_stress.py -v

    # 显示详细日志
    pytest test/test_integration_stress.py -v -s --log-cli-level=INFO
"""
import pytest
import time
import logging
import sys
import os

# 在源码仓库中，需要将项目根目录添加到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 测试次数配置 ====================
STRESS_TEST_TOTAL_COUNT = 100


def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{int(seconds // 60)}分{seconds % 60:.0f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分{seconds % 60:.0f}秒"


# 用于控制进度刷新频率
_last_update_time = {}

def print_progress(current, total, success_count, failure_count, start_time, end_line=False):
    """打印进度信息（每秒刷新一次）"""
    global _last_update_time
    
    key = id(start_time)
    now = time.time()
    
    # 如果不是结束且距离上次刷新不足1秒，则跳过
    if not end_line:
        last_time = _last_update_time.get(key, 0)
        if last_time > 0 and now - last_time < 1.0:
            return
        _last_update_time[key] = now
    
    elapsed = now - start_time
    progress = (current / total * 100) if total > 0 else 0
    rate = current / elapsed if elapsed > 0 else 0
    remaining = (total - current) / rate if rate > 0 else 0
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    
    msg = (f"进度: {current}/{total} ({progress:.1f}%), "
           f"成功: {success_count}, 失败: {failure_count}, "
           f"成功率: {success_rate:.1f}%, "
           f"已用: {format_time(elapsed)}, 速度: {rate:.1f}次/秒, "
           f"预计剩余: {format_time(remaining) if remaining > 0 else '0秒'}")
    
    sys.stderr.write(f"\r{msg}" + ("\n" if end_line else ""))
    sys.stderr.flush()
    
    if end_line and key in _last_update_time:
        del _last_update_time[key]


def check_dataline_support(hub):
    """检查设备是否支持数据线切换"""
    try:
        product_type = hub.product_type
        if product_type is None:
            product_type = hub.get_product_type()
        
        from smartusbhub import PRODUCT_TYPE_TABLE
        product_info = PRODUCT_TYPE_TABLE.get(product_type) if product_type is not None else None
        
        if product_info:
            return (product_info.get("enable_usb2_data_switch") or 
                   product_info.get("enable_usb3_data_switch"))
    except:
        pass
    return False


def test_stress_core_functions(hub, max_channels):
    """
    压力测试：核心功能循环测试
    
    测试内容：
    1. 多通道设置电源
    2. 获取电源状态
    3. 设置数据线（如果支持）
    4. 获取数据线状态（如果支持）
    """
    channels = list(range(1, max_channels + 1))
    logger.info(f"压力测试：核心功能循环测试（{max_channels}个通道）{channels}...")
    
    # 检查是否支持数据线切换
    supports_dataline = check_dataline_support(hub)
    if supports_dataline:
        logger.info("  设备支持数据线切换，将测试数据线功能")
    else:
        logger.info("  设备不支持数据线切换，将跳过数据线测试")
    
    # 初始化：关闭所有通道
    hub.set_channel_power(*channels, state=0)
    if supports_dataline:
        hub.set_channel_usb2_dataline(*channels, state=0)
    time.sleep(0.2)
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    logger.info("=" * 70)
    logger.info(f"测试总次数: {total_operations:,} 次")
    logger.info(f"每次循环包含: 设置电源、获取电源" + ("、设置数据线、获取数据线" if supports_dataline else ""))
    logger.info("=" * 70)
    
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示
    print_progress(0, total_operations, 0, 0, start_time)
    
    power_state = 0
    dataline_state = 0
    
    try:
        for i in range(total_operations):
            cycle_success = True
            
            # 1. 设置电源（反转状态）
            power_state = 1 - power_state
            set_power_result = hub.set_channel_power(*channels, state=power_state)
            if not set_power_result:
                cycle_success = False
                logger.warning(f"  第 {i+1} 次循环：设置电源失败")
            
            # 2. 获取电源状态
            try:
                power_status = hub.get_channel_power_status(*channels)
                if power_status is None:
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取电源状态失败（返回None）")
                else:
                    # 验证所有通道状态是否正确
                    if isinstance(power_status, dict):
                        for ch in channels:
                            if power_status.get(ch) != power_state:
                                cycle_success = False
                                logger.warning(f"  第 {i+1} 次循环：通道 {ch} 电源状态不一致，期望 {power_state}，实际 {power_status.get(ch)}")
                    else:
                        # 单通道返回int
                        if power_status != power_state:
                            cycle_success = False
                            logger.warning(f"  第 {i+1} 次循环：电源状态不一致，期望 {power_state}，实际 {power_status}")
            except Exception as e:
                cycle_success = False
                logger.warning(f"  第 {i+1} 次循环：获取电源状态异常: {e}")
            
            # 3. 设置数据线（如果支持）
            if supports_dataline:
                dataline_state = 1 - dataline_state
                set_dataline_result = hub.set_channel_usb2_dataline(*channels, state=dataline_state)
                if not set_dataline_result:
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置数据线失败")
                
                # 4. 获取数据线状态
                try:
                    dataline_status = hub.get_channel_usb2_dataline_status(*channels)
                    if dataline_status is None:
                        cycle_success = False
                        logger.warning(f"  第 {i+1} 次循环：获取数据线状态失败（返回None）")
                    else:
                        # 验证所有通道状态是否正确
                        if isinstance(dataline_status, dict):
                            for ch in channels:
                                if dataline_status.get(ch) != dataline_state:
                                    cycle_success = False
                                    logger.warning(f"  第 {i+1} 次循环：通道 {ch} 数据线状态不一致，期望 {dataline_state}，实际 {dataline_status.get(ch)}")
                        else:
                            # 单通道返回int
                            if dataline_status != dataline_state:
                                cycle_success = False
                                logger.warning(f"  第 {i+1} 次循环：数据线状态不一致，期望 {dataline_state}，实际 {dataline_status}")
                except Exception as e:
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取数据线状态异常: {e}")
            
            if cycle_success:
                success_count += 1
            else:
                failure_count += 1
            
            # 更新进度
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
            
            # 短暂延迟，避免过快
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n[WARNING] 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次循环")
        raise
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"  总循环次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {format_time(elapsed_time)}")
    logger.info(f"  循环频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  [PASS] 核心功能压力测试通过，成功率 {success_rate:.1f}%")
    
    # 清理：关闭所有通道
    logger.info("正在清理设备状态...")
    try:
        hub.set_channel_power(*channels, state=0)
        if supports_dataline:
            hub.set_channel_usb2_dataline(*channels, state=0)
        time.sleep(0.2)
    except Exception as e:
        logger.warning(f"清理设备状态时出错: {e}")
    
    # 恢复出厂设置，还原设备配置
    logger.info("正在恢复出厂设置...")
    try:
        result = hub.factory_reset()
        if result:
            logger.info("[OK] 设备已恢复出厂设置")
            time.sleep(0.5)  # 等待设备重置完成
        else:
            logger.warning("[WARNING] 恢复出厂设置失败（未收到ACK）")
    except Exception as e:
        logger.warning(f"[WARNING] 恢复出厂设置时出错: {e}")
