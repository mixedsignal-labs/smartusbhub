# SmartUSBHub 测试文件使用指南

本文档说明当前保留的离线单元测试与 SmartUSBHub Pro 真机测试文件。

## 文件结构

```text
test/
├── unit/                       # 离线测试，无需硬件
│   ├── fake_device.py          # 设备模拟器 + 实例工厂（被各离线测试共享）
│   ├── test_api_surface.py
│   ├── test_protocol_frames.py
│   ├── test_packet_encoding.py
│   ├── test_measurements_and_overcurrent.py
│   ├── test_product_capabilities.py
│   ├── test_connection_lifecycle.py
│   ├── test_discovery.py
│   ├── test_device_loopback.py
│   └── test_callbacks_and_dispatch.py
├── SmartUSBHub_Pro/
│   ├── run_tests.py
│   ├── README.md
│   └── tests/
├── conftest.py
├── pytest.ini
└── TEST_FILES_GUIDE.md
```

## 离线测试（无需硬件）

### `test/unit/fake_device.py`

- 用途：在进程内模拟 MCU 的 V1/V2/V3 帧协议。`make_live_hub` 用真实
  `SmartUSBHub.__init__`（含真实接收线程）连接该模拟器，从而离线跑通
  发送 → 编码 → 接收线程 → 解析 → 分发 → ACK 的完整链路。
- 不是测试文件，被其他离线测试导入使用。

### `test/unit/test_device_loopback.py`

- 用途：用模拟器对电源 / 数据线 / 电压电流 / 批量测量 / 过流 / 默认状态 /
  操作模式 / 按键 / 自动恢复 / 设备地址 / 身份查询 / 工厂复位 / 重启 等命令
  做收发回环验证，并覆盖真实 `get_device_info` 握手与无响应超时路径。

### `test/unit/test_packet_encoding.py`

- 用途：断言 `_send_packet` / `_send_v3_packet` 产生的字节（SOF、通道掩码、
  负载、V1 校验和、V3 CRC、超长负载报错）。

### `test/unit/test_callbacks_and_dispatch.py`

- 用途：验证 `register_callback` / `register_disconnect_callback`、
  `get_product_info`，以及接收循环的粘包拆包、半帧重组、前导垃圾跳过、
  流帧不置位 ACK 等行为。

### `test/unit/test_discovery.py`

- 用途：伪造串口枚举与握手，离线验证 `scan_available_ports` /
  `scan_and_connect` / `scan_and_connect_by_address` / `auto_connect`
  的命中、未命中与特性过滤路径。

推荐运行：

```bash
python -m pytest test/unit
python -m coverage run -m pytest test/unit && python -m coverage report -m smartusbhub.py
```

## 真机测试文件

### `test/SmartUSBHub_Pro/tests/test_integration.py`

- 用途：验证设备连接、状态读取、电源控制、数据线控制、配置设置等基础接口。
- 推荐运行：

```bash
python test/SmartUSBHub_Pro/run_tests.py --type integration
pytest test/SmartUSBHub_Pro/tests/test_integration.py -v -s
```

### `test/SmartUSBHub_Pro/tests/test_integration_discovery.py`

- 用途：真机验证发现 / 连接 / 回调 / 重启类接口
  （`scan_available_ports`、`auto_connect`、`scan_and_connect_by_address`、
  `register_callback`、`register_disconnect_callback`、`reboot_mcu` + 重连）。
- 自行管理连接，不使用模块级 `hub` fixture，避免端口争用。
- 已并入 `--type integration` 与 `--all`。

### `test/SmartUSBHub_Pro/tests/test_stress.py`

- 用途：执行核心功能长时间循环压力测试。
- 推荐运行：

```bash
python test/SmartUSBHub_Pro/run_tests.py --type stress
pytest test/SmartUSBHub_Pro/tests/test_stress.py -v -s
```

## 配置文件

### `test/conftest.py`

- 提供公共 fixture、测试命令行参数和 HTML 报告标题处理。

### `test/pytest.ini`

- 定义 pytest 发现规则、默认输出和标记。

## 常见说明

1. 这些测试依赖真实硬件。
2. 压力测试运行时间可能较长。
3. 如果设备不支持某项能力，相关测试可能自动跳过。
