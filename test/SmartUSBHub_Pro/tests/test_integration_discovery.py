"""
真实设备的发现 / 连接 / 回调 / 重启 集成测试。

这些 API 无法用模拟器离线验证连接握手以外的行为，必须连真机。
本文件自行管理连接（每个用例独立连接并断开），不使用 conftest 的模块级
``hub`` fixture，以避免端口被长期占用导致 ``auto_connect`` / 按地址连接 /
``reboot_mcu`` 互相争用同一端口。

运行:
    pytest test/SmartUSBHub_Pro/tests/test_integration_discovery.py -v -s
"""
import os
import sys
import time
import logging

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub
import smartusbhub as m

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.hardware


@pytest.fixture
def connected_hub():
    """Connect for a single test and always disconnect afterwards."""
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        pytest.skip("未找到设备，跳过硬件测试")
    time.sleep(0.3)
    try:
        yield hub
    finally:
        try:
            hub.disconnect()
        except Exception:
            pass
        time.sleep(0.3)


# ==================== 静态查询 ====================

def test_scan_available_ports_finds_device():
    ports = SmartUSBHub.scan_available_ports()
    assert isinstance(ports, list)
    assert len(ports) >= 1, "未发现任何 SmartUSBHub 端口"
    logger.info(f"✓ 发现端口: {ports}")


def test_get_product_info_lookup():
    info = SmartUSBHub.get_product_info(0x03)
    assert info is not None
    assert info["name"] == "HBP_USB2_7CH_ADV"
    assert SmartUSBHub.get_product_info(0xEE) is None
    logger.info("✓ get_product_info 查表正常")


# ==================== 发现 / 连接 ====================

def test_auto_connect(connected_hub):
    # connected_hub 已占用唯一端口；auto_connect 应跳过它并返回 None（无第二台设备）。
    hub2 = SmartUSBHub.auto_connect()
    if hub2 is not None and hub2 is not connected_hub:
        hub2.disconnect()
        pytest.skip("检测到第二台设备，无法断言单设备行为")
    assert hub2 is None
    logger.info("✓ auto_connect 正确跳过已占用端口")


def test_auto_connect_standalone():
    # 没有占用端口时，auto_connect 应能连上设备。
    hub = SmartUSBHub.auto_connect()
    if hub is None:
        pytest.skip("未找到可用设备")
    try:
        assert hub.is_connected()
        assert hub.get_product_name() is not None
        logger.info(f"✓ auto_connect 连接成功: {hub.port}")
    finally:
        hub.disconnect()
        time.sleep(0.3)


def test_scan_and_connect_by_address():
    addr = None
    probe = SmartUSBHub.scan_and_connect()
    if probe is None:
        pytest.skip("未找到设备")
    try:
        addr = probe.get_device_address()
    finally:
        probe.disconnect()
        time.sleep(0.3)

    assert addr is not None
    hub = SmartUSBHub.scan_and_connect_by_address(addr)
    try:
        assert hub is not None, f"按地址 {addr:#06x} 未能连接"
        assert hub.get_device_address() == addr
        logger.info(f"✓ 按地址连接成功: {addr:#06x}")
    finally:
        if hub is not None:
            hub.disconnect()
            time.sleep(0.3)


def test_scan_and_connect_by_wrong_address_returns_none():
    hub = SmartUSBHub.scan_and_connect_by_address(0xBEEF)
    if hub is not None:
        addr = hub.get_device_address()
        hub.disconnect()
        time.sleep(0.3)
        assert addr == 0xBEEF, "返回了地址不匹配的设备"
        pytest.skip("设备地址恰为 0xBEEF")
    logger.info("✓ 不存在的地址返回 None")


# ==================== 回调 ====================

def test_register_callback_fires_on_real_ack(connected_hub):
    received = []
    connected_hub.register_callback(
        m.CMD_GET_CHANNEL_POWER_STATUS,
        lambda channel, value: received.append((channel, value)))

    connected_hub.get_channel_power_status(1)
    time.sleep(0.1)

    assert received, "回调未被真实 ACK 触发"
    logger.info(f"✓ register_callback 收到 {len(received)} 次回调")
    # 还原，避免影响后续
    connected_hub.callbacks[m.CMD_GET_CHANNEL_POWER_STATUS] = None


def test_register_disconnect_callback_fires(connected_hub):
    fired = []
    connected_hub.register_disconnect_callback(lambda: fired.append(True))
    assert connected_hub.disconnect_callback is not None

    # 主动 disconnect 不会触发该回调（仅意外断开会）；这里验证注册成功，
    # 并在断开后确认不会误触发。
    connected_hub.disconnect()
    time.sleep(0.3)
    assert fired == [], "主动断开不应触发意外断开回调"
    logger.info("✓ register_disconnect_callback 注册正常")


# ==================== 重启 ====================

def test_reboot_mcu_and_reconnect():
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        pytest.skip("未找到设备")
    try:
        if getattr(hub, "_is_legacy_v1_firmware", lambda: False)():
            pytest.skip("V1 固件不支持 reboot_mcu")
        result = hub.reboot_mcu()
        assert result is True, "reboot_mcu 未收到 ACK"
        logger.info("✓ reboot_mcu 已确认")
    finally:
        try:
            hub.disconnect()
        except Exception:
            pass

    # 等待 MCU 重启并重新枚举，然后确认可重新连接。
    time.sleep(3.0)
    hub2 = None
    for _ in range(10):
        hub2 = SmartUSBHub.scan_and_connect()
        if hub2 is not None:
            break
        time.sleep(1.0)
    try:
        assert hub2 is not None, "重启后无法重新连接设备"
        assert hub2.is_connected()
        logger.info("✓ 重启后重新连接成功")
    finally:
        if hub2 is not None:
            hub2.disconnect()
            time.sleep(0.3)
