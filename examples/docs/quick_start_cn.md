# 快速上手 Demo

`examples/quick_start.py`

## 功能说明

连接第一台找到的 SmartUSBHub，演示设备最常用的三类操作：

1. **设备报告** — 产品名、硬件/固件版本、通道列表、能力标志，以及每个
   通道当前的电源状态和 USB2 数据线状态。
2. **电源控制** — 单通道开关、全通道同时开关、互锁模式（同一时刻只有
   一个通道供电），最后恢复普通模式。
3. **设备地址** — 读取当前设备地址并写回。

## 环境要求

- Python 3.7+
- 已安装 SDK（`pip install smartusbhub`）或在源码目录下运行（脚本会自动
  把包根目录加入 `sys.path`）
- 一台通过 USB 连接的 SmartUSBHub

## 运行

```shell
python examples/quick_start.py
```

如果想指定串口而不是自动扫描：

```python
hub = SmartUSBHub("/dev/cu.usbmodem132301")
```

## 预期输出

```
=== Device Info ===
  Product name      : SmartUSBHub Pro-4CH
  Hardware version  : V1.2
  ...
=== Power control ===
turn on channel 1
turn off channel 1
turn on all channels [1, 2, 3, 4] at once
...
=== Device address ===
current device address: 0
device address set to: 0
```

## 关键 API

| API | 用途 |
| --- | --- |
| `SmartUSBHub.scan_and_connect()` | 扫描所有串口并连接第一台设备 |
| `get_product_name() / get_hardware_version() / get_firmware_version()` | 设备身份信息 |
| `get_channels()` | 可控通道号元组 |
| `get_capability()` | 当前型号的能力标志 |
| `get_channel_power_status(*channels)` | 每通道当前电源状态 |
| `get_channel_usb2_dataline_status(*channels)` | 每通道当前数据线状态 |
| `set_channel_power(ch, state=1/0)` | 通道上电/断电（支持多通道） |
| `set_channel_power_interlock(ch)` / `set_channel_power_interlock(None)` | 互锁模式：同时只有一个通道供电；`None` 恢复普通模式 |
| `get_device_address()` / `set_device_address(addr)` | 读/写设备地址 |

## 注意事项

- 设备地址演示是"读出什么就写回什么"，重复运行不会改变设备配置。
- 互锁模式适用于多个下游设备不允许同时取电的场景（例如共享功率预算）。
