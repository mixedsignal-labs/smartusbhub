"""
Pytest configuration and fixtures for SmartUSBHub tests
"""
import pytest
import logging
import sys
import os
import time

# 配置pytest不捕获stderr，确保进度显示可见
def pytest_configure(config):
    """配置pytest，确保stderr输出不被捕获"""
    # 设置capture模式，允许stderr输出
    if hasattr(config.option, 'capture'):
        # 如果使用-s参数，capture已经是'no'
        pass

# 配置日志格式（避免使用方括号，pytest会误认为是参数化语法）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

# 在源码仓库中，需要将项目根目录添加到路径
# test/conftest.py -> 父目录是项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def hub():
    """连接设备并返回hub实例"""
    logger.info("=" * 70)
    logger.info("正在扫描并连接设备...")
    
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        pytest.skip("未找到设备，跳过测试")
    
    logger.info(f"[OK] 设备连接成功: {hub.port if hasattr(hub, 'port') else 'N/A'}")
    time.sleep(0.5)  # 等待连接稳定
    
    yield hub
    
    # 清理
    logger.info("正在清理设备状态...")
    try:
        max_channels = hub.get_max_channels() or 4
        channels = list(range(1, max_channels + 1))
        hub.set_channel_power(*channels, state=0)
        time.sleep(0.2)
    except:
        pass
    
    # 恢复出厂设置，还原设备配置
    try:
        logger.info("正在恢复出厂设置...")
        result = hub.factory_reset()
        if result:
            logger.info("[OK] 设备已恢复出厂设置")
            time.sleep(0.5)  # 等待设备重置完成
        else:
            logger.warning("[WARNING] 恢复出厂设置失败")
    except Exception as e:
        logger.warning(f"[WARNING] 恢复出厂设置时出错: {e}")
    
    try:
        hub.disconnect()
        logger.info("[OK] 设备已断开连接")
    except:
        pass
    
    logger.info("=" * 70)


@pytest.fixture(scope="module")
def max_channels(hub):
    """获取设备最大通道数"""
    channels = hub.get_max_channels() or 4
    logger.info(f"设备通道数: {channels}")
    return channels

