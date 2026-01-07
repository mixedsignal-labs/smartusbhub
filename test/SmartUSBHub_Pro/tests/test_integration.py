"""
集成测试 - 直接连接真实设备进行测试

使用方法:
    # 运行所有集成测试
    pytest test/test_integration.py -v

    # 运行特定测试
    pytest test/test_integration.py::test_get_device_info -v

    # 显示详细日志
    pytest test/test_integration.py -v -s --log-cli-level=INFO
"""
import pytest
import time
import logging
import sys
import os

# 在源码仓库中，需要将项目根目录添加到路径（从产品子目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

# 配置日志
logger = logging.getLogger(__name__)

# 使用 conftest.py 中定义的 fixtures (hub, max_channels)


# ==================== 连接和基本信息测试 ====================

def test_device_connection(hub):
    """测试设备连接"""
    assert hub is not None
    assert hub.is_connected()
    logger.info("✓ 设备连接正常")


def test_get_device_info(hub):
    """测试获取设备信息"""
    logger.info("正在获取设备信息...")
    info = hub.get_device_info()
    
    assert info is not None
    
    # 检查必需字段
    required_fields = [
        'id', 'address', 'hardware_version', 'firmware_version',
        'product_type', 'max_channels', 'serial_no',
        'operate_mode', 'auto_restore', 'button_control_status'
    ]
    for field in required_fields:
        assert field in info, f"缺少字段: {field}"
    
    # 打印设备信息
    logger.info("设备信息:")
    logger.info(f"  ID: {info.get('id')}")
    logger.info(f"  地址: 0x{info.get('address'):04X}" if isinstance(info.get('address'), int) else f"  地址: {info.get('address')}")
    logger.info(f"  硬件版本: V1.{info.get('hardware_version')}")
    logger.info(f"  固件版本: V1.{info.get('firmware_version')}")
    logger.info(f"  产品类型: {info.get('product_type')}")
    logger.info(f"  最大通道数: {info.get('max_channels')}")
    logger.info(f"  序列号: {info.get('serial_no')}")
    logger.info(f"  工作模式: {info.get('operate_mode')}")
    logger.info(f"  自动恢复: {info.get('auto_restore')}")
    logger.info(f"  按钮控制: {info.get('button_control_status')}")


def test_get_versions(hub):
    """测试获取版本信息"""
    logger.info("正在获取版本信息...")
    
    hw_version = hub.get_hardware_version()
    fw_version = hub.get_firmware_version()
    
    assert hw_version is not None
    assert fw_version is not None
    
    logger.info(f"  硬件版本: V1.{hw_version}")
    logger.info(f"  固件版本: V1.{fw_version}")


def test_get_serial_no(hub):
    """测试获取序列号"""
    logger.info("正在获取序列号...")
    
    serial_no = hub.get_serial_no()
    assert serial_no is not None
    assert isinstance(serial_no, str)
    assert len(serial_no) > 0
    
    logger.info(f"  序列号: {serial_no}")


# ==================== 电源控制测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_set_channel_power_single(hub, max_channels, channel):
    """测试每个通道的电源控制"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 电源控制...")
    
    # 获取初始状态
    initial_status = hub.get_channel_power_status(channel)
    logger.info(f"  初始状态: {initial_status}")
    
    # 打开
    logger.info(f"  打开通道 {channel}...")
    result = hub.set_channel_power(channel, state=1)
    assert result
    time.sleep(0.2)
    
    status = hub.get_channel_power_status(channel)
    if isinstance(status, dict):
        status = status[channel]
    assert status == 1, f"通道 {channel} 应该打开"
    logger.info(f"  ✓ 通道 {channel} 已打开")
    
    # 关闭
    logger.info(f"  关闭通道 {channel}...")
    result = hub.set_channel_power(channel, state=0)
    assert result
    time.sleep(0.2)
    
    status = hub.get_channel_power_status(channel)
    if isinstance(status, dict):
        status = status[channel]
    assert status == 0, f"通道 {channel} 应该关闭"
    logger.info(f"  ✓ 通道 {channel} 已关闭")


def test_set_channel_power_all(hub, max_channels):
    """测试所有通道电源控制"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试所有通道电源控制: {channels}...")
    
    # 打开所有通道
    logger.info(f"  打开所有通道 {channels}...")
    result = hub.set_channel_power(*channels, state=1)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_power_status(*channels)
    for ch in channels:
        assert status[ch] == 1, f"通道 {ch} 应该打开"
    logger.info(f"  ✓ 所有通道已打开")
    
    # 关闭所有通道
    logger.info(f"  关闭所有通道 {channels}...")
    result = hub.set_channel_power(*channels, state=0)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_power_status(*channels)
    for ch in channels:
        assert status[ch] == 0, f"通道 {ch} 应该关闭"
    logger.info(f"  ✓ 所有通道已关闭")


@pytest.mark.parametrize("channels", [
    [1, 2],
    [1, 3],
    [2, 4],
    [1, 2, 3],
    [2, 3, 4],
])
def test_set_channel_power_combinations(hub, max_channels, channels):
    """测试各种通道组合的电源控制"""
    # 过滤掉超出范围的通道
    valid_channels = [ch for ch in channels if ch <= max_channels]
    if len(valid_channels) < 2:
        pytest.skip(f"需要至少2个有效通道，但只有 {valid_channels}")
    
    logger.info(f"测试通道组合电源控制: {valid_channels}...")
    
    # 打开组合通道
    logger.info(f"  打开通道 {valid_channels}...")
    result = hub.set_channel_power(*valid_channels, state=1)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_power_status(*valid_channels)
    for ch in valid_channels:
        assert status[ch] == 1, f"通道 {ch} 应该打开"
    logger.info(f"  ✓ 通道 {valid_channels} 已打开")
    
    # 关闭组合通道
    logger.info(f"  关闭通道 {valid_channels}...")
    result = hub.set_channel_power(*valid_channels, state=0)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_power_status(*valid_channels)
    for ch in valid_channels:
        assert status[ch] == 0, f"通道 {ch} 应该关闭"
    logger.info(f"  ✓ 通道 {valid_channels} 已关闭")


@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_power_interlock_mode(hub, max_channels, channel):
    """测试互锁模式 - 每个通道"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试互锁模式 - 通道 {channel}...")
    
    # 设置为互锁模式
    logger.info("  设置为互锁模式...")
    result = hub.set_operate_mode(1)
    assert result
    time.sleep(0.2)
    
    # 设置互锁通道
    logger.info(f"  设置互锁通道 {channel}...")
    result = hub.set_channel_power_interlock(channel)
    assert result
    time.sleep(0.3)
    
    # 验证只有这个通道打开
    all_channels = list(range(1, max_channels + 1))
    status = hub.get_channel_power_status(*all_channels)
    for i in all_channels:
        if i == channel:
            assert status[i] == 1, f"通道 {i} 应该打开"
        else:
            assert status[i] == 0, f"通道 {i} 应该关闭"
    logger.info(f"  ✓ 互锁验证通过 (仅通道 {channel} 打开)")
    
    # 禁用互锁
    logger.info("  禁用互锁模式...")
    result = hub.set_channel_power_interlock(None)
    assert result
    time.sleep(0.2)
    
    # 恢复普通模式
    logger.info("  恢复普通模式...")
    result = hub.set_operate_mode(0)
    assert result
    time.sleep(0.2)


# ==================== 监控测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_get_channel_voltage(hub, max_channels, channel):
    """测试每个通道的电压读取"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 电压读取...")
    
    # 检查是否支持ADC
    try:
        supports_adc = hub._check_feature_support("adc")
    except (ValueError, AttributeError):
        pytest.skip("无法确定产品是否支持ADC")
    
    if not supports_adc:
        pytest.skip(f"产品 {hub.get_product_name()} 不支持电压/电流监控")
    
    # 打开通道
    logger.info(f"  打开通道 {channel}...")
    hub.set_channel_power(channel, state=1)
    time.sleep(0.3)
    
    # 读取电压
    logger.info(f"  读取电压...")
    voltage = hub.get_channel_voltage(channel)
    assert voltage is not None, f"通道 {channel} 电压读取失败"
    assert 0 <= voltage <= 1000, f"通道 {channel} 电压值异常: {voltage}"  # 最大100.0V
    
    voltage_v = voltage / 10.0
    logger.info(f"  ✓ 通道 {channel} 电压: {voltage_v:.2f}V (原始值: {voltage})")
    
    # 关闭通道
    hub.set_channel_power(channel, state=0)
    time.sleep(0.2)


@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_get_channel_current(hub, max_channels, channel):
    """测试每个通道的电流读取"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 电流读取...")
    
    # 检查是否支持ADC
    try:
        supports_adc = hub._check_feature_support("adc")
    except (ValueError, AttributeError):
        pytest.skip("无法确定产品是否支持ADC")
    
    if not supports_adc:
        pytest.skip(f"产品 {hub.get_product_name()} 不支持电压/电流监控")
    
    # 打开通道
    logger.info(f"  打开通道 {channel}...")
    hub.set_channel_power(channel, state=1)
    time.sleep(0.3)
    
    # 读取电流
    logger.info(f"  读取电流...")
    current = hub.get_channel_current(channel)
    assert current is not None, f"通道 {channel} 电流读取失败"
    assert 0 <= current <= 10000, f"通道 {channel} 电流值异常: {current}"  # 最大100.00A
    
    current_a = current / 100.0
    logger.info(f"  ✓ 通道 {channel} 电流: {current_a:.2f}A (原始值: {current})")
    
    # 关闭通道
    hub.set_channel_power(channel, state=0)
    time.sleep(0.2)


def test_monitor_all_channels(hub, max_channels):
    """测试监控所有通道"""
    logger.info(f"测试监控所有 {max_channels} 个通道...")
    
    # 检查是否支持ADC
    try:
        supports_adc = hub._check_feature_support("adc")
    except (ValueError, AttributeError):
        pytest.skip("无法确定产品是否支持ADC")
    
    if not supports_adc:
        pytest.skip(f"产品 {hub.get_product_name()} 不支持电压/电流监控")
    
    # 打开所有通道
    channels = list(range(1, max_channels + 1))
    hub.set_channel_power(*channels, state=1)
    time.sleep(0.3)
    
    logger.info("  读取所有通道数据:")
    for ch in channels:
        try:
            voltage = hub.get_channel_voltage(ch)
            current = hub.get_channel_current(ch)
            if voltage is not None and current is not None:
                voltage_v = voltage / 10.0
                current_a = current / 100.0
                logger.info(f"    通道 {ch}: {voltage_v:.2f}V, {current_a:.2f}A")
            else:
                logger.warning(f"    通道 {ch}: 读取失败")
        except ValueError as e:
            logger.warning(f"    通道 {ch}: {e}")
    
    # 关闭所有通道
    hub.set_channel_power(*channels, state=0)
    time.sleep(0.2)


# ==================== 数据线控制测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_set_channel_dataline(hub, max_channels, channel):
    """测试每个通道的数据线控制"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 数据线控制...")
    
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
    
    # 打开数据线
    logger.info(f"  打开通道 {channel} 数据线...")
    result = hub.set_channel_usb2_dataline(channel, state=1)
    assert result
    time.sleep(0.2)
    
    status = hub.get_channel_usb2_dataline_status(channel)
    if isinstance(status, dict):
        status = status[channel]
    assert status == 1, f"通道 {channel} 数据线应该打开"
    logger.info(f"  ✓ 通道 {channel} 数据线已打开")
    
    # 关闭数据线
    logger.info(f"  关闭通道 {channel} 数据线...")
    result = hub.set_channel_usb2_dataline(channel, state=0)
    assert result
    time.sleep(0.2)
    
    status = hub.get_channel_usb2_dataline_status(channel)
    if isinstance(status, dict):
        status = status[channel]
    assert status == 0, f"通道 {channel} 数据线应该关闭"
    logger.info(f"  ✓ 通道 {channel} 数据线已关闭")


# ==================== 设置测试 ====================

def test_operate_mode(hub):
    """测试工作模式设置"""
    logger.info("测试工作模式设置...")
    
    # 设置为互锁模式
    logger.info("  设置为互锁模式...")
    result = hub.set_operate_mode(1)
    assert result
    time.sleep(0.2)
    
    mode = hub.get_operate_mode()
    assert mode == 1
    logger.info(f"  ✓ 工作模式: 互锁")
    
    # 恢复普通模式
    logger.info("  恢复普通模式...")
    result = hub.set_operate_mode(0)
    assert result
    time.sleep(0.2)
    
    mode = hub.get_operate_mode()
    assert mode == 0
    logger.info(f"  ✓ 工作模式: 普通")


def test_button_control(hub):
    """测试按钮控制"""
    logger.info("测试按钮控制...")
    
    # 启用按钮控制
    logger.info("  启用按钮控制...")
    result = hub.set_button_control(1)
    assert result
    time.sleep(0.2)
    
    status = hub.get_button_control_status()
    assert status == 1
    logger.info(f"  ✓ 按钮控制: 启用")
    
    # 禁用按钮控制
    logger.info("  禁用按钮控制...")
    result = hub.set_button_control(0)
    assert result
    time.sleep(0.2)
    
    status = hub.get_button_control_status()
    assert status == 0
    logger.info(f"  ✓ 按钮控制: 禁用")


def test_auto_restore(hub):
    """测试自动恢复设置"""
    logger.info("测试自动恢复设置...")
    
    # 启用自动恢复
    logger.info("  启用自动恢复...")
    result = hub.set_auto_restore(1)
    assert result
    time.sleep(0.2)
    
    status = hub.get_auto_restore_status()
    assert status == 1
    logger.info(f"  ✓ 自动恢复: 启用")
    
    # 禁用自动恢复
    logger.info("  禁用自动恢复...")
    result = hub.set_auto_restore(0)
    assert result
    time.sleep(0.2)
    
    status = hub.get_auto_restore_status()
    assert status == 0
    logger.info(f"  ✓ 自动恢复: 禁用")


def test_device_address(hub):
    """测试设备地址设置"""
    logger.info("测试设备地址设置...")
    
    # 获取原始地址
    original_address = hub.get_device_address()
    logger.info(f"  原始地址: 0x{original_address:04X}")
    
    # 设置新地址
    new_address = 0x0001
    logger.info(f"  设置新地址: 0x{new_address:04X}...")
    result = hub.set_device_address(new_address)
    assert result
    time.sleep(0.2)
    
    address = hub.get_device_address()
    assert address == new_address
    logger.info(f"  ✓ 地址设置成功")
    
    # 恢复原始地址
    logger.info(f"  恢复原始地址: 0x{original_address:04X}...")
    result = hub.set_device_address(original_address)
    assert result
    time.sleep(0.2)
    logger.info(f"  ✓ 地址已恢复")


# ==================== 充电模式测试 ====================

@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_slow_charge_mode(hub, max_channels, channel):
    """测试每个通道的慢充模式"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 慢充模式...")
    
    # 设置为慢充
    logger.info(f"  设置为慢充模式...")
    result = hub.set_channel_slow_charge(channel)
    assert result
    time.sleep(0.3)
    
    mode = hub.get_channel_charge_mode(channel)
    assert mode is not None, f"通道 {channel} 充电模式读取失败"
    mode_value = mode[channel] if isinstance(mode, dict) else mode
    logger.info(f"  ✓ 通道 {channel} 充电模式: {mode_value}")


@pytest.mark.parametrize("channel", [1, 2, 3, 4])
def test_fast_charge_mode(hub, max_channels, channel):
    """测试每个通道的快充模式"""
    if channel > max_channels:
        pytest.skip(f"设备只有 {max_channels} 个通道，跳过通道 {channel}")
    
    logger.info(f"测试通道 {channel} 快充模式...")
    
    # 设置为快充
    logger.info(f"  设置为快充模式...")
    result = hub.set_channel_fast_charge(channel)
    assert result
    time.sleep(0.3)
    
    mode = hub.get_channel_charge_mode(channel)
    assert mode is not None, f"通道 {channel} 充电模式读取失败"
    mode_value = mode[channel] if isinstance(mode, dict) else mode
    logger.info(f"  ✓ 通道 {channel} 充电模式: {mode_value}")


# ==================== 综合测试 ====================

def test_power_sequence_all_channels(hub, max_channels):
    """测试所有通道的电源序列控制"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试所有通道的电源序列控制: {channels}...")
    
    # 按顺序打开每个通道
    for ch in channels:
        logger.info(f"  打开通道 {ch}...")
        result = hub.set_channel_power(ch, state=1)
        assert result
        time.sleep(0.2)
        
        status = hub.get_channel_power_status(ch)
        if isinstance(status, dict):
            status = status[ch]
        assert status == 1, f"通道 {ch} 应该打开"
        logger.info(f"  ✓ 通道 {ch} 已打开")
    
    # 按顺序关闭每个通道
    for ch in reversed(channels):
        logger.info(f"  关闭通道 {ch}...")
        result = hub.set_channel_power(ch, state=0)
        assert result
        time.sleep(0.2)
        
        status = hub.get_channel_power_status(ch)
        if isinstance(status, dict):
            status = status[ch]
        assert status == 0, f"通道 {ch} 应该关闭"
        logger.info(f"  ✓ 通道 {ch} 已关闭")


def test_get_all_channels_status(hub, max_channels):
    """测试获取所有通道的状态（电源、USB2数据线、USB3数据线）并验证返回值是否齐全"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试获取所有通道状态: {channels}...")
    
    # 获取所有通道的电源状态
    power_status = hub.get_channel_power_status(*channels)
    assert power_status is not None, "电源状态读取失败"
    assert isinstance(power_status, dict), f"电源状态应该返回字典，实际返回: {type(power_status)}"
    assert len(power_status) == len(channels), f"电源状态应该包含 {len(channels)} 个通道，实际包含 {len(power_status)} 个"
    logger.info("  电源状态:")
    for ch in channels:
        assert ch in power_status, f"电源状态缺少通道 {ch}"
        status = power_status[ch]
        assert status in [0, 1], f"通道 {ch} 电源状态值异常: {status}"
        logger.info(f"    通道 {ch}: {'ON' if status == 1 else 'OFF'}")
    logger.info(f"  ✓ 电源状态返回值齐全，包含所有 {len(channels)} 个通道")
    
    # 获取所有通道的USB2数据线状态
    try:
        dataline_status = hub.get_channel_usb2_dataline_status(*channels)
        assert dataline_status is not None, "USB2数据线状态读取失败"
        assert isinstance(dataline_status, dict), f"USB2数据线状态应该返回字典，实际返回: {type(dataline_status)}"
        assert len(dataline_status) == len(channels), f"USB2数据线状态应该包含 {len(channels)} 个通道，实际包含 {len(dataline_status)} 个"
        logger.info("  USB2数据线状态:")
        for ch in channels:
            assert ch in dataline_status, f"USB2数据线状态缺少通道 {ch}"
            status = dataline_status[ch]
            assert status in [0, 1], f"通道 {ch} USB2数据线状态值异常: {status}"
            logger.info(f"    通道 {ch}: {'ON' if status == 1 else 'OFF'}")
        logger.info(f"  ✓ USB2数据线状态返回值齐全，包含所有 {len(channels)} 个通道")
    except Exception as e:
        logger.info(f"  USB2数据线状态: 不支持 ({e})")
    
    # 获取所有通道的USB3数据线状态
    try:
        usb3_dataline_status = hub.get_channel_usb3_dataline_status(*channels)
        assert usb3_dataline_status is not None, "USB3数据线状态读取失败"
        assert isinstance(usb3_dataline_status, dict), f"USB3数据线状态应该返回字典，实际返回: {type(usb3_dataline_status)}"
        assert len(usb3_dataline_status) == len(channels), f"USB3数据线状态应该包含 {len(channels)} 个通道，实际包含 {len(usb3_dataline_status)} 个"
        logger.info("  USB3数据线状态:")
        for ch in channels:
            assert ch in usb3_dataline_status, f"USB3数据线状态缺少通道 {ch}"
            status = usb3_dataline_status[ch]
            assert status in [0, 1], f"通道 {ch} USB3数据线状态值异常: {status}"
            logger.info(f"    通道 {ch}: {'ON' if status == 1 else 'OFF'}")
        logger.info(f"  ✓ USB3数据线状态返回值齐全，包含所有 {len(channels)} 个通道")
    except Exception as e:
        logger.info(f"  USB3数据线状态: 不支持 ({e})")


def test_alternating_power_pattern(hub, max_channels):
    """测试交替电源模式"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试交替电源模式: {channels}...")
    
    # 打开奇数通道
    odd_channels = [ch for ch in channels if ch % 2 == 1]
    if odd_channels:
        logger.info(f"  打开奇数通道: {odd_channels}...")
        result = hub.set_channel_power(*odd_channels, state=1)
        assert result
        time.sleep(0.3)
        
        status = hub.get_channel_power_status(*channels)
        for ch in channels:
            expected = 1 if ch in odd_channels else 0
            assert status[ch] == expected, f"通道 {ch} 状态错误，期望 {expected}"
        logger.info(f"  ✓ 奇数通道已打开")
    
    # 关闭奇数通道，打开偶数通道
    even_channels = [ch for ch in channels if ch % 2 == 0]
    if even_channels:
        logger.info(f"  关闭奇数通道，打开偶数通道: {even_channels}...")
        if odd_channels:
            hub.set_channel_power(*odd_channels, state=0)
        result = hub.set_channel_power(*even_channels, state=1)
        assert result
        time.sleep(0.3)
        
        status = hub.get_channel_power_status(*channels)
        for ch in channels:
            expected = 1 if ch in even_channels else 0
            assert status[ch] == expected, f"通道 {ch} 状态错误，期望 {expected}"
        logger.info(f"  ✓ 偶数通道已打开")
    
    # 关闭所有通道
    if even_channels:
        hub.set_channel_power(*even_channels, state=0)
        time.sleep(0.2)


def test_dataline_all_channels(hub, max_channels):
    """测试所有通道的数据线控制"""
    channels = list(range(1, max_channels + 1))
    logger.info(f"测试所有通道的数据线控制: {channels}...")
    
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
    
    # 打开所有通道的数据线
    logger.info(f"  打开所有通道数据线...")
    result = hub.set_channel_usb2_dataline(*channels, state=1)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_usb2_dataline_status(*channels)
    for ch in channels:
        assert status[ch] == 1, f"通道 {ch} 数据线应该打开"
    logger.info(f"  ✓ 所有通道数据线已打开")
    
    # 关闭所有通道的数据线
    logger.info(f"  关闭所有通道数据线...")
    result = hub.set_channel_usb2_dataline(*channels, state=0)
    assert result
    time.sleep(0.3)
    
    status = hub.get_channel_usb2_dataline_status(*channels)
    for ch in channels:
        assert status[ch] == 0, f"通道 {ch} 数据线应该关闭"
    logger.info(f"  ✓ 所有通道数据线已关闭")

