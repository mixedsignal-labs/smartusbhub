# SmartUSBHub python library

[English](./README.md)

![view1](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/view1.png?raw=true)

**本文档适用型号**：`SmartUSBHub Pro 2.0` `SmartUSBHub Pro 3.0` 

**本文档更新日期**：2025年12月28日



## 简介
- 使用前请先了解SmartUSBHub详细信息，详情请阅读[智能USB集线器_使用指南](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/document/智能USB集线器_使用指南.md)

- 如果想直接用软件控制，则请下载配套的控制软件：[配套控制软件](https://github.com/MrzhangF1ghter/smartusbhub_app)

- 这是一个控制SmartUSBHub的Python库，如果不想用python库，则可参考最简单的控制demo：[simple_serial.py](./examples/simple_serial.py)



## 产品概述

SmartUSBHub是一个4端口的可编程USB2.0(480Mbps)集线器，每个下游端口均可独立控制电源和数据通道，同时具备电压/电流测量功能，适用于开发、测试和设备管理。

1. **独立电源/数据控制，模拟热插拔：** SmartUSBHub 每个下游端口支持 **电源（VBUS）** 和 **数据（D+ / D-）** 的独立控制，可通过指令模拟物理插拔USB设备 。工程师无需手动插拔即可远程控制USB设备的连接/断开，实现自动化测试或远程重启设备，极大提升调试和测试效率。

2. **电压/电流监测：** 该集线器提供每端口实时电压、电流采集功能 。这意味着用户可以随时监控各被测设备的供电电压及电流，辅助进行设备功耗分析与状态监测。在测试中若出现异常电压跌落或电流过载，工程师能够及时发现并定位问题。

3. **开源软件生态，易于集成：** SmartUSBHub 提供了开源的协议、控制软件和 Python 控制库，兼容 Windows/macOS/Linux 等主流操作系统 。得益于标准串口指令接口和开放的API，用户可将其无缝集成到现有的自动化测试平台或脚本中（通过Python、CLI等），轻松将USB端口控制纳入自动化流程，加速开发测试周期。

4. **多模式端口管理**

  - 支持 **普通模式**（多通道同时控制）与 **互锁模式**（仅允许操作一个通道）

  - 每端口可设置 **上电默认状态** 与 **断电状态记忆**

5. **扩展性强**

  - 支持集中控制多个SmartUSBHub的拓扑结构

  - 每个设备支持地址配置，适用于级联系统



## 被行业验证的选择

*从消费电子到自动驾驶，从全球领先的消费电子品牌到高性能芯片设计公司，SmartUSBHub 已广泛应用于多个行业头部企业的研发流程、自动化测试系统与产线测试场景中。*

SmartUSBHub 目前已被**全球 20+ 家行业头部企业**广泛采用，其客户涵盖以下代表性领域：

- **汽车行业**
- **智能手机行业 **
- **半导体与芯片设计** 
- **人工智能与大模型平台**
- **通信与物联网设备制造**



## 连接指南

![connection_guide](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/connection_guide_cn.png?raw=true)

> 1. 将随附的USBA-USBC 数据线连接设备的`USB上行端口`与主机USB端口。该端口用于USB数据传输。
> 2. 将随附的USBA-USBC 数据线连接设备的`指令控制口`与主机USB端口。该端口用于串口通信，连接后主机将会把设备识别成:
>    - Windows平台:  `COMx`
>    - Linux平台: `/dev/ttyACMx`
>    - mac平台: `/dev/cu.usbmodemx`





## 部署

### 设置虚拟环境

在开发目录中，设置python虚拟环境（推荐）
`python -m venv venv`

1. 进入python虚拟环境

   - 对于Windows平台:

    `.\venv\Scripts\activate.bat`

   - 对于unix平台:

    `source ./venv/bin/activate`

2. 安装依赖库（如果通过pip安装，则不需要执行此步骤）
    `pip install -r requirements.txt`



### 获取最新的库

#### **方法1**: 通过pip包管理工具获取

```shell
pip install smartusbhub
```

#### **方法2**: 通过github获取

```shell
git clone https://github.com/MrzhangF1ghter/smartusbhub.git
```

库目录结构如下：

```shell
.
├── README.md					# 文档
├── examples					# 例程
├── apps							# 已经编译好的GUI demo
├── requirements.txt	# 安装依赖
└── smartusbhub.py 		# 功能源码
```



### 集成到项目

通过导入smartusbhub库即可即成到你的项目之中。

1. 导入`smartusbhub`库到你的工程.

   ```python
   from smartusbhub import SmartUSBHub
   ```

2. 初始化`SmartUSBhub`实例:

   - 通过自动扫描连接设备：

     ```python
     hub = SmartUSBHub.scan_and_connect()
     ```

   - 通过指定串口号连接设备：

     ```python
     hub = SmartUSBHub("串口路径")
     #例子：
     hub = SmartUSBHub("/dev/cu.usbmodem132301")
     ```



## 运行例程

`smartusbhub`库包含多个例程，其存放在`examples`目录下，目前有以下例子：

- `power_control_example`：展示如何控制指定通道的电源
- `dataline_control_example`：展示如何控制指定通道的USB数据开关通断（保持电源供电）
- `voltage_monitor_example`：展示如何获取指定通道的电压值
- `current_monitor_example`：展示如何获取指定通道的电流值
- `setting_example`:展示如何配置设置项
- `user_callback_example`：展示如何添加用户回调
- `oscilloscope`：一个简单的GUI示波器，可控制通道电源开关、电压及电流采集

![oscilloscope](./assets/oscilloscope.png)

<center>图：示波器demo</center>



若要运行demo，请执行以下指令：

- 激活虚拟环境：

- 进入examples文件夹：

  ```
  cd ./examples/
  ```
  
- 运行demo，例如：

  ```shell
  python oscilloscope.py
  ```




## **用户接口**

### 设备连接

#### `scan_and_connect()`

- **描述**: 扫描可用的 Smart USB Hub 设备，并连接到第一个有效设备。
- **返回值**:
  
  - SmartUSBHub 实例（如果找到设备），否则返回 `None`。
  
- **示例**:
  
  ```python
  hub = SmartUSBHub.scan_and_connect()
  ```

#### `connect(port)`

- **描述**: 连接到指定的Smart USB Hub 设备。

- **参数:**

  - [port](str): 要连接的串口名称。

- **示例:**

  ```python
  hub.connect("/dev/cu.usbmodem132301")
  ```



### 设备断开链接

#### `disconnect()`

- **描述**:断开当前的Smart USB Hub 设备。

- **示例:**

  ```python
  hub.disconnect()
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
  
  - `*channels` (int): 要查询的通道，可变参数形式，范围 1~4。
- **返回值**:
  - `dict` 或 `int` 或 `None`: 如果查询多个通道，返回包含通道状态的字典；如果查询单个通道，返回该通道的状态；若超时则返回 `None`。
- **示例**:
  ```python
  status = hub.get_channel_power_status(1, 2)
  ```



### 控制通道充电模式

> [!NOTE]
>
> **注意**: 通道充电模式API仅适用于 **SmartUSBHub Pro 3.0** 型号。

#### `set_channel_slow_charge(*channels, disconnect_before_switch=True)`

- **描述**: 设置指定通道为慢充模式。慢充模式限制充电电流（启用电流限制）。

- **参数**:
  - `*channels` (int): 要设置的通道，可变参数形式，范围 1~4。
  
  - `disconnect_before_switch` (bool): 如果为 `True`，在切换到慢充模式前会先断开通道连接3秒。默认为 `True`。
  
    > [!NOTE]
    >
    > 不同设备（DUT）的充电策略可能不同。为了让设备重新识别充电器能力，此参数可通过模拟数据线插拔来实现。
    >
    > 部分设备可能不需要此操作，请根据实际测试情况决定是否需要先断开通道连接再切换充电模式。
  
    
  
- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:
  ```python
  # 直接切换到慢充模式（不断开连接）
  hub.set_channel_slow_charge(1, disconnect_before_switch=False)
  
  # 先断开连接再切换到慢充模式
  hub.set_channel_slow_charge(1, disconnect_before_switch=True)
  ```

- **流程图**:

- ![set_channel_slow_charge 流程图](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/set_channel_slow_charge_flowchart.png?raw=true)



#### `set_channel_fast_charge(*channels, disconnect_before_switch=True)`

- **描述**: 设置指定通道为快充模式。快充模式提供全功率充电（禁用电流限制，启用VBUS）。
- **参数**:
  - `*channels` (int): 要设置的通道，可变参数形式，范围 1~4。
  - `disconnect_before_switch` (bool): 如果为 `True`，在切换到慢充模式前会先断开通道连接3秒。默认为 `True`。
  
    > [!NOTE]
    >
    > 快充模式是指 BC1.2  (5V 1.5A)
    >
    > 不同设备（DUT）的充电策略可能不同。为了让设备重新识别充电器能力，此参数可通过模拟数据线插拔来实现。
    >
    > 部分设备可能不需要此操作，请根据实际测试情况决定是否需要先断开通道连接再切换充电模式。
  
- **返回值**:
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
- **示例**:
  ```python
  # 先断开连接再切换到快充模式（默认行为）
  hub.set_channel_fast_charge(1)
  
  # 直接切换到快充模式（不断开连接）
  hub.set_channel_fast_charge(1, disconnect_before_switch=False)
  ```

- **流程图**:
  ![set_channel_fast_charge 流程图](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/set_channel_fast_charge_flowchart.png?raw=true)



### 获取通道充电模式

#### `get_channel_charge_mode(*channels)`

- **描述**: 查询指定通道的充电模式。
- **参数**:
  - `*channels` (int): 要查询的通道，可变参数形式，范围 1~4。
- **返回值**:
  - `dict` 或 `None`: 包含通道充电模式的字典，键为通道号，值为充电模式。充电模式值：`0` 表示关闭，`1` 表示快充模式，`2` 表示慢充模式。若超时则返回 `None`。
- **示例**:
  ```python
  # 查询通道1和通道2的充电模式
  modes = hub.get_channel_charge_mode(1, 2)
  # 返回示例: {1: 1, 2: 2}  # 通道1为快充，通道2为慢充
  ```



### 控制通道电源互锁

#### `set_channel_power_interlock(channel)`

- **描述**: 设置指定通道或所有通道的互锁模式。
- **参数**:
  
  - `channel` (`int` 或 `None`): 要设置的通道。如果为 `None`，则关闭所有通道。
  
- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:
  
  ```python
  hub.set_channel_power_interlock(1)
  ```



### 控制通道USB数据开关

#### `set_channel_dataline(*channels, state)`

- **描述**: 设置指定通道的USB数据开关状态。

- **参数**:
  - `*channels` (int): 要更新的通道，可变参数形式，范围 1~4。
  - `state` (int): `1` 连通 D+ D-的物理连接， `0` 断开D+ D-的物理连接。

- **返回值**:
  
  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。

- **示例**:
  
  连通 通道1 的数据信号
  
  ```python
  hub.set_channel_dataline(1,state=1)
  ```
  
  
### 获取通道USB数据开关状态
#### `get_channel_dataline_status(*channels)`
- **描述**: 查询指定通道的USB数据开关状态。

- **参数**:
  - `*channels` (int): 要查询的通道，可变参数形式，范围 1~4。
  
- **返回值**:
  - `dict` 或 `None`: 包含通道状态的字典，若超时则返回 `None`。
  
- **示例**:
  
  获取 通道2 的数据信号连接状态
  
  ```python
  status = hub.get_channel_dataline_status(1, 2)
  ```



### 获取通道电压

> **注意**: 此API仅适用于 **SmartUSBHub Pro 2.0** 型号。

#### `get_channel_voltage(channel)`

- **描述**: 查询单个通道的电压。
- **参数**:
  - `channel` (int): 要查询的通道。

- **返回值**:
  - `int` 或 `None`: 通道的电压值(mV)，若超时则返回 `None`。
- **示例**:
  
  获取 通道1 的 电压值
  
  ```python
  voltage = hub.get_channel_voltage(1)
  ```
  



### 获取通道电流

> **注意**: 此API仅适用于 **SmartUSBHub Pro 2.0** 型号。

#### `get_channel_current(channel)`

- **描述**: 查询单个通道的电流。
- **参数**:
  - `channel` (int): 要查询的通道。

- **返回值**:
  
  - `int` 或 `None`: 通道的电流值(mA)，若超时则返回 `None`。
- **示例**:
  
  获取 通道1 的 电流值
  
  ```python
  current = hub.get_channel_current(1)
  ```



### 设置通道电源的上电默认状态

#### `set_default_power_status(*channels,enable,status)`

- **描述**: 设置指定通道的上电默认电源状态。

- **参数**:

  - `*channels` (int): 要设置的通道，可变参数形式，范围 1~4。
  - `enable` (int): `1` 启用默认状态， `0` 禁用默认状态。
  - `status` (int): 1 默认打开电源，0 默认关闭电源

- **示例**:

  通道1、2、3、4上电默认打开

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=1,status=0)
  ```

  通道1、2、3、4上电不使用默认值

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=0)
  ```



### 获取通道电源的上电默认状态

#### `get_default_power_status(self,*channels)`

- **描述**: 查询一个或多个通道电源的默认上电状态

- **参数**:

  - `*channels` (int): 要查询的通道，可变参数形式，范围 1~4。

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

#### `set_default_dataline_status(*channels,enable,status)`

- **描述**: 设置指定通道的上电默认数据连接状态。

- **参数**:

  - `*channels` (int): 要设置的通道，可变参数形式，范围 1~4。
  - `enable` (int): `1` 启用默认状态， `0` 禁用默认状态。
  - `status` (int): 1 默认连接数据，0 默认断开数据

- **返回值**:

  - `bool`: 如果命令设置成功返回 `True`，否则返回 `False`。
  
- **示例**:

  通道1、2、3、4上电默认数据连接

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=1,status=1)
  ```




### 获取通道数据连接的上电默认状态

#### `get_default_dataline_status(self,*channels)`

- **描述**: 查询一个或多个通道的上电默认数据连接状态。

- **参数**:

  - `*channels` (int): 要查询的通道，可变参数形式，范围 1~4。

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



### 设置断电状态记忆

#### `get_auto_restore_status()`

- **描述**: 查询是否启用断电状态恢复

- **返回值**:

  - int 或 None: 1 表示启用, 0 表示禁用, None 表示设备无响应.

- **示例**:

  启用断电状态恢复

  ```python
  status = hub.get_auto_restore()
  ```



### 设置按钮控制

#### `set_button_control(enable)`

- **描述**: 启用或禁用集线器的物理按钮。

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

- **描述**: 查询集线器的物理按钮是否启用。
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

  - `int` :地址的编号由用户自定义，其取值范围为: `0x0000 - 0xFFFF`

- **返回值**:

  - `int` 或 `None`: `1` 表示启用，`0` 表示禁用，若无响应则返回 `None`。

- **提示**：

  - 创建SmartUSBHub实例时会自动获取连接设备的地址，不同SmartUSBHub实例可以通过地址区分。

- **示例**:

  设置设备地址为`0x0001`

  ```python
  hub.set_device_address(0x0001)
  ```



### 获取设备地址

#### `get_device_address(address)`

- **描述**: 获取设备的地址

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
  - 互锁模式下，控制只能用互锁指令。

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



### 获取固件版本

#### `get_firmware_version()`

- **描述**: 查询设备的固件版本。
- **返回值**:
  - `int` 或 `None`: 固件版本，若无响应则返回 `None`。
- **示例**:
  ```python
  firmware_version = hub.get_firmware_version()
  ```



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

  | CMD宏                           | 含义                                                         |
  | :------------------------------ | :----------------------------------------------------------- |
  | CMD_GET_CHANNEL_POWER_STATUS    | 获取通道电源开关值                                           |
  | CMD_SET_CHANNEL_POWER           | 控制通道电源                                                 |
  | CMD_SET_CHANNEL_POWER_INTERLOCK | 控制通道电源互锁                                             |
  | CMD_SET_CHANNEL_DATALINE        | 控制通道USB数据开关                                          |
  | CMD_GET_CHANNEL_DATALINE_STATUS | 获取通道USB数据开关状态                                      |
  | CMD_GET_CHANNEL_VOLTAGE         | 获取通道电压                                                 |
  | CMD_GET_CHANNEL_CURRENT         | 获取通道电流                                                 |
  | CMD_SET_BUTTON_CONTROL          | 启用/禁用 按键控制                                           |
  | CMD_GET_BUTTON_CONTROL_STATUS   | 获取按键控制状态                                             |
  | CMD_SET_DEFAULT_POWER_STATUS    | 设置通道默认电源状态                                         |
  | CMD_GET_DEFAULT_POWER_STATUS    | 获取通道默认电源状态                                         |
  | CMD_SET_DEFAULT_DATALINE_STATUS | 设置通道默认数据连接状态                                     |
  | CMD_GET_DEFAULT_DATALINE_STATUS | 获取通道默认数据连接状态                                     |
  | CMD_SET_AUTO_RESTORE            | 启用/禁用 断电保存                                           |
  | CMD_GET_AUTO_RESTORE_STATUS     | 获取断电保存是否启用                                         |
  | CMD_SET_DEVICE_ADDRESS          | 设置设备的地址，用于在多台集线器连接的场景中，标识和区分各个集线器 |
  | CMD_GET_DEVICE_ADDRESS          | 获取设备的地址，用于在多台集线器连接的场景中，标识和区分各个集线器 |
  | CMD_SET_OPERATE_MODE            | 设置设备工作模式 普通/互锁                                   |
  | CMD_GET_OPERATE_MODE            | 获取设备工作模式                                             |
  | CMD_FACTORY_RESET               | 恢复出厂设置                                                 |
  | CMD_GET_FIRMWARE_VERSION        | 获取固件版本号                                               |
  | CMD_GET_HARDWARE_VERSION        | 获取硬件版本号                                               |

- **示例**:

  设置按键回调，当按键按下时，产生回调

  ```python
  def button_press_callback(channel, status):
      print("Button press detected on channel", channel, "with power status", status)
  
  hub.register_callback(CMD_GET_CHANNEL_POWER_STATUS, button_press_callback)
  ```

