# SmartUSBHub Pro 测试套件

本目录包含 SmartUSBHub Pro 产品的所有测试文件，包括接口测试和压力测试。

## 📁 文件结构

```
SmartUSBHub_Pro/
├── test_integration.py                      # 接口测试（22个测试用例）
├── test_stress.py                           # 核心功能压力测试
├── test_stress_charge_mode_switch.py        # 充电模式切换压力测试 ⭐ 新增
├── run_tests.py                             # 主测试运行脚本
├── run_stress_charge_mode.py                # 充电模式切换压力测试运行脚本 ⭐ 新增
├── README.md                                # 本文件
├── README_CHARGE_MODE_STRESS_TEST.md        # 充电模式切换压力测试详细文档 ⭐ 新增
├── QUICKSTART_CHARGE_MODE.md                # 充电模式切换压力测试快速开始 ⭐ 新增
└── report/                                  # 测试报告目录
    ├── report_integration.html              # 接口测试报告
    ├── report_stress.html                   # 核心功能压力测试报告
    └── report_stress_charge_mode.html       # 充电模式切换压力测试报告 ⭐ 新增
```

## 🚀 快速开始

### 1. 接口测试（推荐首次运行）

验证设备的基本功能是否正常。

```bash
# 使用运行脚本（推荐）
python test/SmartUSBHub_Pro/run_tests.py --type integration

# 或使用 pytest
pytest test/SmartUSBHub_Pro/test_integration.py -v -s
```

**预计时间**: 2-5 分钟

### 2. 核心功能压力测试

测试设备在高频操作下的稳定性（电源控制、数据线切换）。

```bash
# 使用运行脚本（推荐）
python test/SmartUSBHub_Pro/run_tests.py --type stress

# 或使用 pytest
pytest test/SmartUSBHub_Pro/test_stress.py -v -s
```

**预计时间**: 5-30 分钟（取决于测试次数配置）

### 3. 充电模式切换压力测试 ⭐ 新增

测试设备在快充/慢充模式之间频繁切换的稳定性。

```bash
# 使用专用运行脚本（推荐）
python test/SmartUSBHub_Pro/run_stress_charge_mode.py

# 或使用主运行脚本
python test/SmartUSBHub_Pro/run_tests.py --type stress_charge_mode

# 或使用 pytest
pytest test/SmartUSBHub_Pro/test_stress_charge_mode_switch.py -v -s
```

**预计时间**: 20-30 分钟（默认 10,000 次切换，每次切换后等待 0.1 秒）

**快速上手**: 查看 [QUICKSTART_CHARGE_MODE.md](QUICKSTART_CHARGE_MODE.md)

### 4. 运行所有测试

```bash
python test/SmartUSBHub_Pro/run_tests.py --all
```

## 📊 测试类型说明

### test_integration.py - 接口测试

**目的**: 验证所有 API 接口的基本功能

**测试内容**:
- ✅ 设备连接和基本信息
- ✅ 电源控制（单通道、多通道、组合控制、互锁模式）
- ✅ 监控功能（电压、电流）
- ✅ 数据线控制（连接/断开、状态读取）
- ✅ 充电模式（慢充、快充）
- ✅ 设备设置（工作模式、按钮控制、自动恢复）
- ✅ 高级功能（电源序列、状态获取）

**测试用例数**: 22 个

**成功标准**: 所有测试通过

### test_stress.py - 核心功能压力测试

**目的**: 通过大量重复操作验证设备稳定性

**测试内容**:
- 🔄 多通道电源开关控制（循环测试）
- 🔄 获取电源状态
- 🔄 USB2/USB3 数据线连接/断开（如果设备支持）
- 🔄 获取数据线状态

**默认测试次数**: 500,000 次操作

**成功标准**: 成功率 ≥95%

### test_stress_charge_mode_switch.py - 充电模式切换压力测试 ⭐ 新增

**目的**: 验证设备在长时间、高频率的充电模式切换下的稳定性

**测试内容**:
- 🔄 设置快充模式（fast_charge）
- ✅ 验证快充模式状态
- 🔄 设置慢充模式（slow_charge/ilim）
- ✅ 验证慢充模式状态

**默认测试次数**: 10,000 次切换

**成功标准**: 成功率 ≥95%

**特点**:
- 实时进度显示（每秒更新）
- 详细统计信息（成功率、平均用时、模式占比）
- 自动验证每次切换的正确性
- 支持自定义测试次数
- HTML 报告生成

**参考示例**: [examples/SmartUSBHub_Pro/auto_charge_mode_switch.py](../../examples/SmartUSBHub_Pro/auto_charge_mode_switch.py)

## 📖 详细文档

- **[QUICKSTART_CHARGE_MODE.md](QUICKSTART_CHARGE_MODE.md)** - 充电模式切换压力测试快速开始（5 分钟上手）⭐ 新增
- **[README_CHARGE_MODE_STRESS_TEST.md](README_CHARGE_MODE_STRESS_TEST.md)** - 充电模式切换压力测试详细文档 ⭐ 新增
- **[../../README.md](../../README.md)** - 测试套件总体说明

## 🛠️ 安装依赖

```bash
# 基本依赖
pip install pytest

# 生成 HTML 报告（推荐）
pip install pytest-html
```

## 📝 运行脚本使用说明

### run_tests.py - 主测试运行脚本

```bash
# 运行接口测试
python test/SmartUSBHub_Pro/run_tests.py --type integration

# 运行核心功能压力测试
python test/SmartUSBHub_Pro/run_tests.py --type stress

# 运行充电模式切换压力测试 ⭐ 新增
python test/SmartUSBHub_Pro/run_tests.py --type stress_charge_mode

# 运行所有测试
python test/SmartUSBHub_Pro/run_tests.py --all

# 不自动打开报告
python test/SmartUSBHub_Pro/run_tests.py --all --no-open

# 不生成 HTML 报告
python test/SmartUSBHub_Pro/run_tests.py --all --no-html
```

### run_stress_charge_mode.py - 充电模式切换压力测试专用脚本 ⭐ 新增

```bash
# 基本用法（自动生成HTML报告并打开）
python test/SmartUSBHub_Pro/run_stress_charge_mode.py

# 运行但不自动打开报告
python test/SmartUSBHub_Pro/run_stress_charge_mode.py --no-open

# 运行但不生成HTML报告
python test/SmartUSBHub_Pro/run_stress_charge_mode.py --no-html

# 自定义测试次数（例如 5000 次）
python test/SmartUSBHub_Pro/run_stress_charge_mode.py --count 5000
```

## 📈 测试报告

### 控制台输出

所有测试都会在控制台显示实时进度和详细统计信息。

**充电模式切换压力测试示例输出**:

```
进度: 5000/10000 (50.0%), 成功: 4985, 失败: 15, 成功率: 99.7%, 
快充: 2500次, 慢充: 2501次, 已用: 5分23秒, 速度: 15.5次/秒, 
预计剩余: 5分18秒

======================================================================
测试摘要
======================================================================
设备信息:
  硬件版本: V1.3
  固件版本: V1.5
  序列号: SUSH1234567890

总切换次数: 10,000
总成功次数: 9,987
总失败次数: 13
总成功率: 99.9%
总耗时: 10分45秒
切换频率: 15.5 次/秒

充电模式统计:
  快充次数: 5,000, 总时长: 5分22秒
  慢充次数: 5,001, 总时长: 5分23秒
  快充占比: 49.9%
  慢充占比: 50.1%

详细统计（每个操作的成功/失败次数）:
----------------------------------------------------------------------
操作                   成功     失败   总次数    成功率       平均用时
----------------------------------------------------------------------
  设置快充模式         4,998        2    5,000     99.96%      12.34ms
  验证快充模式         4,995        5    5,000     99.90%       8.56ms
  设置慢充模式         4,999        1    5,000     99.98%      11.23ms
  验证慢充模式         4,997        3    5,000     99.94%       8.45ms
======================================================================
```

### HTML 报告

如果安装了 `pytest-html` 插件，会自动生成 HTML 报告，包含：

- 设备信息表格
- 总体统计表格
- 充电模式统计表格（仅充电模式切换测试）
- 每个操作的详细统计表格（彩色显示）
- 测试用例的详细日志

报告会在测试完成后自动在浏览器中打开。

## ⚙️ 自定义测试配置

### 修改充电模式切换测试次数

#### 方法 1: 使用命令行参数（推荐）

```bash
python test/SmartUSBHub_Pro/run_stress_charge_mode.py --count 5000
```

#### 方法 2: 使用环境变量

```bash
# Windows PowerShell
$env:STRESS_TEST_COUNT=5000
python test/SmartUSBHub_Pro/run_stress_charge_mode.py

# Linux/macOS
export STRESS_TEST_COUNT=5000
python test/SmartUSBHub_Pro/run_stress_charge_mode.py
```

#### 方法 3: 修改代码

编辑 `test_stress_charge_mode_switch.py`，修改 `STRESS_TEST_TOTAL_COUNT` 变量。

### 修改核心功能压力测试次数

编辑 `test_stress.py`，修改 `STRESS_TEST_TOTAL_COUNT` 变量（默认 500,000）。

## ⚠️ 注意事项

### 运行前准备

1. **设备连接**: 确保 SmartUSBHub 设备已正确连接
2. **驱动安装**: 确认设备驱动已安装
3. **设备占用**: 确保没有其他程序占用设备
4. **环境稳定**: 建议在稳定的环境中运行压力测试

### 运行时

1. **测试时间**: 压力测试需要较长时间
   - 核心功能压力测试: 约 5-30 分钟
   - 充电模式切换压力测试: 约 10-20 分钟
2. **设备占用**: 测试过程中设备将被持续占用
3. **中断测试**: 可以使用 Ctrl+C 安全中断测试
4. **USB 线缆**: 建议使用质量好的 USB 线缆

### 测试后

测试结束后会自动：
1. 关闭所有通道
2. 恢复出厂设置
3. 断开设备连接
4. 生成 HTML 报告（如果安装了 pytest-html）
5. 自动打开报告（可以使用 --no-open 禁用）

## 🔍 故障排查

### 问题 1: 找不到设备

**症状**: 测试跳过，提示 "未找到设备"

**解决方案**:
1. 检查设备连接
2. 检查驱动安装
3. 重新插拔 USB
4. 尝试其他 USB 端口

### 问题 2: 成功率低

**症状**: 成功率低于 95%

**解决方案**:
1. 更换 USB 线缆
2. 更换 USB 端口
3. 关闭其他占用系统资源的程序
4. 更新设备固件

### 问题 3: pytest-html 未安装

**症状**: 提示无法生成 HTML 报告

**解决方案**:
```bash
pip install pytest-html
```

## 📊 成功率标准

- **成功率阈值**: 95%
- **低于 95%**: 测试失败（assert 错误）
- **95% - 99%**: 通过但需关注
- **≥99%**: 优秀

## 🔄 与示例程序的对应关系

| 测试程序 | 对应示例 | 说明 |
|---------|---------|------|
| test_stress_charge_mode_switch.py | auto_charge_mode_switch.py | 充电模式切换压力测试基于该示例开发 |

## 📚 相关资源

- **上级目录**: [../../README.md](../../README.md) - 测试套件总体说明
- **测试框架配置**: [../../conftest.py](../../conftest.py) - pytest fixtures 配置
- **示例程序**: [../../examples/SmartUSBHub_Pro/](../../examples/SmartUSBHub_Pro/) - 示例程序目录

## 📝 更新历史

- **v1.2** (2026-01-07): 新增充电模式切换压力测试
  - 新增 `test_stress_charge_mode_switch.py`
  - 新增 `run_stress_charge_mode.py`
  - 新增 `README_CHARGE_MODE_STRESS_TEST.md`
  - 新增 `QUICKSTART_CHARGE_MODE.md`
  - 更新 `run_tests.py` 支持新的测试类型
- **v1.1** (2024): 初始版本
  - `test_integration.py`
  - `test_stress.py`
  - `run_tests.py`

---

**最后更新**: 2026-01-07


