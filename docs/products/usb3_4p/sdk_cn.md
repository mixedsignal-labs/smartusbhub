# HBP_USB3_4CH RevB Python SDK

适用产品 type=`0x04`，4 个下行口；本页对应当前 RevB 固件1.0.0、协议接口1.2.0、硬件2.0。
SDK 按设备能力声明识别功能，控制串口为独立 CMD USB-C（115200 baud）。
本页为 SDK 接入说明，实板功能仍需按 bring-up 清单验证。

## 能力与边界

| 功能 | 接口 / 说明 |
|---|---|
| 四路电源 | `set_channel_power`、`get_channel_power_status` |
| 四路 USB2 数据 | `set_channel_usb2_dataline`、`get_channel_usb2_dataline_status` |
| 四路 USB3 数据 | `set_channel_usb3_dataline`、`get_channel_usb3_dataline_status` |
| 双主机选择 | `set_upstream_host`、`get_upstream_host`；按设备能力判断 |
| 测量单元 电压/电流 | `get_channel_voltage`、`get_channel_current`、`get_channel_measurements` |
| 测量流 | `set_channel_measurement_stream`、`get_stream_channel_measurements` |
| 默认电源 / 自动恢复 | `set_default_power_status`、`set_auto_restore` |
| 设备别名 / 通道名 | `set_device_alias`、`set_channel_name` |
| 板温 | 按设备板温能力声明查询 |
| 告警 / ILIM | ADV支持设备声明的告警规则，默认过流仅通知；ILIM切换未开放 |

端口编号为 1～4。measurement hardware 的物理通道转换在固件内完成，SDK 返回的编号就是产品端口编号。
`get_capability()` 可查询 `measurement`、`usb3_data_switch`、`upstream_host_switch` 等能力；
主机选择按设备能力声明判断，不按固件主版本推断。

## 连接与识别

安装当前源码：

```sh
python -m pip install -e /path/to/smartusbhub/sdk/python-sdk
```

```python
from smartusbhub import SmartUSBHub

hub = SmartUSBHub("COM3")  # macOS 例如 /dev/cu.usbmodemXXXX
try:
    print(hub.get_identity())
    print(hub.get_capability())
    assert hub.product_type == 0x04
    print(hub.get_upstream_host())
finally:
    hub.disconnect()
```

## USB2 / USB3 数据控制

```python
# 对已连接的 hub 执行；这些调用会改变硬件状态。
assert hub.set_channel_power(1, state=1)
assert hub.set_channel_usb2_dataline(1, state=1)
assert hub.set_channel_usb3_dataline(1, state=1)
print(hub.get_channel_usb3_dataline_status(1, 2, 3, 4))
# 例如 {1: 1, 2: 0, 3: 0, 4: 0}

assert hub.set_channel_usb3_dataline(1, state=0)  # USB2 保持连接
assert hub.set_channel_usb2_dataline(1, state=0)  # 联动断开 USB3
```

USB3 连通会联动连通 USB2；关闭 VBUS 会同时断开两组数据。
重新开启 VBUS 按固件保存的数据策略恢复。数据控制返回值代表协议 ACK，
实物链路是否连通、是否以 SuperSpeed 工作，应通过主机枚举与实际传输确认。
USB3 查询返回 `{端口: 0或1}`；省略端口则查询全部四口，通信失败返回 `None`。
设置的 `state` 仅接受 0/1，端口超出范围抛出 `ValueError`。

## 双主机选择

```python
assert hub.set_upstream_host(1)  # 选择Host1
assert hub.set_upstream_host(1)  # Host1
assert hub.set_upstream_host(2)  # Host2
print(hub.get_upstream_host())  # 0 / 1 / 2；通信失败或设备拒绝为 None
```

设置返回 `True/False`。`host` 必须是整数 0/1/2，否则抛出 `ValueError`；
不支持的型号或固件抛出 `FeatureNotSupportedError`，不会发送切换命令。
切换先断开，再改选路，最后接通。选择保存到Flash并在启动后恢复；未设置或恢复出厂时默认Host1。
Bootloader 阶段上行保持断开；独立 CMD 控制接口可继续用于 DFU。
Hub 初始化失败时，连接 Host1/2 会被拒绝。
切换主机前先卸载正在使用的存储设备。

## 测量

```python
print(hub.get_channel_measurements(1, 2, 3, 4))
assert hub.set_channel_measurement_stream(1, 2, 3, 4, enabled=True)
try:
    print(hub.get_stream_channel_measurements(1, 2, 3, 4, timeout=2))
finally:
    hub.set_channel_measurement_stream(1, 2, 3, 4, enabled=False)
```

结果沿用 SDK 现有的电压、电流及 `valid/fresh/stale` 字段；无效/过期数据不能当作当前读数。
实际流输出速率与芯片内部采样率不同，测量单元 的 1024 SPS 不代表 SDK 每秒收到 1024 帧。

## 批量采集与滤波

固件 1.0.0 配合 SDK 1.3.0 支持四路带序号批量采集，档位为 10/100/250 Sa/s，默认 250。`set_channel_measurement_stream()` 自动协商采样率，`get_stream_channel_measurements()` 按顺序逐条消费批次数据，不会只保留批次最后一条。`sample_time_us` 是 MCU 发出 REFRESH 请求的时间，按 32 位微秒回绕，不是精确的 ADC 转换时刻。`capture_statistics` 和 `measurement_queue_drops` 分别报告设备侧和主机侧的丢样情况。

`set_measurement_filter(0)` 选择瞬时值；`set_measurement_filter(1)` 使用测量单元内置的 8 点滑动平均。窗口约 7.8 ms、群延迟约 3.4 ms、-3 dB 带宽约 57 Hz；输出仍为所选采样率，相邻滤波结果共享原始转换样本，没有额外的软件滤波。切换会短暂停流并清空旧批次；设置只保存在 RAM 中，重启后默认为瞬时值。`get_measurement_filter()` 可查询当前设置。

```python
hub.set_measurement_filter(1)
hub.set_channel_measurement_stream(enabled=True)
try:
    sample = hub.get_stream_channel_measurements(timeout=0.2)
finally:
    hub.set_channel_measurement_stream(enabled=False)
```

## 对应协议

| 指令 | 编码 | 参数 |
|---|---|---|
| USB3 设置 | 0x15 | channel=端口位掩码，data=0/1 |
| USB3 查询 | 0x16 | channel=端口位掩码，逐口回复 |
| 上行主机设置 | 0x22 | channel=0，data=0/1/2 |
| 上行主机查询 | 0x23 | channel=0，data=0 |

上行主机成功响应为 channel=0、data=实际选择；失败为 FF/FF。
SDK 负责协议打包，不需要业务脚本自行生成位掩码或校验和。

## 新增SDK接口与固件边界

`get_channel_power(channel)` 返回mW。`get_cached_measurements()` 仅读缓存。
`reset_hub()` 需要固件明确声明 `device.reset_hub=true`；新增源码协议为V3 `0x2C`，
现有设备未更新固件时不可用。本次实板已验证命令执行、MCU/CMD保持、端口供电保持；USB吞吐不在本次范围。
默认数据状态SDK已明确命名USB2，USB3默认配置使用 `set_default_usb3_dataline_status()` / `get_default_usb3_dataline_status()`，需固件声明 `device.default_usb3_data=true`。
