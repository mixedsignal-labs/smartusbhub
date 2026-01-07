"""
FlexConnect 压力测试

循环测试模式切换和故障检测，验证设备长时间运行的稳定性。

使用方法:
    # 运行压力测试
    pytest FlexConnect/test_stress.py -v

    # 显示详细日志
    pytest FlexConnect/test_stress.py -v -s --log-cli-level=INFO

注意事项：
- 需要连接FlexConnect设备（FLEX_3CH产品）
- 默认循环10,000次（可在代码中修改STRESS_TEST_TOTAL_COUNT）
- 压力测试要求成功率≥95%才算通过
"""
import pytest
import time
import sys
import os
import logging

# 尝试导入pytest_html用于在HTML报告中添加额外信息
try:
    import pytest_html
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

# 添加项目根目录到路径（从产品子目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2, FLEXCONNECT_MODE_DISCONNECT

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 测试次数配置 ====================
STRESS_TEST_TOTAL_COUNT = 10000  # FlexConnect压力测试循环次数


@pytest.fixture(scope="module")
def flexconnect_hub():
    """
    创建FlexConnect设备连接（仅用于FlexConnect产品）
    使用auto_connect自动尝试连接所有可用设备
    """
    # 使用auto_connect自动连接FlexConnect设备
    hub = SmartUSBHub.auto_connect(feature_filter="flexconnect")
    
    if hub is None:
        pytest.skip("No available FlexConnect devices found (all devices may be occupied)")
    
    yield hub
    
    # 清理：恢复出厂设置
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
    
    # 断开连接
    try:
        hub.disconnect()
        logger.info("[OK] 设备已断开连接")
    except Exception as e:
        logger.warning(f"[WARNING] 断开连接时出错: {e}")


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


def generate_flexconnect_stats_html(mode_stats, mode_names, other_stats, total_operations, success_count, failure_count, 
                                   success_rate, elapsed_time, ops_per_sec,
                                   hardware_version=None, firmware_version=None, serial_no=None):
    """生成用于HTML报告的FlexConnect统计信息表格"""
    html = '<div style="margin: 20px 0;">'
    html += '<h3>FlexConnect压力测试详细统计</h3>'
    
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
    
    # 按模式分类的详细统计
    html += '<div style="margin-bottom: 20px;">'
    html += '<h4>设置模式统计（按模式分类）</h4>'
    html += '<table style="border-collapse: collapse; width: 100%;">'
    html += '<tr style="background-color: #f0f0f0;">'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">模式</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">失败次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">总次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功率</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">平均用时</th>'
    html += '</tr>'
    
    for mode, mode_name in mode_names.items():
        stat = mode_stats[mode]
        total_op = stat['success'] + stat['failure']
        if total_op > 0:
            op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
            avg_time = (stat['total_time'] / total_op * 1000) if total_op > 0 else 0  # 转换为毫秒
            success_color = 'green' if op_success_rate >= 95 else 'orange' if op_success_rate >= 80 else 'red'
            html += '<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{mode_name}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: green;">{stat["success"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: red;">{stat["failure"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_op:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; color: {success_color};">{op_success_rate:.2f}%</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{avg_time:.2f} ms</td>'
            html += '</tr>'
        else:
            html += '<tr style="color: #999;">'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{mode_name}</td>'
            html += '<td colspan="5" style="border: 1px solid #ddd; padding: 8px; text-align: center;">未执行</td>'
            html += '</tr>'
    
    html += '</table>'
    html += '</div>'
    
    # 其他操作统计
    html += '<div>'
    html += '<h4>其他操作统计</h4>'
    html += '<table style="border-collapse: collapse; width: 100%;">'
    html += '<tr style="background-color: #f0f0f0;">'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">操作</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">失败次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">总次数</th>'
    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: right;">成功率</th>'
    html += '</tr>'
    
    other_op_names = {
        'get_mode': '获取模式',
        'get_fault': '获取故障状态',
    }
    
    for op_key, op_name in other_op_names.items():
        stat = other_stats[op_key]
        total_op = stat['success'] + stat['failure']
        if total_op > 0:
            op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
            success_color = 'green' if op_success_rate >= 95 else 'orange' if op_success_rate >= 80 else 'red'
            html += '<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{op_name}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: green;">{stat["success"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: red;">{stat["failure"]:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_op:,}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; color: {success_color};">{op_success_rate:.2f}%</td>'
            html += '</tr>'
        else:
            html += '<tr style="color: #999;">'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{op_name}</td>'
            html += '<td colspan="4" style="border: 1px solid #ddd; padding: 8px; text-align: center;">未执行</td>'
            html += '</tr>'
    
    html += '</table>'
    html += '</div>'
    html += '</div>'
    
    return html


class TestFlexConnectStress:
    """FlexConnect压力测试"""
    
    def test_flexconnect_stress(self, flexconnect_hub, request):
        """
        FlexConnect压力测试：循环测试模式切换和故障检测
        
        测试内容：
        1. 设置模式（PC/UDISK1/UDISK2/DISCONNECT循环）
        2. 获取模式
        3. 获取故障状态
        """
        logger.info("=" * 70)
        logger.info("FlexConnect压力测试开始")
        logger.info("=" * 70)
        
        # 获取设备信息（用于在报告中显示）
        hardware_version = flexconnect_hub.hardware_version
        firmware_version = flexconnect_hub.firmware_version
        serial_no = flexconnect_hub.serial_no
        
        total_operations = STRESS_TEST_TOTAL_COUNT
        logger.info(f"测试总次数: {total_operations:,} 次")
        logger.info("每次循环包含: 设置模式、获取模式、获取故障状态")
        logger.info("=" * 70)
        
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        # 详细统计：按模式分类统计设置模式的成功/失败次数和用时
        # 每个模式统计：success, failure, total_time, count
        mode_stats = {
            FLEXCONNECT_MODE_PC: {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
            FLEXCONNECT_MODE_UDISK1: {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
            FLEXCONNECT_MODE_UDISK2: {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
            FLEXCONNECT_MODE_DISCONNECT: {'success': 0, 'failure': 0, 'total_time': 0.0, 'count': 0},
        }
        
        # 其他操作的统计
        other_stats = {
            'get_mode': {'success': 0, 'failure': 0},
            'get_fault': {'success': 0, 'failure': 0},
        }
        
        # 模式名称映射
        mode_names = {
            FLEXCONNECT_MODE_PC: 'PC模式',
            FLEXCONNECT_MODE_UDISK1: 'UDISK1模式',
            FLEXCONNECT_MODE_UDISK2: 'UDISK2模式',
            FLEXCONNECT_MODE_DISCONNECT: 'DISCONNECT模式',
        }
        
        # 模式循环序列（包含DISCONNECT模式）
        mode_sequence = [
            FLEXCONNECT_MODE_PC,
            FLEXCONNECT_MODE_UDISK1,
            FLEXCONNECT_MODE_UDISK2,
            FLEXCONNECT_MODE_DISCONNECT
        ]
        mode_index = 0
        
        # 初始化进度显示
        print_progress(0, total_operations, 0, 0, start_time)
        
        try:
            for i in range(total_operations):
                cycle_success = True
                
                # 1. 设置模式（循环切换）- 记录用时
                target_mode = mode_sequence[mode_index]
                mode_stats[target_mode]['count'] += 1
                
                # 记录设置模式的开始时间
                set_mode_start = time.time()
                set_mode_result = flexconnect_hub.set_flexconnect_mode(target_mode)
                set_mode_elapsed = time.time() - set_mode_start
                
                # 统计成功/失败和用时
                if set_mode_result:
                    mode_stats[target_mode]['success'] += 1
                    mode_stats[target_mode]['total_time'] += set_mode_elapsed
                else:
                    mode_stats[target_mode]['failure'] += 1
                    mode_stats[target_mode]['total_time'] += set_mode_elapsed
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：设置{mode_names[target_mode]}失败")
                
                # 切换到下一个模式
                mode_index = (mode_index + 1) % len(mode_sequence)
                
                # 等待模式切换完成
                time.sleep(0.2)
                
                # 2. 获取模式
                try:
                    actual_mode = flexconnect_hub.get_flexconnect_mode()
                    if actual_mode == target_mode:
                        other_stats['get_mode']['success'] += 1
                    else:
                        other_stats['get_mode']['failure'] += 1
                        cycle_success = False
                        logger.warning(f"  第 {i+1} 次循环：获取模式验证失败 - 期望{target_mode}，实际{actual_mode}")
                except Exception as e:
                    other_stats['get_mode']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取模式异常: {e}")
                
                # 3. 获取故障状态
                try:
                    fault = flexconnect_hub.get_flexconnect_fault()
                    if fault is not None and isinstance(fault, int) and 0 <= fault <= 0xFF:
                        other_stats['get_fault']['success'] += 1
                    else:
                        other_stats['get_fault']['failure'] += 1
                        cycle_success = False
                        logger.warning(f"  第 {i+1} 次循环：获取故障状态验证失败 - 返回值无效: {fault}")
                except Exception as e:
                    other_stats['get_fault']['failure'] += 1
                    cycle_success = False
                    logger.warning(f"  第 {i+1} 次循环：获取故障状态异常: {e}")
                
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
        logger.info(f"总循环次数: {total_operations:,}")
        logger.info(f"总成功次数: {success_count:,}")
        logger.info(f"总失败次数: {failure_count:,}")
        logger.info(f"总成功率: {success_rate:.1f}%")
        logger.info(f"总耗时: {format_time(elapsed_time)}")
        logger.info(f"循环频率: {ops_per_sec:.1f} 次/秒")
        logger.info("")
        logger.info("详细统计（按模式分类的设置模式统计）:")
        logger.info("-" * 70)
        logger.info(f"{'模式':<20s} {'成功':>8s} {'失败':>8s} {'总次数':>8s} {'成功率':>10s} {'平均用时':>12s}")
        logger.info("-" * 70)
        
        # 显示每个模式的统计
        for mode, mode_name in mode_names.items():
            stat = mode_stats[mode]
            total_op = stat['success'] + stat['failure']
            if total_op > 0:
                op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
                avg_time = (stat['total_time'] / total_op * 1000) if total_op > 0 else 0  # 转换为毫秒
                logger.info(f"  {mode_name:<20s} {stat['success']:>8d} {stat['failure']:>8d} {total_op:>8d} {op_success_rate:>9.2f}% {avg_time:>11.2f}ms")
            else:
                logger.info(f"  {mode_name:<20s} {'未执行':>8s}")
        
        logger.info("")
        logger.info("其他操作统计:")
        logger.info("-" * 70)
        other_op_names = {
            'get_mode': '获取模式',
            'get_fault': '获取故障状态',
        }
        
        for op_key, op_name in other_op_names.items():
            stat = other_stats[op_key]
            total_op = stat['success'] + stat['failure']
            if total_op > 0:
                op_success_rate = (stat['success'] / total_op * 100) if total_op > 0 else 0
                logger.info(f"  {op_name:20s}: 成功 {stat['success']:6d}, 失败 {stat['failure']:6d}, 总次数 {total_op:6d}, 成功率 {op_success_rate:6.2f}%")
            else:
                logger.info(f"  {op_name:20s}: 未执行")
        
        logger.info("=" * 70)
        
        # 生成HTML报告中的详细统计表格
        try:
            # 尝试获取extras fixture（如果pytest-html已安装）
            extras = request.getfixturevalue('extras')
            html_content = generate_flexconnect_stats_html(mode_stats, mode_names, other_stats,
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
        logger.info(f"  [PASS] FlexConnect压力测试通过，总成功率 {success_rate:.1f}%")
        
        # 恢复出厂设置，还原设备配置
        logger.info("正在恢复出厂设置...")
        try:
            result = flexconnect_hub.factory_reset()
            if result:
                logger.info("[OK] 设备已恢复出厂设置")
                time.sleep(0.5)  # 等待设备重置完成
            else:
                logger.warning("[WARNING] 恢复出厂设置失败（未收到ACK）")
        except Exception as e:
            logger.warning(f"[WARNING] 恢复出厂设置时出错: {e}")
