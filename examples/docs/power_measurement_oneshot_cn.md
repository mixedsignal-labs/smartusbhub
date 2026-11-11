# 电压电流测量 Demo（请求/响应方式）

`examples/power_measurement_oneshot.py`

## 功能说明

先给所有通道上电，然后循环查询每个通道的电压和电流并打印（单位
mV / mA），可选把数据写入 CSV 文件。按 Ctrl-C 停止。

本 demo 使用 V2 请求/响应测量：每轮由脚本主动向设备请求一次各通道采样。
所有带测量能力（ADC）的型号都支持。

## 环境要求

- Python 3.7+，已安装 SDK 或在源码目录运行
- 一台支持测量的 SmartUSBHub，通过 USB 连接
- 通道上最好接一个耗电设备（手机、小负载等），否则电流读数接近 0 mA

## 运行

```shell
python examples/power_measurement_oneshot.py
python examples/power_measurement_oneshot.py --interval-ms 500
python examples/power_measurement_oneshot.py --csv data.csv
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--interval-ms` | 200 | 每轮轮询间隔，单位 ms |
| `--csv FILE` | 关闭 | 同时把采样写入 CSV 文件 |

## 预期输出

```
Product: SmartUSBHub Pro-4CH  Channels: [1, 2, 3, 4]
Polling every 200 ms - Ctrl-C to stop

CH1    5100 mV     420 mA
CH2    5098 mV       0 mA
CH3    5101 mV     180 mA
CH4    5099 mV       0 mA
```

CSV 文件每轮一行：`timestamp_s, ch1_mV, ..., ch1_mA, ...`。

## 关键 API

| API | 用途 |
| --- | --- |
| `get_channel_voltage(ch)` | 单通道瞬时电压，单位 mV |
| `get_channel_current(ch)` | 单通道瞬时电流，单位 mA |
| `set_channel_power(ch, state=1)` | 测量前先上电 |

## 注意事项

- 不带测量硬件的型号调用这些接口会返回错误；不确定型号是否支持测量时，
  可先调用 `get_capability()` 查看。
- 需要连续高速采集时请参考 SDK 文档中的流式测量部分——本 demo 刻意保持
  简单。
