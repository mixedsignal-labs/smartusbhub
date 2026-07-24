# SmartUSBHub 测试套件

本目录保留 SmartUSBHub Pro 相关测试，并补充不需要真实硬件的离线测试，用于发布前快速自测。

## 目录结构

```text
test/
├── unit/
├── SmartUSBHub_Pro/
│   ├── run_tests.py
│   ├── README.md
│   └── tests/
├── conftest.py
├── pytest.ini
└── TEST_FILES_GUIDE.md
```

## 快速开始

```bash
python -m pip install -e ".[test]"
python -m pytest test/unit
python -m coverage run -m pytest test/unit
python -m coverage report -m smartusbhub.py
python test/SmartUSBHub_Pro/run_tests.py --all
python test/SmartUSBHub_Pro/run_tests.py --type integration
python test/SmartUSBHub_Pro/run_tests.py --type stress
```

## 测试类型

- `integration`: 常规接口测试。
- `stress`: 核心功能压力测试。
- `unit`: 离线单元测试，不需要连接设备。
- `protocol`: 离线协议解析测试，不需要连接设备。
- `all`: 运行全部测试。

## 发布前建议

先运行离线测试：

```bash
python -m pytest test/unit
./scripts/release_check.sh
```

editable install 需要支持现代 PEP 517/660 的 pip。若系统自带 pip 版本较旧，请先升级构建工具：

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[test]"
```

旧版 pip 仍可使用普通（非 editable）源码安装：`python -m pip install ".[test]"`。

在虚拟环境中执行时，请先确认 `python` 指向虚拟环境：

```bash
which python
python -m pip --version
```

连接真实设备后再运行硬件测试：

```bash
python test/SmartUSBHub_Pro/run_tests.py --type integration
python test/SmartUSBHub_Pro/run_tests.py --type stress
```

## 常用参数

- `--count`: 指定压力测试循环次数。
- `--no-open`: 不自动打开 HTML 报告。
- `--no-html`: 不生成 HTML 报告。

## 注意事项

1. 运行前确认设备已连接且未被其他程序占用。
2. 压力测试耗时较长，建议在稳定环境下执行。
3. 测试结束后脚本会尝试恢复设备状态并断开连接。

## 相关文档

- `SmartUSBHub_Pro/README.md`
- `TEST_FILES_GUIDE.md`
