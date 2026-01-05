# SmartUSBHub 测试文件使用指南

本文档详细说明 `test/` 目录下每个测试文件的用途、使用方法和注意事项。

## 📁 文件结构概览

```
test/
├── 测试文件 (Test Files)
│   ├── test_integration.py          # 常规集成测试
│   ├── test_stress_core.py          # 核心功能压力测试
│   └── test_flexconnect.py          # FlexConnect模式测试
│
├── 运行脚本 (Runner Scripts)
│   ├── run_integration_tests.py     # 集成测试运行器（自动生成HTML报告）
│   └── run_stress_tests.py          # 压力测试运行器（自动生成HTML报告）
│
├── 配置文件 (Configuration Files)
│   ├── conftest.py                  # Pytest fixtures配置
│   ├── pytest.ini                   # Pytest配置文件
│   └── __init__.py                  # Python包初始化
│
└── 文档文件 (Documentation)
    ├── README.md                    # 快速开始指南
    └── TEST_FILES_GUIDE.md          # 测试文件使用指南（本文档）
```

---

## 🧪 测试文件详解

### 1. `test_integration.py` - 常规集成测试

**用途：** 对 SmartUSBHub 设备进行全面的功能集成测试，验证所有核心功能是否正常工作。

**测试内容：**
- ✅ 设备连接和基本信息（连接、设备信息、版本、序列号）
- ✅ 电源控制（单通道、多通道、组合控制、互锁模式）
- ✅ 监控功能（电压、电流、所有通道监控）
- ✅ 数据线控制（连接/断开、状态读取）
- ✅ 充电模式（慢充、快充）
- ✅ 设备设置（工作模式、按钮控制、自动恢复、设备地址）
- ✅ 高级功能（电源序列、状态获取、交替模式）

**测试数量：** 22个测试用例

**运行方法：**

```bash
# 方法1: 使用pytest直接运行（推荐）
pytest test/test_integration.py -v -s

# 方法2: 使用运行脚本（自动生成HTML报告）
python test/run_integration_tests.py

# 方法3: 运行特定测试
pytest test/test_integration.py::test_get_device_info -v

# 方法4: 运行包含关键字的测试
pytest test/test_integration.py -k "voltage" -v

# 方法5: 显示详细日志
pytest test/test_integration.py -v -s --log-cli-level=INFO
```

**参数说明：**
- `-v`: 详细输出
- `-s`: 显示print输出
- `-k`: 运行包含关键字的测试
- `--log-cli-level=INFO`: 显示INFO级别日志

**注意事项：**
- ⚠️ 需要连接真实的 SmartUSBHub 设备
- ⚠️ 测试结束后会自动清理设备状态（关闭所有通道）
- ⚠️ 如果设备不支持某些功能（如ADC），相关测试会自动跳过
- ⚠️ 使用 `module` 级别的 fixture，所有测试共享同一个设备连接

**预计运行时间：** 约 2-5 分钟（取决于设备响应速度）

---

### 2. `test_stress_core.py` - 核心功能压力测试

**用途：** 对 SmartUSBHub 设备进行长时间、高强度的压力测试，通过大量重复操作验证设备在长时间运行下的稳定性和可靠性。

**测试内容：**
- 🔄 核心功能循环测试（默认2万次，可配置）
  - 多通道电源开关控制
  - 获取电源状态
  - USB2/USB3数据线连接/断开（如果设备支持）
  - 获取数据线状态
- 📊 实时进度显示和统计信息
- 📈 HTML报告生成（包含详细统计）
- ✅ 自动验证每次操作的正确性

**测试数量：** 1个压力测试用例（包含大量循环操作）

**运行方法：**

```bash
# 方法1: 使用运行脚本（推荐，自动生成HTML报告）
python test/run_stress_tests.py

# 方法2: 使用pytest直接运行
pytest test/test_stress_core.py -v -s

# 方法3: 运行但不自动打开报告
python test/run_stress_tests.py --no-open

# 方法4: 运行但不生成HTML报告
python test/run_stress_tests.py --no-html
```

**参数说明：**
- `--no-open`: 不自动打开HTML报告（默认会自动打开）
- `--no-html`: 不生成HTML报告

**注意事项：**
- ⚠️ **测试时间较长**：默认2万次操作，根据设备响应速度，通常需要数分钟到数十分钟
- ⚠️ 需要连接真实的 SmartUSBHub 设备
- ⚠️ 建议在稳定的环境中运行，避免中断
- ⚠️ 测试过程中会持续占用设备，其他程序无法使用
- ⚠️ 建议在测试前确保设备连接稳定
- ⚠️ 测试会自动清理设备状态并恢复出厂设置

**预计运行时间：** 约 5-30 分钟（取决于设备响应速度和测试次数配置）

**报告位置：** `test/report_stress.html`

---

### 3. `test_flexconnect.py` - FlexConnect模式测试

**用途：** 专门测试 FlexConnect 产品的模式切换功能，验证 PC/U盘1/U盘2 三种模式之间的切换是否正常。

**测试内容：**
- 🔄 模式切换测试
  - 获取当前模式
  - 切换到PC模式
  - 切换到U盘1模式
  - 切换到U盘2模式
- ⚠️ 故障状态检测
- 🛡️ 错误处理测试
- 🔁 压力测试（1000次循环）

**运行方法：**

```bash
# 方法1: 使用运行脚本（推荐，自动生成HTML报告并打开）
python test/run_flexconnect_tests.py

# 方法2: 使用pytest直接运行
pytest test/test_flexconnect.py -v

# 方法3: 运行特定测试类
pytest test/test_flexconnect.py::TestFlexConnectMode -v

# 方法4: 运行单个测试
pytest test/test_flexconnect.py::test_get_flexconnect_mode -v

# 方法5: 运行但不自动打开报告
python test/run_flexconnect_tests.py --no-open

# 方法6: 直接运行（不使用pytest）
python test/test_flexconnect.py
```

**注意事项：**
- ⚠️ 需要连接 FlexConnect 设备（FLEX_3CH产品）
- ⚠️ 如果第一个设备被占用，会自动尝试下一个设备
- ⚠️ 如果设备不是 FlexConnect 产品，测试会被跳过
- ⚠️ 模式切换后需要等待约 0.2 秒以确保切换完成

**预计运行时间：** 约 5-10 分钟

---

## 🚀 运行脚本详解

### 1. `run_integration_tests.py` - 集成测试运行器

**用途：** 便捷运行常规集成测试，自动生成HTML报告并打开浏览器。

**使用方法：**

```bash
# 基本用法（自动生成报告并打开）
python test/run_integration_tests.py

# 运行但不自动打开报告
python test/run_integration_tests.py --no-open

# 运行但不生成HTML报告
python test/run_integration_tests.py --no-html

# 传递pytest参数（如运行特定测试）
python test/run_integration_tests.py -k voltage

# 传递pytest参数（如简短错误信息）
python test/run_integration_tests.py --tb=short
```

**功能特性：**
- ✅ 自动生成HTML测试报告
- ✅ 自动打开浏览器显示报告
- ✅ 支持传递pytest命令行参数
- ✅ 自动检测pytest-html插件是否安装

**报告位置：** `test/report.html`

---

### 2. `run_stress_tests.py` - 压力测试运行器

**用途：** 便捷运行压力测试，自动生成HTML报告并打开浏览器。

**使用方法：**

```bash
# 基本用法（自动生成报告并打开）
python test/run_stress_tests.py

# 运行但不自动打开报告
python test/run_stress_tests.py --no-open

# 运行但不生成HTML报告
python test/run_stress_tests.py --no-html
```

**功能特性：**
- ✅ 自动生成HTML测试报告
- ✅ 自动打开浏览器显示报告
- ✅ 实时显示测试进度
- ✅ 自动检测pytest-html插件是否安装

**报告位置：** `test/report_stress.html`

---


## ⚙️ 配置文件详解

### 1. `conftest.py` - Pytest Fixtures配置

**用途：** 定义pytest fixtures，为所有测试提供共享的设备连接和配置。

**主要Fixtures：**
- `hub`: SmartUSBHub设备连接实例（module级别）
- `max_channels`: 设备支持的最大通道数

**使用方式：** 测试函数通过参数自动注入，无需手动调用。

**示例：**
```python
def test_example(hub, max_channels):
    # hub 和 max_channels 会自动注入
    assert hub is not None
    assert max_channels > 0
```

---

### 2. `pytest.ini` - Pytest配置文件

**用途：** 配置pytest的默认行为和测试发现规则。

**主要配置：**
- 测试文件模式：`test_*.py`
- 测试类模式：`Test*`
- 测试函数模式：`test_*`
- 默认参数：`-v -s --tb=short`
- 日志配置：INFO级别
- 标记（markers）：
  - `slow`: 标记慢速测试
  - `hardware`: 标记需要硬件的测试

**使用方式：** 自动生效，无需手动配置。

---

## 📋 快速参考

### 运行所有测试

```bash
# 运行所有测试（包括常规和压力测试）
pytest test/ -v

# 运行所有测试并生成报告
pytest test/ --html=report.html --self-contained-html
```

### 运行特定类型的测试

```bash
# 只运行常规集成测试
pytest test/test_integration.py -v

# 只运行压力测试
pytest test/test_stress_core.py -v

# 只运行FlexConnect测试
pytest test/test_flexconnect.py -v
```

### 跳过慢速测试

```bash
# 跳过标记为slow的测试
pytest test/ -v -m "not slow"
```

### 跳过需要硬件的测试

```bash
# 跳过标记为hardware的测试
pytest test/ -v -m "not hardware"
```

---

## 🔍 故障排查

### 问题1: 找不到设备

**症状：** 测试失败，提示"No available devices found"

**解决方案：**
1. 检查设备是否正确连接
2. 检查设备驱动是否安装
3. 检查是否有其他程序占用设备
4. 尝试重新插拔USB连接

### 问题2: 测试超时

**症状：** 测试运行时间过长或卡住

**解决方案：**
1. 检查设备连接是否稳定
2. 检查USB线缆质量
3. 尝试降低测试强度（修改循环次数）
4. 检查是否有其他程序干扰

### 问题3: HTML报告未生成

**症状：** 运行脚本后没有生成HTML报告

**解决方案：**
```bash
# 安装pytest-html插件
pip install pytest-html
```

### 问题4: 某些测试被跳过

**症状：** 测试结果显示为"SKIPPED"

**可能原因：**
- 设备不支持该功能（如ADC、FlexConnect等）
- 测试条件不满足（如设备未连接）
- 这是正常行为，测试会自动检测设备能力

---

## 📚 相关文档

- **[README.md](./README.md)** - 快速开始指南

---

## 📝 文件命名规范

### 测试文件
- 格式：`test_<功能>_<类型>.py`
- 示例：
  - `test_integration.py` - 常规集成测试
  - `test_stress_core.py` - 核心功能压力测试
  - `test_flexconnect.py` - FlexConnect功能测试

### 运行脚本
- 格式：`run_<测试类型>_tests.py`
- 示例：
  - `run_integration_tests.py` - 运行集成测试
  - `run_stress_tests.py` - 运行压力测试


### 配置文件
- 标准命名：
  - `conftest.py` - pytest fixtures
  - `pytest.ini` - pytest配置
  - `__init__.py` - Python包初始化

---

## ✅ 最佳实践

1. **首次使用：** 先运行 `test_integration.py` 验证设备连接和基本功能
2. **日常测试：** 使用 `run_integration_tests.py` 快速运行常规测试（自动生成报告）
3. **发布前测试：** 运行完整的压力测试 `run_stress_tests.py`（自动生成报告）
4. **问题排查：** 使用 `-v -s` 参数查看详细输出
5. **报告生成：** 运行脚本会自动生成HTML报告，或使用 `pytest --html=report.html` 手动生成

---

**最后更新：** 2024年

