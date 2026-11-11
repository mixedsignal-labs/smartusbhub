# 多设备通道控制 Demo

`examples/multi_device_channel_control.py`

## 功能说明

扫描并连接电脑上接的**所有** SmartUSBHub，然后跑一个"流水灯"：所有设备
的通道按顺序逐个点亮 0.1 秒，通道指示灯随之流动。按 Ctrl-C 停止，退出时
统一关闭所有通道并断开全部设备。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台或多台通过 USB 连接的 SmartUSBHub

## 运行

```shell
python examples/multi_device_channel_control.py
```

## 预期输出

```
Device 1: SmartUSBHub Pro-4CH (port: /dev/cu.usbmodem132301)
Device 2: SmartUSBHub Pro-4CH (port: /dev/cu.usbmodem132302)
Found 2 device(s), 8 channels total. Ctrl-C to stop.
```

之后所有设备的通道指示灯依次流动，直到你手动停止。

## 关键 API

| API | 用途 |
| --- | --- |
| `SmartUSBHub.scan_and_connect(exclude_ports=...)` | 扫描连接，跳过已占用的端口 |
| `hub.port` / `hub.name` | 串口路径和设备名 |
| `set_channel_power(ch, state=1/0)` | 通道上电/断电 |
| `hub.disconnect()` | 释放串口 |

## 注意事项

- 枚举多台同型号设备的关键是 `exclude_ports`：维护一个已连接端口集合，
  每连上一台就加入集合并传给下一次扫描，直到扫描返回 `None`。
- 任意时刻只有一个通道在供电，即使接了很多台设备总功耗也很低。
