"""
充电模式切换压力测试 - 在快充和慢充模式之间循环切换，验证设备稳定性

测试内容：
1. 快充模式设置
2. 慢充模式设置
3. 获取充电模式状态
4. 验证模式切换正确性

使用方法:
    # 运行压力测试
    pytest test/SmartUSBHub_Pro/test_stress_charge_mode_switch.py -v -s

    # 生成HTML报告
    pytest test/SmartUSBHub_Pro/test_stress_charge_mode_switch.py -v -s --html=test/SmartUSBHub_Pro/report/report_stress_charge_mode.html --self-contained-html
"""
import pytest
import time
import logging
import sys
import os
from datetime import datetime, timedelta

# 尝试导入pytest_html用于在HTML报告中添加额外信息
try:
    import pytest_html
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

# 在源码仓库中，需要将项目根目录添加到路径（从产品子目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 测试配置 ====================
# 可以通过环境变量 STRESS_TEST_COUNT 来覆盖默认值
STRESS_TEST_TOTAL_COUNT = int(os.environ.get('STRESS_TEST_COUNT', 10000))  # 默认测试1万次切换

# 充电模式切换后用于验证的重试次数及间隔
CHARGE_MODE_VERIFY_MAX_RETRY = int(os.environ.get('CHARGE_MODE_VERIFY_MAX_RETRY', 3))
CHARGE_MODE_VERIFY_RETRY_DELAY = float(os.environ.get('CHARGE_MODE_VERIFY_RETRY_DELAY', 0.1))  # 秒


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

def print_progress(current, total, success_count, failure_count, start_time, 
                  fast_charge_count=0, slow_charge_count=0, end_line=False):
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
           f"快充: {fast_charge_count}次, 慢充: {slow_charge_count}次, "
           f"已用: {format_time(elapsed)}, 速度: {rate:.1f}次/秒, "
           f"预计剩余: {format_time(remaining) if remaining > 0 else '0秒'}")
    
    sys.stderr.write(f"\r{msg}" + ("\n" if end_line else ""))
    sys.stderr.flush()
    
    if end_line and key in _last_update_time:
        del _last_update_time[key]


def generate_stats_html(stats, mode_names, total_operations, success_count, failure_count, 
                       success_rate, elapsed_time, ops_per_sec,
                       fast_charge_count, slow_charge_count, 
                       fast_charge_time, slow_charge_time,
                       hardware_version=None, firmware_version=None, serial_no=None):
    """生成用于HTML报告的统计信息表格"""
    html = '<div style="margin: 20px 0;">'
    html += '<h3>充电模式切换压力测试详细统计</h3>'
    
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
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总切换次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_operations:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总成功次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: green;">{success_count:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总失败次数</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: red;">{failure_count:,}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总成功率</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold;">{success_rate:.2f}%</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">总耗时</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format_time(elapsed_time)}</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">切换频率</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{ops_per_sec:.2f} 次/秒</td></tr>'
    html += '</table>'
    html += '</div>'
    
    # 充电模式统计
    html += '<div style="margin-bottom: 20px;">'
    html += '<h4>充电模式统计</h4>'
    html += '<table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">'
    html += '<tr style="background-color: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">模式</th><th style="border: 1px solid #ddd; padding: 8px; text-align: right;">次数</th><th style="border: 1px solid #ddd; padding: 8px; text-align: right;">总时长</th><th style="border: 1px solid #ddd; padding: 8px; text-align: right;">占比</th></tr>'
    
    total_time = fast_charge_time + slow_charge_time
    fast_charge_percent = (fast_charge_time / total_time * 100) if total_time > 0 else 0
    slow_charge_percent = (slow_charge_time / total_time * 100) if total_time > 0 else 0
    
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">快充模式</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{fast_charge_count:,}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format_time(fast_charge_time)}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{fast_charge_percent:.1f}%</td></tr>'
    html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">慢充模式</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{slow_charge_count:,}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format_time(slow_charge_time)}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{slow_charge_percent:.1f}%</td></tr>'
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
    
    for op_key, op_name in mode_names.items():
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


def validate_charge_mode_response(status, channels, expected_value, status_name="充电模式"):
    """
    验证充电模式返回值的完整性和正确性
    
    Args:
        status: 返回值（可能是dict或int）
        channels: 请求的通道列表
        expected_value: 期望的值（1=快充, 2=慢充）
        status_name: 状态名称（用于错误信息）
    
    Returns:
        (is_valid, error_msg): (是否有效, 错误信息)
    """
    if status is None:
        return (False, "返回值为None")
    
    # 按 auto_charge_mode_switch.py 的实际用法：
    #   charge_modes = hub.get_channel_charge_mode(args.channels[0])
    #   for ch, mode_val in charge_modes.items():
    #       if ch in args.channels: ...
    # 可以确认：
    #   - get_channel_charge_mode() 始终返回 dict
    #   - dict 里可能包含比 channels 更多的通道，我们只关心自己测的那些通道
    if not isinstance(status, dict):
        return (False, f"应返回dict，实际返回{type(status).__name__}")
    
    # 只验证我们关心的通道，其他通道忽略（与 demo 行为保持一致）
    for ch in channels:
        if ch not in status:
            return (False, f"通道{ch}缺失")
        value = status[ch]
        if not isinstance(value, int):
            return (False, f"通道{ch}的值类型不正确，期望int，实际{type(value).__name__}")
        if value != expected_value:
            return (False, f"通道{ch}的值不正确，期望{expected_value}，实际{value}")
    
    return (True, None)


def verify_charge_mode_with_retry(hub, channels, expected_value, stats_entry_key, 
                                  stats, cycle_index, mode_name):
    """
    多次读取并验证充电模式，增加对硬件时序的容错能力。

    在限定的重试次数和时间窗口内，只要至少有一次读取到期望模式，就认为本轮成功。
    """
    stats[stats_entry_key]['count'] += 1
    attempt = 0
    last_error_msg = None
    start = time.time()
    success = False

    while attempt < CHARGE_MODE_VERIFY_MAX_RETRY:
        attempt += 1
        verify_start = time.time()
        try:
            charge_mode = hub.get_channel_charge_mode(*channels)
            verify_elapsed = time.time() - verify_start
            stats[stats_entry_key]['total_time'] += verify_elapsed

            is_valid, error_msg = validate_charge_mode_response(
                charge_mode, channels, expected_value, mode_name
            )
            if is_valid:
                stats[stats_entry_key]['success'] += 1
                success = True
                break
            else:
                last_error_msg = error_msg
        except Exception as e:
            verify_elapsed = time.time() - verify_start
            stats[stats_entry_key]['total_time'] += verify_elapsed
            last_error_msg = f"获取{mode_name}异常: {e}"

        # 如果还没成功且还有重试机会，等待一小段时间再试
        if attempt < CHARGE_MODE_VERIFY_MAX_RETRY:
            time.sleep(CHARGE_MODE_VERIFY_RETRY_DELAY)

    if not success:
        stats[stats_entry_key]['failure'] += 1
        if last_error_msg is None:
            last_error_msg = "未知错误"
        logger.warning(
            f"  第 {cycle_index + 1} 次循环：验证{mode_name}失败 "
            f"(重试{attempt}次) - {last_error_msg}"
        )

    return success


@pytest.mark.hardware
@pytest.mark.slow
def test_stress_charge_mode_switch(hub, max_channels, request):
    """
    压力测试：充电模式切换循环测试
    
    测试内容：
    1. 在快充和慢充模式之间循环切换
    2. 验证每次切换后的状态
    3. 统计切换成功率和耗时
    """
    # 测试所有通道（对于 4CH 产品即通道 1-4）
    channels = list(range(1, max_channels + 1))
    logger.info(f"充电模式切换压力测试（{max_channels} 个通道）{channels}...")
    
    # 获取设备信息（用于在报告中显示）
    hardware_version = hub.hardware_version
    firmware_version = hub.firmware_version
    serial_no = hub.serial_no
    
    # 初始化：先关闭所有通道，然后设置为快充模式
    logger.info("初始化设备状态...")
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
    hub.set_channel_fast_charge(*channels, disconnect_before_switch=True)
    time.sleep(0.2)
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    logger.info("=" * 70)
    logger.info(f"测试总次数: {total_operations:,} 次充电模式切换")
    logger.info(f"测试模式: 快充 <-> 慢充 循环切换")
    logger.info("=" * 70)
    
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 详细统计：每个操作的成功、失败次数和用时
    stats = {
        'set_fast_charge': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'verify_fast_charge': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'set_slow_charge': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        'verify_slow_charge': {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
    }
    
    # 模式统计
    fast_charge_count = 0
    slow_charge_count = 0
    fast_charge_time = 0.0
    slow_charge_time = 0.0
    mode_start_time = time.time()
    
    # 初始化进度显示
    print_progress(0, total_operations, 0, 0, start_time, fast_charge_count, slow_charge_count)
    
    # 当前模式（从快充开始）
    current_mode = "FAST_CHARGE"
    fast_charge_count = 1
    
    try:
        for i in range(total_operations):
            cycle_success = True
            
            # 切换模式
            if current_mode == "FAST_CHARGE":
                # 计算上一个模式的持续时间
                mode_duration = time.time() - mode_start_time
                fast_charge_time += mode_duration
                
                # 切换到慢充
                current_mode = "SLOW_CHARGE"
                slow_charge_count += 1
                mode_start_time = time.time()
                
                # 1. 设置慢充模式
                stats['set_slow_charge']['count'] += 1
                set_start = time.time()
                # 慢充模式不需要断开连接
                set_result = hub.set_channel_slow_charge(*channels, disconnect_before_switch=False)
                set_elapsed = time.time() - set_start
                stats['set_slow_charge']['total_time'] += set_elapsed
                
                if set_result:
                    stats['set_slow_charge']['success'] += 1
                else:
                    stats['set_slow_charge']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置慢充模式失败")
                
                # 等待设备完成模式切换
                time.sleep(0.1)
                
                # 2. 验证慢充模式（期望值：2，带重试）
                if not verify_charge_mode_with_retry(
                    hub,
                    channels,
                    expected_value=2,
                    stats_entry_key='verify_slow_charge',
                    stats=stats,
                    cycle_index=i,
                    mode_name="慢充模式"
                ):
                    cycle_success = False
                
            else:  # current_mode == "SLOW_CHARGE"
                # 计算上一个模式的持续时间
                mode_duration = time.time() - mode_start_time
                slow_charge_time += mode_duration
                
                # 切换到快充
                current_mode = "FAST_CHARGE"
                fast_charge_count += 1
                mode_start_time = time.time()
                
                # 1. 设置快充模式
                stats['set_fast_charge']['count'] += 1
                set_start = time.time()
                # 快充模式需要先断开连接
                set_result = hub.set_channel_fast_charge(*channels, disconnect_before_switch=True)
                set_elapsed = time.time() - set_start
                stats['set_fast_charge']['total_time'] += set_elapsed
                
                if set_result:
                    stats['set_fast_charge']['success'] += 1
                else:
                    stats['set_fast_charge']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置快充模式失败")
                
                # 等待设备完成模式切换
                time.sleep(0.1)
                
                # 2. 验证快充模式（期望值：1，带重试）
                if not verify_charge_mode_with_retry(
                    hub,
                    channels,
                    expected_value=1,
                    stats_entry_key='verify_fast_charge',
                    stats=stats,
                    cycle_index=i,
                    mode_name="快充模式"
                ):
                    cycle_success = False
            
            if cycle_success:
                success_count += 1
            else:
                failure_count += 1
            
            # 更新进度
            print_progress(i + 1, total_operations, success_count, failure_count, start_time, 
                         fast_charge_count, slow_charge_count)
            
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        # 计算当前模式的持续时间
        mode_duration = time.time() - mode_start_time
        if current_mode == "FAST_CHARGE":
            fast_charge_time += mode_duration
        else:
            slow_charge_time += mode_duration
        
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, 
                     fast_charge_count, slow_charge_count, end_line=True)
        logger.warning(f"\n[WARNING] 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次切换")
        raise
    
    # 计算最后一个模式的持续时间
    mode_duration = time.time() - mode_start_time
    if current_mode == "FAST_CHARGE":
        fast_charge_time += mode_duration
    else:
        slow_charge_time += mode_duration
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, 
                 fast_charge_count, slow_charge_count, end_line=True)
    
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
    logger.info(f"总切换次数: {total_operations:,}")
    logger.info(f"总成功次数: {success_count:,}")
    logger.info(f"总失败次数: {failure_count:,}")
    logger.info(f"总成功率: {success_rate:.1f}%")
    logger.info(f"总耗时: {format_time(elapsed_time)}")
    logger.info(f"切换频率: {ops_per_sec:.1f} 次/秒")
    logger.info("")
    logger.info("充电模式统计:")
    logger.info(f"  快充次数: {fast_charge_count:,}, 总时长: {format_time(fast_charge_time)}")
    logger.info(f"  慢充次数: {slow_charge_count:,}, 总时长: {format_time(slow_charge_time)}")
    total_mode_time = fast_charge_time + slow_charge_time
    if total_mode_time > 0:
        fast_charge_percent = (fast_charge_time / total_mode_time) * 100
        slow_charge_percent = (slow_charge_time / total_mode_time) * 100
        logger.info(f"  快充占比: {fast_charge_percent:.1f}%")
        logger.info(f"  慢充占比: {slow_charge_percent:.1f}%")
    logger.info("")
    logger.info("详细统计（每个操作的成功/失败次数）:")
    logger.info("-" * 70)
    
    # 显示每个操作的统计
    mode_names = {
        'set_fast_charge': '设置快充模式',
        'verify_fast_charge': '验证快充模式',
        'set_slow_charge': '设置慢充模式',
        'verify_slow_charge': '验证慢充模式',
    }
    
    logger.info(f"{'操作':<20s} {'成功':>8s} {'失败':>8s} {'总次数':>8s} {'成功率':>10s} {'平均用时':>12s}")
    logger.info("-" * 70)
    
    for op_key, op_name in mode_names.items():
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
        html_content = generate_stats_html(stats, mode_names, 
                                          total_operations, success_count, failure_count, 
                                          success_rate, elapsed_time, ops_per_sec,
                                          fast_charge_count, slow_charge_count,
                                          fast_charge_time, slow_charge_time,
                                          hardware_version, firmware_version, serial_no)
        # 使用标准的extras fixture添加到pytest-html报告中
        extras.append(pytest_html.extras.html(html_content))
    except (pytest.FixtureLookupError, AttributeError, NameError) as e:
        # 如果extras不可用（pytest-html未安装），只记录警告，不影响测试
        logger.debug(f"无法添加HTML统计信息到报告（pytest-html可能未安装）: {e}")
    except Exception as e:
        logger.warning(f"无法添加HTML统计信息到报告: {e}")
    
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  [PASS] 充电模式切换压力测试通过，总成功率 {success_rate:.1f}%")
    
    # 清理：关闭所有通道
    logger.info("正在清理设备状态...")
    try:
        hub.set_channel_power(*channels, state=0)
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

