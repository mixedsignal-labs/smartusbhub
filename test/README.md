# SmartUSBHub 测试套件

本目录包含 SmartUSBHub Python 库的测试，按产品组织，直接连接真实设备进行测试。

## 目录结构

```
test/
├── SmartUSBHub_Pro/          # SmartUSBHub Pro 产品测试
│   ├── test_integration.py   # 接口测试
│   ├── test_stress.py        # 压力测试
│   ├── run_tests.py          # 测试运行脚本
│   └── report/               # 测试报告目录
├── FlexConnect/              # FlexConnect 产品测试
│   ├── test_integration.py   # 接口测试
│   ├── test_stress.py        # 压力测试
│   ├── run_tests.py          # 测试运行脚本
│   └── report/               # 测试报告目录
├── conftest.py               # Pytest fixtures 配置
├── pytest.ini                # Pytest 配置文件
├── frame_generate.py         # 协议帧生成工具
├── report/                   # 通用测试报告目录
└── README.md                 # 本文件
```

## 快速开始

### SmartUSBHub Pro 测试

```bash
# 运行所有测试
python test/SmartUSBHub_Pro/run_tests.py --all

# 只运行接口测试
python test/SmartUSBHub_Pro/run_tests.py --type integration

# 只运行压力测试
python test/SmartUSBHub_Pro/run_tests.py --type stress

# 使用pytest直接运行
pytest test/SmartUSBHub_Pro/test_integration.py -v
pytest test/SmartUSBHub_Pro/test_stress.py -v
```

### FlexConnect 测试

```bash
# 运行所有测试
python test/FlexConnect/run_tests.py --all

# 只运行接口测试
python test/FlexConnect/run_tests.py --type integration

# 只运行压力测试
python test/FlexConnect/run_tests.py --type stress

# 使用pytest直接运行
pytest test/FlexConnect/test_integration.py -v
pytest test/FlexConnect/test_stress.py -v
```

## 测试类型说明

### 接口测试 (test_integration.py)
- 测试所有API接口的基本功能
- 验证设备的基本操作和状态读取
- 包含错误处理测试

### 压力测试 (test_stress.py)
- 通过大量重复操作验证设备稳定性
- 统计成功率和性能指标
- 生成详细的统计报告

## 测试报告

测试运行脚本会自动生成HTML报告，保存在各产品目录的 `report/` 子目录中。

### 安装依赖

```bash
pip install pytest pytest-html
```

### 查看报告

报告会在测试完成后自动在浏览器中打开。如果不想自动打开，使用 `--no-open` 参数：

```bash
python test/SmartUSBHub_Pro/run_tests.py --no-open
```

## 详细文档

- **[TEST_FILES_GUIDE.md](./TEST_FILES_GUIDE.md)** - 测试文件详细使用指南

## 要求

- Python 3.9+
- pytest
- pytest-html (可选，用于生成HTML报告)
- 已连接的 SmartUSBHub 设备

## 注意事项

- 测试需要物理 SmartUSBHub 设备连接
- 测试结束后会自动清理设备状态
- 如果设备不支持某些功能，相关测试会自动跳过
- 使用 `module` 级别的 fixture，所有测试共享同一个设备连接
