# 集成测试说明

## 概述

集成测试直接连接真实设备进行测试，不依赖任何模拟（mock）。

## 快速开始

### 1. 运行所有测试

```bash
# 使用 pytest 直接运行
pytest test/test_integration.py -v

# 或使用运行脚本
python test/run_integration_tests.py
```

### 2. 运行特定测试

```bash
# 运行单个测试
pytest test/test_integration.py::test_get_device_info -v

# 运行包含关键字的测试
pytest test/test_integration.py -k "voltage" -v
pytest test/test_integration.py -k "power" -v
```

### 3. 查看详细日志

```bash
# 显示详细日志（推荐）
pytest test/test_integration.py -v -s --log-cli-level=INFO

# 或使用运行脚本（已包含日志配置）
python test/run_integration_tests.py
```

## 测试分类

### 连接和基本信息测试
- `test_device_connection` - 设备连接测试
- `test_get_device_info` - 获取设备信息
- `test_get_versions` - 获取版本信息
- `test_get_serial_no` - 获取序列号

### 电源控制测试
- `test_set_channel_power_single` - 单通道电源控制
- `test_set_channel_power_multiple` - 多通道电源控制
- `test_power_interlock_mode` - 互锁模式测试

### 监控测试
- `test_get_channel_voltage` - 电压读取
- `test_get_channel_current` - 电流读取
- `test_monitor_all_channels` - 监控所有通道

### 数据线控制测试
- `test_set_channel_dataline` - 数据线控制

### 设置测试
- `test_operate_mode` - 工作模式设置
- `test_button_control` - 按钮控制
- `test_auto_restore` - 自动恢复设置
- `test_device_address` - 设备地址设置

### 充电模式测试
- `test_slow_charge_mode` - 慢充模式
- `test_fast_charge_mode` - 快充模式

## 日志说明

测试过程中会输出详细的日志信息，包括：

- **连接信息**: 设备扫描和连接状态
- **操作步骤**: 每个测试步骤的详细信息
- **设备状态**: 设备状态变化
- **测试结果**: 每个断言的结果

日志格式：
```
HH:MM:SS [    INFO] 消息内容
```

## 注意事项

1. **设备连接**: 测试前请确保设备已正确连接
2. **自动清理**: 测试结束后会自动关闭所有通道并断开连接
3. **跳过测试**: 如果设备不支持某些功能（如ADC），相关测试会自动跳过
4. **测试顺序**: 使用 `module` 级别的 fixture，所有测试共享同一个设备连接

## 常见问题

### Q: 测试找不到设备？
A: 确保设备已连接，并且驱动已正确安装。可以手动检查：
```python
from smartusbhub import SmartUSBHub
ports = SmartUSBHub.scan_available_ports()
print(ports)
```

### Q: 如何只运行部分测试？
A: 使用 `-k` 参数：
```bash
pytest test/test_integration.py -k "power" -v
```

### Q: 如何查看更详细的错误信息？
A: 使用 `--tb=long` 参数：
```bash
pytest test/test_integration.py --tb=long -v
```


