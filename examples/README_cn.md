# SmartUSBHub 示例

SmartUSBHub Python 库的可运行示例。每个脚本都是独立的，会自动连接找到的第一台
设备，并在文件顶部的 docstring 中说明其用途。

[English](./README.md)

## 前置条件

- 一台通过 USB 连接的 SmartUSBHub。示例通过 `SmartUSBHub.scan_and_connect()`
  自动识别设备，无需指定串口名。
- 确保串口未被其他程序占用。

任选一种使用方式：

1. 直接安装发布包：

```bash
pip install smartusbhub
```

2. 引用当前源码库：

```bash
cd smartusbhub
pip install -r requirements.txt
python examples/power_control_example.py
```

GUI 示例需要额外依赖：

```bash
pip install pyqtgraph PyQt5 numpy
```

## 运行

在安装包环境或当前源码库中运行任意脚本：

```bash
python examples/power_control_example.py
```

## 基础

| 示例 | 演示内容 |
| --- | --- |
| [device_report.py](./device_report.py) | 读取设备身份信息 + 运行时状态；支持 `--info-only`、`--json`、`--port` |
| [power_control_example.py](./power_control_example.py) | 单通道、多通道电源开关；互锁模式 |
| [setting_example.py](./setting_example.py) | 读取设备信息；配置默认状态、地址、工作模式、按钮；恢复出厂 |
| [cycle_all_channels.py](./cycle_all_channels.py) | 依次对每个可控通道进行上下电循环 |
| [set_default_power_dataline_on.py](./set_default_power_dataline_on.py) | 配置上电默认状态（默认上电、USB2 数据线连接） |

## 监测（支持电压/电流检测的型号）

| 示例 | 演示内容 |
| --- | --- |
| [advanced/power_measurement_oneshot.py](./advanced/power_measurement_oneshot.py) | 使用 V2 请求/响应持续打印各通道电压与电流 |
| [advanced/power_measurement_stream.py](./advanced/power_measurement_stream.py) | 使用 V3 测量流协议持续打印各通道电压与电流 |
| [advanced/oscilloscope.py](./advanced/oscilloscope.py) | 电压/电流实时图形界面（需 PyQt5 + pyqtgraph） |
| [advanced/oscilloscope_stream.py](./advanced/oscilloscope_stream.py) | 同上，但使用 V3 测量流协议驱动 |
| [advanced/oc_monitor_usb2_7p.py](./advanced/oc_monitor_usb2_7p.py) | 轮询 USB2 7P 型号的过流实时/锁存状态 |

## 进阶

| 示例 | 演示内容 |
| --- | --- |
| [advanced/dataline_control_example.py](./advanced/dataline_control_example.py) | 保持供电的同时，断开/恢复某通道的 USB2.0 数据线 |
| [advanced/user_callback_example.py](./advanced/user_callback_example.py) | 注册命令 ACK 回调 |
| [advanced/multi_device_channel_control.py](./advanced/multi_device_channel_control.py) | 同时发现并控制多台设备 |
