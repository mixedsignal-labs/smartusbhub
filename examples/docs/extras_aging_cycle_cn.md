# 老化/产测循环 Demo

`examples/extras/aging_cycle.py`

## 功能说明

逐个通道反复上电/断电——用于快速老化测试或产线测试。按 Ctrl-C 可随时
停止，退出前统一关闭所有通道。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台通过 USB 连接的 SmartUSBHub；被测通道上可以接负载

## 运行

```shell
python examples/extras/aging_cycle.py
python examples/extras/aging_cycle.py --cycles 50 --on-ms 1000
python examples/extras/aging_cycle.py --cycles 100 --on-ms 2000 --off-ms 300
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--cycles` | 10 | 每个通道的上电/断电次数 |
| `--on-ms` | 500 | 每次循环的通电时长，单位 ms |
| `--off-ms` | 500 | 每次循环的断电时长，单位 ms |

## 预期输出

```
Product: SmartUSBHub Pro-4CH  Channels: [1, 2, 3, 4]
10 cycles x 4 channels - Ctrl-C to stop

cycle 1/10  CH1  ON
cycle 1/10  CH2  ON
...
```

## 关键 API

| API | 用途 |
| --- | --- |
| `set_channel_power(ch, state=1/0)` | 单通道上电/断电 |
| `set_channel_power(*channels, state=0)` | 结束时统一关闭全部通道 |

## 注意事项

- 通道是逐个循环的；配合测量 demo（`power_measurement_oneshot.py`）可以
  在老化过程中同步记录电压电流。
- 总时长约为 `次数 × 通道数 × (on_ms + off_ms)`——默认参数下 10 次 × 4
  通道约 4 秒跑完。
