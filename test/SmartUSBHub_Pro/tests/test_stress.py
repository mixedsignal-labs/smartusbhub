"""
核心功能压力测试 - 通过大量重复操作验证设备稳定性

测试内容：
1. 多通道设置电源
2. 获取电源状态
3. 设置数据线
4. 获取数据线状态

使用方法:
    # 运行压力测试
    pytest test/test_stress_core.py -v

    # 显示详细日志
    pytest test/test_stress_core.py -v -s --log-cli-level=INFO
"""
import pytest
import time
import logging
import sys
import os

# 尝试导入pytest_html用于在HTML报告中添加额外信息
try:
    import pytest_html
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

# 在源码仓库中，需要将项目根目录添加到路径（从产品子目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 测试次数配置 ====================
STRESS_TEST_TOTAL_COUNT = 500000


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


def generate_stats_html(stats, op_names, supports_usb2, supports_usb3, 
                       total_operations, success_count, failure_count, 
                       success_rate, elapsed_time, ops_per_sec,
                       hardware_version=None, firmware_version=None, serial_no=None):
    """生成用于HTML报告的统计信息表格"""
    html = '<div style="margin: 20px 0;">'
    html += '<h3>压力测试详细统计</h3>'
    
    # 设备信息
    html += '<div style="margin-bottom: 20px;">'
    html += '<h4>设备信息</h4>'
    html += '<table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">'
    html += '<tr style="background-color: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">项目</th><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">数值</th></tr>'
    
    hw_version_str = f"V1.{hardware_version}" if hardware_version is not None else "未知"
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">硬件版本</td><td style="border: 1px solid #ddd; padding: 8px;">{hw_version_str}</td></tr>'
    
    fw_version_str = f"V1.{firmware_version}" if firmware_version is not None else "未知"
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">固件版本</td><td style="border: 1px solid #ddd; padding: 8px;">{fw_version_str}</td></tr>'
    
    serial_str = serial_no if serial_no is not None else "未知"
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">序列号</td><td style="border: 1px solid #ddd; padding: 8px;">{serial_str}</td></tr>'
    html += '</table>'
    html += '</div>'
    
    # 总体统计
    html += '<div style="margin-bottom: 20px;">'
    html += '<h4>总体统计</h4>'
    html += '<table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">'
    html += '<tr style="background-color: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">项目</th><th style="border: 1px solid #ddd; padding: 8px; text-align: right;">数值</th></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总循环次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_operations:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总成功次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: green;">{success_count:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总失败次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: red;">{failure_count:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总成功率</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold;">{success_rate:.2f}%</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总耗时</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format_time(elapsed_time)}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">循环频率</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{ops_per_sec:.2f} 次/秒</td></tr>'
    html += '</table>'
    html += '</div>'
    
    # 详细操作统计
    html += '<div>'
    html += '<h4>每个操作的详细统计</h4>'
    html += '<table style="border-collapse: collapse; width: 100%;">'
    html += '<tr style="background-color: #f0f0f0;">'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">操作</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">失败次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">总次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功率</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">平均用时</th>'
    html += '</tr>'
    
    for op_key, op_name in op_names.items():
        # 只显示实际执行的操作
        if op_key.startswith('usb2') and not supports_usb2:
            continue
        if op_key.startswith('usb3') and not supports_usb3:
            continue
        
        stat = stats[op_key]
        total_op = stat['success'] + stat['failure']
        if total_op > 0:
            op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
            avg_time = (stat['total_time'] / total_op * 1000) if total_op > 0 else 0  # 转换为毫秒
            success_color = 'green' if op_success_rate >= 95 else 'orange' if op_success_rate >= 80 else 'red'
            html += '<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{op_name}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: green;">{stat["success"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: red;">{stat["failure"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_op:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; color: {success_color};">{op_success_rate:.2f}%</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{avg_time:.2f} ms</td>'
            html += '</tr>'
        else:
            html += '<tr style="color: #999;">'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{op_name}</td>'
            html += '<td colspan="5" style="border: 1px solid #ddd; padding: 8px; text-align: center;">未执行</td>'
            html += '</tr>'
    
    html += '</table>'
    html += '</div>'
    html += '</div>'
    
    return html


def check_dataline_support(hub):
    """检查设备是否支持数据线切换，返回 (usb2_support, usb3_support)"""
    try:
        product_type = hub.product_type
        if product_type is None:
            product_type = hub.get_product_type()
        
        from smartusbhub import PRODUCT_TYPE_TABLE
        product_info = PRODUCT_TYPE_TABLE.get(product_type) if product_type is not None else None
        
        if product_info:
            usb2_support = product_info.get("enable_usb2_data_switch", False)
            usb3_support = product_info.get("enable_usb3_data_switch", False)
            return (usb2_support, usb3_support)
    except:
        pass
    return (False, False)


def validate_multi_channel_response(status, channels, expected_value, status_name="状态"):
    """
    验证多通道返回值的完整性和正确性
    
    Args:
        status: 返回值（可能是dict或int）
        channels: 请求的通道列表
        expected_value: 期望的值
        status_name: 状态名称（用于错误信息）
    
    Returns:
        (is_valid, error_msg): (是否有效, 错误信息)
    """
    if status is None:
        return (False, f"返回值为None")
    
    # 单通道情况
    if len(channels) == 1:
        if not isinstance(status, int):
            return (False, f"单通道应返回int，实际返回{type(status).__name__}")
        if status != expected_value:
            return (False, f"值不正确，期望{expected_value}，实际{status}")
        return (True, None)
    
    # 多通道情况
    if not isinstance(status, dict):
        return (False, f"多通道应返回dict，实际返回{type(status).__name__}")
    
    # 检查返回的通道数量
    if len(status) != len(channels):
        return (False, f"返回通道数量不正确，期望{len(channels)}个，实际{len(status)}个")
    
    # 检查是否包含所有请求的通道
    missing_channels = [ch for ch in channels if ch not in status]
    if missing_channels:
        return (False, f"缺少通道: {missing_channels}")
    
    # 检查是否有多余的通道
    extra_channels = [ch for ch in status.keys() if ch not in channels]
    if extra_channels:
        return (False, f"包含多余通道: {extra_channels}")
    
    # 检查每个通道的值是否正确
    for ch in channels:
        if ch not in status:
            return (False, f"通道{ch}缺失")
        value = status[ch]
        if not isinstance(value, int):
            return (False, f"通道{ch}的值类型不正确，期望int，实际{type(value).__name__}")
        if value != expected_value:
            return (False, f"通道{ch}的值不正确，期望{expected_value}，实际{value}")
    
    return (True, None)


def test_stress_core_functions(hub, max_channels, request):
    """
    压力测试：核心功能循环测试
    
    测试内容：
    1. 多通道设置电源
    2. 获取电源状态
    3. 设置USB2数据线（如果支持）
    4. 获取USB2数据线状态（如果支持）
    5. 设置USB3数据线（如果支持）
    6. 获取USB3数据线状态（如果支持）
    """
    channels = list(range(1, max_channels + 1))
    logger.info(f"压力测试：核心功能循环测试（{max_channels}个通道）{channels}...")
    
    # 获取设备信息（用于在报告中显示）
    hardware_version = hub.hardware_version
    firmware_version = hub.firmware_version
    serial_no = hub.serial_no
    
    # 检查是否支持数据线切换
    supports_usb2, supports_usb3 = check_dataline_support(hub)
    if supports_usb2:
        logger.info("  设备支持USB2数据线切换，将测试USB2数据线功能")
    if supports_usb3:
        logger.info("  设备支持USB3数据线切换，将测试USB3数据线功能")
    if not supports_usb2 and not supports_usb3:
        logger.info("  设备不支持数据线切换，将跳过数据线测试")
    
    # 初始化：关闭所有通道
    hub.set_channel_power(*channels, state=0)
    if supports_usb2:
        hub.set_channel_usb2_dataline(*channels, state=0)
    if supports_usb3:
        hub.set_channel_usb3_dataline(*channels, state=0)
    time.sleep(0.2)
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    logger.info("=" * 70)
    logger.info(f"测试总次数: {total_operations:,} 次")
    dataline_desc = []
    if supports_usb2:
        dataline_desc.append("USB2数据线")
    if supports_usb3:
        dataline_desc.append("USB3数据线")
    dataline_str = "、".join(dataline_desc) if dataline_desc else ""
    logger.info(f"每次循环包含: 设置电源、获取电源" + (f"、设置{dataline_str}、获取{dataline_str}" if dataline_str else ""))
    logger.info("=" * 70)
    
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 详细统计：每个操作的成功、失败次数和用时
    # 每个操作统计：success, failure, total_time, count
    stats = {
        'set_power': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'get_power': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'set_usb2_dataline': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'get_usb2_dataline': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'set_usb3_dataline': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'get_usb3_dataline': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
    }
    
    # 初始化进度显示
    print_progress(0, total_operations, 0, 0, start_time)
    
    power_state = 0
    usb2_dataline_state = 0
    usb3_dataline_state = 0
    
    try:
        for i in range(total_operations):
            cycle_success = True
            
            # 1. 设置电源（反转状态）- 记录用时
            power_state = 1 - power_state
            stats['set_power']['count'] += 1
            set_power_start = time.time()
            set_power_result = hub.set_channel_power(*channels, state=power_state)
            set_power_elapsed = time.time() - set_power_start
            stats['set_power']['total_time'] += set_power_elapsed
            
            if set_power_result:
                stats['set_power']['success'] += 1
            else:
                stats['set_power']['failure'] += 1
                cycle_success = False
                logger.warning(f"  第 {i+1} 次循环：设置电源失败")
            
            # 2. 获取电源状态 - 记录用时
            stats['get_power']['count'] += 1
            get_power_start = time.time()
            try:
                power_status = hub.get_channel_power_status(*channels)
                get_power_elapsed = time.time() - get_power_start
                stats['get_power']['total_time'] += get_power_elapsed
                
                is_valid, error_msg = validate_multi_channel_response(
                    power_status, channels, power_state, "电源状态"
                )
                if is_valid:
                    stats['get_power']['success'] += 1
                else:
                    stats['get_power']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取电源状态验证失败 - {error_msg}")
            except Exception as e:
                get_power_elapsed = time.time() - get_power_start
                stats['get_power']['total_time'] += get_power_elapsed
                stats['get_power']['failure'] += 1
                cycle_success = False
                logger.warning(f"  第 {i+1} 次循环：获取电源状态异常: {e}")
            
            # 3. 设置USB2数据线（如果支持）- 记录用时
            if supports_usb2:
                usb2_dataline_state = 1 - usb2_dataline_state
                stats['set_usb2_dataline']['count'] += 1
                set_usb2_start = time.time()
                set_usb2_result = hub.set_channel_usb2_dataline(*channels, state=usb2_dataline_state)
                set_usb2_elapsed = time.time() - set_usb2_start
                stats['set_usb2_dataline']['total_time'] += set_usb2_elapsed
                
                if set_usb2_result:
                    stats['set_usb2_dataline']['success'] += 1
                else:
                    stats['set_usb2_dataline']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置USB2数据线失败")
                
                # 4. 获取USB2数据线状态 - 记录用时
                stats['get_usb2_dataline']['count'] += 1
                get_usb2_start = time.time()
                try:
                    usb2_status = hub.get_channel_usb2_dataline_status(*channels)
                    get_usb2_elapsed = time.time() - get_usb2_start
                    stats['get_usb2_dataline']['total_time'] += get_usb2_elapsed
                    
                    is_valid, error_msg = validate_multi_channel_response(
                        usb2_status, channels, usb2_dataline_state, "USB2数据线状态"
                    )
                    if is_valid:
                        stats['get_usb2_dataline']['success'] += 1
                    else:
                        stats['get_usb2_dataline']['failure'] += 1
                        cycle_success = False
                        logger.warning(f"  第 {i+1} 次循环：获取USB2数据线状态验证失败 - {error_msg}")
                except Exception as e:
                    get_usb2_elapsed = time.time() - get_usb2_start
                    stats['get_usb2_dataline']['total_time'] += get_usb2_elapsed
                    stats['get_usb2_dataline']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取USB2数据线状态异常: {e}")
            
            # 5. 设置USB3数据线（如果支持）- 记录用时
            if supports_usb3:
                usb3_dataline_state = 1 - usb3_dataline_state
                stats['set_usb3_dataline']['count'] += 1
                set_usb3_start = time.time()
                set_usb3_result = hub.set_channel_usb3_dataline(*channels, state=usb3_dataline_state)
                set_usb3_elapsed = time.time() - set_usb3_start
                stats['set_usb3_dataline']['total_time'] += set_usb3_elapsed
                
                if set_usb3_result:
                    stats['set_usb3_dataline']['success'] += 1
                else:
                    stats['set_usb3_dataline']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置USB3数据线失败")
                
                # 6. 获取USB3数据线状态 - 记录用时
                stats['get_usb3_dataline']['count'] += 1
                get_usb3_start = time.time()
                try:
                    usb3_status = hub.get_channel_usb3_dataline_status(*channels)
                    get_usb3_elapsed = time.time() - get_usb3_start
                    stats['get_usb3_dataline']['total_time'] += get_usb3_elapsed
                    
                    is_valid, error_msg = validate_multi_channel_response(
                        usb3_status, channels, usb3_dataline_state, "USB3数据线状态"
                    )
                    if is_valid:
                        stats['get_usb3_dataline']['success'] += 1
                    else:
                        stats['get_usb3_dataline']['failure'] += 1
                        cycle_success = False
                        logger.warning(f"  第 {i+1} 次循环：获取USB3数据线状态验证失败 - {error_msg}")
                except Exception as e:
                    get_usb3_elapsed = time.time() - get_usb3_start
                    stats['get_usb3_dataline']['total_time'] += get_usb3_elapsed
                    stats['get_usb3_dataline']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取USB3数据线状态异常: {e}")
            
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
    
    logger.info("=" * 70)
    logger.info("测试摘要")
    logger.info("=" * 70)
    logger.info("设备信息:")
    hw_version_str = f"V1.{hardware_version}" if hardware_version is not None else "未知"
    fw_version_str = f"V1.{firmware_version}" if firmware_version is not None else "未知"
    serial_str = serial_no if serial_no is not None else "未知"
    logger.info(f"  硬件版本: {hw_version_str}")
    logger.info(f"  固件版本: {fw_version_str}")
    logger.info(f"  序列号: {serial_str}")
    logger.info("")
    logger.info(f"总循环次数: {total_operations}")
    logger.info(f"总成功次数: {success_count}")
    logger.info(f"总失败次数: {failure_count}")
    logger.info(f"总成功率: {success_rate:.1f}%")
    logger.info(f"总耗时: {format_time(elapsed_time)}")
    logger.info(f"循环频率: {ops_per_sec:.1f} 次/秒")
    logger.info("")
    logger.info("详细统计（每个操作的成功/失败次数）:")
    logger.info("-" * 70)
    
    # 显示每个操作的统计
    op_names = {
        'set_power': '设置电源',
        'get_power': '获取电源状态',
        'set_usb2_dataline': '设置USB2数据线',
        'get_usb2_dataline': '获取USB2数据线状态',
        'set_usb3_dataline': '设置USB3数据线',
        'get_usb3_dataline': '获取USB3数据线状态',
    }
    
    logger.info(f"{'操作':<20s} {'成功':>8s} {'失败':>8s} {'总次数':>8s} {'成功率':>10s} {'平均用时':>12s}")
    logger.info("-" * 70)
    
    for op_key, op_name in op_names.items():
        # 只显示实际执行的操作
        if op_key.startswith('usb2') and not supports_usb2:
            continue
        if op_key.startswith('usb3') and not supports_usb3:
            continue
        
        stat = stats[op_key]
        total_op = stat['success'] + stat['failure']
        if total_op > 0:
            op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
            avg_time = (stat['total_time'] / total_op * 1000) if total_op > 0 else 0  # 转换为毫秒
            logger.info(f"  {op_name:<20s} {stat['success']:>8d} {stat['failure']:>8d} {total_op:>8d} {op_success_rate:>9.2f}% {avg_time:>11.2f}ms")
        else:
            logger.info(f"  {op_name:<20s} {'未执行':>8s}")
    
    logger.info("=" * 70)
    
    # 生成HTML报告中的详细统计表格（使用标准的extras fixture）
    try:
        # 尝试获取extras fixture（如果pytest-html已安装）
        extras = request.getfixturevalue('extras')
        html_content = generate_stats_html(stats, op_names, supports_usb2, supports_usb3, 
                                          total_operations, success_count, failure_count, 
                                          success_rate, elapsed_time, ops_per_sec,
                                          hardware_version, firmware_version, serial_no)
        # 使用标准的extras fixture添加到pytest-html报告中
        extras.append(pytest_html.extras.html(html_content))
    except (pytest.FixtureLookupError, AttributeError, NameError) as e:
        # 如果extras不可用（pytest-html未安装），只记录警告，不影响测试
        logger.debug(f"无法添加HTML统计信息到报告（pytest-html可能未安装）: {e}")
    except Exception as e:
        logger.warning(f"无法添加HTML统计信息到报告: {e}")
    
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  [PASS] 核心功能压力测试通过，总成功率 {success_rate:.1f}%")
    
    # 清理：关闭所有通道
    logger.info("正在清理设备状态...")
    try:
        hub.set_channel_power(*channels, state=0)
        if supports_usb2:
            hub.set_channel_usb2_dataline(*channels, state=0)
        if supports_usb3:
            hub.set_channel_usb3_dataline(*channels, state=0)
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
