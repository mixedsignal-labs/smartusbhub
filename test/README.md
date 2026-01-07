# SmartUSBHub 测试套件

本目录包含 SmartUSBHub Python 库的测试，按产品组织，直接连接真实设备进行测试。

## 目录结构

```
test/
├── SmartUSBHub_Pro/          # SmartUSBHub Pro 产品测试
│   ├── run_tests.py          # 测试运行脚本（统一入口）
│   ├── README.md             # 产品测试文档
│   ├── tests/                # 测试文件目录
│   │   ├── test_integration.py
│   │   ├── test_stress.py
│   │   └── test_stress_charge_mode_switch.py
│   └── report/               # 测试报告目录
├── FlexConnect/              # FlexConnect 产品测试
│   ├── run_tests.py          # 测试运行脚本（统一入口）
│   ├── README.md             # 产品测试文档
│   ├── tests/                # 测试文件目录
│   │   ├── test_integration.py
│   │   ├── test_stress.py
│   │   └── ...              # 其他测试文件
│   └── report/               # 测试报告目录
├── conftest.py               # Pytest fixtures 配置
├── pytest.ini                # Pytest 配置文件
└── README.md                 # 本文件
```

## 快速开始

### 基本要求

- Python 3.9+
- pytest
- pytest-html (可选，用于生成HTML报告)
- 已连接的 SmartUSBHub 设备

### 安装依赖

```bash
pip install pytest pytest-html
```

### 运行测试

每个产品都提供了统一的 `run_tests.py` 脚本，通过参数选择不同的测试类型：

#### SmartUSBHub Pro

```bash
# 运行所有测试
python test/SmartUSBHub_Pro/run_tests.py --all

# 运行接口测试
python test/SmartUSBHub_Pro/run_tests.py --type integration

# 运行压力测试
python test/SmartUSBHub_Pro/run_tests.py --type stress

# 运行压力测试，指定测试次数
python test/SmartUSBHub_Pro/run_tests.py --type stress --count 10000

# 运行充电模式切换压力测试
python test/SmartUSBHub_Pro/run_tests.py --type stress_charge_mode

# 运行充电模式切换压力测试，指定测试次数
python test/SmartUSBHub_Pro/run_tests.py --type stress_charge_mode --count 1000

# 不自动打开报告
python test/SmartUSBHub_Pro/run_tests.py --all --no-open
```

#### FlexConnect

```bash
# 运行所有测试
python test/FlexConnect/run_tests.py --all

# 运行接口测试
python test/FlexConnect/run_tests.py --type integration

# 运行压力测试
python test/FlexConnect/run_tests.py --type stress

# 运行压力测试，指定测试次数
python test/FlexConnect/run_tests.py --type stress --count 5000

# 不自动打开报告
python test/FlexConnect/run_tests.py --all --no-open
```

## 测试类型说明

### 接口测试 (integration)

- **目的**: 验证所有 API 接口的基本功能
- **内容**: 设备连接、电源控制、数据线控制、充电模式、设备设置等
- **预计时间**: 2-5 分钟
- **成功标准**: 所有测试用例通过

### 压力测试 (stress)

- **目的**: 通过大量重复操作验证设备稳定性
- **内容**: 高频操作测试、状态读取、模式切换等
- **预计时间**: 5-30 分钟（取决于测试次数）
- **成功标准**: 成功率 ≥95%
- **自定义测试次数**: 使用 `--count` 参数指定测试次数

## 命令行参数说明

### --type

指定测试类型：
- `integration`: 接口测试
- `stress`: 压力测试
- `stress_charge_mode`: 充电模式切换压力测试（仅 SmartUSBHub Pro）
- `all`: 运行所有测试

### --count

指定压力测试的测试次数。适用于所有压力测试类型（`stress` 和 `stress_charge_mode`）。

- SmartUSBHub Pro 核心功能压力测试默认 500,000 次
- SmartUSBHub Pro 充电模式切换压力测试默认 10,000 次
- FlexConnect 压力测试默认 10,000 次

示例：
```bash
# SmartUSBHub Pro 核心功能压力测试，指定 10,000 次
python test/SmartUSBHub_Pro/run_tests.py --type stress --count 10000

# FlexConnect 压力测试，指定 5,000 次
python test/FlexConnect/run_tests.py --type stress --count 5000
```

### --no-open

不自动打开 HTML 报告。

### --no-html

不生成 HTML 报告。

## 测试报告

测试运行脚本会自动生成 HTML 报告，保存在各产品目录的 `report/` 子目录中。

报告会在测试完成后自动在浏览器中打开。如果不想自动打开，使用 `--no-open` 参数：

```bash
python test/SmartUSBHub_Pro/run_tests.py --all --no-open
```

## 注意事项

### 运行前准备

1. **设备连接**: 确保 SmartUSBHub 设备已正确连接
2. **驱动安装**: 确认设备驱动已安装
3. **设备占用**: 确保没有其他程序占用设备
4. **环境稳定**: 建议在稳定的环境中运行压力测试

### 运行时

1. **测试时间**: 压力测试需要较长时间，请耐心等待
2. **设备占用**: 测试过程中设备将被持续占用
3. **中断测试**: 可以使用 Ctrl+C 安全中断测试
4. **USB 线缆**: 建议使用质量好的 USB 线缆

### 测试后

测试结束后会自动：
1. 关闭所有通道
2. 恢复设备状态
3. 断开设备连接
4. 生成 HTML 报告（如果安装了 pytest-html）
5. 自动打开报告（可以使用 --no-open 禁用）

## 详细文档

- **[SmartUSBHub_Pro/README.md](./SmartUSBHub_Pro/README.md)** - SmartUSBHub Pro 测试详细文档
- **[FlexConnect/README.md](./FlexConnect/README.md)** - FlexConnect 测试详细文档
- **[TEST_FILES_GUIDE.md](./TEST_FILES_GUIDE.md)** - 测试文件详细使用指南

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

## 设计说明

### 文件组织原则

- **统一入口**: 每个产品目录下只有一个 `run_tests.py` 脚本，通过 `--type` 参数选择不同的测试类型
- **测试文件隔离**: 所有测试文件都放在 `tests/` 子文件夹中，保持产品目录整洁
- **文档分离**: 产品特定的文档放在各自的产品目录下

### 为什么这样组织？

1. **清晰的结构**: 产品目录下只保留运行脚本和文档，测试文件统一放在 `tests/` 文件夹
2. **易于维护**: 新增测试文件只需放在 `tests/` 文件夹，不需要修改产品目录结构
3. **统一接口**: 所有测试都通过 `run_tests.py` 运行，使用方式一致

---

**最后更新**: 2026-01-07
