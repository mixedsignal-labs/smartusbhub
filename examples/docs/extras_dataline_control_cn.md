# 数据线控制 Demo

`examples/extras/dataline_control.py`

## 功能说明

断开第一通道的数据线，等待 2 秒后重新连接——全程**电源保持供电**。观察
下游设备：它会重新枚举（主机播放断开/接入提示音），但从未断电。

这是 SmartUSBHub 区别于普通 USB Hub 的招牌能力：数据线可以由软件单独
控制，与电源互不影响。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台 SmartUSBHub，第 1 通道上插一个设备（这样才能看到重新枚举效果）

## 运行

```shell
python examples/extras/dataline_control.py
```

## 预期输出

```
Product: SmartUSBHub Pro-4CH  Channel under test: 1
disconnect data line (power stays on)
data line status: [{'channel': 1, 'dataline': 0}]
reconnect data line
data line status: [{'channel': 1, 'dataline': 1}]
```

## 关键 API

| API | 用途 |
| --- | --- |
| `set_channel_dataline(ch, state=0/1)` | 断开/恢复通道数据线 |
| `get_channel_dataline_status(ch)` | 回读数据线状态 |
| `set_channel_power(ch, state=1)` | 先上电——demo 全程保持供电 |

## 注意事项

- USB2 型号切换的是 D+/D- 差分对；USB3 型号同时覆盖 SuperSpeed 差分对，
  整条数据通路都会断开。
- 典型用途：不拔线强制 USB 设备重新枚举、远程恢复卡死的设备、测试台架
  中脚本化地开关设备。
