"""
压力测试 - 长时间、高频率、大规模测试

这些测试运行时间较长（特别是100万次测试需要约33分钟），
主要用于验证系统在极端条件下的稳定性和可靠性。

使用方法:
    # 运行所有压力测试
    pytest test/test_integration_stress.py -v

    # 运行特定压力测试
    pytest test/test_integration_stress.py::test_power_status_read_stability_single -v

    # 跳过压力测试（运行常规测试）
    pytest test/test_integration.py -v

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

# 使用 conftest.py 中的 fixtures
# 这些 fixtures 会在 conftest.py 中定义，这里直接使用即可

# ==================== 测试次数配置 ====================
STRESS_TEST_TOTAL_COUNT = 10000


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


def estimate_test_time(operations_count, ops_per_sec=25.0):
    """估算测试时间"""
    return operations_count / ops_per_sec, format_time(operations_count / ops_per_sec)


def log_test_header(total_operations, ops_per_sec=25.0):
    """输出测试头部信息"""
    logger.info("━" * 70)
    logger.info(f"测试总次数: {total_operations:,} 次")
    _, time_str = estimate_test_time(total_operations, ops_per_sec)
    logger.info(f"预估耗时: {time_str} (基于实际速度 {ops_per_sec}次/秒)")
    logger.info("━" * 70)


# ==================== 4通道ACK测试（重要：验证ACK不丢失）====================

def test_four_channels_power_ack(hub, max_channels):
    """测试4个通道同时操作时的ACK响应（验证ACK不丢失）"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道同时操作ACK响应: {channels}...")
    
    # 测试1: 同时打开4个通道，验证ACK
    logger.info("  测试1: 同时打开4个通道...")
    result = hub.set_channel_power(1, 2, 3, 4, state=1)
    assert result, "4个通道同时打开应该返回成功"
    time.sleep(0.5)  # 给更多时间等待ACK
    
    # 验证所有通道状态
    status = hub.get_channel_power_status(1, 2, 3, 4)
    for ch in channels:
        assert status[ch] == 1, f"通道 {ch} 应该打开，可能ACK丢失"
    logger.info("  ✓ 4个通道同时打开成功，ACK正常")
    
    # 测试2: 同时关闭4个通道，验证ACK
    logger.info("  测试2: 同时关闭4个通道...")
    result = hub.set_channel_power(1, 2, 3, 4, state=0)
    assert result, "4个通道同时关闭应该返回成功"
    time.sleep(0.5)
    
    # 验证所有通道状态
    status = hub.get_channel_power_status(1, 2, 3, 4)
    for ch in channels:
        assert status[ch] == 0, f"通道 {ch} 应该关闭，可能ACK丢失"
    logger.info("  ✓ 4个通道同时关闭成功，ACK正常")


def test_four_channels_power_multiple_operations(hub, max_channels):
    """测试4个通道多次连续操作的ACK响应"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道多次连续操作ACK响应: {channels}...")
    
    # 连续执行多次4通道操作
    for i in range(3):
        logger.info(f"  第 {i+1} 次操作: 打开4个通道...")
        result = hub.set_channel_power(1, 2, 3, 4, state=1)
        assert result, f"第 {i+1} 次操作失败，可能ACK丢失"
        time.sleep(0.5)
        
        status = hub.get_channel_power_status(1, 2, 3, 4)
        for ch in channels:
            assert status[ch] == 1, f"第 {i+1} 次操作后通道 {ch} 状态错误"
        
        logger.info(f"  第 {i+1} 次操作: 关闭4个通道...")
        result = hub.set_channel_power(1, 2, 3, 4, state=0)
        assert result, f"第 {i+1} 次操作失败，可能ACK丢失"
        time.sleep(0.5)
        
        status = hub.get_channel_power_status(1, 2, 3, 4)
        for ch in channels:
            assert status[ch] == 0, f"第 {i+1} 次操作后通道 {ch} 状态错误"
    
    logger.info("  ✓ 4个通道多次连续操作成功，ACK正常")


def test_four_channels_dataline_ack(hub, max_channels):
    """测试4个通道数据线同时操作的ACK响应"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道数据线同时操作ACK响应: {channels}...")
    
    # 检查是否支持数据线切换
    try:
        product_type = hub.product_type
        if product_type is None:
            product_type = hub.get_product_type()
        
        from smartusbhub import PRODUCT_TYPE_TABLE
        product_info = PRODUCT_TYPE_TABLE.get(product_type) if product_type is not None else None
        
        if product_info and not (product_info.get("enable_usb2_data_switch") or 
                                 product_info.get("enable_usb3_data_switch")):
            pytest.skip(f"产品 {hub.get_product_name()} 不支持数据线切换")
    except:
        pass
    
    # 测试同时打开4个通道的数据线
    logger.info("  同时打开4个通道数据线...")
    result = hub.set_channel_usb2_dataline(1, 2, 3, 4, state=1)
    assert result, "4个通道数据线同时打开应该返回成功"
    time.sleep(0.5)
    
    status = hub.get_channel_usb2_dataline_status(1, 2, 3, 4)
    for ch in channels:
        assert status[ch] == 1, f"通道 {ch} 数据线应该打开，可能ACK丢失"
    logger.info("  ✓ 4个通道数据线同时打开成功，ACK正常")
    
    # 测试同时关闭4个通道的数据线
    logger.info("  同时关闭4个通道数据线...")
    result = hub.set_channel_usb2_dataline(1, 2, 3, 4, state=0)
    assert result, "4个通道数据线同时关闭应该返回成功"
    time.sleep(0.5)
    
    status = hub.get_channel_usb2_dataline_status(1, 2, 3, 4)
    for ch in channels:
        assert status[ch] == 0, f"通道 {ch} 数据线应该关闭，可能ACK丢失"
    logger.info("  ✓ 4个通道数据线同时关闭成功，ACK正常")


def test_four_channels_status_read_ack(hub, max_channels):
    """测试4个通道状态读取的ACK响应"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道状态读取ACK响应: {channels}...")
    
    # 先设置一些通道为打开状态
    hub.set_channel_power(1, 3, state=1)
    hub.set_channel_power(2, 4, state=0)
    time.sleep(0.3)
    
    # 测试同时读取4个通道状态
    logger.info("  同时读取4个通道电源状态...")
    status = hub.get_channel_power_status(1, 2, 3, 4)
    assert status is not None, "4个通道状态读取失败，可能ACK丢失"
    assert len(status) == 4, f"应该返回4个通道状态，实际返回 {len(status)}"
    
    for ch in channels:
        assert ch in status, f"通道 {ch} 状态缺失，可能ACK丢失"
        logger.info(f"    通道 {ch}: {'ON' if status[ch] == 1 else 'OFF'}")
    
    logger.info("  ✓ 4个通道状态读取成功，ACK正常")
    
    # 清理
    hub.set_channel_power(1, 3, state=0)
    time.sleep(0.2)


def test_four_channels_voltage_current_ack(hub, max_channels):
    """测试4个通道电压电流读取的ACK响应"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道电压电流读取ACK响应: {channels}...")
    
    # 检查是否支持ADC
    try:
        supports_adc = hub._check_feature_support("adc")
    except (ValueError, AttributeError):
        pytest.skip("无法确定产品是否支持ADC")
    
    if not supports_adc:
        pytest.skip(f"产品 {hub.get_product_name()} 不支持电压/电流监控")
    
    # 打开所有通道
    hub.set_channel_power(1, 2, 3, 4, state=1)
    time.sleep(0.3)
    
    logger.info("  连续读取4个通道的电压和电流...")
    results = {}
    for ch in channels:
        try:
            voltage = hub.get_channel_voltage(ch)
            current = hub.get_channel_current(ch)
            assert voltage is not None, f"通道 {ch} 电压读取失败，可能ACK丢失"
            assert current is not None, f"通道 {ch} 电流读取失败，可能ACK丢失"
            results[ch] = (voltage, current)
            voltage_v = voltage / 10.0
            current_a = current / 100.0
            logger.info(f"    通道 {ch}: {voltage_v:.2f}V, {current_a:.2f}A")
        except Exception as e:
            logger.error(f"    通道 {ch} 读取失败: {e}")
            raise
    
    assert len(results) == 4, f"应该读取4个通道数据，实际读取 {len(results)} 个"
    logger.info("  ✓ 4个通道电压电流读取成功，ACK正常")
    
    # 关闭所有通道
    hub.set_channel_power(1, 2, 3, 4, state=0)
    time.sleep(0.2)


def test_four_channels_rapid_operations(hub, max_channels):
    """测试4个通道快速连续操作的ACK响应（压力测试）"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]
    logger.info(f"测试4个通道快速连续操作ACK响应（压力测试）: {channels}...")
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    log_test_header(total_operations, ops_per_sec=5.0)
    
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_operations, 0, 0, start_time)
    
    try:
        for i in range(total_operations):
            # 快速打开
            result1 = hub.set_channel_power(1, 2, 3, 4, state=1)
            time.sleep(0.1)  # 短暂等待
            
            # 快速关闭
            result2 = hub.set_channel_power(1, 2, 3, 4, state=0)
            time.sleep(0.1)
            
            if result1 and result2:
                success_count += 1
            else:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作失败: result1={result1}, result2={result2}")
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次操作")
        raise
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    success_rate = (success_count / total_operations) * 100
    logger.info(f"  成功率: {success_count}/{total_operations} ({success_rate:.1f}%)")
    
    assert success_rate >= 80, f"ACK成功率过低: {success_rate:.1f}%，可能存在ACK丢失问题"
    logger.info(f"  ✓ 4个通道快速操作测试通过，成功率 {success_rate:.1f}%")


# ==================== 高速压力测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_high_speed_single_channel_power(hub, max_channels, channel):
    """压力测试：单个通道电源控制 - 设置、读取、校验、反转状态"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"压力测试：通道 {channel} 电源控制（设置->读取->校验->反转）...")
    
    # 初始化状态为关闭
    hub.set_channel_power(channel, state=0)
    time.sleep(0.2)
    expected_state = 0
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    log_test_header(total_operations, ops_per_sec=26.5)
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_operations, 0, 0, start_time)
    
    try:
        for i in range(total_operations):
            # 反转状态
            expected_state = 1 - expected_state
            
            # 设置通道电源
            set_result = hub.set_channel_power(channel, state=expected_state)
            
            if not set_result:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：设置通道 {channel} 失败")
                continue
            
            # 短暂等待，确保状态已更新
            time.sleep(0.01)
            
            # 获取通道电源值并校验
            try:
                status = hub.get_channel_power_status(channel)
                if isinstance(status, dict):
                    actual_state = status[channel]
                else:
                    actual_state = status
                
                # 校验是否一致
                if actual_state == expected_state:
                    success_count += 1
                else:
                    failure_count += 1
                    logger.warning(f"  第 {i+1} 次操作：通道 {channel} 状态不一致，期望 {expected_state}，实际 {actual_state}")
            except Exception as e:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：读取通道 {channel} 状态失败: {e}")
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次操作")
        raise  # 重新抛出异常，让 pytest 知道测试被中断
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time
    
    logger.info(f"  总操作次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 99, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ 通道 {channel} 压力测试通过，成功率 {success_rate:.1f}%")


def test_high_speed_all_channels_power(hub, max_channels):
    """压力测试：所有通道同时电源控制 - 设置、读取、校验、反转状态"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"压力测试：所有 {max_channels} 个通道同时电源控制（设置->读取->校验->反转）{channels}...")
    
    # 初始化所有通道为关闭
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
    expected_state = 0
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    log_test_header(total_operations, ops_per_sec=20.0)
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    for i in range(total_operations):
        # 反转状态
        expected_state = 1 - expected_state
        
        # 设置所有通道电源
        set_result = hub.set_channel_power(*channels, state=expected_state)
        
        if not set_result:
            failure_count += 1
            logger.warning(f"  第 {i+1} 次操作：设置所有通道失败")
            continue
        
        # 短暂等待，确保状态已更新
        time.sleep(0.01)
        
        # 获取所有通道电源值并校验
        try:
            status = hub.get_channel_power_status(*channels)
            
            if status is None:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：读取所有通道状态失败（返回None）")
                continue
            
            # 校验所有通道是否一致
            all_match = True
            for ch in channels:
                if status[ch] != expected_state:
                    all_match = False
                    logger.warning(f"  第 {i+1} 次操作：通道 {ch} 状态不一致，期望 {expected_state}，实际 {status[ch]}")
            
            if all_match:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            failure_count += 1
            logger.warning(f"  第 {i+1} 次操作：读取所有通道状态失败: {e}")
        
        # 每次操作后更新进度（在同一行更新）
        print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time
    
    logger.info(f"  总操作次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 99, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ 所有 {max_channels} 个通道同时压力测试通过，成功率 {success_rate:.1f}%")


def test_high_speed_four_channels_flip(hub, max_channels):
    """压力测试：固定4个通道（1,2,3,4）同时翻转 - 设置、读取、校验、反转状态"""
    if max_channels < 4:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要4个通道进行测试")
    
    channels = [1, 2, 3, 4]  # 固定4个通道
    logger.info(f"压力测试：固定4个通道（1,2,3,4）同时翻转（设置->读取->校验->反转）...")
    
    # 初始化所有通道为关闭
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
    expected_state = 0
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    log_test_header(total_operations, ops_per_sec=20.0)
    logger.info(f"测试通道: {channels}")
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_operations, 0, 0, start_time)
    
    try:
        for i in range(total_operations):
            # 反转状态
            expected_state = 1 - expected_state
            
            # 设置4个通道电源（同时翻转）
            set_result = hub.set_channel_power(1, 2, 3, 4, state=expected_state)
            
            if not set_result:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：设置4个通道失败")
                continue
            
            # 短暂等待，确保状态已更新
            time.sleep(0.01)
            
            # 获取4个通道电源值并校验
            try:
                status = hub.get_channel_power_status(1, 2, 3, 4)
                
                if status is None:
                    failure_count += 1
                    logger.warning(f"  第 {i+1} 次操作：读取4个通道状态失败（返回None）")
                    continue
                
                # 校验所有4个通道是否一致
                all_match = True
                for ch in channels:
                    if status[ch] != expected_state:
                        all_match = False
                        logger.warning(f"  第 {i+1} 次操作：通道 {ch} 状态不一致，期望 {expected_state}，实际 {status[ch]}")
                
                if all_match:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：读取4个通道状态失败: {e}")
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次操作")
        raise
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time
    
    logger.info(f"  总操作次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 99, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ 4个通道（1,2,3,4）同时翻转压力测试通过，成功率 {success_rate:.1f}%")


@pytest.mark.parametrize("num_channels", [2, 3, 4])
def test_high_speed_multiple_channels_power(hub, max_channels, num_channels):
    """压力测试：多个通道电源控制 - 设置、读取、校验、反转状态"""
    if num_channels > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要 {num_channels} 个通道")
    
    channels = list(range(1, num_channels + 1))
    logger.info(f"压力测试：{num_channels} 个通道电源控制（设置->读取->校验->反转）{channels}...")
    
    # 初始化状态为关闭
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
    expected_state = 0
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"测试总次数: {total_operations:,} 次")
    # 显示预估时间（多通道操作稍慢，约20次/秒）
    _, time_str = estimate_test_time(total_operations, ops_per_sec=20.0)
    logger.info(f"预估耗时: {time_str} (基于实际速度 20次/秒)")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_operations, 0, 0, start_time)
    
    try:
        for i in range(total_operations):
            # 反转状态
            expected_state = 1 - expected_state
            
            # 设置通道电源
            set_result = hub.set_channel_power(*channels, state=expected_state)
            
            if not set_result:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：设置通道 {channels} 失败")
                continue
            
            # 短暂等待，确保状态已更新
            time.sleep(0.02)
            
            # 获取通道电源值并校验
            try:
                status = hub.get_channel_power_status(*channels)
                
                if status is None:
                    failure_count += 1
                    logger.warning(f"  第 {i+1} 次操作：读取通道 {channels} 状态失败（返回None）")
                    continue
                
                # 校验所有通道是否一致
                all_match = True
                for ch in channels:
                    if status[ch] != expected_state:
                        all_match = False
                        logger.warning(f"  第 {i+1} 次操作：通道 {ch} 状态不一致，期望 {expected_state}，实际 {status[ch]}")
                
                if all_match:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作：读取通道 {channels} 状态失败: {e}")
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次操作")
        raise
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time
    
    logger.info(f"  总操作次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 98, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ {num_channels} 个通道压力测试通过，成功率 {success_rate:.1f}%")


def test_high_speed_alternating_channels(hub, max_channels):
    """压力测试：交替控制不同通道 - 设置、读取、校验、反转状态"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"压力测试：交替控制通道（设置->读取->校验->反转）{channels}...")
    
    # 初始化所有通道为关闭
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
    
    total_cycles = STRESS_TEST_TOTAL_COUNT
    log_test_header(total_cycles, ops_per_sec=18.0)
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_cycles, 0, 0, start_time)
    
    try:
        for cycle in range(total_cycles):
            cycle_success = True
            
            # 反转状态：奇数通道打开，偶数通道关闭
            expected_states = {}
            for ch in channels:
                if cycle % 2 == 0:
                    # 偶数周期：奇数通道开，偶数通道关
                    expected_states[ch] = 1 if ch % 2 == 1 else 0
                else:
                    # 奇数周期：偶数通道开，奇数通道关
                    expected_states[ch] = 1 if ch % 2 == 0 else 0
            
            # 设置每个通道的状态
            for ch in channels:
                result = hub.set_channel_power(ch, state=expected_states[ch])
                if not result:
                    cycle_success = False
            
            # 短暂等待
            time.sleep(0.02)
            
            # 读取并校验所有通道状态
            try:
                status = hub.get_channel_power_status(*channels)
                
                if status is None:
                    failure_count += 1
                    cycle_success = False
                    logger.warning(f"  第 {cycle+1} 次周期：读取状态失败（返回None）")
                else:
                    # 校验每个通道
                    for ch in channels:
                        if status[ch] != expected_states[ch]:
                            cycle_success = False
                            logger.warning(f"  第 {cycle+1} 次周期：通道 {ch} 状态不一致，期望 {expected_states[ch]}，实际 {status[ch]}")
            except Exception as e:
                failure_count += 1
                cycle_success = False
                logger.warning(f"  第 {cycle+1} 次周期：读取状态失败: {e}")
            
            if cycle_success:
                success_count += 1
            else:
                failure_count += 1
            
            # 按秒刷新进度（避免刷屏）
            print_progress(cycle + 1, total_cycles, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(cycle + 1, total_cycles, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {cycle+1}/{total_cycles} 次周期")
        raise
    
    # 完成时换行
    print_progress(total_cycles, total_cycles, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_cycles / elapsed_time
    
    logger.info(f"  总周期数: {total_cycles}")
    logger.info(f"  成功周期: {success_count}")
    logger.info(f"  失败周期: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  周期频率: {ops_per_sec:.1f} 周期/秒")
    
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ 交替控制压力测试通过，成功率 {success_rate:.1f}%")


def test_high_speed_mixed_operations(hub, max_channels):
    """压力测试：混合操作（单通道、多通道、全部通道）- 设置、读取、校验、反转状态"""
    all_channels = list(range(1, max_channels + 1))
    logger.info(f"压力测试：混合操作模式（设置->读取->校验->反转）...")
    
    # 初始化所有通道为关闭
    hub.set_channel_power(*all_channels, state=0)
    time.sleep(0.2)
    
    operations = []
    # 生成混合操作序列
    for i in range(STRESS_TEST_TOTAL_COUNT):
        if i % 4 == 0:
            # 全部通道
            operations.append(("all", all_channels))
        elif i % 4 == 1:
            # 单通道
            operations.append(("single", [1]))
        elif i % 4 == 2:
            # 两个通道
            if max_channels >= 2:
                operations.append(("pair", [1, 2]))
        else:
            # 三个通道
            if max_channels >= 3:
                operations.append(("triple", [1, 2, 3]))
    
    success_count = 0
    failure_count = 0
    start_time = time.time()
    expected_state = 0
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, len(operations), 0, 0, start_time)
    
    try:
        for i, (op_type, channels) in enumerate(operations):
            # 反转状态
            expected_state = 1 - expected_state
            
            # 设置通道电源
            set_result = hub.set_channel_power(*channels, state=expected_state)
            
            if not set_result:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作（{op_type} {channels}）：设置失败")
                continue
            
            # 短暂等待
            time.sleep(0.02)
            
            # 读取并校验
            try:
                status = hub.get_channel_power_status(*channels)
                
                if status is None:
                    failure_count += 1
                    logger.warning(f"  第 {i+1} 次操作（{op_type} {channels}）：读取失败（返回None）")
                    continue
                
                # 校验所有通道是否一致（单通道返回int，多通道返回dict）
                all_match = True
                if len(channels) == 1:
                    # 单通道返回int
                    if status != expected_state:
                        all_match = False
                        logger.warning(f"  第 {i+1} 次操作（{op_type} {channels}）：通道 {channels[0]} 状态不一致，期望 {expected_state}，实际 {status}")
                else:
                    # 多通道返回dict
                    for ch in channels:
                        if status[ch] != expected_state:
                            all_match = False
                            logger.warning(f"  第 {i+1} 次操作（{op_type} {channels}）：通道 {ch} 状态不一致，期望 {expected_state}，实际 {status[ch]}")
                
                if all_match:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                failure_count += 1
                logger.warning(f"  第 {i+1} 次操作（{op_type} {channels}）：读取失败: {e}")
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, len(operations), success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, len(operations), success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{len(operations)} 次操作")
        raise
    
    # 完成时换行
    print_progress(len(operations), len(operations), success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = len(operations) / elapsed_time
    
    logger.info(f"  总操作次数: {len(operations)}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，压力测试失败"
    logger.info(f"  ✓ 混合操作压力测试通过，成功率 {success_rate:.1f}%")


def test_high_speed_extreme_stress(hub, max_channels):
    """极限压力测试：极高频率操作 - 设置、读取、校验、反转状态"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"极限压力测试：极高频率操作（设置->读取->校验->反转）{channels}...")
    
    # 初始化所有通道为关闭
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.1)
    expected_state = 0
    
    total_operations = STRESS_TEST_TOTAL_COUNT
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"测试总次数: {total_operations:,} 次")
    # 显示预估时间（极限测试不等待，约30次/秒）
    _, time_str = estimate_test_time(total_operations, ops_per_sec=30.0)
    logger.info(f"预估耗时: {time_str} (基于实际速度 30次/秒)")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, total_operations, 0, 0, start_time)
    
    # 极限测试：几乎不等待
    try:
        for i in range(total_operations):
            # 反转状态
            expected_state = 1 - expected_state
            
            # 设置通道电源
            set_result = hub.set_channel_power(*channels, state=expected_state)
            
            if not set_result:
                failure_count += 1
                continue
            
            # 立即读取并校验（不等待）
            try:
                status = hub.get_channel_power_status(*channels)
                
                if status is None:
                    failure_count += 1
                    continue
                
                # 校验所有通道是否一致
                all_match = True
                for ch in channels:
                    if status[ch] != expected_state:
                        all_match = False
                        break
                
                if all_match:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception:
                failure_count += 1
            
            # 每次操作后更新进度（在同一行更新）
            print_progress(i + 1, total_operations, success_count, failure_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, total_operations, success_count, failure_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{total_operations} 次操作")
        raise
    
    # 完成时换行
    print_progress(total_operations, total_operations, success_count, failure_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    total_checks = success_count + failure_count
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    ops_per_sec = total_operations / elapsed_time
    
    logger.info(f"  总操作次数: {total_operations}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  失败次数: {failure_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  操作频率: {ops_per_sec:.1f} 次/秒")
    
    # 极限测试要求稍低，因为频率极高
    assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%，极限压力测试失败"
    logger.info(f"  ✓ 极限压力测试通过，最高频率 {ops_per_sec:.1f} 次/秒，成功率 {success_rate:.1f}%")


# ==================== 获取电源状态稳定性测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_power_status_read_stability_single(hub, max_channels, channel):
    """测试单个通道状态读取的稳定性"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 状态读取稳定性...")
    
    # 先设置为关闭状态
    hub.set_channel_power(channel, state=0)
    time.sleep(0.2)
    
    # 连续读取，验证一致性
    read_count = STRESS_TEST_TOTAL_COUNT
    log_test_header(read_count, ops_per_sec=500.0)
    success_count = 0
    inconsistent_count = 0
    last_status = None
    
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, read_count, 0, 0, start_time)
    
    try:
        for i in range(read_count):
            try:
                status = hub.get_channel_power_status(channel)
                if isinstance(status, dict):
                    status = status[channel]
                
                if status is not None:
                    success_count += 1
                    if last_status is not None and status != last_status:
                        inconsistent_count += 1
                    last_status = status
                
                # 按秒刷新进度（避免刷屏）
                print_progress(i + 1, read_count, success_count, inconsistent_count, start_time)
            except Exception as e:
                logger.warning(f"  第 {i+1} 次读取失败: {e}")
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, read_count, success_count, inconsistent_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{read_count} 次读取")
        raise
    
    # 完成时换行
    print_progress(read_count, read_count, success_count, inconsistent_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    success_rate = (success_count / read_count) * 100
    read_per_sec = read_count / elapsed_time
    
    logger.info(f"  读取次数: {read_count}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  不一致次数: {inconsistent_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  读取频率: {read_per_sec:.1f} 次/秒")
    
    assert success_rate >= 95, f"状态读取成功率过低: {success_rate:.1f}%"
    assert inconsistent_count == 0, f"状态不一致: {inconsistent_count} 次，状态应该保持稳定"
    logger.info(f"  ✓ 通道 {channel} 状态读取稳定")


def test_power_status_read_stability_all_channels(hub, max_channels):
    """测试所有通道状态读取的稳定性"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试所有通道状态读取稳定性: {channels}...")
    
    # 设置已知状态：奇数通道打开，偶数通道关闭
    odd_channels = [ch for ch in channels if ch % 2 == 1]
    even_channels = [ch for ch in channels if ch % 2 == 0]
    
    if odd_channels:
        hub.set_channel_power(*odd_channels, state=1)
    if even_channels:
        hub.set_channel_power(*even_channels, state=0)
    time.sleep(0.3)
    
    # 连续读取
    read_count = STRESS_TEST_TOTAL_COUNT
    log_test_header(read_count, ops_per_sec=400.0)
    
    success_count = 0
    inconsistent_count = 0
    
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, read_count, 0, 0, start_time)
    
    try:
        for i in range(read_count):
            try:
                status = hub.get_channel_power_status(*channels)
                if status is not None and len(status) == len(channels):
                    success_count += 1
                    # 验证状态是否正确
                    for ch in channels:
                        expected = 1 if ch in odd_channels else 0
                        if status[ch] != expected:
                            inconsistent_count += 1
                            # 只在每10万次时记录错误，避免日志过多
                            if (i + 1) % 100000 == 0:
                                logger.warning(f"  第 {i+1} 次读取：通道 {ch} 状态错误，期望 {expected}，实际 {status[ch]}")
                
                # 按秒刷新进度（避免刷屏）
                print_progress(i + 1, read_count, success_count, inconsistent_count, start_time)
            except Exception as e:
                logger.warning(f"  第 {i+1} 次读取失败: {e}")
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, read_count, success_count, inconsistent_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{read_count} 次读取")
        raise
    
    # 完成时换行
    print_progress(read_count, read_count, success_count, inconsistent_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    success_rate = (success_count / read_count) * 100
    read_per_sec = read_count / elapsed_time
    
    logger.info(f"  读取次数: {read_count}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  不一致次数: {inconsistent_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  读取频率: {read_per_sec:.1f} 次/秒")
    
    assert success_rate >= 95, f"状态读取成功率过低: {success_rate:.1f}%"
    assert inconsistent_count < read_count * max_channels * 0.05, f"状态不一致过多: {inconsistent_count} 次"
    logger.info(f"  ✓ 所有通道状态读取稳定")
    
    # 清理
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)


def test_power_status_read_accuracy(hub, max_channels):
    """测试状态读取的准确性"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试状态读取准确性: {channels}...")
    
    test_cases = [
        ([1], 1, "单通道打开"),
        ([1], 0, "单通道关闭"),
        ([1, 2], 1, "两通道打开"),
        ([1, 2], 0, "两通道关闭"),
        (channels, 1, "所有通道打开"),
        (channels, 0, "所有通道关闭"),
    ]
    
    accuracy_count = 0
    total_tests = len(test_cases)
    
    for test_channels, expected_state, description in test_cases:
        # 过滤有效通道
        valid_channels = [ch for ch in test_channels if ch <= max_channels]
        if not valid_channels:
            continue
        
        logger.info(f"  测试: {description} {valid_channels}...")
        
        # 设置状态
        hub.set_channel_power(*valid_channels, state=expected_state)
        time.sleep(0.2)
        
        # 读取状态
        status = hub.get_channel_power_status(*valid_channels)
        assert status is not None, f"{description} 状态读取失败"
        
        # 验证准确性（单通道返回int，多通道返回dict）
        all_correct = True
        if len(valid_channels) == 1:
            # 单通道返回int
            if status != expected_state:
                all_correct = False
                logger.error(f"    通道 {valid_channels[0]} 状态错误：期望 {expected_state}，实际 {status}")
        else:
            # 多通道返回dict
            for ch in valid_channels:
                if status[ch] != expected_state:
                    all_correct = False
                    logger.error(f"    通道 {ch} 状态错误：期望 {expected_state}，实际 {status[ch]}")
        
        if all_correct:
            accuracy_count += 1
            logger.info(f"    ✓ {description} 状态准确")
        else:
            logger.error(f"    ✗ {description} 状态不准确")
    
    accuracy_rate = (accuracy_count / total_tests) * 100
    logger.info(f"  准确率: {accuracy_count}/{total_tests} ({accuracy_rate:.1f}%)")
    
    assert accuracy_rate == 100, f"状态读取准确率不足: {accuracy_rate:.1f}%"
    logger.info(f"  ✓ 状态读取准确性测试通过")


def test_power_status_read_during_operations(hub, max_channels):
    """测试在操作过程中读取状态的稳定性"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试操作过程中状态读取稳定性: {channels}...")
    
    operations = STRESS_TEST_TOTAL_COUNT
    read_errors = 0
    status_mismatches = 0
    
    try:
        for i in range(operations):
            # 打开通道
            result = hub.set_channel_power(*channels, state=1)
            time.sleep(0.05)  # 短暂等待
            
            # 立即读取状态
            try:
                status = hub.get_channel_power_status(*channels)
                if status is None:
                    read_errors += 1
                else:
                    # 验证状态
                    for ch in channels:
                        if status[ch] != 1:
                            status_mismatches += 1
                            logger.warning(f"  第 {i+1} 次操作：通道 {ch} 状态不匹配，期望1，实际{status[ch]}")
            except Exception as e:
                read_errors += 1
                logger.warning(f"  第 {i+1} 次读取失败: {e}")
            
            # 关闭通道
            result = hub.set_channel_power(*channels, state=0)
            time.sleep(0.05)
            
            # 立即读取状态
            try:
                status = hub.get_channel_power_status(*channels)
                if status is None:
                    read_errors += 1
                else:
                    # 验证状态
                    for ch in channels:
                        if status[ch] != 0:
                            status_mismatches += 1
                            logger.warning(f"  第 {i+1} 次操作：通道 {ch} 状态不匹配，期望0，实际{status[ch]}")
            except Exception as e:
                read_errors += 1
                logger.warning(f"  第 {i+1} 次读取失败: {e}")
    except KeyboardInterrupt:
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{operations} 次操作")
        raise
    
    total_reads = operations * 2
    error_rate = (read_errors / total_reads) * 100
    mismatch_rate = (status_mismatches / (total_reads * max_channels)) * 100
    
    logger.info(f"  操作次数: {operations}")
    logger.info(f"  总读取次数: {total_reads}")
    logger.info(f"  读取错误: {read_errors}")
    logger.info(f"  状态不匹配: {status_mismatches}")
    logger.info(f"  错误率: {error_rate:.1f}%")
    logger.info(f"  不匹配率: {mismatch_rate:.1f}%")
    
    assert error_rate < 5, f"读取错误率过高: {error_rate:.1f}%"
    assert mismatch_rate < 5, f"状态不匹配率过高: {mismatch_rate:.1f}%"
    logger.info(f"  ✓ 操作过程中状态读取稳定")


def test_power_status_read_high_frequency(hub, max_channels):
    """测试高频状态读取的稳定性"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试高频状态读取稳定性: {channels}...")
    
    # 设置一个已知状态
    hub.set_channel_power(*channels, state=1)
    time.sleep(0.2)
    
    # 高频读取
    read_count = STRESS_TEST_TOTAL_COUNT
    log_test_header(read_count, ops_per_sec=500.0)
    
    success_count = 0
    error_count = 0
    inconsistent_count = 0
    last_status = None
    
    start_time = time.time()
    logger.info(f"  开始100万次高频状态读取测试，预计耗时约33分钟...")
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, read_count, 0, 0, start_time)
    
    try:
        for i in range(read_count):
            try:
                status = hub.get_channel_power_status(*channels)
                if status is not None and len(status) == len(channels):
                    success_count += 1
                    
                    # 检查一致性
                    if last_status is not None:
                        for ch in channels:
                            if status[ch] != last_status[ch]:
                                inconsistent_count += 1
                                break
                    last_status = status
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                if (i + 1) % 100000 == 0:  # 每10万次记录一次错误
                    logger.warning(f"  第 {i+1} 次读取失败: {e}")
            
            # 按秒刷新进度（避免刷屏）
            print_progress(i + 1, read_count, success_count, error_count + inconsistent_count, start_time)
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, read_count, success_count, error_count + inconsistent_count, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{read_count} 次读取")
        raise
    
    # 完成时换行
    print_progress(read_count, read_count, success_count, error_count + inconsistent_count, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    success_rate = (success_count / read_count) * 100
    read_per_sec = read_count / elapsed_time
    
    logger.info(f"  读取次数: {read_count}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  错误次数: {error_count}")
    logger.info(f"  不一致次数: {inconsistent_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  读取频率: {read_per_sec:.1f} 次/秒")
    
    assert success_rate >= 98, f"高频读取成功率过低: {success_rate:.1f}%"
    assert inconsistent_count < read_count * 0.02, f"状态不一致过多: {inconsistent_count} 次"
    logger.info(f"  ✓ 高频状态读取稳定，频率 {read_per_sec:.1f} 次/秒")
    
    # 清理
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)


def test_power_status_read_after_state_change(hub, max_channels):
    """测试状态改变后立即读取的准确性"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试状态改变后立即读取准确性: {channels}...")
    
    test_count = STRESS_TEST_TOTAL_COUNT
    accurate_count = 0
    
    try:
        for i in range(test_count):
            # 打开通道
            hub.set_channel_power(*channels, state=1)
            # 立即读取（不等待）
            status = hub.get_channel_power_status(*channels)
            
            if status is not None:
                all_on = all(status[ch] == 1 for ch in channels)
                if all_on:
                    accurate_count += 1
                else:
                    logger.warning(f"  第 {i+1} 次：打开后立即读取，部分通道状态不正确")
            
            # 关闭通道
            hub.set_channel_power(*channels, state=0)
            # 立即读取（不等待）
            status = hub.get_channel_power_status(*channels)
            
            if status is not None:
                all_off = all(status[ch] == 0 for ch in channels)
                if all_off:
                    accurate_count += 1
                else:
                    logger.warning(f"  第 {i+1} 次：关闭后立即读取，部分通道状态不正确")
    except KeyboardInterrupt:
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{test_count} 次操作")
        raise
    
    total_checks = test_count * 2
    accuracy_rate = (accurate_count / total_checks) * 100
    
    logger.info(f"  测试次数: {test_count}")
    logger.info(f"  总检查次数: {total_checks}")
    logger.info(f"  准确次数: {accurate_count}")
    logger.info(f"  准确率: {accuracy_rate:.1f}%")
    
    # 状态改变后立即读取可能不够准确，所以要求稍低
    assert accuracy_rate >= 80, f"状态改变后立即读取准确率过低: {accuracy_rate:.1f}%"
    logger.info(f"  ✓ 状态改变后立即读取测试通过")


@pytest.mark.parametrize("num_channels", [1, 2, 3, 4])
def test_power_status_read_different_channel_counts(hub, max_channels, num_channels):
    """测试不同通道数量的状态读取稳定性"""
    if num_channels > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，需要 {num_channels} 个通道")
    
    channels = list(range(1, num_channels + 1))
    logger.info(f"测试 {num_channels} 个通道状态读取稳定性: {channels}...")
    
    # 设置状态
    hub.set_channel_power(*channels, state=1)
    time.sleep(0.2)
    
    # 读取
    read_count = STRESS_TEST_TOTAL_COUNT
    ops_per_sec = 500.0 if num_channels == 1 else 400.0
    logger.info("━" * 70)
    logger.info(f"测试总次数: {read_count:,} 次 ({num_channels} 个通道)")
    _, time_str = estimate_test_time(read_count, ops_per_sec)
    logger.info(f"预估耗时: {time_str} (基于实际速度 {ops_per_sec}次/秒)")
    logger.info("━" * 70)
    
    success_count = 0
    
    start_time = time.time()
    
    # 初始化进度显示（立即显示一次）
    print_progress(0, read_count, 0, 0, start_time)
    
    try:
        for i in range(read_count):
            # 按秒刷新进度（避免刷屏）
            print_progress(i + 1, read_count, success_count, 0, start_time)
            
            try:
                status = hub.get_channel_power_status(*channels)
                if status is not None:
                    # 验证所有通道都是打开状态（单通道返回int，多通道返回dict）
                    if num_channels == 1:
                        # 单通道返回int
                        if status == 1:
                            success_count += 1
                    else:
                        # 多通道返回dict（只包含查询的通道）
                        if isinstance(status, dict) and len(status) == num_channels:
                            # 检查所有查询的通道都在返回的dict中，且状态都是1
                            if all(status.get(ch) == 1 for ch in channels):
                                success_count += 1
            except Exception as e:
                if (i + 1) % 100000 == 0:
                    logger.warning(f"  第 {i+1} 次读取失败: {e}")
    except KeyboardInterrupt:
        # 用户按 Ctrl+C，立即退出
        print_progress(i + 1, read_count, success_count, 0, start_time, end_line=True)
        logger.warning(f"\n⚠ 测试被用户中断（Ctrl+C），已完成 {i+1}/{read_count} 次读取")
        raise
    
    # 完成时换行
    print_progress(read_count, read_count, success_count, 0, start_time, end_line=True)
    
    elapsed_time = time.time() - start_time
    success_rate = (success_count / read_count) * 100
    read_per_sec = read_count / elapsed_time
    
    logger.info(f"  读取次数: {read_count}")
    logger.info(f"  成功次数: {success_count}")
    logger.info(f"  成功率: {success_rate:.1f}%")
    logger.info(f"  总耗时: {elapsed_time:.2f}s")
    logger.info(f"  读取频率: {read_per_sec:.1f} 次/秒")
    
    assert success_rate >= 95, f"{num_channels} 个通道状态读取成功率过低: {success_rate:.1f}%"
    logger.info(f"  ✓ {num_channels} 个通道状态读取稳定")
    
    # 清理
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)
