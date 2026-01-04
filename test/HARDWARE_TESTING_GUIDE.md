# 硬件测试指南

本文档说明如何使用真实 SmartUSBHub 设备进行集成测试。

## 概述

SmartUSBHub 测试套件包含两种类型的测试：

1. **单元测试** (Unit Tests) - 使用 Mock 串口，无需硬件
2. **集成测试** (Integration Tests) - 连接真实设备，验证实际功能

## 测试类型

### 单元测试

- **文件**: `test_smartusbhub.py`, `test_protocol.py`, `test_concurrency.py`
- **特点**: 使用 MockSerial 模拟设备，无需硬件
- **用途**: 快速验证代码逻辑和协议处理
- **运行**: `python -m unittest test.test_smartusbhub`

### 集成测试

- **文件**: `test_integration.py`
- **特点**: 连接真实 SmartUSBHub 设备
- **用途**: 验证与真实硬件的交互
- **运行**: `python -m unittest test.test_integration`

## 准备工作

### 硬件要求

1. **SmartUSBHub 设备**
   - 确保设备已正确连接
   - USB 线连接稳定
   - 设备已上电

2. **系统要求**
   - 已安装驱动程序
   - 串口可正常访问
   - 有足够的 USB 端口

### 软件要求

1. **Python 环境**
   ```bash
   python --version  # 需要 Python 3.9+
   ```

2. **依赖库**
   ```bash
   pip install pyserial colorlog numpy
   ```

3. **权限设置** (Linux/macOS)
   ```bash
   # 将用户添加到 dialout 组 (Linux)
   sudo usermod -a -G dialout $USER
   
   # 或使用 sudo 运行测试
   sudo python -m unittest test.test_integration
   ```

## 运行集成测试

### 基本用法

```bash
# 运行所有集成测试
python -m unittest test.test_integration

# 或使用测试运行器
python test/run_all_tests.py --integration-only
```

### 跳过硬件测试

如果设备未连接，可以跳过硬件测试：

```bash
# 使用环境变量
SKIP_HARDWARE_TESTS=1 python -m unittest test.test_integration

# 或使用测试运行器
python test/run_all_tests.py --all --skip-hardware
```

### 运行所有测试

```bash
# 运行单元测试 + 集成测试
python test/run_all_tests.py --all

# 只运行单元测试
python test/run_all_tests.py --unit-only

# 只运行集成测试
python test/run_all_tests.py --integration-only
```

## 测试内容

### 1. 硬件连接测试 (`TestHardwareConnection`)

- 设备连接验证
- 设备信息获取
- 版本信息读取

**示例输出：**
```
Found 1 SmartUSBHub device(s): ['COM3']

Device Info:
  Hardware Version: V1.3
  Firmware Version: V1.15
  Product Type: 0x00
  Max Channels: 4
```

### 2. 电源控制测试 (`TestHardwarePowerControl`)

- 单通道电源控制
- 多通道电源控制
- 互锁模式测试

**注意事项：**
- 测试会自动关闭所有通道
- 测试过程中会看到 LED 指示灯变化
- 确保没有重要设备连接到测试通道

### 3. 监控测试 (`TestHardwareMonitoring`)

- 电压读取
- 电流读取
- 多通道监控

**示例输出：**
```
Channel 1 voltage: 5.00V (raw: 50)
Channel 1 current: 0.15A (raw: 15)

Monitoring all 4 channels:
  Channel 1: 5.00V, 0.15A
  Channel 2: 5.00V, 0.00A
  Channel 3: 5.00V, 0.00A
  Channel 4: 5.00V, 0.00A
```

### 4. 数据线控制测试 (`TestHardwareDatalineControl`)

- USB2 数据线连接/断开
- 数据线状态读取

### 5. 设备设置测试 (`TestHardwareSettings`)

- 操作模式设置
- 按钮控制设置
- 自动恢复设置
- 设备地址设置

**注意事项：**
- 测试会恢复默认设置
- 设备地址测试会恢复原始地址

### 6. 充电模式测试 (`TestHardwareChargeMode`)

- 慢充模式设置
- 快充模式设置
- 充电模式读取

## 测试安全

### 重要警告

⚠️ **在运行硬件测试前，请确保：**

1. **没有重要设备连接**
   - 测试会控制电源和数据线
   - 可能影响连接的设备

2. **测试环境安全**
   - 确保测试环境稳定
   - 避免在关键系统上运行

3. **数据备份**
   - 测试可能修改设备设置
   - 重要配置请先备份

### 安全措施

测试套件包含以下安全措施：

1. **自动清理**
   - 测试结束后自动关闭所有通道
   - 恢复默认设置

2. **错误处理**
   - 连接失败时自动跳过
   - 异常时安全断开

3. **状态检查**
   - 测试前检查设备连接
   - 验证操作结果

## 故障排除

### 问题：找不到设备

**症状：**
```
No SmartUSBHub devices found. Hardware tests will be skipped.
```

**解决方案：**
1. 检查设备连接
2. 检查 USB 驱动
3. 检查串口权限
4. 验证 VID/PID 匹配

```python
# 手动检查可用端口
from smartusbhub import SmartUSBHub
ports = SmartUSBHub.scan_available_ports()
print(f"Available ports: {ports}")
```

### 问题：连接失败

**症状：**
```
Failed to connect to SmartUSBHub device
```

**解决方案：**
1. 检查端口是否被其他程序占用
2. 检查设备是否正常工作
3. 尝试重新连接设备
4. 检查串口权限

### 问题：测试超时

**症状：**
```
Timeout waiting for ACK
```

**解决方案：**
1. 检查设备响应速度
2. 增加等待时间
3. 检查 USB 连接质量
4. 尝试降低通信速率

### 问题：权限错误

**症状：**
```
PermissionError: [Errno 13] Permission denied
```

**解决方案：**

**Linux:**
```bash
sudo usermod -a -G dialout $USER
# 重新登录或使用 newgrp dialout
```

**macOS:**
```bash
# 通常不需要特殊权限
# 如果遇到问题，检查系统偏好设置 > 安全性与隐私
```

**Windows:**
```bash
# 通常不需要特殊权限
# 如果遇到问题，以管理员身份运行
```

### 问题：测试结果不一致

**可能原因：**
1. 设备状态未正确初始化
2. 之前的测试未清理
3. 设备硬件问题

**解决方案：**
1. 重新连接设备
2. 运行工厂重置（谨慎使用）
3. 检查设备固件版本

## 测试最佳实践

### 1. 测试顺序

建议的测试顺序：
1. 先运行单元测试（快速验证）
2. 再运行集成测试（硬件验证）

### 2. 测试环境

- 使用专用的测试设备
- 避免在生产环境运行
- 保持测试环境稳定

### 3. 测试数据

- 记录测试结果
- 保存设备配置
- 记录异常情况

### 4. 定期测试

- 每次代码更改后运行单元测试
- 发布前运行完整集成测试
- 定期验证硬件兼容性

## 持续集成

### GitHub Actions 示例

```yaml
name: Hardware Tests

on:
  workflow_dispatch:  # 手动触发
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点

jobs:
  hardware-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run hardware tests
        run: |
          python test/run_all_tests.py --integration-only
        env:
          SKIP_HARDWARE_TESTS: 0
```

**注意**: CI 环境通常没有硬件，需要特殊配置。

## 测试报告

### 生成测试报告

```bash
# 使用 pytest 生成 HTML 报告
pytest test/test_integration.py --html=report.html --self-contained-html

# 使用 coverage 生成覆盖率报告
coverage run -m unittest test.test_integration
coverage report
coverage html
```

## 常见问题

### Q: 可以同时连接多个设备测试吗？

A: 可以，但需要修改测试代码以支持多设备。当前测试默认连接第一个可用设备。

### Q: 测试会影响设备设置吗？

A: 测试会修改一些设置（如操作模式、按钮控制等），但会在测试结束后尝试恢复。建议使用专用测试设备。

### Q: 如何测试特定功能？

A: 可以运行特定的测试类或测试方法：

```bash
# 只运行电源控制测试
python -m unittest test.test_integration.TestHardwarePowerControl

# 只运行特定测试方法
python -m unittest test.test_integration.TestHardwarePowerControl.test_set_channel_power_single
```

### Q: 测试需要多长时间？

A: 集成测试通常需要 1-5 分钟，取决于设备响应速度和测试数量。

## 参考

- [测试指南](./TESTING_GUIDE.md) - 完整的测试文档
- [MockSerial 指南](./MOCK_SERIAL_GUIDE.md) - Mock 实现文档
- [README](./README.md) - 快速开始

## 更新日志

- **2024-01-XX**: 初始版本
  - 创建硬件测试框架
  - 添加集成测试
  - 编写测试指南


