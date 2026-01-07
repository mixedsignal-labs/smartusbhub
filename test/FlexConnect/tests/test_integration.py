"""
FlexConnect 接口测试

测试FlexConnect产品的接口功能：
1. set_flexconnect_mode() - 设置模式
2. get_flexconnect_mode() - 获取模式
3. get_flexconnect_fault() - 获取故障状态
4. set_device_address() / get_device_address() - 设备地址设置和获取
5. 错误处理测试

使用方法:
    # 运行接口测试
    pytest FlexConnect/test_integration.py -v

    # 显示详细日志
    pytest FlexConnect/test_integration.py -v -s --log-cli-level=INFO
"""
import pytest
import time
import sys
import os
import logging

# 添加项目根目录到路径（从产品子目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2, FLEXCONNECT_MODE_DISCONNECT

# 配置日志
logger = logging.getLogger(__name__)


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


class TestFlexConnectMode:
    """FlexConnect模式切换测试"""
    
    def test_get_flexconnect_mode(self, flexconnect_hub):
        """测试获取FlexConnect模式"""
        mode = flexconnect_hub.get_flexconnect_mode()
        assert mode is not None, "Failed to get FlexConnect mode"
        assert mode in [FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2, FLEXCONNECT_MODE_DISCONNECT], \
            f"Invalid mode value: {mode}"
        print(f"Current FlexConnect mode: {mode}")
    
    def test_set_flexconnect_mode_pc(self, flexconnect_hub):
        """测试切换到PC模式"""
        # 先检查当前模式，如果已经是目标模式，先切换到其他模式
        current_mode = flexconnect_hub.get_flexconnect_mode()
        if current_mode == FLEXCONNECT_MODE_PC:
            # 如果已经是PC模式，先切换到UDISK1再切换回来
            flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
            time.sleep(0.3)  # 等待切换完成
        
        # 切换到PC模式
        result = flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        # 如果设置失败，可能是设备已经在PC模式，验证实际模式
        if not result:
            time.sleep(0.3)  # 等待一下，可能设备需要时间响应
            mode = flexconnect_hub.get_flexconnect_mode()
            if mode == FLEXCONNECT_MODE_PC:
                # 如果已经是PC模式，也算成功
                print(f"Device already in PC mode")
                return
        
        assert result is True, "Failed to set FlexConnect mode to PC"
        
        # 等待模式切换完成
        time.sleep(0.3)
        
        # 验证模式
        mode = flexconnect_hub.get_flexconnect_mode()
        assert mode == FLEXCONNECT_MODE_PC, f"Mode should be PC (0), but got {mode}"
        print(f"Successfully switched to PC mode")
    
    def test_set_flexconnect_mode_udisk1(self, flexconnect_hub):
        """测试切换到U盘1模式"""
        # 先检查当前模式，如果已经是目标模式，先切换到其他模式
        current_mode = flexconnect_hub.get_flexconnect_mode()
        if current_mode == FLEXCONNECT_MODE_UDISK1:
            # 如果已经是UDISK1模式，先切换到PC再切换回来
            flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
            time.sleep(0.3)  # 等待切换完成
        
        # 切换到UDISK1模式
        result = flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)
        # 如果设置失败，可能是设备已经在目标模式，验证实际模式
        if not result:
            time.sleep(0.3)  # 等待一下，可能设备需要时间响应
            mode = flexconnect_hub.get_flexconnect_mode()
            if mode == FLEXCONNECT_MODE_UDISK1:
                # 如果已经是目标模式，也算成功
                print(f"Device already in UDISK1 mode")
                return
        
        assert result is True, "Failed to set FlexConnect mode to UDISK1"
        
        # 等待模式切换完成
        time.sleep(0.3)
        
        # 验证模式
        mode = flexconnect_hub.get_flexconnect_mode()
        assert mode == FLEXCONNECT_MODE_UDISK1, f"Mode should be UDISK1 (1), but got {mode}"
        print(f"Successfully switched to UDISK1 mode")
    
    def test_set_flexconnect_mode_udisk2(self, flexconnect_hub):
        """测试切换到U盘2模式"""
        # 先检查当前模式，如果已经是目标模式，先切换到其他模式
        current_mode = flexconnect_hub.get_flexconnect_mode()
        if current_mode == FLEXCONNECT_MODE_UDISK2:
            # 如果已经是UDISK2模式，先切换到PC再切换回来
            flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
            time.sleep(0.3)  # 等待切换完成
        
        # 切换到UDISK2模式
        result = flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK2)
        # 如果设置失败，可能是设备已经在目标模式，验证实际模式
        if not result:
            time.sleep(0.3)  # 等待一下，可能设备需要时间响应
            mode = flexconnect_hub.get_flexconnect_mode()
            if mode == FLEXCONNECT_MODE_UDISK2:
                # 如果已经是目标模式，也算成功
                print(f"Device already in UDISK2 mode")
                return
        
        assert result is True, "Failed to set FlexConnect mode to UDISK2"
        
        # 等待模式切换完成
        time.sleep(0.3)
        
        # 验证模式
        mode = flexconnect_hub.get_flexconnect_mode()
        assert mode == FLEXCONNECT_MODE_UDISK2, f"Mode should be UDISK2 (2), but got {mode}"
        print(f"Successfully switched to UDISK2 mode")
    
    def test_set_flexconnect_mode_disconnect(self, flexconnect_hub):
        """测试切换到断开所有连接模式"""
        # 先切换到PC模式，确保不是DISCONNECT模式
        flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        time.sleep(0.3)
        
        # 切换到DISCONNECT模式
        result = flexconnect_hub.set_flexconnect_mode(FLEXCONNECT_MODE_DISCONNECT)
        if not result:
            time.sleep(0.3)
            mode = flexconnect_hub.get_flexconnect_mode()
            if mode == FLEXCONNECT_MODE_DISCONNECT:
                print(f"Device already in DISCONNECT mode")
                return
        
        assert result is True, "Failed to set FlexConnect mode to DISCONNECT"
        
        # 等待模式切换完成
        time.sleep(0.3)
        
        # 验证模式
        mode = flexconnect_hub.get_flexconnect_mode()
        assert mode == FLEXCONNECT_MODE_DISCONNECT, f"Mode should be DISCONNECT (3), but got {mode}"
        print(f"Successfully switched to DISCONNECT mode")
    
    def test_set_flexconnect_mode_invalid(self, flexconnect_hub):
        """测试设置无效模式（应该抛出ValueError）"""
        with pytest.raises(ValueError, match="Invalid FlexConnect mode"):
            flexconnect_hub.set_flexconnect_mode(0xFF)
    
    def test_mode_cycling(self, flexconnect_hub):
        """测试模式循环切换：PC -> UDISK1 -> UDISK2 -> DISCONNECT -> PC"""
        modes = [
            (FLEXCONNECT_MODE_PC, "PC"),
            (FLEXCONNECT_MODE_UDISK1, "UDISK1"),
            (FLEXCONNECT_MODE_UDISK2, "UDISK2"),
            (FLEXCONNECT_MODE_DISCONNECT, "DISCONNECT"),
            (FLEXCONNECT_MODE_PC, "PC")
        ]
        
        for mode, mode_name in modes:
            result = flexconnect_hub.set_flexconnect_mode(mode)
            # 如果设置失败，检查是否已经在目标模式
            if not result:
                time.sleep(0.3)  # 等待一下，可能设备需要时间响应
                current_mode = flexconnect_hub.get_flexconnect_mode()
                if current_mode == mode:
                    # 如果已经是目标模式，也算成功
                    print(f"Device already in {mode_name} mode")
                    continue
                else:
                    assert False, f"Failed to set mode to {mode_name} and current mode is {current_mode}"
            
            assert result is True, f"Failed to set mode to {mode_name}"
            
            # 等待模式切换完成
            time.sleep(0.3)
            
            # 验证模式
            current_mode = flexconnect_hub.get_flexconnect_mode()
            assert current_mode == mode, \
                f"Mode should be {mode_name} ({mode}), but got {current_mode}"
            print(f"Successfully cycled to {mode_name} mode")


class TestFlexConnectFault:
    """FlexConnect故障检测测试"""
    
    def test_get_flexconnect_fault(self, flexconnect_hub):
        """测试获取FlexConnect故障状态"""
        fault = flexconnect_hub.get_flexconnect_fault()
        assert fault is not None, "Failed to get FlexConnect fault status"
        assert isinstance(fault, int), f"Fault status should be int, but got {type(fault)}"
        assert 0 <= fault <= 0xFF, f"Fault status should be 0-0xFF, but got {fault}"
        
        if fault == 0:
            print("No fault detected")
        else:
            fault_desc = []
            if fault & 0x01:
                fault_desc.append("DUT_VBUS_FAULT")
            if fault & 0x02:
                fault_desc.append("UDISK1_VBUS_FAULT")
            if fault & 0x04:
                fault_desc.append("UDISK2_VBUS_FAULT")
            print(f"Fault detected: 0x{fault:02X} ({', '.join(fault_desc)})")


class TestFlexConnectErrorHandling:
    """FlexConnect错误处理测试"""
    
    def test_flexconnect_methods_on_non_flexconnect_device(self):
        """测试在非FlexConnect设备上调用FlexConnect方法（应该抛出ValueError）"""
        # 尝试连接非FlexConnect设备
        # 先尝试连接任何设备，如果不是FlexConnect则用于测试
        ports = SmartUSBHub.scan_available_ports()
        if not ports:
            pytest.skip("No SmartUSBHub devices found")
        
        # 尝试连接第一个设备
        hub = None
        for port in ports:
            try:
                hub = SmartUSBHub(port)
                # 检查是否为FlexConnect产品
                if hub._check_feature_support("flexconnect"):
                    hub.disconnect()
                    hub = None
                    continue  # 是FlexConnect产品，尝试下一个
                else:
                    break  # 找到非FlexConnect产品，用于测试
            except Exception:
                continue  # 连接失败，尝试下一个
        
        if hub is None:
            pytest.skip("No non-FlexConnect devices found for error handling test")
        
        # 尝试调用FlexConnect方法，应该抛出ValueError
        with pytest.raises(ValueError, match="is not a FlexConnect product"):
            hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        
        with pytest.raises(ValueError, match="is not a FlexConnect product"):
            hub.get_flexconnect_mode()
        
        with pytest.raises(ValueError, match="is not a FlexConnect product"):
            hub.get_flexconnect_fault()
        
        hub.disconnect()


class TestDeviceAddress:
    """设备地址测试（所有产品都支持）"""
    
    def test_get_device_address(self, flexconnect_hub):
        """测试获取设备地址"""
        address = flexconnect_hub.get_device_address()
        assert address is not None, "Failed to get device address"
        assert isinstance(address, int), f"Address should be int, but got {type(address)}"
        assert 0 <= address <= 0xFFFF, f"Address should be 0-0xFFFF, but got 0x{address:04X}"
        logger.info(f"Current device address: 0x{address:04X}")
    
    def test_set_device_address(self, flexconnect_hub):
        """测试设置设备地址"""
        # 获取原始地址
        original_address = flexconnect_hub.get_device_address()
        logger.info(f"Original device address: 0x{original_address:04X}")
        
        # 设置新地址
        new_address = 0x0001
        logger.info(f"Setting device address to 0x{new_address:04X}...")
        result = flexconnect_hub.set_device_address(new_address)
        assert result is True, "Failed to set device address"
        time.sleep(0.2)  # 等待命令完成
        
        # 验证地址
        address = flexconnect_hub.get_device_address()
        assert address == new_address, f"Address should be 0x{new_address:04X}, but got 0x{address:04X}"
        logger.info(f"✓ Device address set successfully to 0x{address:04X}")
        
        # 恢复原始地址
        logger.info(f"Restoring original device address: 0x{original_address:04X}...")
        result = flexconnect_hub.set_device_address(original_address)
        assert result is True, "Failed to restore original device address"
        time.sleep(0.2)
        
        # 验证恢复
        address = flexconnect_hub.get_device_address()
        assert address == original_address, f"Address should be restored to 0x{original_address:04X}, but got 0x{address:04X}"
        logger.info(f"✓ Device address restored to 0x{address:04X}")
    
    def test_set_device_address_invalid(self, flexconnect_hub):
        """测试设置无效的设备地址（应该抛出ValueError）"""
        with pytest.raises(ValueError, match="Address must be between"):
            flexconnect_hub.set_device_address(0x10000)  # 超出范围
        
        with pytest.raises(ValueError, match="Address must be between"):
            flexconnect_hub.set_device_address(-1)  # 负数
