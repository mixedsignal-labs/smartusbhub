# SmartUSBHub 示例

SmartUSBHub Python 库的可运行示例。每个脚本都是独立的，会自动连接找到的第一台
设备，并在文件顶部的 docstring 中说明其用途。

[English](./README.md)

## 前置条件

- 一台通过 USB 连接的 SmartUSBHub。示例通过 `SmartUSBHub.scan_and_connect()`
  自动识别设备，无需指定串口名。
- 确保串口未被其他程序占用。
- SDK 与示例均只依赖 `pyserial`，无需额外安装其他包。

任选一种使用方式：

1. 直接安装发布包：

```bash
pip install smartusbhub
```

2. 引用当前源码库：

```bash
cd smartusbhub
python -m pip install -r requirements.txt
python examples/quick_start.py
```

## 快速上手

按以下顺序运行三个示例即可跑通设备：

| 步骤 | 示例 | 演示内容 | 使用文档 |
| --- | --- | --- | --- |
| 1 | [quick_start.py](./quick_start.py) | 打印完整设备报告（身份信息、能力、运行状态），随后演示电源控制：单通道、全通道同时开关、互锁模式、设备地址读写 | [中文](./docs/quick_start_cn.md) / [en](./docs/quick_start.md) |
| 2 | [power_measurement_oneshot.py](./power_measurement_oneshot.py) | 通过 V2 请求/响应持续读取各通道电压与电流；支持 `--csv` 导出、`--interval-ms` | [中文](./docs/power_measurement_oneshot_cn.md) / [en](./docs/power_measurement_oneshot.md) |
| 3 | [multi_device_channel_control.py](./multi_device_channel_control.py) | 同时发现并控制多台设备 | [中文](./docs/multi_device_channel_control_cn.md) / [en](./docs/multi_device_channel_control.md) |

```bash
python examples/quick_start.py
python examples/power_measurement_oneshot.py
python examples/multi_device_channel_control.py
```

## 扩展示例

不常用需求的补充示例，位于 [extras/](./extras/)：

| 示例 | 演示内容 | 使用文档 |
| --- | --- | --- |
| [extras/dataline_control.py](./extras/dataline_control.py) | 保持供电断开/恢复通道数据线 | [中文](./docs/extras_dataline_control_cn.md) / [en](./docs/extras_dataline_control.md) |
| [extras/power_on_defaults.py](./extras/power_on_defaults.py) | 配置上电默认状态：电源开、数据线连接 | [中文](./docs/extras_power_on_defaults_cn.md) / [en](./docs/extras_power_on_defaults.md) |
| [extras/aging_cycle.py](./extras/aging_cycle.py) | 每通道 N 次上下电循环——老化/产测 | [中文](./docs/extras_aging_cycle_cn.md) / [en](./docs/extras_aging_cycle.md) |
| [extras/alerts.py](./extras/alerts.py) | 配置过流告警规则并订阅事件 | [中文](./docs/extras_alerts_cn.md) / [en](./docs/extras_alerts.md) |
