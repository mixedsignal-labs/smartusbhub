# 告警 Demo（过流保护）

`examples/extras/alerts.py`

## 功能说明

在一个通道上设置过流告警规则（阈值单位 mA），注册事件回调、订阅告警
事件，并每秒轮询一次告警状态。想看到触发效果，让被监控通道的电流超过
阈值即可。

demo 的动作是 `power_off_lock`：超过阈值后设备切断该通道电源并锁定——
这是真实的保护动作，不只是通知。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台通过 USB 连接的 SmartUSBHub，被监控通道上接设备/负载

## 运行

```shell
python examples/extras/alerts.py
python examples/extras/alerts.py --channel 2 --threshold 200
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--channel` | 1 | 要监控的通道 |
| `--threshold` | 500 | 过流阈值，单位 mA |

## 预期输出

```
alert rule: {'channel': 1, 'type': 'overcurrent', 'threshold': 500, 'action': 'power_off_lock'}
watching CH1 for overcurrent > 500 mA - Ctrl-C to stop

alert status: [...]
ALERT on CH1: {...}          <- 超过阈值时触发
alert status: [...]          <- 通道显示告警/电源锁定
```

## 关键 API

| API | 用途 |
| --- | --- |
| `set_alert_config(channel, "overcurrent", threshold_ma, action=...)` | 创建告警规则；`threshold` 单位为 mA |
| `register_callback(CMD_ALERT_EVENT, fn)` | 注册告警事件到达时的回调函数 |
| `subscribe_alert_events(True/False)` | 开始/停止向主机推送告警事件 |
| `get_alert_status()` | 轮询当前告警状态 |

## 注意事项

- `power_off_lock` 触发后通道保持锁定状态；重新使用该通道前需先解除
  锁定（可通过上位机或 SDK 操作）。
- 回调由设备推送事件时触发；demo 中的每秒轮询是额外一道保险，可以同时
  观察状态字段的变化。
