# Python API 参考

<!-- 由 smartusbhub.py 的结构与 api/python.po 的既有译文生成；正文请改 po，不要在此手工增删。 -->

## 模块

通过 USB CDC 控制端口控制 SmartUSBHub 设备。

使用方法见 README.md，帧格式和命令说明见 docs/protocol.md。

## SmartUSBHub

通过 USB CDC 串口控制工业级 Smart USB Hub 的高层接口。

提供逐端口电源与数据连接控制、电压/电流监测、默认状态配置和恢复出厂设置功能，适用于自动化测试系统和硬件开发。

实例可用作上下文管理器；退出上下文时会断开设备连接：

```python
with SmartUSBHub(port) as hub:
    hub.set_channel_power(1, state=1)
```

<a id="smartusbhub.SmartUSBHub.close"></a>

### `close`

```python
close()
```

关闭连接。``disconnect()`` 的别名。

<a id="smartusbhub.SmartUSBHub.get_alert_config"></a>

### `get_alert_config`

```python
get_alert_config(channel, kind)
```

读取已生效的比较器规则。阈值单位为 mA、mV 或 mW。

<a id="smartusbhub.SmartUSBHub.get_alert_defaults"></a>

### `get_alert_defaults`

```python
get_alert_defaults(channel, kind)
```

读取 MCU 出厂默认值，不改变当前生效的规则。

<a id="smartusbhub.SmartUSBHub.set_alert_config"></a>

### `set_alert_config`

```python
set_alert_config(channel, kind, threshold, enabled=True, samples=1, action='notify')
```

设置一条规则；成功时返回已生效的规则，失败时返回 None。

USB3 FW1.0.0 在返回成功前会将设置保存到 App Flash。设置未变化时不会擦除 Flash。

power_off_lock 会断开电源和数据连接，并阻止所有上电途径。通道断电期间及上电后的 100ms 内忽略 UC/UV。比较器阈值会量化；raw_threshold 是经校验的寄存器值。

<a id="smartusbhub.SmartUSBHub.get_alert_status"></a>

### `get_alert_status`

```python
get_alert_status()
```

查询 MCU 缓存的状态，不读取芯片中读后清零的寄存器。

<a id="smartusbhub.SmartUSBHub.clear_alert_latch"></a>

### `clear_alert_latch`

```python
clear_alert_latch(channel_mask)
```

清除告警历史。

**参数**
- `channel_mask`（int）：通道位掩码；第 0 位选择 CH1。

**返回**（bool）：设备是否已确认该位掩码。

**异常**
- `FeatureNotSupportedError`：不支持告警功能。
- `ValueError`：通道位掩码无效。

<a id="smartusbhub.SmartUSBHub.reset_protection_trip"></a>

### `reset_protection_trip`

```python
reset_protection_trip(channel_mask)
```

仅在获得最新且正常的监测读数后，解除已断电端口的锁定；此操作不会上电。

电源关闭时，比较器状态清除并不能证明负载故障已排除。此后的上电操作属于主动重试，仍可能再次触发保护。

<a id="smartusbhub.SmartUSBHub.subscribe_alert_events"></a>

### `subscribe_alert_events`

```python
subscribe_alert_events(enabled=True)
```

请先注册 CMD_ALERT_EVENT 回调；回调在接收线程中执行。

<a id="smartusbhub.SmartUSBHub.set_debug_log_enabled"></a>

### `set_debug_log_enabled`

```python
set_debug_log_enabled(enabled)
```

订阅或取消订阅 MCU 推送的 V3 日志帧（0x24，STREAM）。

0x26 的回复通过 register_callback 交付；不执行 ACK 恢复。每次连接后调用一次，并在关闭会话前禁用。

<a id="smartusbhub.SmartUSBHub.request_board_temperature"></a>

### `request_board_temperature`

```python
request_board_temperature()
```

异步请求板温；此方法不直接返回温度。

请求前请先注册 CMD_GET_DEBUG_TEMPERATURE 回调。日志独立到达；此请求不会启用日志。

<a id="smartusbhub.SmartUSBHub.register_disconnect_callback"></a>

### `register_disconnect_callback`

```python
register_disconnect_callback(callback)
```

register_callback("disconnect", callback) 的已弃用别名。

<a id="smartusbhub.SmartUSBHub.register_callback"></a>

### `register_callback`

```python
register_callback(cmd, callback)
```

注册命令回调或主机侧的断连事件回调。

命令回调在接收线程中执行，参数为 ``(channel, value)``；``value`` 的类型取决于命令，可以是整数、列表或解码后的字典。连接意外断开时，"disconnect" 会在端口清理完成后，由接收线程调用一个无参数回调。主动调用 disconnect() 不会触发此回调。传入 None 可注销任一类回调。每个键只对应一个回调；再次注册会替换原回调。

<a id="smartusbhub.SmartUSBHub.get_product_info"></a>

### `get_product_info`

```python
get_product_info(product_type_id)
```

查询产品元数据和已弃用的旧版能力字段。

对于已连接的设备，请使用 get_capability() 读取 MCU 的能力声明。

**参数**
- `product_type_id`：产品类型 ID（见 ``PRODUCT_TYPE_TABLE``）。

**返回**：产品信息字典；ID 未知时返回 None。

<a id="smartusbhub.SmartUSBHub.scan_available_ports"></a>

### `scan_available_ports`

```python
scan_available_ports()
```

扫描 USB VID/PID 与 Smart USB Hub 匹配的串口。

**返回**：匹配的端口设备名称列表。

<a id="smartusbhub.SmartUSBHub.scan_candidates"></a>

### `scan_candidates`

```python
scan_candidates()
```

返回操作系统提供的 SmartUSBHub CMD 端口结构化元数据。

此方法仅枚举 USB 串口设备，不会打开端口或改变设备状态。平台无法提供的字段返回 ``None``。

**返回**：字典列表，每个字典包含端口、VID/PID 和 USB 描述符元数据。

<a id="smartusbhub.SmartUSBHub.capabilities_source"></a>

### `capabilities_source`

```python
capabilities_source()
```

device / legacy / unavailable；缺少能力声明绝不表示支持该能力。

<a id="smartusbhub.SmartUSBHub.get_capability"></a>

### `get_capability`

```python
get_capability(refresh=False)
```

返回合并了已声明详细信息的 MCU JSON 文档。

不会添加根据旧版信息或型号推导的标志。None 表示没有 MCU 声明。refresh=True 会重新请求摘要及其中已声明的已知章节。

**参数**
- `refresh`（bool）：重新查询声明。

**返回**（dict or None）：独立的 MCU 声明，或 None。

<a id="smartusbhub.SmartUSBHub.get_identity"></a>

### `get_identity`

```python
get_identity()
```

以适合 JSON 的原始值返回缓存的设备身份信息。

与 `get_device_info` 不同，无法获取的值保留为 ``None``，不会格式化为 ``"N/A"``。

<a id="smartusbhub.SmartUSBHub.scan_and_connect"></a>

### `scan_and_connect`

```python
scan_and_connect(exclude_ports=None, device_address=None)
```

扫描 Smart USB Hub 设备并连接第一个有效设备。

**参数**
- `exclude_ports`：要跳过的端口集合；默认跳过已连接的端口。
- `device_address`：指定后，仅连接上报此地址的设备。注意：设备地址默认为 0，多台设备可能使用同一地址，建议优先按端口选择。参见 `scan_and_connect_by_address`。

**返回**：已连接的 SmartUSBHub 实例；未找到设备时返回 None。

<a id="smartusbhub.SmartUSBHub.scan_and_connect_by_address"></a>

### `scan_and_connect_by_address`

```python
scan_and_connect_by_address(device_address)
```

按设备地址连接 Smart USB Hub。

设备地址默认为 0，多台设备可能共用一个地址，因此按地址选择并不可靠。请使用 ``SmartUSBHub(port)`` 指定串口，或先为设备分配不同的地址。

**参数**
- `device_address`：要匹配的设备地址（0x0000 - 0xFFFF）。

**返回**：已连接的 SmartUSBHub 实例；未找到匹配设备时返回 None。

<a id="smartusbhub.SmartUSBHub.auto_connect"></a>

### `auto_connect`

```python
auto_connect(exclude_ports=None, feature_filter=None)
```

扫描并连接第一个可用设备，跳过被占用的设备。

与 `scan_and_connect` 相同，会跳过被占用或连接失败的端口。

**参数**
- `exclude_ports`：要跳过的端口集合；默认跳过已连接的端口。
- `feature_filter`：指定后，仅连接支持此功能的设备（有效名称见 ``_check_feature_support``）。

**返回**：已连接的 SmartUSBHub 实例；没有可用设备时返回 None。

<a id="smartusbhub.SmartUSBHub.disconnect"></a>

### `disconnect`

```python
disconnect()
```

断开设备连接并停止接收线程。

此操作具有幂等性，可安全地重复调用，例如在退出上下文管理器和执行 atexit 时调用。它会注销当前进程中的端口登记，并释放持有的进程间协调锁。

<a id="smartusbhub.SmartUSBHub.is_connected"></a>

### `is_connected`

```python
is_connected()
```

返回串口当前是否打开。

**返回**：已连接时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.supports_measurement_capture"></a>

### `supports_measurement_capture`

```python
supports_measurement_capture()
```

设备是否声明支持批量采集，与采样率无关。

<a id="smartusbhub.SmartUSBHub.supported_sample_rates"></a>

### `supported_sample_rates`

```python
supported_sample_rates()
```

返回设备声明的测量采样率，单位为 samples/s。

**返回**（tuple）：设备声明的采样率；未声明时返回空元组。

<a id="smartusbhub.SmartUSBHub.get_measurement_sample_rate"></a>

### `get_measurement_sample_rate`

```python
get_measurement_sample_rate()
```

读取测量采样率。

对于仅声明支持 500 samples/s 的设备，不发送查询，直接返回 500。

**返回**（int or None）：采样率，单位为 samples/s；查询失败时返回 None。

**异常**
- `FeatureNotSupportedError`：未声明采样率。

<a id="smartusbhub.SmartUSBHub.set_measurement_sample_rate"></a>

### `set_measurement_sample_rate`

```python
set_measurement_sample_rate(rate)
```

选择设备已声明的测量采样率。

切换前会暂停正在进行的采集，切换后恢复采集。

**参数**
- `rate`（int）：采样率，单位为 samples/s。

**返回**（bool）：采样率切换及采集恢复是否成功。

**异常**
- `ValueError`：采样率不是正的 uint16 值。
- `FeatureNotSupportedError`：设备未声明此采样率。

<a id="smartusbhub.SmartUSBHub.get_measurement_filter"></a>

### `get_measurement_filter`

```python
get_measurement_filter()
```

读取测量滤波模式。

**返回**（int or None）：0 表示瞬时值，1 表示八次转换平均；失败时返回 None。

**异常**
- `FeatureNotSupportedError`：设备未声明滤波功能。

<a id="smartusbhub.SmartUSBHub.set_measurement_filter"></a>

### `set_measurement_filter`

```python
set_measurement_filter(mode)
```

选择测量硬件的瞬时值（0）或内部八次转换平均值（1）。设置仅保存在 RAM 中。在 1024SPS 下，平均窗口约为 7.8ms；输出遵循所选采样率。切换时会停止并重新启动数据流，队列中的样本不会混用不同设置。

<a id="smartusbhub.SmartUSBHub.get_channels"></a>

### `get_channels`

```python
get_channels()
```

返回已连接产品的所有有效通道编号，编号从 1 开始。

优先使用缓存的通道数，其次查询 CMD_GET_MAX_CHANNELS 或使用设备声明。仅旧版固件会回退到产品表。

**返回**：元组，例如 (1, 2, 3, 4)。

**异常**
- `RuntimeError`：无法确定通道数时抛出。

<a id="smartusbhub.SmartUSBHub.get_protocol_info"></a>

### `get_protocol_info`

```python
get_protocol_info()
```

返回协议 API 版本和固件升级建议。

仅对已知的不支持能力声明的旧设备，使用 SDK 的旧版兼容基线。当前设备缺少版本或版本无效时，仍保持未知。

**返回**（dict）：协议版本、来源和升级建议。

<a id="smartusbhub.SmartUSBHub.get_device_info"></a>

### `get_device_info`

```python
get_device_info()
```

读取并缓存集线器的身份信息和配置。

版本、工作模式等关键项目各自最多重试约 10 s，以容忍设备仍处于初始化状态。旧版固件不支持的可选项目按不可用处理。

**返回**：描述集线器的字典，包含 id、address、versions、product、mode 等。

<a id="smartusbhub.SmartUSBHub.set_operate_mode"></a>

### `set_operate_mode`

```python
set_operate_mode(mode)
```

设置设备工作模式。

**参数**
- `mode`：``OPERATE_MODE_NORMAL``（0）或 ``OPERATE_MODE_INTERLOCK``（1）。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_operate_mode"></a>

### `get_operate_mode`

```python
get_operate_mode()
```

查询当前工作模式。

**返回**：0（普通模式）、1（互锁模式）；无响应时返回 None。

<a id="smartusbhub.SmartUSBHub.set_channel_power"></a>

### `set_channel_power`

```python
set_channel_power(*channels, state)
```

设置一个或多个通道的电源状态。

**参数**
- `channels`：要修改的通道编号，从 1 开始。
- `state`：1 表示上电，0 表示断电。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_channel_power_status"></a>

### `get_channel_power_status`

```python
get_channel_power_status(*channels)
```

查询一个或多个通道的电源状态。

**参数**
- `channels`：要查询的通道。

**返回**：查询单个通道时返回其电源状态；查询多个通道时返回字典 {channel: state}；超时时返回 None。

<a id="smartusbhub.SmartUSBHub.get_channel_oc_status"></a>

### `get_channel_oc_status`

```python
get_channel_oc_status()
```

查询各通道的过流状态。

**返回**：字典 {channel: {'active': bool, 'latch': bool}}，超时时返回 None。'active' 表示 OC 引脚或比较器的当前状态；'latch' 表示自上次清除后锁存的过流历史。

**异常**
- `FeatureNotSupportedError`：过流上报不可用时抛出。

<a id="smartusbhub.SmartUSBHub.clear_channel_oc_latch"></a>

### `clear_channel_oc_latch`

```python
clear_channel_oc_latch(*channels)
```

清除一个或多个通道锁存的过流历史。

对于 ``overcurrent.status_api == "alerts"`` 的设备，应改用 ``clear_alert_latch()`` 清除历史，并使用 ``reset_protection_trip()`` 解除保护锁定。

**参数**
- `channels`：要清除的通道；不传参数时清除所有通道。

**返回**：收到应答时为 True，否则为 False。

**异常**
- `FeatureNotSupportedError`：不支持过流状态，或设备使用告警接口时抛出。

<a id="smartusbhub.SmartUSBHub.set_channel_power_interlock"></a>

### `set_channel_power_interlock`

```python
set_channel_power_interlock(channel)
```

选择唯一上电的通道，或关闭所有通道。

此操作不会改变工作模式；请使用 ``set_operate_mode()`` 配置工作模式。

**参数**
- `channel`：要上电的通道；传入 None 可关闭所有通道。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_channel_voltage"></a>

### `get_channel_voltage`

```python
get_channel_voltage(channel)
```

读取单个通道的电压。

**参数**
- `channel`：要查询的通道。

**返回**：电压，单位为 mV；超时时返回 None。

**异常**
- `FeatureNotSupportedError`：型号不支持 ADC 监测时抛出。
- `ValueError`：传入列表或元组而非单个通道时抛出。

<a id="smartusbhub.SmartUSBHub.get_channel_current"></a>

### `get_channel_current`

```python
get_channel_current(channel)
```

读取单个通道的电流。

**参数**
- `channel`：要查询的通道。

**返回**：电流，单位为 mA；超时时返回 None。

**异常**
- `FeatureNotSupportedError`：型号不支持 ADC 监测时抛出。
- `ValueError`：传入列表或元组而非单个通道时抛出。

<a id="smartusbhub.SmartUSBHub.get_channel_power"></a>

### `get_channel_power`

```python
get_channel_power(channel)
```

查询单个通道的功率，单位为 mW；不可用时返回 None。

测量帧提供硬件功率时使用该值。旧设备会依次查询电压和电流，并用 V*I/1000 估算；该估算值并非硬件同步采样的功率值。

<a id="smartusbhub.SmartUSBHub.get_channel_measurements"></a>

### `get_channel_measurements`

```python
get_channel_measurements(*channels)
```

发送请求并等待电压、电流和功率读数。

此方法会查询设备；与 get_cached_measurements() 不同，它不是直接返回缓存值。此方法不会启动数据流。

**参数**
- `channels`：要查询的通道；省略时查询所有通道。

**返回**：字典 {channel: {"voltage", "current", "power", "fresh", "stale", "valid"}}，单位分别为 mV、mA 和 mW。设备提供功率时，``power`` 使用设备值；旧版固件使用依次查询的电压和电流估算；不可用时为 None。未获得有效回复时返回 None。

**异常**
- `FeatureNotSupportedError`：型号不支持 ADC 监测时抛出。

<a id="smartusbhub.SmartUSBHub.get_stream_channel_measurements"></a>

### `get_stream_channel_measurements`

```python
get_stream_channel_measurements(*channels, timeout=None, wait_new_sample=True)
```

从已启用的 V3 数据流读取下一组测量值。

此方法不发送请求；设备必须已通过 `set_channel_measurement_stream` 启用数据流。

批量采集按顺序取出未读样本，仅在队列为空时等待。其他数据流则等待新的采样时间标记（tick）或数据帧。

**参数**
- `channels`：要包含的通道；省略时包含所有通道。
- `timeout`：等待超时，单位为秒；默认为 ``self.com_timeout``。
- `wait_new_sample`：对于非批量采集的数据流，True 表示等待新的采样时间标记（tick）；False 表示接受下一帧，即使其时间标记相同。批量采集始终取出未读队列中的样本，不受此标志影响。

**返回**：各通道读数的字典（包含 sample_tick/sample_period_ms），或 None。

<a id="smartusbhub.SmartUSBHub.discard_measurement_backlog"></a>

### `discard_measurement_backlog`

```python
discard_measurement_backlog()
```

高级 App 集成：恢复时丢弃尚未读取的采集样本。

<a id="smartusbhub.SmartUSBHub.measurement_stream_counter"></a>

### `measurement_stream_counter`

```python
measurement_stream_counter()
```

高级 App 集成：获取样本计数及主机单调时钟时间戳。

两者来自同一个已接收完成的批次。将较新的计数值与较早的应用侧时间戳配对，会使速率估算偏高。空的健康状态报告和采集模式查询应答不计入样本数。

<a id="smartusbhub.SmartUSBHub.set_channel_measurement_stream"></a>

### `set_channel_measurement_stream`

```python
set_channel_measurement_stream(*channels, enabled=True, wait_ack=True)
```

启用或禁用 V3 测量数据流。

数据流帧是设备主动发送的 V3 通知，主机不对其发送应答。

**参数**
- `channels`：要传输测量数据流的通道；省略时包含全部通道。
- `enabled`：True 启用数据流，False 禁用。
- `wait_ack`：为 True 时，等待命令应答后再返回。

**返回**：成功时（或 ``wait_ack`` 为 False 时）返回 True；设备拒绝或超时时返回 False。

<a id="smartusbhub.SmartUSBHub.get_cached_measurements"></a>

### `get_cached_measurements`

```python
get_cached_measurements(*channels)
```

直接返回缓存的测量数据，不发送命令，也不等待。

这不等同于重新查询电压/电流。缓存数据可能早于本次调用；fresh/valid 描述的是最后收到的数据帧，不能据此保证数据距当前时刻不超过某一时限。

返回测量查询或数据流最近更新的缓存，无需先启动数据流。

**参数**
- `channels`：要包含的通道；省略时包含所有通道。

**返回**：各通道读数的字典；尚未收到数据时返回 None。

<a id="smartusbhub.SmartUSBHub.get_latest_measurements"></a>

### `get_latest_measurements`

```python
get_latest_measurements(*channels)
```

已弃用的别名，仅返回缓存数据；请使用 get_cached_measurements()。

<a id="smartusbhub.SmartUSBHub.set_channel_usb3_dataline"></a>

### `set_channel_usb3_dataline`

```python
set_channel_usb3_dataline(*channels, state)
```

设置一个或多个通道的 USB3.0 数据线状态。

**参数**
- `channels`：要更新的通道。
- `state`：1 连接数据线，0 断开。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_channel_usb3_dataline_status"></a>

### `get_channel_usb3_dataline_status`

```python
get_channel_usb3_dataline_status(*channels)
```

查询一个或多个通道的 USB3.0 数据线状态。

**参数**
- `channels`：要查询的通道；省略时返回所有已知通道的结果。

**返回**：所请求通道的 {channel: state} 字典；超时时返回 None。

<a id="smartusbhub.SmartUSBHub.set_channel_usb2_dataline"></a>

### `set_channel_usb2_dataline`

```python
set_channel_usb2_dataline(*channels, state)
```

设置一个或多个通道的 USB2.0 数据线状态。

**参数**
- `channels`：要更新的通道。
- `state`：1 连接数据线，0 断开。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.set_channel_dataline"></a>

### `set_channel_dataline`

```python
set_channel_dataline(*channels, state)
```

已弃用的别名，仅适用于 USB2；请使用 ``set_channel_usb2_dataline()``。

<a id="smartusbhub.SmartUSBHub.get_channel_usb2_dataline_status"></a>

### `get_channel_usb2_dataline_status`

```python
get_channel_usb2_dataline_status(*channels)
```

查询一个或多个通道的 USB2.0 数据线状态。

**参数**
- `channels`：要查询的通道；省略时返回所有已知通道的结果。

**返回**：所请求通道的 {channel: state} 字典；超时时返回 None。

<a id="smartusbhub.SmartUSBHub.get_channel_dataline_status"></a>

### `get_channel_dataline_status`

```python
get_channel_dataline_status(*channels)
```

已弃用的别名，仅适用于 USB2；请使用 ``get_channel_usb2_dataline_status()``。

<a id="smartusbhub.SmartUSBHub.set_button_control"></a>

### `set_button_control`

```python
set_button_control(enable: bool)
```

启用或禁用集线器的实体按键。

**参数**
- `enable`：True 启用按键，False 禁用。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_button_control_status"></a>

### `get_button_control_status`

```python
get_button_control_status()
```

查询集线器的实体按键是否启用。

**返回**：已启用时返回 1，已禁用时返回 0；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.set_default_power_status"></a>

### `set_default_power_status`

```python
set_default_power_status(*channels, enable, status=None)
```

设置一个或多个通道的上电默认电源状态。

**参数**
- `channels`：要配置的通道。
- `enable`：1 表示应用默认电源状态，0 表示不应用默认状态。
- `status`：启用时采用的默认状态：1 为开启，0 为关闭（默认 0）。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_default_power_status"></a>

### `get_default_power_status`

```python
get_default_power_status(*channels)
```

查询一个或多个通道的默认电源配置。

**参数**
- `channels`：要查询的通道。

**返回**：{channel: {"enabled", "value"}} 字典；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.set_default_usb2_dataline_status"></a>

### `set_default_usb2_dataline_status`

```python
set_default_usb2_dataline_status(*channels, enable, status=None)
```

设置 USB2 的上电默认状态，不改变 USB3 的默认状态。

**参数**
- `channels`：要配置的通道。
- `enable`：1 表示应用默认数据线状态，0 表示不应用默认状态。
- `status`：启用时采用的默认状态：1 为连接，0 为断开（默认 0）。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_default_usb2_dataline_status"></a>

### `get_default_usb2_dataline_status`

```python
get_default_usb2_dataline_status(*channels)
```

查询 USB2 的默认配置，不返回 USB3 的默认状态。

**参数**
- `channels`：要查询的通道。

**返回**：{channel: {"enabled", "value"}} 字典；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.set_default_usb3_dataline_status"></a>

### `set_default_usb3_dataline_status`

```python
set_default_usb3_dataline_status(*channels, enable, status=None)
```

持久化保存 USB3 的上电默认状态，不改变当前数据线控制 GPIO 的状态。

enable/status 接受 0/1 或 bool。禁用的配置项恢复为常规默认值（value=1）。恢复状态时，USB2 断开和 VBUS 关闭优先。仅在固件验证持久化保存成功并回传相应值后，才返回 True。

<a id="smartusbhub.SmartUSBHub.get_default_usb3_dataline_status"></a>

### `get_default_usb3_dataline_status`

```python
get_default_usb3_dataline_status(*channels)
```

查询 USB3 的上电默认状态：{channel: {enabled, value}}，失败时返回 None。

<a id="smartusbhub.SmartUSBHub.set_default_dataline_status"></a>

### `set_default_dataline_status`

```python
set_default_dataline_status(*channels, enable, status=None)
```

已弃用的别名，仅适用于 USB2，不配置 USB3 的默认状态。

<a id="smartusbhub.SmartUSBHub.get_default_dataline_status"></a>

### `get_default_dataline_status`

```python
get_default_dataline_status(*channels)
```

已弃用的别名，仅适用于 USB2。

<a id="smartusbhub.SmartUSBHub.set_auto_restore"></a>

### `set_auto_restore`

```python
set_auto_restore(enable: bool)
```

启用或禁用断电状态自动恢复功能。

**参数**
- `enable`：True 启用断电状态自动恢复，False 禁用。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_auto_restore_status"></a>

### `get_auto_restore_status`

```python
get_auto_restore_status()
```

查询断电状态自动恢复是否启用。

**返回**：已启用时返回 1，已禁用时返回 0；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.set_upstream_host"></a>

### `set_upstream_host`

```python
set_upstream_host(host: int)
```

选择 Host1 或 Host2。当前固件会将选择结果持久化保存到 Flash。

要求设备声明具备上行主机切换能力。不支持的设备会引发 FeatureNotSupportedError。设备拒绝或超时时返回 False。

**参数**
- `host`（int）：上行主机编号，1 或 2。

**返回**（bool）：是否收到匹配的确认应答。

**异常**
- `ValueError`：主机编号无效。
- `FeatureNotSupportedError`：不支持主机切换。

<a id="smartusbhub.SmartUSBHub.get_upstream_host"></a>

### `get_upstream_host`

```python
get_upstream_host()
```

返回 0/1/2；设备拒绝或通信失败时返回 None。

不支持的产品/固件会引发 FeatureNotSupportedError。

**返回**（int or None）：固件返回的主机值 0、1 或 2，或 None。

**异常**
- `FeatureNotSupportedError`：不支持主机切换。

<a id="smartusbhub.SmartUSBHub.set_device_address"></a>

### `set_device_address`

```python
set_device_address(address: int)
```

设置 16 位设备地址。

**参数**
- `address`：地址范围为 0x0000 - 0xFFFF。

**返回**：收到应答时为 True，否则为 False。

**异常**
- `ValueError`：地址超出范围。

<a id="smartusbhub.SmartUSBHub.get_device_address"></a>

### `get_device_address`

```python
get_device_address()
```

查询当前设备地址。

**返回**：16 位设备地址；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.reset_hub"></a>

### `reset_hub`

```python
reset_hub()
```

仅复位 USB 数据集线器；已连接的 USB 设备会断开。

不复位 MCU/CMD，也不重置端口电源策略。集线器芯片的易失性配置恢复为复位/OTP 默认值。要求固件声明 device.reset_hub=true；绝不会对旧固件进行破坏性探测。

<a id="smartusbhub.SmartUSBHub.reboot_mcu"></a>

### `reboot_mcu`

```python
reboot_mcu()
```

重启设备 MCU。

MCU 在发送应答后约 100 ms 重启，因此连接会断开，之后通常需要重新连接设备。

**返回**：重启命令收到应答时返回 True，否则返回 False。

<a id="smartusbhub.SmartUSBHub.factory_reset"></a>

### `factory_reset`

```python
factory_reset()
```

将设备恢复为出厂设置。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.identify_device"></a>

### `identify_device`

```python
identify_device()
```

使设备状态 LED 快速闪烁数秒。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.set_device_alias"></a>

### `set_device_alias`

```python
set_device_alias(alias)
```

将自定义设备别名保存到设备中。

空别名会清除自定义别名。别名采用 UTF-8 编码，最长 15 字节。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_device_alias"></a>

### `get_device_alias`

```python
get_device_alias()
```

查询自定义设备别名。

**返回**：返回别名字符串；未设置或未收到应答时返回 ""。

<a id="smartusbhub.SmartUSBHub.set_channel_name"></a>

### `set_channel_name`

```python
set_channel_name(channel, name)
```

将自定义通道显示名称保存到设备中。

空名称会清除自定义名称，使设备恢复使用 CHn。名称以 UTF-8 编码保存，最长 15 字节。

**返回**：收到应答时为 True，否则为 False。

<a id="smartusbhub.SmartUSBHub.get_channel_name"></a>

### `get_channel_name`

```python
get_channel_name(channel)
```

从设备查询通道显示名称。

**返回**：返回已保存的名称；未设置或未收到应答时返回默认名称 CHn。

<a id="smartusbhub.SmartUSBHub.get_channel_names"></a>

### `get_channel_names`

```python
get_channel_names(*channels)
```

查询一个或多个通道的显示名称。

<a id="smartusbhub.SmartUSBHub.authenticate_device"></a>

### `authenticate_device`

```python
authenticate_device(trusted_issuers, nonce=None, timeout=2.0)
```

可选地验证设备专属证书，并执行一次新的 P-256 挑战验证。

构造函数不会自动调用此方法，这是有意的设计。开放协议、Python 自动化和用户自行开发的软件无需采用任何认证策略即可使用；官方应用可以在连接后调用此方法，并执行各自的认证策略。

``trusted_issuers`` 将证书中的整数签发者 ID 映射到 P-256 公钥。值可以是 cryptography 公钥对象、PEM/DER 字节串、PEM 字符串，或压缩/未压缩的 SEC1 点。

``timeout`` 控制证书交换的超时时间，同时作为调用者为挑战交换请求的最短超时时间。由于当前 HBL 固件在 MCU 上以软件执行 P-256 签名，挑战交换的超时时间始终至少为 ``AUTH_CHALLENGE_TIMEOUT_MIN`` 秒。

**返回**：包含已通过认证的证书元数据的字典。

**异常**
- `AuthenticationNotSupportedError`：固件未实现认证命令。
- `DeviceAuthenticationCommunicationError`：交换超时，或数据格式不正确。
- `AuthenticationTrustError`：提供的信任库中不存在该签发者。
- `DeviceAuthenticationRejectedError`：证书或证明无效。
- `AuthenticationDependencyError`：请先安装 ``smartusbhub[auth]``。

<a id="smartusbhub.SmartUSBHub.get_firmware_version"></a>

### `get_firmware_version`

```python
get_firmware_version()
```

查询固件版本。

**返回**：固件版本；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.get_firmware_version_major"></a>

### `get_firmware_version_major`

```python
get_firmware_version_major()
```

返回缓存的固件主版本号，必要时查询设备。

旧固件仅应答次版本号字节；为保持向后兼容，这些设备的主版本号按 1 处理。

<a id="smartusbhub.SmartUSBHub.get_firmware_version_string"></a>

### `get_firmware_version_string`

```python
get_firmware_version_string()
```

将缓存的固件版本格式化为显示文本。

返回不补零的 ``V<major>.<minor>``；USB3 首个公开版本返回 ``V1.0.0``。无法获取版本时返回 "Unknown"。

<a id="smartusbhub.SmartUSBHub.get_hardware_version"></a>

### `get_hardware_version`

```python
get_hardware_version()
```

查询硬件版本。

**返回**：硬件版本；无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.get_product_type"></a>

### `get_product_type`

```python
get_product_type()
```

查询产品类型 ID。

可选命令：旧固件不应答，此时返回 None（仅记录调试级别日志，不作为错误）。

**返回**：产品类型 ID；不支持或无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.get_product_name"></a>

### `get_product_name`

```python
get_product_name()
```

获取已连接设备的产品名称。

**返回**：产品名称（例如 "HBP_USB2_4CH"）、"Unknown(...)" 字符串；无法获取产品类型时返回 None。

<a id="smartusbhub.SmartUSBHub.get_max_channels"></a>

### `get_max_channels`

```python
get_max_channels()
```

查询最大通道数。

可选命令：旧固件不应答，此时返回 None（仅记录调试级别日志，不作为错误）。

**返回**：最大通道数；不支持或无应答时返回 None。

<a id="smartusbhub.SmartUSBHub.get_serial_no"></a>

### `get_serial_no`

```python
get_serial_no()
```

查询设备序列号。

**返回**：序列号字符串（无法获取时为 "N/A"）；无应答时返回 None。

## 异常

<a id="smartusbhub.LegacyAPIWarning"></a>

### `LegacyAPIWarning`

针对仍受支持、此前已发布的 API，向调用者明确提示迁移。

<a id="smartusbhub.FirmwareUpdateRecommendedWarning"></a>

### `FirmwareUpdateRecommendedWarning`

非阻断性提示：仍可通过兼容 API 使用旧固件。

<a id="smartusbhub.SmartUSBHubError"></a>

### `SmartUSBHubError`

本库引发的所有错误的基类。

捕获此异常即可处理任意 SmartUSBHub 专属故障，无需区分具体子类型。

<a id="smartusbhub.PortBusyError"></a>

### `PortBusyError`

串口已被另一个实例或进程使用时引发。

此异常同时继承 ``ValueError``，以兼容此前捕获端口占用所引发 ``ValueError`` 的调用代码。

<a id="smartusbhub.PortPermissionError"></a>

### `PortPermissionError`

操作系统拒绝访问串口时引发。

与 `PortBusyError` 分开定义，使命令行应用能够给出可执行的权限处理提示，避免将权限问题误报为端口被其他进程占用。

<a id="smartusbhub.DeviceConnectionError"></a>

### `DeviceConnectionError`

建立连接时设备未应答所引发的异常。

通常表示该端口连接的不是 SmartUSBHub，或设备无响应。

<a id="smartusbhub.FeatureNotSupportedError"></a>

### `FeatureNotSupportedError`

已连接产品型号不支持请求的功能时引发。

此异常同时继承 ``ValueError``，以保持向后兼容。

<a id="smartusbhub.DeviceAuthenticationError"></a>

### `DeviceAuthenticationError`

可选的正品设备认证过程中各类失败异常的基类。

<a id="smartusbhub.DeviceAuthenticationCommunicationError"></a>

### `DeviceAuthenticationCommunicationError`

认证交换超时，或返回的应答格式不正确。

<a id="smartusbhub.DeviceAuthenticationRejectedError"></a>

### `DeviceAuthenticationRejectedError`

证书或挑战证明无法确认设备为正品。

<a id="smartusbhub.AuthenticationNotSupportedError"></a>

### `AuthenticationNotSupportedError`

所连接设备的固件未实现正品设备认证。

<a id="smartusbhub.AuthenticationTrustError"></a>

### `AuthenticationTrustError`

调用者未提供可用的受信任签发者公钥。

<a id="smartusbhub.AuthenticationDependencyError"></a>

### `AuthenticationDependencyError`

缺少验证所需的可选 ``cryptography`` 包。

## 辅助函数

<a id="smartusbhub.load_trusted_issuers"></a>

### `load_trusted_issuers`

```python
load_trusted_issuers(path)
```

加载由 ``auth_keygen.py`` 生成、供官方应用使用的公开签发者映射。

该 JSON 文件属于公开资料，并非秘密。其结构为 ``{"format_version": 1, "issuers": {"1": {"public_key_pem": "..."}}}``。返回的映射可直接传给 `authenticate_device`。

<a id="smartusbhub.synchronized"></a>

### `synchronized`

```python
synchronized(method)
```

当 ``ENABLE_SYNC_LOCK`` 为 True 时，在整个方法执行期间持有 ``self.lock``。

<a id="smartusbhub.decode_usb3_capture_batch"></a>

### `decode_usb3_capture_batch`

```python
decode_usb3_capture_batch(payload)
```

解码 0x28 测量数据流（STREAM）批次，不用于解码单字节命令应答。

时间戳界定主机请求获取测量硬件快照的时间区间：``refresh_us`` 是请求时刻，``read_us`` 是读取完成时刻，不是 ADC 转换时刻或 USB 发送时刻。数值使用 mV/mA。所有计数器均在 2**32 处回绕。转换计数用于标识测量硬件的进展，与 MCU 序列计数相互独立。
