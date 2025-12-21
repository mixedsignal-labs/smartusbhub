# SmartUSBHub python library

[简体中文](./README_cn.md)

![view1](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/view1.png?raw=true)**This document applies to model:** SmartUSBHub_V1.3a

**Last updated on:** June 24, 2026



## Introduction

- Before using, please familiarize yourself with the details of SmartUSBHub. For more information, read the  [smartusbhub_user_guide](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/document/smartusbhub_user_guide.md)

- If you prefer direct software control, download the software suit here: [software suite](https://github.com/MrzhangF1ghter/smartusbhub_app).

- This is a Python library for controlling SmartUSBHub. If you do not wish to use the Python library, you can refer to the simplest control demo: [simple_serial.py](./examples/simple_serial.py).

  

## Overview

The SmartUSBHub is a 4-port, software-programmable USB 2.0 (480 Mbps) hub that offers per-port power and data control, as well as voltage and current sensing. It is designed for development, testing, and device management applications.

1. **Programmable USB Port Switching**

   - Individually enable or disable power and data lines on any downstream port
   - Simulates manual hot-plug behavior via button or command/software

2. **Voltage and Current Monitoring**

   - Each port supports real-time voltage and current measurement for power analysis and device diagnostics

3. **Software-Controllable & Multi-Platform Compatible**

   - USB CDC-based serial command interface, provide Python libraries and software for easy integration
   - Supports on Windows, macOS, Linux; no additional drivers required

4. **Multiple Operating Modes**

   - **Normal Mode**: all ports operate independently
   - **Interlock Mode**: only one port is active at any time
   - Each downstream port supports customizable **power-on defaults** and **power-loss state recover**

5. **Topology Support for Scalable Deployment**
   - Each hub can be assigned a unique address for large-scale, multi-hub configurations

## Trusted by Industry Leaders

*From consumer electronics to autonomous driving, from global smartphone leaders to high-performance chip design companies, SmartUSBHub is widely deployed in the R&D, automated testing, and production validation flows of top-tier enterprises.*

SmartUSBHub is now used by **20+ global industry leaders**, Representative use cases include:

- **Automotive Industry:** Used by over 3 of the global top 5 Tier 1 suppliers.
- **Smartphone:** Used by over 3 of the top 5 global smartphone OEMs.
- **Semiconductors & Chip Design:** Deployed by over 5 leading chip design companies worldwide.
- **AI & Large Model Platforms:** Integrated into internal testing flows of at least 2 global AI tech giants.
- **Telecom & IoT Equipment:** Adopted at scale by multiple leading global and regional vendors.



### Connection Guide

![connection_guide](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/connection_guide.png?raw=true)

> [!NOTE]
>
> 1. Connect the included USB-A to USB-C cable between the device’s **USB upstream port** and a USB port on the host computer. This port is used for USB data transmission.Once connected, the device will appear as a Generic USB Hub.
> 2. Connect the included USB-A to USB-C cable between the device’s **Command Port** and a USB port on the host computer. This port is used for serial communication. Once connected, the device will appear as:
>    - On Windows: `COMx`
>    - On Linux: `/dev/ttyACMx` or `/dev/cu.usbmodemx`
>    - On macOS:  `/dev/cu.usbmodemx`



## Deployment

> [!NOTE]
>
> If you don't want to control the SmartUSBHub by using the python library, you can refer the most simplest control demo: [simple_serial.py](./examples/simple_serial.py)

### Setup Virtual Environment

In the development directory, create a Python virtual environment (recommended):
`python -m venv venv`

1. Activate the Python virtual environment:

   - On Windows:

    `.\venv\Scripts\activate.bat`

   - On Unix:

    `source ./venv/bin/activate`

2. Install dependencies (skip this step if using pip installation):
   
    `pip install -r requirements.txt`
    
    

### Get the Latest Library

#### Method 1: Install via pip

```shell
pip install smartusbhub
```

#### Method 2: Clone from GitHub

```shell
cd my_project
git clone https://github.com/MrzhangF1ghter/smartusbhub.git
```

Library structure:

```shell
.
├── README.md                # Documentation
├── examples                 # Demo examples
├── apps                     # Precompiled demo binaries
├── requirements.txt         # Dependency list
└── smartusbhub.py           # Core functionality source code
```



### Run Examples

`smartusbhub` Python library includes several usage examples in the `examples` directory:

- `power_control_example`:Demonstrates how to control the power supply of a specified port.
- `dataline_control_example`:Demonstrates how to toggle the USB differential signal line switch of a specified port for data connect/disconnect while keeping power enabled.
- `voltage_monitor_example`:Demonstrates how to retrieve the voltage value of a specified port.
- `current_monitor_example`:Demonstrates how to retrieve the current value of a specified port.
- `setting_example`: Demonstrates how to configure parameters.
- `user_callback_example`:Demonstrates how to add user callbacks for specfic command.
- `oscilloscope`:A Qt GUI-based oscilloscope that allows control of channel power switching, as well as voltage and current acquisition.

![oscilloscope](https://github.com/MrzhangF1ghter/smartusbhub/blob/main/assets/oscilloscope.png?raw=true)

<center>Figure: Oscilloscope app</center>



To run a demo, execute the following commands:

- Activate the virtual environment:

- Navigate to the examples folder:

  ```
  cd ./examples/
  ```
  
- Run a demo (for example):

  ```shell
  python oscilloscope.py
  ```

  

### Integrating with Your Project

You can integrate this library into your project by importing the smartusbhub module.

1. Follow the configuration steps from the earlier sections (steps 1 through 5) to set up the environment.

2. Import the smartusbhub library into your project:

   ```python
   import sys
   sys.path.append('../')#if you install by pip,you don't need this
   from smartusbhub import SmartUSBHub
   ```

3. Initialize a `SmartUSBhub`instance:

   - By automatically scanning and connecting to the device:

     ```python
     hub = SmartUSBHub.scan_and_connect()
     ```

   - By specifying the serial port to connect to the device:

     ```python
     hub = SmartUSBHub("serial port path")
     Example:
     hub = SmartUSBHub("/dev/cu.usbmodem132301")
     ```



## User Interface

### Device Connection

#### `scan_and_connect()`

- **Description**: Scans for available Smart USB Hub devices and connects to the first one found.
- **Return Value**:
  
  - SmartUSBHub instance (if a device is found), otherwise returns None.
  
- **Example**:
  
  ```python
  hub = SmartUSBHub.scan_and_connect()
  ```

#### `connect(port)`

- **Description**: Connects to the specified Smart USB Hub device.

- **Parameters:**

  - `port`(str): The serial port name to connect to.

- **Example:**

  ```python
  hub.connect("/dev/cu.usbmodem132301")
  ```



### Device Disconnection

#### `disconnect()`

- **Description**: Disconnects the current Smart USB Hub device.

- **Example:**

  ```python
  hub.disconnect()
  ```



### Channel Power Control

#### `set_channel_power(*channels, state)`

- **Description**: Sets the power state of the specified channel(s).

- **Parameters**:
  
  - `*channels` (int): The channel(s) to control.
  - state (int): `1` to turn the power，`0` to turn the power off.
  
- **Return Value**:

  - bool: Returns `True` if the command is successful, otherwise `False`.

- **Example**:

  ```python
  hub.set_channel_power(1, 2, state=1)
  ```



### Getting Channel Power Status

#### `get_channel_power_status(*channels)`

- **Description**: Queries the power status of the specified channel(s).
- **Parameters**:
  
  - `*channels` (int): The channel(s) to query.
- **Return Value**:
  - `dict` or `int` or `None`: If querying multiple channels, returns a dictionary of channel statuses; if querying a single channel, returns that channel’s status; if a timeout occurs, returns `None`.
- **Example**:
  ```python
  status = hub.get_channel_power_status(1, 2)
  ```



### Channel Power Interlock Control

#### `set_channel_power_interlock(channel)`

- **Description**: Sets the interlock mode for the specified channel or all channels.
- **Parameters**:
  
  - channel (int or `None`): The channel to set. If None, all channels will be turned off.
  
- **Return Value**:
  
  - bool: Returns True if the command is successful, otherwise False.
  
- **Example**:
  
  ```python
  hub.set_channel_power_interlock(1)
  ```



### Channel USB Data Line Control

#### `set_channel_usb2_dataline(*channels, state)`

- **Description**: Sets the USB data line (D+ and D-) connection state for the specified channel(s).

- **Parameters**:
  - `*channels` (int): The channel(s) to update.
  - state (int): `1`  to connect the D+ and D- lines, `0` to disconnect the D+ and D- lines.

- **Return Value**:
  
  - bool: Returns `True` if the command is successful, otherwise `False`.

- **Example**:
  
  Connect the data lines of channel 1:
  
  ```python
  hub.set_channel_usb2_dataline(1,state=1)
  ```
  
  
### Getting Channel USB Data Line Status
#### `get_channel_usb2_dataline_status(*channels)`
- **Description**: Queries the USB data line switch status of the specified channel(s).

- **Parameters**:
  - `*channels` (int): The channel(s) to query.
  
- **Return Value**:
  - `dict` or `None`: A dictionary containing each channel’s data line status; if a timeout occurs, returns `None`.
  
- **Example**:
  
  Get the data line connection status of channels 1 and 2:
  
  ```python
  status = hub.get_channel_usb2_dataline_status(1, 2)
  ```



### Getting Channel Voltage

#### `get_channel_voltage(channel)`

- **Description**: Queries the voltage of a single channel.
- **Parameters**:
  - channel (int): The channel(s) to query.

- **Return Value**:
  - `int` or `None`: The voltage value of the channel (in mV); if a timeout occurs, returns `None`.
- **Example**:
  
  Get the voltage of channel 1:
  
  ```python
  voltage = hub.get_channel_voltage(1)
  ```
  



### Getting Channel Current

#### `get_channel_current(channel)`

- **Description**: Queries the current of a single channel.
- **Parameters**:
  
  - channel (int): The channel(s) to query.
  
- **Return Value**:
  
  - `int` or `None`: The current value of the channel (in mA); if a timeout occurs, returns `None`.
- **Example**:
  
  Get the current of channel 1:
  
  ```python
  current = hub.get_channel_current(1)
  ```



### Setting Channel Power-On Default State

#### `set_default_power_status(*channels,enable,status)`

- **Description**: Sets the power-on default power state for the specified channel(s).

- **Parameters**:

  - `*channels` (int): The channel(s) to configure.
  - enable (int): `1` to enable using the default state, `0` to disable using the default state.
  - status (int): `1` for default power ON, `0` for default power OFF.

- **Example**:

  Channels 1, 2, 3, 4 default power ON at startup:

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=1,status=0)
  ```

  Channels 1, 2, 3, 4 do not use default values at startup:

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=0)
  ```



### **Getting Channel Power-On Default State**

#### `get_default_power_status(self,*channels)`

- **Description**: Queries the power-on default power state of one or multiple channels.

- **Parameters**:

  - `*channels` (int): The channel(s) to query.

- **Return Value**:

  - dict or None: A dictionary in the format {channel: {"enabled": enabled_flag, "value": state}}, where enabled is 0 (disabled) or 1 (enabled), and value is 0 (default OFF) or 1 (default ON). 
  - Returns None if a timeout occurs.

- **Example**:

  Channels 1, 2, 3, 4 default power ON at startup:

  ```python
  hub.get_default_power_status(1,2,3,4)
  ```

  Returns:

  ```python
  {1: {'enabled': 0, 'value': 0}, 2: {'enabled': 0, 'value': 0}, 3: {'enabled': 0, 'value': 0}, 4: {'enabled': 0, 'value': 0}}
  ```



### Setting Channel USB Data Line Power-On Default State

#### `set_default_dataline_status(*channels,enable,status)`

- **Description**: Sets the power-on default state of the USB data line connection for the specified channel(s).

- **Parameters**:

  - `*channels` (int): The channel(s) to configure.
  - enable (int): `1` to enable using the default state, `0` to disable using the default state.
  - status (int): `1` for default data line connected, `0` for default data line disconnected.

- **Return Value**:

  - bool: Returns `True` if the command is successful, otherwise `False`.
  
- **Example**:

  Channels 1, 2, 3, 4 default data line connected at startup:

  ```python
  hub.set_default_dataline_status(1,2,3,4,enable=1,status=1)
  ```




### Getting Channel USB Data Line Power-On Default State

#### `get_default_dataline_status(self,*channels)`

- **Description**: Queries the power-on default state of the USB data line connection for one or multiple channels.

- **Parameters**:

  - `*channels` (int): The channel(s) to query.

- **Return Value**:

  - `dict` or `None`: A dictionary in the format {channel: {"enabled": enabled_flag, "value": state}}, where enabled is 0 (disabled) or 1 (enabled), and value is 0 (default disconnected) or 1 (default connected). 
  - Returns `None` if a timeout occurs.

- **Example**:

  Get the power-on default USB data line state of channels 1, 2, 3, 4:

  ```python
  hub.get_default_dataline_status(1,2,3,4)
  ```

  Returns:

  ```python
  {1: {'enabled': 0, 'value': 1}, 2: {'enabled': 0, 'value': 1}, 3: {'enabled': 0, 'value': 1}, 4: {'enabled': 0, 'value': 1}}
  ```



### Setting Device Auto Restore

#### `set_auto_restore(enable)`

- **Description**: Enables or disables the power down auto-restore feature.

- **Parameters**:

  - enable (bool): `True` to enable auto-restore; `False` to disable.

- **Return Value**:

  - bool: Returns `True` if the command is successful, otherwise `False`.

- **Example**:

  Enable auto restore:

  ```python
  hub.set_auto_restore(True)
  ```



### Getting Device Auto Restore state

#### `get_auto_restore_status()`

- **Description**: Queries whether auto-restore is enabled.

- **Return Value**:

  - int or None: 1 if auto-restore is enabled, 0 if disabled, or None if no response.

- **Example**:

  Get auto restore status:

  ```python
  status = hub.get_auto_restore()
  ```



### Setting Button Control

#### `set_button_control(enable)`

- **Description**: Enables or disables the hub’s physical button.

- **Parameters**:
  
  - enable (bool): `True` to enable the button, `False` to disable the button.
  
- **Return Value**:
  
  - bool: Returns `True` if the command is successful, otherwise `False`.
  
- **Example**:

  Enable the button:

  ```python
  hub.set_button_control(True)
  ```



### Getting Button Control Status

#### `get_button_control_status()`

- **Description**: Queries whether the hub’s physical button is enabled.
- **Return Value**:
  - `int` or `None`: `1` if enabled, `0` if disabled. Returns None if no response.
- **Example**:
  
  Check if the button is enabled:
  
  ```python
  status = hub.get_button_control_status()
  ```



### Set Device Address

#### `set_device_address(address)`

- **Description**: The device address is used to identify and distinguish each hub when multiple hubs are connected.

- **Parameter**:

  - `int`: The address is user-defined and should be within the range `0x0000 - 0xFFFF`.

- **Return Value**:

  - `int` or `None`: Returns `1` if successful, `0` if failed, or `None` if no response.

- **Note**:

  - When a `SmartUSBHub` instance is created, the device address is automatically retrieved. Different instances can be distinguished by their unique addresses.

- **Example**:

  Set the device address to `0x0001`:

  ```python
  hub.set_device_address(0x0001)



### Get Device Address

#### `get_device_address()`

- **Description**: Retrieves the address of the connected device.

- **Return Value**:

  - `int` or `None`: The device address, or `None` if no response is received.

- **Example**:

  Query the device address:

  ```python
  device_address = hub.get_device_address()
  ```



### Setting Device Operating Mode

#### `set_operate_mode(mode)`

- **Description**: Sets the device’s operating mode.

- **Parameters**:

  - mode (int): Operating mode (0 for normal mode, 1 for interlock mode).

- **Return Value**:

  - bool: Returns `True` if the command is successful, otherwise `False`.

- **Attention:**

  - In interlock mode, control can only be done using interlock commands.

- **Example**:

  Set the device to normal mode:

  ```python
  hub.set_operate_mode(0)
  ```



### Getting Device Operating Mode

#### `get_operate_mode()`

- **Description**: Queries the device’s current operating mode.

- **Return Value**:
  - `int` or `None`: The current operating mode. Returns `None` if no response.
  
- **Example**:
  
  Check the device’s operating mode:
  
  ```python
  mode = hub.get_operate_mode()
  ```



### Getting Device Information

#### `get_device_info()`

- **Description**: Retrieves the hub’s ID, hardware version, firmware version, operating mode, and button control status.
- **Return Value**:
  - `dict`: A dictionary containing the device information.
- **Example**:
  ```python
  info = hub.get_device_info()
  print(info)
  ```



### Factory Reset

#### `factory_reset()`

- **Description**: reset the device to factory settings.
- **Return Value**:
  - bool: Returns `True` if the command is successful, otherwise `False`.
- **Example**:

```python
hub.factory_reset()
```



### Getting Firmware Version

#### `get_firmware_version()`

- **Description**: Queries the device’s firmware version.
- **Return Value**:
  - `int` or `None`: The firmware version. Returns None if no response.
- **Example**:
  ```python
  firmware_version = hub.get_firmware_version()
  ```



### Getting Hardware Version

#### `get_hardware_version()`

- **Description**: Queries the device’s hardware version.
- **Return Value**:
  - `int` or `None`: The hardware version. Returns `None` if no response.
- **Example**:
  ```python
  hardware_version = hub.get_hardware_version()
  ```



### Registering User Callback

#### `register_callback(cmd, callback)`

- **Description**: Registers a user callback function for a specified command. When the device returns an ACK for that command, the callback function will be triggered.

- **Parameters**:

  - cmd (int): The command for which to register the callback.
  - callback (function): The callback function to execute when the command’s ACK is received. The callback function should accept two parameters:
    - channel (int): The channel number that triggered the callback.
    - status (int): The status value of that channel.

- **Return Value:**

  - (None)

- **Notes**:

  - If cmd is not in the supported command list, a warning will be logged and the callback will not be registered.

  

  | CMD                             | **Meaning**                                                  |
  | :------------------------------ | :----------------------------------------------------------- |
  | CMD_GET_CHANNEL_POWER_STATUS    | Get channel power status                                     |
  | CMD_SET_CHANNEL_POWER           | Control channel power                                        |
  | CMD_SET_CHANNEL_POWER_INTERLOCK | Control channel power interlock                              |
  | CMD_SET_CHANNEL_DATALINE        | Control channel USB data line switch                         |
  | CMD_GET_CHANNEL_DATALINE_STATUS | Get channel USB data line switch status                      |
  | CMD_GET_CHANNEL_VOLTAGE         | Get channel voltage                                          |
  | CMD_GET_CHANNEL_CURRENT         | Get channel current                                          |
  | CMD_SET_BUTTON_CONTROL          | Enable/disable button control                                |
  | CMD_GET_BUTTON_CONTROL_STATUS   | Get button control status                                    |
  | CMD_SET_DEFAULT_POWER_STATUS    | Set channel default power status                             |
  | CMD_GET_DEFAULT_POWER_STATUS    | Get channel default power status                             |
  | CMD_SET_DEFAULT_DATALINE_STATUS | Set channel default data line status                         |
  | CMD_GET_DEFAULT_DATALINE_STATUS | Get channel default data line status                         |
  | CMD_SET_AUTO_RESTORE            | Enable/disable power-loss auto restore                       |
  | CMD_GET_AUTO_RESTORE_STATUS     | Get power-loss auto restore status                           |
  | CMD_SET_DEVICE_ADDRESS          | Set the device address, used to identify and distinguish hubs in multi-hub setups |
  | CMD_GET_DEVICE_ADDRESS          | Get the device address, used to identify and distinguish hubs in multi-hub setups |
  | CMD_SET_OPERATE_MODE            | Set device operating mode (normal/interlock)                 |
  | CMD_GET_OPERATE_MODE            | Get device operating mode                                    |
  | CMD_FACTORY_RESET               | Restore factory settings                                     |
  | CMD_GET_FIRMWARE_VERSION        | Get firmware version                                         |
  | CMD_GET_HARDWARE_VERSION        | Get hardware version                                         |

- **Example**:

  Set a button press callback; when the button is pressed, a callback is triggered:

  ```python
  def button_press_callback(channel, status):
      print("Button press detected on channel", channel, "with power status", status)
  
  hub.register_callback(CMD_GET_CHANNEL_POWER_STATUS, button_press_callback)
  ```

