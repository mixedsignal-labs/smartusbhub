# SmartUSBHub Python 库

[English](./README.md)

**官方网站**：[www.mixedsignallab.com](https://www.mixedsignallab.com)

**文档导航**：[快速上手](#快速上手) · [通信协议](./docs/protocol_cn.md) · [产品文档](./docs/README_cn.md) · [示例说明](./examples/README_cn.md)

**本 SDK 说明适用于**：SDK 支持的 SmartUSBHub 型号。下方产品说明书链接目前覆盖 4CH 与 7CH USB 2.0 产品。

**本文档更新日期**：2026年7月24日

## 简介

SmartUSBHub 不同型号的端口数量、供电能力、测量能力和专用功能可能不同。使用前请根据产品型号选择对应文档。

- 如果想直接用软件控制，请使用随 SmartUSBHub 发行包提供的配套控制软件。

- 这是一个用于在脚本、测试系统和自动化流程中控制 SmartUSBHub 设备的 Python 库。

### 已发布的产品说明书

| 产品名称 | 型号 / 订购代码 | 通道数量 | USB 规格 | 使用指南 | 技术规格书 |
| --- | --- | ---: | --- | --- | --- |
| SmartUSBHub Pro 4CH USB2.0 | `HBP_USB2_4CH`、`HBP_USB2_4CH_PSU` | 4 | USB 2.0 High-Speed | [使用指南](./docs/products/usb2_4p/user_guide_cn.md) | [技术规格书](./docs/products/usb2_4p/datasheet_cn.md) |
| SmartUSBHub Pro 7CH USB2.0 | `HBP_USB2_7CH`、`HBP_USB2_7CH_ADV` | 7 | USB 2.0 High-Speed | [使用指南](./docs/products/usb2_7p/user_guide_cn.md) | [技术规格书](./docs/products/usb2_7p/datasheet_cn.md) |

如使用其它受支持的订购代码，请查阅随该设备提供的型号专用资料。

### 通用软件文档

- [快速上手](#快速上手)
- [通信协议与指令集](./docs/protocol_cn.md)
- [Python 示例说明](./examples/README_cn.md)
- [完整产品文档索引](./docs/README_cn.md)



## 产品概述

SmartUSBHub 是一系列可编程 USB 集线器，支持按通道控制电源；部分型号支持数据线控制，部分型号支持电压/电流检测。该系列产品适用于开发、自动化测试和设备管理。

1. **独立电源和数据控制，模拟热插拔：** SmartUSBHub 的每个下游端口均支持独立控制 **电源（VBUS）** 和 **USB 2.0 数据线（D+ / D−）**。工程师无需手动插拔，即可通过指令远程控制 USB 设备的连接与断开，实现自动化测试或远程重启设备，显著提升调试和测试效率。

2. **电压/电流监测：** 支持电压/电流检测的型号可实时采集各通道的电压和电流。用户可随时监控被测设备的供电状态，进行功耗分析与状态监测；测试中若出现异常压降或电流过载，也能及时发现并定位问题。

3. **开源软件生态，易于集成：** SmartUSBHub 提供开放的通信协议、控制软件和 Python 控制库。Windows 10/11、macOS 和常用 Linux 发行版无需专用驱动；Windows 7 需要安装随产品提供的 CDC 驱动。标准串口接口便于把端口控制集成到自动化测试平台、Python 脚本或其他工具中。

4. **多模式端口管理**

  - 支持 **普通模式**（多通道同时控制）与 **互锁模式**（仅允许操作一个通道）

  - 每端口可设置 **上电默认状态** 与 **断电状态记忆**

5. **扩展性强**

  - 支持集中控制多个SmartUSBHub的拓扑结构

  - 每个设备支持地址配置，适用于级联系统



## 典型工程用途

- 硬件研发调试与异常恢复。
- 自动化回归测试与兼容性测试。
- 固件刷写与产线验证。
- 远程设备管理与无人值守测试工装。
- 在支持测量的型号上观察各通道电压和电流。



## 连接说明

> [!WARNING]
>
> 接入外部电源前，先确认准确型号并查阅对应的[产品指南](./docs/README_cn.md)。4CH 的 AUX POWER 仅可接入稳压 5 V DC（绝对最大值 5.5 V）；7CH 的 DC IN 工作范围为 9–20 V。即使插头尺寸相同，也不得混用电源。

> [!NOTE]
>
> 1. 使用 USB 数据线连接设备的 **DATA 上行口**与 USB 主机。该连接承载下游设备的数据，操作系统会识别到通用 USB Hub。
> 2. 使用 USB 数据线连接设备的 **CMD 控制口**与控制计算机。系统会显示：
>    - Windows：`COMx`
>    - Linux：`/dev/ttyACMx`
>    - macOS：`/dev/cu.usbmodemx`
>
> 当同一台主机既要控制 SmartUSBHub，又要与下游 USB 设备通信时，DATA 与 CMD 都必须连接。



## 性能

> 实测环境：HBP_USB2_4CH，USB CDC（免驱动虚拟串口，115200），Python SDK 默认参数，macOS。

- **控制延迟**：单条通道控制命令（set + 读回）往返约 **2.5 ms**。
- **控制频率 / 吞吐**：持续约 **200 命令/秒**（4 通道电源 + 数据线 set/读回混合负载）；单条简单命令可达 **~400 命令/秒**。
- **多通道读**：一次性读取全部通道的电压/电流/状态约 **10～13 ms** 返回完整快照，无固定等待延时。
- **可靠性**：连续 **100 万次**操作压力测试 **100% 成功（0 失败）**。
## 快速上手

任选一种使用方式。

### 方法1：直接安装发布包

```shell
pip install smartusbhub
```

### 方法2：引用当前源码库

```shell
cd smartusbhub
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

库目录结构如下：

```shell
.
├── README.md					# 文档
├── docs						# 产品指南与通信协议
├── examples					# 例程
├── requirements.txt	# 安装依赖
└── smartusbhub.py 		# 功能源码
```

## 运行例程

`smartusbhub` 库包含多个示例程序，存放在 `examples` 目录中：

- [device_report.py](./examples/device_report.py)：读取设备身份信息和运行状态
- [power_control_example.py](./examples/power_control_example.py)：控制通道电源，包括互锁模式
- [setting_example.py](./examples/setting_example.py)：读取设备信息，配置默认状态、地址、工作模式和按钮
- [cycle_all_channels.py](./examples/cycle_all_channels.py)：依次对每个可控通道进行上下电循环
- [set_default_power_dataline_on.py](./examples/set_default_power_dataline_on.py)：配置上电默认状态
- [dataline_control_example.py](./examples/dataline_control_example.py)：保持供电的同时断开/恢复某通道 USB 2.0 数据线
- [power_monitor.py](./examples/power_monitor.py)：在支持测量的型号上读取电压和电流
- [oscilloscope.py](./examples/oscilloscope.py)：使用请求/响应测量的 GUI 示波器
- [oscilloscope_stream.py](./examples/oscilloscope_stream.py)：使用流式测量的 GUI 示波器
- [user_callback_example.py](./examples/user_callback_example.py)：注册用户回调
- [multi_device_channel_control.py](./examples/multi_device_channel_control.py)：发现并控制多台设备

![SmartUSBHub 示波器实时显示各通道电压和电流](./assets/oscilloscope.png)

<center>图：示波器示例程序</center>



在包根目录下运行示例程序，例如：

  ```shell
  python examples/power_control_example.py
  python examples/oscilloscope.py
  ```


### 集成到项目

通过导入 `smartusbhub` 库即可集成到你的项目之中。

1. 导入 `smartusbhub` 库到你的工程：

   ```python
   from smartusbhub import SmartUSBHub
   ```

2. 初始化 `SmartUSBHub` 实例：

   - 通过自动扫描连接设备：

     ```python
     hub = SmartUSBHub.scan_and_connect()
     ```

   - 通过指定串口号连接设备：

     ```python
     hub = SmartUSBHub("串口路径")
     # 例子：
     hub = SmartUSBHub("/dev/cu.usbmodem132301")
     ```




## **用户接口**

### 设备连接

#### `scan_and_connect(exclude_ports=None, device_address=None)`

- **描述**：扫描匹配的 USB CDC 串口并连接第一台可用设备。`exclude_ports` 用于跳过指定串口。`device_address` 可按已配置的 16 位地址筛选，但设备地址默认为零，配置前不具备唯一性。
- **返回值**:
  
  - `SmartUSBHub` 或 `None`：连接成功的实例；没有可用设备时返回 `None`。
  
- **示例**:
  
  ```python
  hub = SmartUSBHub.scan_and_connect()
  ```

#### `scan_available_ports()`

- **描述**：返回 USB VID/PID 与 SmartUSBHub 匹配的串口路径。
- **返回值**：`list[str]`。

```python
ports = SmartUSBHub.scan_available_ports()
```

#### `auto_connect(exclude_ports=None, feature_filter=None)`

- **描述**：依次尝试候选串口，自动跳过被占用或连接失败的端口。`feature_filter` 可指定 `adc`、`usb2_data_switch`、`usb3_data_switch` 或 `ilim_switch`。
- **返回值**：`SmartUSBHub` 或 `None`。

```python
hub = SmartUSBHub.auto_connect(feature_filter="adc")
```

#### `scan_and_connect_by_address(device_address)`

- **描述**：连接第一台报告指定 16 位地址的设备。
- **返回值**：`SmartUSBHub` 或 `None`。
- **注意**：设备地址默认为零。除非已为每台设备配置唯一地址，否则应优先按已知串口连接。

#### `SmartUSBHub(port)`

- **描述**：打开指定的 SmartUSBHub 串口。

```python
hub = SmartUSBHub("/dev/cu.usbmodem132301")
```



### 断开设备连接

#### `disconnect()`

- **描述**：停止接收线程、关闭串口并释放进程锁。可以安全地重复调用。

- **示例:**

  ```python
  hub.disconnect()
  ```

#### `is_connected()`

- **描述**：返回串口当前是否处于打开状态。
- **返回值**：`bool`。

#### `close()`

- **描述**：`disconnect()` 的别名。
- **返回值**：`None`。

#### `register_disconnect_callback(callback)`

- **描述**：注册设备意外断开时调用的无参数函数。
- **返回值**：`None`。

```python
hub.register_disconnect_callback(lambda: print("SmartUSBHub 已断开"))
```

`SmartUSBHub` 也支持上下文管理器，离开代码块时会自动断开：

```python
with SmartUSBHub("/dev/cu.usbmodem132301") as hub:
    hub.set_channel_power(1, state=1)
```


### 获取通道列表

#### `get_channels()`

- **描述**: 返回当前连接产品的所有有效通道编号，通道编号从 1 开始。

- **返回值**:

  - tuple: 当前设备可用通道，例如 `(1, 2, 3, 4)` 或 `(1, 2, 3, 4, 5, 6, 7)`。

- **示例**:

  ```python
  channels = hub.get_channels()
  hub.set_channel_power(*channels, state=1)
  ```



### 控制通道电源开关

#### `set_channel_power(*channels, state)`

- **描述**: 设置指定通道的电源状态。
- **参数**:
  - `*channels` (int): 要控制的通道。
  - `state` (int): `1` 开启电源，`0` 关闭电源。

- **返回值**:

  - bool: 如果命令设置成功返回 `True`，否则返回 `False`。

- **示例**:

  ```python
  hub.set_channel_power(1, 2, state=1)
  ```



### 获取通道电源状态

#### `get_channel_power_status(*channels)`

- **描述**: 查询指定通道的电源状态。
- **参数**:
  
  - `*channels` (int): 要查询的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。
- **返回值**:
  - `dict` 或 `int` 或 `None`: 如果查询多个通道，返回包含通道状态的字典；如果查询单个通道，返回该通道的状态；若超时则返回 `None`。
- **示例**:
  ```python
  status = hub.get_channel_power_status(1, 2)
  ```



### 控制通道电源互锁

#### `set_channel_power_interlock(channel)`

- **描述**：在互锁模式下选择唯一供电通道，或关闭所有通道。关闭通道电源时，该通道的数据线也会随之断开。
- **注意**：互锁模式下，普通电源控制指令 `set_channel_power()` 无效，必须使用 `set_channel_power_interlock()` 选择供电通道。互锁指令本身控制电源；如需控制所选通道的 USB 2.0 数据线，请使用 `set_channel_usb2_dataline()`。
- **参数**:
  
  - `channel` (`int` 或 `None`): 要设置的通道。如果为 `None`，则关闭所有通道。
  
- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:
  
  ```python
  hub.set_channel_power_interlock(1)
  ```



### 控制通道USB数据开关

#### `set_channel_usb2_dataline(*channels, state)`

- **描述**: 设置指定通道的USB数据开关状态。

- **参数**:
  - `*channels` (int): 要更新的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。
  - `state`（int）：`1` 表示连通 D+ / D−，`0` 表示断开 D+ / D−。

- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。

- **示例**:
  
  连通 通道1 的数据信号
  
  ```python
  hub.set_channel_usb2_dataline(1,state=1)
  ```
  
  
### 获取通道USB数据开关状态
#### `get_channel_usb2_dataline_status(*channels)`
- **描述**: 查询指定通道的USB数据开关状态。

- **参数**:
  - `*channels` (int): 要查询的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。
  
- **返回值**:
  - `dict` 或 `None`: 包含通道状态的字典，若超时则返回 `None`。
  
- **示例**:
  
  获取通道 2 的 USB 2.0 数据线连接状态
  
  ```python
  status = hub.get_channel_usb2_dataline_status(1, 2)
  ```

#### `set_channel_dataline(*channels, state)` 与 `get_channel_dataline_status(*channels)`

这两个名称用于兼容旧版 API，分别调用 `set_channel_usb2_dataline()` 和
`get_channel_usb2_dataline_status()`。新代码应使用名称中带 `usb2` 的明确写法。



### 获取通道电压

> **注意**: 此API仅适用于 **带有电压、电流检测的** 型号。

#### `get_channel_voltage(channel)`

- **描述**: 查询单个通道的电压。
- **参数**:
  - `channel` (int): 要查询的通道。

- **返回值**:
  - `int` 或 `None`: 通道的电压值(mV)，若超时则返回 `None`。
- **示例**:
  
  获取通道 1 的电压值
  
  ```python
  voltage = hub.get_channel_voltage(1)
  ```
  



### 获取通道电流

> **注意**: 此API仅适用于 **带有电压、电流检测的** 型号。

#### `get_channel_current(channel)`

- **描述**: 查询单个通道的电流。
- **参数**:
  - `channel` (int): 要查询的通道。

- **返回值**:
  
  - `int` 或 `None`: 通道的电流值(mA)，若超时则返回 `None`。
- **示例**:
  
  获取通道 1 的电流值
  
  ```python
  current = hub.get_channel_current(1)
  ```


### 批量获取通道电压/电流

> **注意**: 此 API 仅适用于 **带有电压、电流检测的** 型号。

#### `get_channel_measurements(*channels)`

- **描述**: 一次请求读取一个或多个通道的电压、电流测量值。未指定通道时，读取当前产品的所有有效通道。

- **参数**:
  - `*channels` (int): 要查询的通道，可变参数形式，可用通道可通过 `hub.get_channels()` 获取。

- **返回值**:
  - `dict` 或 `None`: 返回 `{通道号: {"voltage": mV, "current": mA, "fresh": bool, "stale": bool, "valid": bool}}`，若超时或无有效数据则返回 `None`。

- **示例**:

  ```python
  measurements = hub.get_channel_measurements(1, 2)
  all_measurements = hub.get_channel_measurements(*hub.get_channels())
  ```


### 连续测量数据输出

> **注意**: 此 API 仅适用于支持连续测量数据输出的型号。

#### `set_channel_measurement_stream(*channels, enabled=True, wait_ack=True)`

- **描述**: 开启或关闭指定通道的连续测量数据输出。未指定通道时，默认作用于当前产品的所有有效通道。

- **参数**:
  - `*channels` (int): 要输出测量数据的通道。
  - `enabled` (bool): `True` 开启，`False` 关闭。
  - `wait_ack` (bool): 是否等待设备应答。

- **返回值**:
  - `bool`: 成功返回 `True`，超时返回 `False`。

- **示例**:

  ```python
  hub.set_channel_measurement_stream(*hub.get_channels(), enabled=True)
  ```

#### `get_stream_channel_measurements(*channels, timeout=None, wait_new_sample=True)`

- **描述**: 等待下一帧连续测量数据并返回指定通道的测量值。调用前需要先开启连续测量数据输出。

- **参数**:
  - `*channels` (int): 要读取的通道。
  - `timeout` (float): 等待超时时间，单位为秒；不传则使用默认通信超时。
  - `wait_new_sample` (bool): `True` 时等待新的采样点，`False` 时接受下一帧数据。

- **返回值**:
  - `dict` 或 `None`: 返回包含 `voltage`、`current`、`sample_tick`、`sample_period_ms` 等字段的字典，超时返回 `None`。

- **示例**:

  ```python
  data = hub.get_stream_channel_measurements(1, 2, timeout=1.0)
  ```

#### `get_latest_measurements(*channels)`

- **描述**: 直接读取后台接收线程缓存的最新测量值，不阻塞等待新数据。通常与连续测量数据输出配合使用。

- **参数**:
  - `*channels` (int): 要读取的通道。

- **返回值**:
  - `dict` 或 `None`: 返回最新缓存测量值；如果还没有收到测量数据，则返回 `None`。

- **示例**:

  ```python
  latest = hub.get_latest_measurements(*hub.get_channels())
  ```


### 获取过流状态

> **注意**：HBP_USB2_7CH 与 HBP_USB2_7CH_ADV 都支持各端口过流状态。其他型号是否支持取决于硬件和固件。

#### `get_channel_oc_status()`

- **描述**: 查询每个通道的过流实时状态和锁存状态。

- **返回值**:
  - `dict` 或 `None`: 返回 `{通道号: {"active": bool, "latch": bool}}`。`active` 表示当前过流状态，`latch` 表示锁存过流事件。若超时则返回 `None`。

- **示例**:

  ```python
  oc_status = hub.get_channel_oc_status()
  ```

#### `clear_channel_oc_latch(*channels)`

- **描述**: 清除指定通道的过流锁存状态。未指定通道时，清除所有通道的锁存状态。

- **参数**:
  - `*channels` (int): 要清除锁存状态的通道。

- **返回值**:
  - `bool`: 成功返回 `True`，超时返回 `False`。

- **示例**:

  ```python
  hub.clear_channel_oc_latch(1, 2)
  hub.clear_channel_oc_latch()
  ```



### 设置通道电源的上电默认状态

#### `set_default_power_status(*channels, enable, status=None)`

- **描述**: 设置指定通道的上电默认电源状态。

- **参数**:

  - `*channels` (int): 要设置的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。
  - `enable`（int 或 bool）：`1`/`True` 启用默认状态，`0`/`False` 禁用。
  - `status`（int 或 bool，可选）：`1`/`True` 默认打开电源，`0`/`False` 默认关闭；省略时为关闭。

- **示例**:

  通道1、2、3、4上电默认打开

  ```python
  hub.set_default_power_status(1, 2, 3, 4, enable=1, status=1)
  ```

  通道1、2、3、4上电不使用默认值

  ```python
  hub.set_default_power_status(1, 2, 3, 4, enable=0)
  ```



### 获取通道电源的上电默认状态

#### `get_default_power_status(*channels)`

- **描述**: 查询一个或多个通道电源的默认上电状态

- **参数**:

  - `*channels` (int): 要查询的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。

- **返回值**:

  - `dict` 或 `None`:  {通道号: {"enabled": 是否启用, "value": 状态}}，其中 enabled 为 0（禁用）或 1（启用），value 为 0（默认关闭）或 1（默认开启）。
  - 若超时则返回 `None`。

- **示例**:

  获取通道1、2、3、4的电源上电默认状态

  ```python
  hub.get_default_power_status(1,2,3,4)
  ```

  返回：

  ```python
  {1: {'enabled': 0, 'value': 0}, 2: {'enabled': 0, 'value': 0}, 3: {'enabled': 0, 'value': 0}, 4: {'enabled': 0, 'value': 0}}
  ```



### 设置通道数据连接的上电默认状态

#### `set_default_dataline_status(*channels, enable, status=None)`

- **描述**: 设置指定通道的上电默认数据连接状态。

- **参数**:

  - `*channels` (int): 要设置的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。
  - `enable`（int 或 bool）：`1`/`True` 启用默认状态，`0`/`False` 禁用。
  - `status`（int 或 bool，可选）：`1`/`True` 默认连接数据，`0`/`False` 默认断开；省略时为断开。

- **返回值**:

  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:

  通道1、2、3、4上电默认数据连接

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=1,status=1)
  ```




### 获取通道数据连接的上电默认状态

#### `get_default_dataline_status(*channels)`

- **描述**: 查询一个或多个通道的上电默认数据连接状态。

- **参数**:

  - `*channels` (int): 要查询的通道，可变参数形式，可用通道可通过 hub.get_channels() 获取。

- **返回值**:

  - `dict` 或 `None`:  {通道号: {"enabled": 是否启用, "value": 状态}}，其中 enabled 为 0（禁用）或 1（启用），value 为 0（默认断开）或 1（默认连接）。
  - 若超时则返回 `None`。

- **示例**:

  获取通道1、2、3、4的数据连接的上电默认状态

  ```python
  hub.get_default_dataline_status(1,2,3,4)
  ```

  返回：

  ```python
  {1: {'enabled': 0, 'value': 1}, 2: {'enabled': 0, 'value': 1}, 3: {'enabled': 0, 'value': 1}, 4: {'enabled': 0, 'value': 1}}
  ```



### 设置断电状态记忆

#### `set_auto_restore(enable)`

- **描述**: 启用或禁用断电状态恢复。

- **参数**:

  - `enable` (bool): `True` 启用，`False` 禁用。

- **返回值**:

  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。

- **示例**:

  启用断电状态恢复

  ```python
  hub.set_auto_restore(True)
  ```



### 获取断电状态记忆

#### `get_auto_restore_status()`

- **描述**: 查询是否启用断电状态恢复

- **返回值**:

  - `int` 或 `None`：`1` 表示启用，`0` 表示禁用，设备无响应时返回 `None`。

- **示例**:

  查询断电状态恢复

  ```python
  status = hub.get_auto_restore_status()
  ```



### 设置按钮控制

#### `set_button_control(enable)`

- **描述**: 启用或禁用集线器的物理按钮（如有）。

- **参数**:
  
  - `enable` (bool): `True` 启用按钮，`False` 禁用按钮。
  
- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:

  设置按钮为启用

  ```python
  hub.set_button_control(True)
  ```



### 获取按钮控制状态

#### `get_button_control_status()`

- **描述**: 查询集线器的物理按钮是否启用（如有）。
- **返回值**:
  
  - `int` 或 `None`: `1` 表示启用，`0` 表示禁用，若无响应则返回 `None`。
- **示例**:
  
  查询按钮是否启用
  
  ```python
  status = hub.get_button_control_status()
  ```



### 设置设备地址

#### `set_device_address(address)`

- **描述**: 设备地址用于在多台集线器连接的场景中，标识和区分各个集线器。

- **参数**:

  - `address`（int）：用户自定义地址，范围为 `0x0000`～`0xFFFF`。

- **返回值**:

  - `bool`：设备确认修改时返回 `True`，否则返回 `False`。

- **提示**：

  - 创建 SmartUSBHub 实例时会自动获取连接设备的地址。多设备按地址选择前，必须先为每台设备配置唯一地址。

- **示例**:

  设置设备地址为`0x0001`

  ```python
  hub.set_device_address(0x0001)
  ```



### 获取设备地址

#### `get_device_address()`

- **描述**: 获取设备的地址。

- **返回值**:

  - `int` 或 `None`: 设备地址，若无响应则返回 `None`。

- **示例**:

  查询设备地址

  ```python
  device_address = hub.get_device_address()
  ```



### 设置设备的操作模式

#### `set_operate_mode(mode)`

- **描述**: 设置设备的操作模式。
- **参数**:
  
  - mode (int): 操作模式（`0` 为普通模式，`1` 为互锁模式）。
  
- **返回值**:
  - bool: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **注意:**
  - 互锁模式下，电源只能通过 `set_channel_power_interlock()` 控制；普通电源指令无效。通道断电时数据线会同步断开。

- **示例**:

  设置设备为普通模式

  ```python
  hub.set_operate_mode(0)
  ```




### 获取设备的操作模式

#### `get_operate_mode()`

- **描述**: 查询设备的当前操作模式。

- **返回值**:
  - `int` 或 `None`: 当前操作模式，若无响应则返回 `None`。
  
- **示例**:
  
  查询设备操作模式
  
  ```python
  mode = hub.get_operate_mode()
  ```



### 获取设备信息

#### `get_device_info()`

- **描述**: 获取集线器的 ID、硬件版本、固件版本、操作模式和按钮控制状态。
- **返回值**:
  - `dict`: 包含设备信息的字典。
- **示例**:
  ```python
  info = hub.get_device_info()
  print(info)
  ```


### 获取产品类型

#### `get_product_type()`

- **描述**: 查询当前连接设备的产品类型 ID。

- **返回值**:
  - `int` 或 `None`: 产品类型 ID，若无响应则返回 `None`。

- **示例**:

  ```python
  product_type = hub.get_product_type()
  ```

#### `get_product_info(product_type_id)`

- **描述**：按产品类型 ID 查询静态能力记录。
- **返回值**：`dict`；类型 ID 未知时返回 `None`。

```python
product_info = SmartUSBHub.get_product_info(product_type)
```


### 获取产品名称

#### `get_product_name()`

- **描述**: 查询当前连接设备的产品名称，例如 `HBP_USB2_4CH` 或 `HBP_USB2_7CH_ADV`。

- **返回值**:
  - `str` 或 `None`: 产品名称，若无响应则返回 `None`。

- **示例**:

  ```python
  product_name = hub.get_product_name()
  ```


### 获取最大通道数

#### `get_max_channels()`

- **描述**: 查询当前设备的最大通道数量。新代码通常应优先使用 `get_channels()` 获取实际可用通道列表。

- **返回值**:
  - `int` 或 `None`: 最大通道数量；旧固件可能不支持该命令，此时返回 `None`。

- **示例**:

  ```python
  max_channels = hub.get_max_channels()
  channels = hub.get_channels()
  ```


### 获取设备序列号

#### `get_serial_no()`

- **描述**: 查询设备序列号。

- **返回值**:
  - `str` 或 `None`: 设备序列号；如果设备未提供序列号，可能返回 `"N/A"`。

- **示例**:

  ```python
  serial_no = hub.get_serial_no()
  ```

### 设备定位与名称

#### `identify_device()`

- **描述**：让当前设备的状态指示灯快速闪烁，便于在多台设备中完成物理定位。
- **返回值**：`bool`；设备确认命令时返回 `True`，否则返回 `False`。

#### `set_device_alias(alias)` 与 `get_device_alias()`

- **描述**：设置或读取 UTF-8 设备别名。别名最多 31 个 UTF-8 字节，传入空字符串可清除别名。
- **返回值**：`set_device_alias()` 返回 `bool`；`get_device_alias()` 返回别名字符串，未设置或旧固件不支持时返回空字符串。

```python
hub.set_device_alias("机架 A")
print(hub.get_device_alias())
```

#### `set_channel_name(channel, name)` 与 `get_channel_name(channel)`

- **描述**：设置或读取单通道 UTF-8 显示名称。名称最多 15 个 UTF-8 字节，空字符串恢复默认 `CHn`。
- **返回值**：`set_channel_name()` 返回 `bool`；`get_channel_name()` 返回已存名称或默认通道名。

#### `get_channel_names(*channels)`

- **描述**：读取指定通道的显示名称；未传通道时读取全部有效通道。
- **返回值**：`dict[int, str]`。

```python
hub.set_channel_name(1, "被测设备")
names = hub.get_channel_names()
```

### 重启设备

#### `reboot_mcu()`

- **描述**：请求 MCU 重启。设备确认后很快断开，通常需要重新连接。
- **返回值**：`bool`；设备确认命令时返回 `True`，否则返回 `False`。

> 重启前必须停止下游设备的写入和固件操作。



### 恢复出厂设置

#### `factory_reset()`

- **描述**: 将设备重置为出厂设置。
- **返回值**:
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
- **示例**:
  ```python
  hub.factory_reset()
  ```



### 获取固件版本

#### `get_firmware_version()`

- **描述**: 查询设备的固件版本。
- **返回值**:
  - `int` 或 `None`: 固件版本，若无响应则返回 `None`。
- **示例**:
  ```python
  firmware_version = hub.get_firmware_version()
  ```

#### `get_firmware_version_major()`

- **描述**：返回缓存的固件主版本；必要时先查询设备。旧版固件按主版本 1 处理。
- **返回值**：`int` 或 `None`。

#### `get_firmware_version_string()`

- **描述**：把缓存的固件版本格式化为显示字符串，例如 `V2.1`。
- **返回值**：`str`；无法读取时返回 `"Unknown"`。



### 获取硬件版本

#### `get_hardware_version()`

- **描述**: 查询设备的硬件版本。
- **返回值**:
  - `int` 或 `None`: 硬件版本，若无响应则返回 `None`。
- **示例**:
  ```python
  hardware_version = hub.get_hardware_version()
  ```



### 注册用户回调

#### `register_callback(cmd, callback)`

- **描述**: 为指定的命令注册一个用户回调函数。当设备返回该命令的应答时，回调函数会被触发。

- **参数**:

  - cmd (int): 要注册回调的命令。
  - callback (function): 当命令的 ACK 被接收到时执行的回调函数。回调函数应接受两个参数：
    - channel (int): 触发回调的通道编号。
    - status (int): 通道的状态值。

- **返回值:**

  - 无返回值。

- **注意事项**:

  - 如果 cmd 不在支持的命令列表中，将记录警告日志，并不会注册回调。
  - 回调函数的签名应与设备返回的数据结构匹配。
  - 普通控制和查询指令使用 V1/V2 协议帧。V3 用于高速或流式数据传输，例如测量数据流；普通应用代码不需要手动选择协议版本。

  | CMD宏                           | 含义                                                         |
  | :------------------------------ | :----------------------------------------------------------- |
  | CMD_GET_CHANNEL_POWER_STATUS    | 获取通道 VBUS 电源状态                                       |
  | CMD_SET_CHANNEL_POWER           | 设置通道 VBUS 电源状态                                       |
  | CMD_SET_CHANNEL_POWER_INTERLOCK | 选择单个供电通道，或清除互锁                                 |
  | CMD_GET_CHANNEL_VOLTAGE         | 获取单通道电压采样                                           |
  | CMD_GET_CHANNEL_CURRENT         | 获取单通道电流采样                                           |
  | CMD_SET_CHANNEL_DATALINE        | 设置 USB2 D+/D- 数据线开关状态                               |
  | CMD_GET_CHANNEL_DATALINE_STATUS | 获取 USB2 D+/D- 数据线开关状态                               |
  | CMD_SET_BUTTON_CONTROL          | 启用/禁用面板按键控制                                        |
  | CMD_GET_BUTTON_CONTROL_STATUS   | 获取面板按键控制状态                                         |
  | CMD_SET_DEFAULT_POWER_STATUS    | 设置上电/默认 VBUS 电源状态                                  |
  | CMD_GET_DEFAULT_POWER_STATUS    | 获取上电/默认 VBUS 电源状态                                  |
  | CMD_SET_DEFAULT_DATALINE_STATUS | 设置上电/默认 USB2 数据线状态                                |
  | CMD_GET_DEFAULT_DATALINE_STATUS | 获取上电/默认 USB2 数据线状态                                |
  | CMD_SET_AUTO_RESTORE            | 启用/禁用断电自动恢复                                        |
  | CMD_GET_AUTO_RESTORE_STATUS     | 获取断电自动恢复状态                                         |
  | CMD_SET_OPERATE_MODE            | 设置设备工作模式                                             |
  | CMD_GET_OPERATE_MODE            | 获取设备工作模式                                             |
  | CMD_SET_DEVICE_ADDRESS          | 设置多设备场景下的设备地址                                   |
  | CMD_GET_DEVICE_ADDRESS          | 获取多设备场景下的设备地址                                   |
  | CMD_GET_CHANNEL_MEASUREMENTS    | V3 电压/电流采样查询或流式上报命令                           |
  | CMD_GET_CHANNEL_OC_STATUS       | 获取或接收通道过流 active/latch 掩码                         |
  | CMD_CLEAR_CHANNEL_OC_LATCH      | 清除指定通道掩码的过流 latch                                 |
  | CMD_IDENTIFY_DEVICE             | 闪烁设备状态灯，用于物理定位                                 |
  | CMD_SET_CHANNEL_NAME            | 设置通道 UTF-8 显示名称                                      |
  | CMD_GET_CHANNEL_NAME            | 获取通道 UTF-8 显示名称                                      |
  | CMD_SET_DEVICE_ALIAS            | 设置设备 UTF-8 别名                                          |
  | CMD_GET_DEVICE_ALIAS            | 获取设备 UTF-8 别名                                          |
  | CMD_REBOOT_MCU                  | 重启设备 MCU                                                 |
  | CMD_GET_SERIAL_NO               | 获取设备序列号                                               |
  | CMD_GET_PRODUCT_TYPE            | 获取产品类型码                                               |
  | CMD_GET_MAX_CHANNELS            | 获取最大支持通道数                                           |
  | CMD_FACTORY_RESET               | 恢复出厂设置                                                 |
  | CMD_GET_FIRMWARE_VERSION        | 获取固件版本号                                               |
  | CMD_GET_HARDWARE_VERSION        | 获取硬件版本号                                               |

- **示例**:

  设置按键回调，当按键按下时，产生回调

  ```python
  from smartusbhub import CMD_GET_CHANNEL_POWER_STATUS

  def button_press_callback(channel, status):
      print("Button press detected on channel", channel, "with power status", status)
  
  hub.register_callback(CMD_GET_CHANNEL_POWER_STATUS, button_press_callback)
  ```
