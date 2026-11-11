# 上电默认状态 Demo

`examples/extras/power_on_defaults.py`

## 功能说明

把所有通道的上电默认状态配置为"电源开 + 数据线连接"，然后回读确认。

这些默认值保存在设备的非易失存储中，设备每次上电（或通道重新使能）时
自动生效。这是一次性配置，不需要反复运行。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台通过 USB 连接的 SmartUSBHub

## 运行

```shell
python examples/extras/power_on_defaults.py
```

## 预期输出

```
set defaults: power ON, data line connected
default power status : [{'channel': 1, 'enable': 1, 'status': 1}, ...]
default dataline     : [{'channel': 1, 'enable': 1, 'status': 1}, ...]
```

## 关键 API

| API | 用途 |
| --- | --- |
| `set_default_power_status(*channels, enable=1, status=1)` | 上电时应用的电源默认状态；`enable` 控制规则是否生效，`status` 为开/关 |
| `set_default_dataline_status(*channels, enable=1, status=1)` | 上电时应用的数据线默认状态 |
| `get_default_power_status(*channels)` / `get_default_dataline_status(*channels)` | 回读已保存的默认值 |

## 注意事项

- 配置写入 Flash，断电重启后依然保留。
- 想让通道上电时默认断电，把同一脚本里的 `status` 改成 `0` 即可。
- 这些配置也可以在 SmartUSBHub 上位机里修改；本 demo 演示的是程序化
  设置方法。
