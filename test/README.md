# SmartUSBHub 集成测试

本目录包含 SmartUSBHub Python 库的集成测试，直接连接真实设备进行测试。

## 文档

- **[README.md](./README.md)** (本文件) - 快速开始指南
- **[README_INTEGRATION.md](./README_INTEGRATION.md)** - 集成测试详细说明

## 测试结构

### 集成测试（需要硬件）
- `test_integration.py` - 使用真实 SmartUSBHub 设备的常规集成测试（22个测试）
- `test_integration_stress.py` - 压力测试（19个测试，包含100万次测试，约33分钟/个）

### 测试运行器
- `run_integration_tests.py` - 集成测试运行脚本
- `generate_report.py` - 生成 HTML 测试报告的便捷脚本

### 配置文件
- `pytest.ini` - Pytest 配置文件（已配置 HTML 报告）
- `conftest.py` - Pytest fixtures 配置

## 快速开始

### 运行测试

#### 使用 pytest 运行（推荐）：
```bash
# 运行所有测试
pytest test/test_integration.py -v -s

# 运行特定测试
pytest test/test_integration.py::test_get_device_info -v

# 运行包含关键字的测试
pytest test/test_integration.py -k "voltage" -v
```

#### 使用运行脚本：
```bash
# 运行所有集成测试
python test/run_integration_tests.py
```

### 查看详细日志

```bash
# 显示详细日志（推荐）
pytest test/test_integration.py -v -s --log-cli-level=INFO
```

## 测试覆盖

测试套件覆盖以下功能：

1. **设备连接和基本信息**
   - 设备连接
   - 设备信息获取
   - 版本信息
   - 序列号获取

2. **电源控制**
   - 单通道和多通道电源控制
   - 电源状态读取
   - 互锁模式

3. **监控功能**
   - 电压读取
   - 电流读取
   - 所有通道监控

4. **数据线控制**
   - 数据线连接/断开
   - 数据线状态读取

5. **充电模式**
   - 慢充模式
   - 快充模式

6. **设备设置**
   - 工作模式（普通/互锁）
   - 按钮控制
   - 自动恢复
   - 设备地址

## 要求

测试需要：
- Python 3.9+
- pytest
- 已连接的 SmartUSBHub 设备

## 注意事项

- 测试需要物理 SmartUSBHub 设备连接
- 测试结束后会自动清理设备状态（关闭所有通道）
- 如果设备不支持某些功能（如 ADC），相关测试会自动跳过
- 使用 `module` 级别的 fixture，所有测试共享同一个设备连接

## 生成 HTML 测试报告

### 安装 pytest-html

```bash
pip install pytest-html
```

### 使用方法

#### 方法1: 使用便捷脚本（推荐）

```bash
# 生成常规测试报告
python test/generate_report.py

# 生成压力测试报告
python test/generate_report.py --stress

# 生成所有测试报告
python test/generate_report.py --all

# 生成报告并自动打开浏览器
python test/generate_report.py --open
python test/generate_report.py --stress --open
```

#### 方法2: 直接使用 pytest

```bash
# 生成常规测试报告
pytest test/test_integration.py --html=report.html --self-contained-html

# 生成压力测试报告
pytest test/test_integration_stress.py --html=report.html --self-contained-html

# 生成所有测试报告
pytest test/ --html=report.html --self-contained-html
```

报告文件会生成在 `test/report.html`，可以直接在浏览器中打开查看。

### 报告内容

HTML 报告包含：
- 测试概览（通过/失败/跳过统计）
- 详细的测试结果列表
- 每个测试的执行时间
- 失败测试的错误信息和堆栈跟踪
- 测试日志输出

## 更多信息

详细的使用说明请参考：
- **[README_INTEGRATION.md](./README_INTEGRATION.md)** - 集成测试详细说明和使用指南
