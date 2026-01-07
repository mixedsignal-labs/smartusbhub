# FlexConnect 测试套件

本目录包含 FlexConnect 产品的所有测试文件。

## 文件结构

```
FlexConnect/
├── run_tests.py                      # 测试运行脚本（统一入口）
├── README.md                         # 本文件
├── tests/                            # 测试文件目录
│   ├── test_integration.py          # 接口测试
│   ├── test_stress.py               # 压力测试
│   ├── flexconnect_advanced_test.py # 高级功能测试
│   ├── flexconnect_test_default_set.py
│   ├── flexconnect_test_power_recover.py
│   ├── flexconnect_test_scenarios.py
│   └── scenarios/                    # 场景测试
│       ├── test_scenario_2_3.py
│       ├── test_scenario_2_4.py
│       ├── test_scenario_3_priority.py
│       ├── test_scenario_4_factory_reset.py
│       ├── test_scenario_5_button_poweroff.py
│       └── test_scenario_6_boundary.py
└── report/                          # 测试报告目录
    ├── report_integration.html      # 接口测试报告
    └── report_stress.html           # 压力测试报告
```

## 快速开始

### 1. 接口测试（推荐首次运行）

验证设备的基本功能是否正常。

```bash
python test/FlexConnect/run_tests.py --type integration
```

**预计时间**: 2-5 分钟

### 2. 压力测试

测试设备在高频操作下的稳定性（模式切换、故障检测）。

```bash
# 使用默认测试次数（10,000 次）
python test/FlexConnect/run_tests.py --type stress

# 指定测试次数
python test/FlexConnect/run_tests.py --type stress --count 5000
```

**预计时间**: 10-30 分钟（取决于测试次数配置）

### 3. 运行所有测试

```bash
python test/FlexConnect/run_tests.py --all
```

## 测试类型说明

### test_integration.py - 接口测试

**目的**: 验证所有 API 接口的基本功能

**测试内容**:
- 设备连接和基本信息
- FlexConnect 模式设置（PC、UDISK1、UDISK2、断开）
- 模式状态读取
- 故障检测
- 错误处理

**成功标准**: 所有测试通过

### test_stress.py - 压力测试

**目的**: 通过大量重复操作验证设备稳定性

**测试内容**:
- 模式切换循环测试
- 故障检测
- 状态读取

**默认测试次数**: 10,000 次循环

**成功标准**: 成功率 ≥95%

### 其他测试文件

`tests/` 目录下还包含其他专门的测试文件：

- **flexconnect_advanced_test.py**: 高级功能测试（默认模式、掉电恢复、恢复出厂设置等）
- **flexconnect_test_default_set.py**: 默认模式设置测试
- **flexconnect_test_power_recover.py**: 掉电恢复功能测试
- **flexconnect_test_scenarios.py**: 统一场景测试入口
- **scenarios/**: 各种场景测试（优先级、边界条件、按钮功能等）

这些测试文件可以直接运行，或通过 `flexconnect_test_scenarios.py` 统一入口运行。

## 运行脚本使用说明

### run_tests.py - 统一测试运行脚本

所有测试都通过 `run_tests.py` 运行，使用 `--type` 参数选择测试类型：

```bash
# 运行接口测试
python test/FlexConnect/run_tests.py --type integration

# 运行压力测试
python test/FlexConnect/run_tests.py --type stress

# 运行压力测试，指定测试次数
python test/FlexConnect/run_tests.py --type stress --count 5000

# 运行所有测试
python test/FlexConnect/run_tests.py --all

# 不自动打开报告
python test/FlexConnect/run_tests.py --all --no-open

# 不生成 HTML 报告
python test/FlexConnect/run_tests.py --all --no-html
```

### 命令行参数说明

#### --type

指定测试类型：
- `integration`: 接口测试
- `stress`: 压力测试
- `all`: 运行所有测试

#### --count

指定压力测试的测试次数。适用于 `stress` 类型。

默认测试次数为 10,000 次。

示例：
```bash
# 压力测试，指定 5,000 次
python test/FlexConnect/run_tests.py --type stress --count 5000

# 压力测试，指定 20,000 次
python test/FlexConnect/run_tests.py --type stress --count 20000
```

#### --no-open

不自动打开 HTML 报告。

#### --no-html

不生成 HTML 报告。

### 运行场景测试

```bash
# 运行统一场景测试入口
python test/FlexConnect/tests/flexconnect_test_scenarios.py

# 或直接运行单个场景
python test/FlexConnect/tests/scenarios/test_scenario_2_3.py
```

## 测试报告

### 控制台输出

所有测试都会在控制台显示实时进度和详细统计信息。

### HTML 报告

如果安装了 `pytest-html` 插件，会自动生成 HTML 报告，包含：
- 设备信息表格
- 总体统计表格
- 每个操作的详细统计表格
- 测试用例的详细日志

报告会在测试完成后自动在浏览器中打开。

## 自定义测试配置

### 修改压力测试次数

#### 方法 1: 使用命令行参数（推荐）

```bash
python test/FlexConnect/run_tests.py --type stress --count 5000
```

#### 方法 2: 使用环境变量

```bash
# Windows PowerShell
$env:STRESS_TEST_COUNT=5000
python test/FlexConnect/run_tests.py --type stress

# Linux/macOS
export STRESS_TEST_COUNT=5000
python test/FlexConnect/run_tests.py --type stress
```

#### 方法 3: 修改代码

编辑 `tests/test_stress.py`，修改 `STRESS_TEST_TOTAL_COUNT` 变量（默认 10,000）。

## 注意事项

### 运行前准备

1. **设备连接**: 确保 FlexConnect 设备已正确连接
2. **驱动安装**: 确认设备驱动已安装
3. **设备占用**: 确保没有其他程序占用设备
4. **环境稳定**: 建议在稳定的环境中运行压力测试

### 运行时

1. **测试时间**: 压力测试需要较长时间（约 10-30 分钟，取决于测试次数）
2. **设备占用**: 测试过程中设备将被持续占用
3. **中断测试**: 可以使用 Ctrl+C 安全中断测试
4. **USB 线缆**: 建议使用质量好的 USB 线缆

### 测试后

测试结束后会自动：
1. 恢复设备状态
2. 断开设备连接
3. 生成 HTML 报告（如果安装了 pytest-html）
4. 自动打开报告（可以使用 --no-open 禁用）

## 故障排查

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

## 成功率标准

- **成功率阈值**: 95%
- **低于 95%**: 测试失败（assert 错误）
- **95% - 99%**: 通过但需关注
- **≥99%**: 优秀

---

**最后更新**: 2026-01-07
