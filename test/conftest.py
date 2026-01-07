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


# 在报告生成后修改HTML标题
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束后，修改HTML报告的标题"""
    try:
        import pytest_html
        # 获取HTML报告路径
        html_path = getattr(session.config.option, 'htmlpath', None)
        if html_path and os.path.exists(html_path):
            product = os.environ.get('TEST_PRODUCT', '')
            test_type = os.environ.get('TEST_TYPE', '')
            if product and test_type:
                title = f"{product} - {test_type}"
                # 读取HTML文件
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换标题（替换 <title> 标签和页面中的标题）
                import re
                # 1. 替换 <title> 标签
                content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.DOTALL)
                
                # 2. 替换页面中的标题（pytest-html 的标题可能在多个位置）
                # 2.1 class="title" 的 div（最常见）
                content = re.sub(r'(<div[^>]*class=["\']title["\'][^>]*>)(.*?)(</div>)', 
                                f'\\1{title}\\3', content, flags=re.DOTALL | re.IGNORECASE)
                
                # 2.2 h1 标签中的标题
                content = re.sub(r'(<h1[^>]*>)(.*?)(</h1>)', 
                                f'\\1{title}\\3', content, flags=re.DOTALL)
                
                # 2.3 替换可能包含文件名的标题（如 "report_stress.html"）
                # 匹配各种可能的标题格式
                patterns = [
                    r'report_\w+\.html',  # report_stress.html
                    r'Test Report',       # Test Report
                    r'Pytest Report',     # Pytest Report
                ]
                for pattern in patterns:
                    content = re.sub(pattern, title, content, flags=re.IGNORECASE)
                
                # 2.4 替换可能出现在 body 开头的标题文本
                # 查找并替换页面主体中第一个明显的标题文本
                content = re.sub(r'(<body[^>]*>.*?<div[^>]*>)(report_\w+\.html|Test Report|Pytest Report)(</div>)',
                                f'\\1{title}\\3', content, flags=re.DOTALL | re.IGNORECASE)
                
                # 写回文件
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    except Exception as e:
        # 记录错误但不影响测试结果
        import logging
        logging.getLogger(__name__).debug(f"无法修改HTML报告标题: {e}")

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

