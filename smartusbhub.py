# Description: Python class to control Smart USB Hub with serial communication.
# copyright: (c) 2026 makerlabtools
# license: Apache-2.0
# version: 1.0
# author: makerlabtools
# email: makerlabtools@outlook.com
# for more information: https://github.com/MrzhangF1ghter/smartusbhub

# protocol examples:

# Single Channel ON/OFF   send                ack                
#     ch1_on              55 5A 01 01 01 03   55 5A 01 01 01 03 
#     ch2_on              55 5A 01 02 01 04   55 5A 01 02 01 04 
#     ch3_on              55 5A 01 04 01 06   55 5A 01 04 01 06 
#     ch4_on              55 5A 01 08 01 0A   55 5A 01 08 01 0A 
#     ch1_off             55 5A 01 01 00 02   55 5A 01 01 00 02 
#     ch2_off             55 5A 01 02 00 03   55 5A 01 02 00 03 
#     ch3_off             55 5A 01 04 00 05   55 5A 01 04 00 05 
#     ch4_off             55 5A 01 08 00 09   55 5A 01 08 00 09 

# All Channel
#     ch_all_on           55 5A 01 0F 01 11   55 5A 01 0F 01 11  
#     ch_all_off          55 5A 01 0F 00 10   55 5A 01 0F 00 10 

# Combine Channel
#     ch_13_on            55 5A 01 05 01 07   55 5A 01 05 01 07 
#     ch_13_off           55 5A 01 05 00 06   55 5A 01 05 00 06 
#     ch_24_on            55 5A 01 0A 01 0C   55 5A 01 0A 01 0C 
#     ch_24_off           55 5A 01 0A 00 0B   55 5A 01 0A 00 0B 

# Get digital level       [channel,value]     
#     ch1_get_level       55 5A 00 01 00 01   
#                                             55 5A 00 01 00 01 [OFF]     
#                                             55 5A 00 01 01 02 [ON]

#     ch2_get_level       55 5A 00 02 00 02   
#                                             55 5A 00 02 00 02 [OFF]     
#                                             55 5A 00 02 01 03 [ON]

#     ch3_get_level       55 5A 00 04 00 04  
#                                             55 5A 00 04 00 04 [OFF]     
#                                             55 5A 00 04 01 05 [ON]

#     ch4_get_level       55 5A 00 08 00 08   
#                                             55 5A 00 08 00 08 [OFF]     
#                                             55 5A 00 08 01 09 [ON]

#     ch_all_get_level    55 5A 00 0F 00 0F   55 5A 00 01 00 01 55 5A 00 02 00 02 55 5A 00 04 00 04 55 5A 00 08 00 08 

# Initerlock mode         [channel,0x01]
#     interlock_set_ch1   55 5A 02 01 01 04   55 5A 02 01 01 04 
#     interlock_set_ch2   55 5A 02 02 01 05   55 5A 02 02 01 05
#     interlock_set_ch3   55 5A 02 04 01 07   55 5A 02 04 01 07
#     interlock_set_ch4   55 5A 02 08 01 0B   55 5A 02 08 01 0B
#     interlock_set_all   55 5A 02 0F 01 12   55 5A 02 0F 01 12

# Get Channel Voltage     [channel,0x00]      [channel,voltage]
#     ch1_get_voltage     55 5A 03 01 00 04   55 5A 03 01 00 00 04
#     ch2_get_voltage     55 5A 03 02 00 05   55 5A 03 02 00 00 05 
#     ch3_get_voltage     55 5A 03 04 00 07   55 5A 03 04 00 00 07 
#     ch4_get_voltage     55 5A 03 08 00 0B   55 5A 03 08 00 00 0B 

# Get Channel Current     [channel,0x00]      [channel,current]
#     ch1_get_current     55 5A 04 01 00 05   55 5A 04 01 00 00 05
#     ch2_get_current     55 5A 04 02 00 06   55 5A 04 02 00 00 06
#     ch3_get_current     55 5A 04 04 00 08   55 5A 04 04 00 00 08
#     ch4_get_current     55 5A 04 08 00 0C   55 5A 04 08 00 00 0C

# Set Channel Dataline    [channel,value]     
#     ch1_set_data_on     55 5A 05 01 01 07   55 5A 05 01 01 07
#     ch2_set_data_on     55 5A 05 02 01 08   55 5A 05 02 01 08
#     ch3_set_data_on     55 5A 05 04 01 0A   55 5A 05 02 01 0A
#     ch4_set_data_on     55 5A 05 08 01 0E   55 5A 05 08 01 0E

#     ch1_set_data_off    55 5A 05 01 00 06   55 5A 05 01 00 06
#     ch2_set_data_off    55 5A 05 02 00 07   55 5A 05 02 00 07
#     ch3_set_data_off    55 5A 05 04 00 09   55 5A 05 02 00 09
#     ch4_set_data_off    55 5A 05 08 00 0D   55 5A 05 08 00 0D
    
# All Channel
#     ch_dataline_all_on  55 5A 05 0F 01 15   55 5A 05 0F 01 15  
#     ch_dataline_all_off 55 5A 05 0F 00 14   55 5A 05 0F 00 14 

# Get Channel Dataline    [channel,value]     
#     ch1_get_data_status 55 5A 08 01 00 09           
#                                             55 5A 08 01 00 09[disconnect]   
#                                             55 5A 08 01 01 0A[connected]

#     ch2_get_data_status 55 5A 08 02 00 0A   
#                                             55 5A 08 02 00 0A[disconnect]   
#                                             55 5A 08 02 01 0B[connected]

#     ch3_get_data_status 55 5A 08 04 00 0C   
#                                             55 5A 08 04 00 0C[disconnect]   
#                                             55 5A 08 04 01 0D[connected]

#     ch4_get_data_status 55 5A 08 08 00 10   
#                                             55 5A 08 08 00 10[disconnect]   
#                                             55 5A 08 08 01 11[connected]

#     All Channel
#     ch_all_get_dataline 55 5A 08 0F 00 17   

# Set Button control Mode [0x00,enable]
#     disable_btn_control 55 5A 09 00 00 09   55 5A 09 00 00 09
#     enable_btn_control  55 5A 09 00 01 0A   55 5A 09 00 01 0A

# Get Button control Mode [0x00,value]
#     get_btn_control     55 5A 0A 00 00 0A   55 5A 0A 00 00 0A [disable] 55 5A 0A 00 01 0B[enable]

# Set default power status [channel,enable,value] protocol_v2
#     ch1_set_default_power_status_enable_on      55 5A 0B 01 01 01 0E    55 5A 0B 01 01 01 0E [default power status enable,value is on]
#     ch2_set_default_power_status_enable_on      55 5A 0B 02 01 01 0F    55 5A 0B 02 01 01 0F [default power status enable,value is on]
#     ch3_set_default_power_status_enable_on      55 5A 0B 04 01 01 11    55 5A 0B 04 01 01 11 [default power status enable,value is on]
#     ch4_set_default_power_status_enable_on      55 5A 0B 08 01 01 15    55 5A 0B 08 01 01 15 [default power status enable,value is on]
#     all_ch_set_default_power_status_enable_on   55 5A 0B 0F 01 01 1C    55 5A 0B 0F 01 01 1C [all default power status enable,value is on]

#     ch1_set_default_power_status_enable_off     55 5A 0B 01 01 00 0D    55 5A 0B 01 01 00 0D [default power status enable,value is off]
#     ch2_set_default_power_status_enable_off     55 5A 0B 02 01 00 0E    55 5A 0B 02 01 00 0E [default power status enable,value is off]
#     ch3_set_default_power_status_enable_off     55 5A 0B 04 01 00 10    55 5A 0B 04 01 00 10 [default power status enable,value is off]
#     ch4_set_default_power_status_enable_off     55 5A 0B 08 01 00 14    55 5A 0B 08 01 00 14 [default power status enable,value is off]
#     all_ch_set_default_power_status_enable_off  55 5A 0B 0F 01 00 1B    55 5A 0B 0F 01 00 1B [all default power status enable,value is off]

#     ch1_set_default_power_status_disable        55 5A 0B 01 00 00 0C    55 5A 0B 01 00 0C [default power status disable]
#     ch2_set_default_power_status_disable        55 5A 0B 02 00 00 0D    55 5A 0B 02 00 0D [default power status disable]
#     ch3_set_default_power_status_disable        55 5A 0B 04 00 00 0F    55 5A 0B 04 00 0F [default power status disable]
#     ch4_set_default_power_status_disable        55 5A 0B 08 00 00 13    55 5A 0B 08 00 13 [default power status disable]
#     all_ch_set_default_power_status_disable     55 5A 0B 0F 00 00 1A    55 5A 0B 0F 00 00 1A [all default power status enable,value is off]

# Get default power status [channel,enable,value] protocol_v2                     
#     ch1_get_default_power_status                55 5A 0C 01 00 00 0D            
#                                                                         55 5A 0C 01 00 00 0D [default power status disabled, poweroff]    
#                                                                         55 5A 0C 01 01 01 0F [default power status enable, poweron]

#     ch2_get_default_power_status                55 5A 0C 02 00 00 0E    
#                                                                         55 5A 0C 02 00 00 0E [default power status disabled, poweroff]    
#                                                                         55 5A 0C 02 01 01 10 [default power status enable, poweron]

#     ch3_get_default_power_status                55 5A 0C 04 00 00 10    
#                                                                         55 5A 0C 04 00 00 10 [default power status disabled, poweroff]   
#                                                                         55 5A 0C 04 01 01 12 [default power status enable, poweron]

#     ch4_get_default_power_status                55 5A 0C 08 00 00 14    
#                                                                         55 5A 0C 08 00 00 14 [default power status disabled, poweroff]    
#                                                                         55 5A 0C 08 01 01 16 [default power status enable, poweron]
#     all_ch_get_default_power_status             55 5A 0C 0F 00 00 1B

# Set default dataline status [channel,enable,value] protocol_v2
#     ch1_set_default_dataline_status_enable_on   55 5A 0D 01 01 01 10    55 5A 0D 01 01 01 10 [default dataline status enable, connected]
#     ch2_set_default_dataline_status_enable_on   55 5A 0D 02 01 01 11    55 5A 0D 02 01 01 11 [default dataline status enable, connected]
#     ch3_set_default_dataline_status_enable_on   55 5A 0D 04 01 01 13    55 5A 0D 04 01 01 13 [default dataline status enable, connected]
#     ch4_set_default_dataline_status_enable_on   55 5A 0D 08 01 01 17    55 5A 0D 08 01 01 17 [default dataline status enable, connected]
#     all_ch_set_default_power_status_enable_on   55 5A 0D 0F 01 01 1E    55 5A 0D 0F 01 01 1E [all default dataline status enable, connected]

#     ch1_set_default_dataline_status_enable_off  55 5A 0D 01 01 00 0F    55 5A 0D 01 01 01 0F [default dataline status enable, connected]
#     ch2_set_default_dataline_status_enable_off  55 5A 0D 02 01 00 10    55 5A 0D 02 01 01 10 [default dataline status enable, connected]
#     ch3_set_default_dataline_status_enable_off  55 5A 0D 04 01 00 12    55 5A 0D 04 01 01 12 [default dataline status enable, connected]
#     ch4_set_default_dataline_status_enable_off  55 5A 0D 08 01 00 16    55 5A 0D 08 01 01 16 [default dataline status enable, connected]
#     all_ch_set_default_power_status_enable_off  55 5A 0D 0F 01 00 1D    55 5A 0D 0F 01 00 1D [all default dataline status enable, disconnected]

#     ch1_set_default_dataline_status_disable     55 5A 0D 01 00 00 0E    55 5A 0D 01 00 00 0E [default dataline status disable, connected]
#     ch2_set_default_dataline_status_disable     55 5A 0D 02 00 00 0F    55 5A 0D 02 00 00 0F [default dataline status disable, connected]
#     ch3_set_default_dataline_status_disable     55 5A 0D 04 00 00 11    55 5A 0D 04 00 00 11 [default dataline status disable, connected]
#     ch4_set_default_dataline_status_disable     55 5A 0D 08 00 00 15    55 5A 0D 08 00 00 15 [default dataline status disable, connected]
#     all_ch_set_default_dataline_status_disable  55 5A 0D 0F 00 01 1D    55 5A 0D 0F 00 01 1D [all default dataline status disable, connected]

# Get default dataline status [channel,enable,value] protocol_v2
#     ch1_get_default_dataline_status             55 5A 0E 01 00 00 0F            
#                                                                         55 5A 0E 01 00 01 10 [default dataline status disabled, dataline connected]    
#                                                                         55 5A 0E 01 01 00 10 [default dataline status enabled, dataline disconnected]    
#                                                                         55 5A 0E 01 01 01 11 [default dataline status enabled, dataline connected]

#     ch2_get_default_dataline_status             55 5A 0E 02 00 00 10    
#                                                                         55 5A 0E 02 00 01 11 [default dataline status disabled, dataline connected]    
#                                                                         55 5A 0E 02 01 00 11 [default dataline status enabled, dataline disconnected]    
#                                                                         55 5A 0E 02 01 01 12 [default dataline status enabled, dataline connected]

#     ch3_get_default_dataline_status             55 5A 0E 04 00 00 12    
#                                                                         55 5A 0E 04 00 01 13 [default dataline status disabled, dataline connected]    
#                                                                         55 5A 0E 04 01 00 13 [default dataline status enabled, dataline disconnected]    
#                                                                         55 5A 0E 04 00 01 13 [default dataline status enabled, dataline connected]

#     ch4_get_default_dataline_status             55 5A 0E 08 00 00 16    
#                                                                         55 5A 0E 08 00 01 17 [default dataline status disabled, dataline connected]    
#                                                                         55 5A 0E 08 00 01 17 [default dataline status enabled, dataline disconnected]    
#                                                                         55 5A 0E 08 00 01 17 [default dataline status enabled, dataline connected]

#     all_ch_get_default_dataline_status          55 5A 0E 0F 00 00 1D
    
# Set auto restore [0x00,value]
#     enable auto restore                         55 5A 0F 00 01 10   55 5A 0F 00 01 10
#     disable auto restore                        55 5A 0F 00 00 0F   55 5A 0F 00 00 0F

# Get auto restore state                          55 5A 10 00 00 10   
#                                                                     55 5A 10 00 01 11[enable]   
#                                                                     55 5A 10 00 00 10[disable]

# Set Operate Mode [0x00,mode]
#     oper_mode_normal    55 5A 06 00 00 06   55 5A 06 00 00 06
#     oper_mode_interlock 55 5A 06 00 01 07   55 5A 06 00 01 07

# Get Operate Mode        55 5A 07 00 00 07
#                                             55 5A 07 00 00 07 [normal]
#                                             55 5A 07 00 01 08 [interlock]

# Set device address [MSB] [LSB]
#     device address:0x0000     55 5A 11 00 00 11
#     device address:0x0001     55 5A 11 00 01 12
#     device address:0x0002     55 5A 11 00 02 13
#     device address:0x0003     55 5A 11 00 03 14
#     device address:0x1A01     55 5A 11 1A 01 2C

# Get device address
#     55 5A 12 00 00 12
#                         55 5A 12 00 00 12  [device address:0x0000]
#                         55 5A 12 00 01 13  [device address:0x0001]

# Factory Reset           55 5A FC 00 00 FC   55 5A FC 00 00 FC

# Get software version    55 5A FD 00 00 FD   55 5A FD 00 0F 0C

# Get hardware version    55 5A FE 00 00 FE   55 5A FE 00 03 01

import serial
import serial.tools.list_ports
import time
import threading
import signal
import sys
from functools import wraps
import os
import tempfile
import atexit

import logging
import colorlog

# 跨进程文件锁支持
try:
    import fcntl  # Unix/Linux/macOS
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt  # Windows
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

# Command definitions
CMD_GET_CHANNEL_POWER_STATUS        = 0x00
CMD_SET_CHANNEL_POWER               = 0x01

CMD_SET_CHANNEL_POWER_INTERLOCK     = 0x02

CMD_GET_CHANNEL_VOLTAGE             = 0x03
CMD_GET_CHANNEL_CURRENT             = 0x04

CMD_SET_CHANNEL_DATALINE            = 0x05
CMD_GET_CHANNEL_DATALINE_STATUS     = 0x08

CMD_SET_CHANNEL_USB3_DATALINE        = 0x15
CMD_GET_CHANNEL_USB3_DATALINE_STATUS = 0x16

CMD_SET_BUTTON_CONTROL              = 0x09
CMD_GET_BUTTON_CONTROL_STATUS       = 0x0A

CMD_SET_DEFAULT_POWER_STATUS        = 0x0B
CMD_GET_DEFAULT_POWER_STATUS        = 0x0C

CMD_SET_DEFAULT_DATALINE_STATUS     = 0x0D
CMD_GET_DEFAULT_DATALINE_STATUS     = 0x0E

CMD_SET_AUTO_RESTORE                = 0x0F
CMD_GET_AUTO_RESTORE_STATUS         = 0x10

CMD_SET_OPERATE_MODE                = 0x06
CMD_GET_OPERATE_MODE                = 0x07

CMD_SET_DEVICE_ADDRESS              = 0x11
CMD_GET_DEVICE_ADDRESS              = 0x12

CMD_SET_CHANNEL_SLOW_CHARGE         = 0x13
CMD_SET_CHANNEL_FAST_CHARGE         = 0x17
CMD_GET_CHANNEL_CHARGE_MODE         = 0x19

# FlexConnect commands
CMD_SET_FLEXCONNECT_MODE            = 0x20
CMD_GET_FLEXCONNECT_MODE            = 0x21
CMD_GET_FLEXCONNECT_FAULT           = 0x22
CMD_SET_FLEXCONNECT_DEFAULT_MODE    = 0x24
CMD_GET_FLEXCONNECT_DEFAULT_MODE    = 0x25

CMD_REBOOT_MCU                      = 0xF7
CMD_GET_SERIAL_NO                   = 0xF9
CMD_GET_PRODUCT_TYPE                = 0xF0
CMD_GET_MAX_CHANNELS                = 0xF1
CMD_FACTORY_RESET                   = 0xFC   
CMD_GET_FIRMWARE_VERSION            = 0xFD
CMD_GET_HARDWARE_VERSION            = 0xFE

# Channel value definitions
CHANNEL_1 = 0x01
CHANNEL_2 = 0x02
CHANNEL_3 = 0x04
CHANNEL_4 = 0x08

OPERATE_MODE_NORMAL = 0
OPERATE_MODE_INTERLOCK = 1

# FlexConnect mode definitions
FLEXCONNECT_MODE_PC = 0x00         # PC模式（ADB调试）
FLEXCONNECT_MODE_UDISK1 = 0x01     # U盘1模式
FLEXCONNECT_MODE_UDISK2 = 0x02     # U盘2模式
FLEXCONNECT_MODE_DISCONNECT = 0x03 # 断开所有连接模式

# Product type definitions
# 产品类型表：包含产品类型ID、名称、通道数量和功能支持标志
# 功能支持标志说明：
#   - enable_adc: 是否支持电压电流检测 (PRODUCT_ENABLE_CH_ADC)
#   - enable_usb2_data_switch: 是否支持USB2.0数据线切换 (PRODUCT_ENABLE_USB2_DATA_SWITCH)
#   - enable_usb3_data_switch: 是否支持USB3.0数据线切换 (PRODUCT_ENABLE_USB3_DATA_SWITCH)
#   - enable_ilim_switch: 是否支持限流开关/慢充快充模式 (PRODUCT_ENABLE_ILIM_SWITCH)
#   - is_flexconnect: 是否为FlexConnect产品 (PRODUCT_IS_FLEXCONNECT)
PRODUCT_TYPE_TABLE = {
    0x00: {
        "name": "HBP_USB2_4CH",
        "channels": 4,
        "description": "USB2.0 4通道集线器",
        "enable_adc": False,              # 不支持电压电流检测
        "enable_usb2_data_switch": False, # 不支持USB2.0数据线切换
        "enable_usb3_data_switch": False, # 不支持USB3.0数据线切换
        "enable_ilim_switch": False,       # 不支持限流开关
        "is_flexconnect": False,
        "ack_timeout": 0.1                 # ACK超时时间（秒），默认100ms
    },
    0x01: {
        "name": "HBP_USB2_2CH",
        "channels": 2,
        "description": "USB2.0 2通道集线器",
        "enable_adc": False,              # 不支持电压电流检测
        "enable_usb2_data_switch": False, # 不支持USB2.0数据线切换
        "enable_usb3_data_switch": False, # 不支持USB3.0数据线切换
        "enable_ilim_switch": False,       # 不支持限流开关
        "is_flexconnect": False,
        "ack_timeout": 0.1                 # ACK超时时间（秒），默认100ms
    },
    0x02: {
        "name": "HBP_USB3_4CH",
        "channels": 4,
        "description": "USB3.0 4通道集线器",
        "enable_adc": False,              # 不支持电压电流检测
        "enable_usb2_data_switch": True, # 支持USB2.0数据线切换
        "enable_usb3_data_switch": True,  # 支持USB3.0数据线切换
        "enable_ilim_switch": True,        # 支持限流开关（慢充/快充模式）
        "is_flexconnect": False,
        "ack_timeout": 0.1                 # ACK超时时间（秒），默认100ms
    },
    0x03: {
        "name": "FLEX_3CH",
        "channels": 3,
        "description": "FlexConnect 3通道切换器",
        "enable_adc": False,              # 不支持电压电流检测
        "enable_usb2_data_switch": False, # 不支持USB2.0数据线切换（使用MUX）
        "enable_usb3_data_switch": False, # 不支持USB3.0数据线切换（使用MUX）
        "enable_ilim_switch": False,       # 不支持限流开关
        "is_flexconnect": True,            # 是FlexConnect产品
        "ack_timeout": 0.3                 # ACK超时时间（秒），FlexConnect需要更长时间（考虑模式切换延迟）
    }
}

# Configure logging
logger = logging.getLogger(__name__)
# log level
logger.setLevel(logging.ERROR)

# Create console handler with a higher log level
ch = colorlog.StreamHandler()

console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)
ch.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(ch)

# Set this flag to False to disable synchronization locking for testing purposes
ENABLE_SYNC_LOCK = True
# Synchronization decorator for thread-safe serial command methods
def synchronized(method):
    """Decorator to optionally serialize access to SmartUSBHub methods.

    If ENABLE_SYNC_LOCK is True, the decorated method will acquire the instance's lock before
    execution. If it is False, the method will run without acquiring the lock, allowing
    concurrent access for testing.
    """
    @wraps(method)
    def _synchronized(self, *args, **kwargs):
        if ENABLE_SYNC_LOCK:
            # Acquire the instance lock to serialize access
            with self.lock:
                return method(self, *args, **kwargs)
        else:
            # Bypass locking to test behavior without synchronization
            return method(self, *args, **kwargs)
    return _synchronized

class SmartUSBHub:
    """
    SmartUSBHub Lib provides a high-level interface for interacting with an industrial Smart USB Hub via UART.

    This class enables robust per-port control of power and data connections, voltage/current monitoring,
    configuration of default states, and factory resets.

    Suitable for automated test systems and development workflows in hardware engineering environments.
    """
    
    # 类级别的已连接端口跟踪（用于多设备场景）
    _connected_ports = set()
    _connected_addresses = {}  # {port: address} 映射
    # 跨进程文件锁字典 {port: lock_file_handle}
    _port_locks = {}
    _lock_dir = None  # 锁文件目录
    
    @classmethod
    def _get_lock_dir(cls):
        """获取锁文件目录"""
        if cls._lock_dir is None:
            # 使用临时目录存放锁文件
            cls._lock_dir = os.path.join(tempfile.gettempdir(), 'smartusbhub_locks')
            os.makedirs(cls._lock_dir, exist_ok=True)
        return cls._lock_dir
    
    @classmethod
    def _check_process_exists(cls, pid):
        """
        检查进程是否存在（跨平台）
        
        Args:
            pid (int): 进程ID
            
        Returns:
            bool: 如果进程存在返回 True，否则返回 False
        """
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:  # Unix/Linux/macOS
                os.kill(pid, 0)  # 发送信号0，不实际杀死进程，只检查是否存在
                return True
        except (OSError, ProcessLookupError, AttributeError):
            return False
    
    @classmethod
    def _acquire_port_lock(cls, port):
        """
        获取端口的跨进程文件锁
        
        Args:
            port (str): 串口名称
            
        Returns:
            bool: 如果成功获取锁返回 True，否则返回 False
        """
        if port in cls._port_locks:
            # 如果已经持有锁，返回 True
            return True
        
        # 生成锁文件路径（将端口名中的特殊字符替换为安全字符）
        safe_port_name = port.replace('/', '_').replace('\\', '_').replace(':', '_')
        lock_file_path = os.path.join(cls._get_lock_dir(), f'{safe_port_name}.lock')
        
        try:
            # 尝试获取文件锁（非阻塞）
            if HAS_FCNTL:
                # Unix/Linux/macOS 使用 fcntl
                try:
                    # 打开锁文件（如果不存在则创建）
                    lock_file = open(lock_file_path, 'w')
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    cls._port_locks[port] = lock_file
                    # 写入当前进程ID，便于调试
                    lock_file.write(str(os.getpid()))
                    lock_file.flush()
                    logger.debug(f"Acquired file lock for port {port}")
                    return True
                except (IOError, OSError):
                    # 锁已被其他进程持有，检查进程是否还存在
                    if os.path.exists(lock_file_path):
                        try:
                            with open(lock_file_path, 'r') as f:
                                pid_str = f.read().strip()
                                if pid_str.isdigit():
                                    pid = int(pid_str)
                                    if not cls._check_process_exists(pid):
                                        # 进程不存在，清理残留锁文件
                                        logger.debug(f"Cleaning up stale lock file for port {port} (process {pid} no longer exists)")
                                        os.remove(lock_file_path)
                                        # 重试获取锁
                                        lock_file = open(lock_file_path, 'w')
                                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                                        cls._port_locks[port] = lock_file
                                        lock_file.write(str(os.getpid()))
                                        lock_file.flush()
                                        logger.debug(f"Acquired file lock for port {port} after cleanup")
                                        return True
                        except Exception as e:
                            logger.debug(f"Error checking lock file: {e}")
                    if 'lock_file' in locals():
                        lock_file.close()
                    logger.warning(f"Port {port} is locked by another process")
                    return False
            elif HAS_MSVCRT:
                # Windows 使用 msvcrt.locking
                # 注意：msvcrt.locking需要以二进制模式打开文件，并锁定特定字节
                try:
                    # 先检查文件是否存在，如果存在则检查进程是否还在运行
                    if os.path.exists(lock_file_path):
                        try:
                            with open(lock_file_path, 'rb') as f:
                                pid_bytes = f.read(16).strip()  # 读取前16字节（足够存储进程ID）
                                if pid_bytes:
                                    try:
                                        pid = int(pid_bytes.decode().strip())
                                        if not cls._check_process_exists(pid):
                                            # 进程不存在，清理残留锁文件
                                            logger.debug(f"Cleaning up stale lock file for port {port} (process {pid} no longer exists)")
                                            try:
                                                os.remove(lock_file_path)
                                            except:
                                                pass
                                    except (ValueError, UnicodeDecodeError):
                                        pass
                        except Exception as e:
                            logger.debug(f"Error checking lock file: {e}")
                    
                    # 以二进制读写模式打开文件（如果不存在则创建）
                    lock_file = open(lock_file_path, 'a+b')  # 使用追加模式，文件不存在时自动创建
                    lock_file.seek(0)  # 移动到文件开头
                    # 如果文件为空，先写入一个字节
                    if lock_file.tell() == 0 or os.path.getsize(lock_file_path) == 0:
                        lock_file.write(b'0')
                        lock_file.flush()
                    # 锁定文件的第一个字节（非阻塞）
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    cls._port_locks[port] = lock_file
                    # 写入当前进程ID
                    lock_file.seek(0)
                    lock_file.write(str(os.getpid()).encode().ljust(16))  # 左对齐，填充到16字节
                    lock_file.flush()
                    logger.debug(f"Acquired file lock for port {port}")
                    return True
                except IOError as e:
                    # 锁已被其他进程持有
                    if 'lock_file' in locals():
                        try:
                            lock_file.close()
                        except:
                            pass
                    # 检查是否是文件不存在错误（不应该发生，因为我们用了'a+b'模式）
                    if not os.path.exists(lock_file_path):
                        logger.debug(f"Lock file does not exist, retrying: {e}")
                        # 重试一次
                        try:
                            lock_file = open(lock_file_path, 'a+b')
                            lock_file.seek(0)
                            if lock_file.tell() == 0 or os.path.getsize(lock_file_path) == 0:
                                lock_file.write(b'0')
                                lock_file.flush()
                            lock_file.seek(0)
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                            cls._port_locks[port] = lock_file
                            lock_file.seek(0)
                            lock_file.write(str(os.getpid()).encode().ljust(16))
                            lock_file.flush()
                            logger.debug(f"Acquired file lock for port {port} on retry")
                            return True
                        except Exception as retry_e:
                            logger.warning(f"Port {port} is locked by another process (retry failed: {retry_e})")
                            if 'lock_file' in locals():
                                try:
                                    lock_file.close()
                                except:
                                    pass
                            return False
                    else:
                        logger.warning(f"Port {port} is locked by another process: {e}")
                        return False
            else:
                # 不支持文件锁的系统，回退到进程内检查
                logger.warning("File locking not supported on this system, falling back to process-level check")
                return True
        except Exception as e:
            logger.error(f"Failed to acquire lock for port {port}: {e}")
            if 'lock_file' in locals():
                try:
                    lock_file.close()
                except:
                    pass
            return False
    
    @classmethod
    def _release_port_lock(cls, port):
        """
        释放端口的跨进程文件锁
        
        Args:
            port (str): 串口名称
        """
        if port not in cls._port_locks:
            return
        
        lock_file = cls._port_locks.pop(port)
        try:
            if HAS_FCNTL:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif HAS_MSVCRT:
                # Windows: 解锁文件的第一个字节
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            logger.debug(f"Released file lock for port {port}")
        except Exception as e:
            logger.error(f"Failed to release lock for port {port}: {e}")

    def __init__(self, port):
        """
        Initializes the Smart USB Hub.

        Args:
            port (str): The serial port name to connect to the device.
        """
        self.port = port
        self._lock_file = None
        self._lock_file_handle = None
        
        # 检查端口是否已被占用（进程内检查）
        if port in SmartUSBHub._connected_ports:
            raise ValueError(f"Port {port} is already in use by another SmartUSBHub instance. "
                           f"Please disconnect the existing instance first or use a different port.")
        
        # 获取跨进程文件锁
        if not self._acquire_port_lock(port):
            raise ValueError(f"Port {port} is already in use by another process. "
                           f"Please disconnect the existing connection first or use a different port.")
        
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.5)
            # 记录已连接的端口（只有在成功打开串口后才记录）
            SmartUSBHub._connected_ports.add(port)
        except serial.SerialException as e:
            # 如果打开串口失败，释放文件锁
            self._release_port_lock(port)
            if "could not open port" in str(e).lower() or "access is denied" in str(e).lower():
                raise ValueError(f"Port {port} is already in use. Please disconnect the existing connection first.")
            raise
        
        # 默认超时时间，会在获取产品类型后根据产品配置更新
        self.com_timeout = 0.1
        logger.info(f"SmartUSBHub initialized on port {self.port}")

        self.ack_events = {
            CMD_GET_OPERATE_MODE: threading.Event(),
            CMD_SET_OPERATE_MODE: threading.Event(),
            CMD_SET_CHANNEL_POWER: threading.Event(),
            CMD_GET_CHANNEL_POWER_STATUS: threading.Event(),
            CMD_SET_CHANNEL_POWER_INTERLOCK: threading.Event(),
            CMD_GET_CHANNEL_VOLTAGE: threading.Event(),
            CMD_GET_CHANNEL_CURRENT: threading.Event(),
            CMD_SET_CHANNEL_DATALINE: threading.Event(),
            CMD_GET_CHANNEL_DATALINE_STATUS: threading.Event(),
            CMD_SET_CHANNEL_USB3_DATALINE: threading.Event(),
            CMD_GET_CHANNEL_USB3_DATALINE_STATUS: threading.Event(),
            CMD_SET_CHANNEL_SLOW_CHARGE: threading.Event(),
            CMD_SET_CHANNEL_FAST_CHARGE: threading.Event(),
            CMD_GET_CHANNEL_CHARGE_MODE: threading.Event(),
            CMD_SET_BUTTON_CONTROL: threading.Event(),
            CMD_GET_BUTTON_CONTROL_STATUS: threading.Event(),
            CMD_SET_DEFAULT_POWER_STATUS: threading.Event(),
            CMD_GET_DEFAULT_POWER_STATUS: threading.Event(),
            CMD_SET_DEFAULT_DATALINE_STATUS: threading.Event(),
            CMD_GET_DEFAULT_DATALINE_STATUS: threading.Event(),
            CMD_SET_AUTO_RESTORE: threading.Event(),
            CMD_GET_AUTO_RESTORE_STATUS: threading.Event(),
            CMD_SET_DEVICE_ADDRESS: threading.Event(),
            CMD_GET_DEVICE_ADDRESS: threading.Event(),
            CMD_REBOOT_MCU: threading.Event(),
            CMD_GET_PRODUCT_TYPE: threading.Event(),
            CMD_GET_MAX_CHANNELS: threading.Event(),
            CMD_GET_SERIAL_NO: threading.Event(),
            CMD_FACTORY_RESET:threading.Event(),
            CMD_GET_FIRMWARE_VERSION: threading.Event(),
            CMD_GET_HARDWARE_VERSION: threading.Event(),
            # FlexConnect commands
            CMD_SET_FLEXCONNECT_MODE: threading.Event(),
            CMD_GET_FLEXCONNECT_MODE: threading.Event(),
            CMD_GET_FLEXCONNECT_FAULT: threading.Event(),
            CMD_SET_FLEXCONNECT_DEFAULT_MODE: threading.Event(),
            CMD_GET_FLEXCONNECT_DEFAULT_MODE: threading.Event(),
        }
        
        self.lock = threading.Lock()  # 用于串口操作的互斥锁
        
        # 串口发送同步锁（即使 ENABLE_SYNC_LOCK = False 也保护串口发送，避免命令交错）
        self._send_lock = threading.Lock()
        self._last_send_time = 0  # 上次发送命令的时间戳
        # 最小发送间隔：确保命令之间至少间隔一定时间，避免 MCU 状态机混乱
        # 即使 ENABLE_SYNC_LOCK = False，也通过此机制保证串口命令不会交错
        self._min_send_interval = 0.010  # 最小发送间隔 10ms
        # MCU 响应等待时间：发送命令后等待 MCU 开始响应的时间
        # 这确保 MCU 有时间处理命令并开始发送 ACK，实现命令-响应同步
        self._mcu_response_wait = 0.005  # 5ms，让 MCU 有时间处理命令并开始发送 ACK

        self.callbacks = {cmd: None for cmd in self.ack_events.keys()}
        
        self.poweroff_recover = None
        self.hardware_version = None
        self.firmware_version = None
        self.product_type = None
        self.max_channels = None
        self.serial_no = None
        self.operate_mode = None
        self.auto_restore_status = None
        self.button_control_status = None

        self.channel_default_power_flag = {}
        self.channel_default_power_status = {}
        self.channel_default_dataline_flag = {}
        self.channel_default_dataline_status = {}

        self.channel_power_status = {}
        self.channel_dataline_status = {}
        self.channel_usb3_dataline_status = {}
        self.channel_voltages = {}
        self.channel_currents = {}
        self.channel_charge_modes = {}

        # FlexConnect state
        self.flexconnect_mode = None
        self.flexconnect_fault_status = None
        self.flexconnect_default_mode = None

        self.device_address = None

        self.disconnect_callback = None
        
        # 错误恢复机制：跟踪连续失败次数
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5  # 连续5次失败后触发恢复

        self._start()
        # 等待 MCU 状态机恢复（如果之前处于错误状态）
        # MCU 的状态卡住检测是 100ms，超时检测是 20ms，所以等待 150ms 确保恢复
        time.sleep(0.15)
        self.get_device_info()
        
        if self.operate_mode is None:
            logger.error("Failed to get operate mode.")
            # 清理已连接端口记录和串口
            if self.port in SmartUSBHub._connected_ports:
                SmartUSBHub._connected_ports.discard(self.port)
            if self.port in SmartUSBHub._connected_addresses:
                del SmartUSBHub._connected_addresses[self.port]
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except:
                    pass
            sys.exit(1)
        
        # 记录设备地址
        if self.device_address is not None:
            SmartUSBHub._connected_addresses[port] = self.device_address
            
        logger.info(f"Hardware version: V1.{self.hardware_version}")
        logger.info(f"Firmware version: V1.{self.firmware_version}")
        logger.info(f"Operate mode: {'normal' if self.operate_mode == 0 else 'interlock'}")
        logger.info(f"button control: {'enable' if self.button_control_status == 1 else 'disabled'}")

    def register_disconnect_callback(self, callback):
        """
        Registers a callback to be called when the hub is disconnected.
        Args:
            callback (function): The callback function to execute on disconnect.
        """
        self.disconnect_callback = callback


    def register_callback(self, cmd, callback):
        """
        Registers a user callback for a specific command.

        Args:
            cmd (int): The command for which the callback is registered.
            callback (function): The callback function to execute when the command's ACK is received.
        """
        if cmd in self.callbacks:
            self.callbacks[cmd] = callback
            logger.info(f"Callback registered for command: {cmd:#04x}")
        else:
            logger.warning(f"Invalid command: {cmd:#04x}. Cannot register callback.")
    
    def _invoke_callback(self, cmd, *args, **kwargs):
        """
        Invokes the user callback for a specific command, if registered.

        Args:
            cmd (int): The command for which the callback is invoked.
            *args: Positional arguments to pass to the callback.
            **kwargs: Keyword arguments to pass to the callback.
        """
        if cmd in self.callbacks and self.callbacks[cmd]:
            try:
                self.callbacks[cmd](*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback for command {cmd:#04x}: {e}")
                
    @staticmethod
    def get_product_info(product_type_id):
        """
        从产品类型ID获取产品信息。
        
        Args:
            product_type_id (int): 产品类型ID（0x00-0x03）
            
        Returns:
            dict or None: 包含产品信息的字典，如果产品类型ID无效则返回None。
            字典包含以下键：
                - name: 产品名称（如 "HBP_USB2_4CH"）
                - channels: 通道数量
                - description: 产品描述
                - enable_adc: 是否支持电压电流检测
                - enable_usb2_data_switch: 是否支持USB2.0数据线切换
                - enable_usb3_data_switch: 是否支持USB3.0数据线切换
                - enable_ilim_switch: 是否支持限流开关（慢充/快充模式）
                - is_flexconnect: 是否为FlexConnect产品
                
        Example:
            >>> info = SmartUSBHub.get_product_info(0x00)
            >>> print(info['name'])  # "HBP_USB2_4CH"
            >>> print(info['channels'])  # 4
            >>> print(info['enable_adc'])  # False
        """
        return PRODUCT_TYPE_TABLE.get(product_type_id)
    
    def _check_feature_support(self, feature_name):
        """
        检查当前设备是否支持指定功能。
        
        Args:
            feature_name (str): 功能名称，可选值：
                - "adc": 电压电流检测
                - "usb2_data_switch": USB2.0数据线切换
                - "usb3_data_switch": USB3.0数据线切换
                - "ilim_switch": 限流开关（慢充/快充模式）
                - "flexconnect": FlexConnect产品
        
        Returns:
            bool: 如果支持该功能返回True，否则返回False
            
        Raises:
            ValueError: 如果产品类型未知或功能名称无效
        """
        if self.product_type is None:
            # 如果产品类型未知，尝试获取
            self.product_type = self.get_product_type()
        
        if self.product_type is None:
            raise ValueError("Product type is unknown. Cannot check feature support.")
        
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        if product_info is None:
            raise ValueError(f"Unknown product type: {self.product_type:#02x}")
        
        feature_map = {
            "adc": "enable_adc",
            "usb2_data_switch": "enable_usb2_data_switch",
            "usb3_data_switch": "enable_usb3_data_switch",
            "ilim_switch": "enable_ilim_switch",
            "flexconnect": "is_flexconnect"
        }
        
        if feature_name not in feature_map:
            raise ValueError(f"Unknown feature name: {feature_name}. Valid features: {list(feature_map.keys())}")
        
        return product_info.get(feature_map[feature_name], False)
    
    @classmethod
    def scan_available_ports(cls):
        """
        Scan for all available serial ports and return a list of port names
        that match specific VID and PID.
        """
        ports = serial.tools.list_ports.comports()
        port_list = []

        for port in ports:
            if port.vid == 0x1A86 and port.pid == 0xfe0c:
                port_list.append(port.device)

        return port_list
    
    @classmethod
    def scan_and_connect(cls, exclude_ports=None, device_address=None):
        """
        Searches for available Smart USB Hub devices and connects to the first valid one.
        
        Args:
            exclude_ports (set, optional): 要排除的端口集合（已连接的端口）。如果为None，自动排除已连接的端口。
            device_address (int, optional): 要连接的设备地址。如果指定，会尝试连接所有未连接的设备，直到找到匹配地址的设备。
                                            **注意**: 由于设备地址默认为0，多个设备可能地址相同，建议使用端口号来区分设备。

        Returns:
            SmartUSBHub or None: An instance of SmartUSBHub if found, otherwise None.
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()
        
        for port_info in serial.tools.list_ports.comports():
            port_name = port_info.device
            
            # 跳过已连接的端口
            if port_name in exclude_ports:
                logger.debug(f"Skipping already connected port {port_name}")
                continue
            
            logger.debug(f"Trying to connect to port {port_name}")
            if port_info.vid == 0x1A86 and port_info.pid == 0xfe0c:
                try:
                    hub = cls(port_name)
                    port_suffix = port_name.split("/")[-1]
                    hub.name = f"smarthub_id:{port_suffix}"
                    
                    # 如果指定了设备地址，检查是否匹配
                    # 注意：设备地址默认为0，多个设备可能地址相同，所以此方法可能不够准确
                    if device_address is not None:
                        if hub.device_address != device_address:
                            logger.debug(f"Device address mismatch on port {port_name}: expected {device_address:#04x}, got {hub.device_address:#04x}")
                            hub.disconnect()
                            continue
                        else:
                            logger.info(f"Found device with address {device_address:#04x} on port {port_name}")
                    
                    return hub
                except (ValueError, serial.SerialException) as e:
                    logger.warning(f"Failed to connect to {port_name}: {e}")
                    continue

        if device_address is not None:
            logger.warning(f"No Smart USB Hub found with address {device_address:#04x}, or all devices are already connected.")
        else:
            logger.warning("No Smart USB Hub found, or all devices are already connected.")
        return None
    
    @classmethod
    def scan_and_connect_by_address(cls, device_address):
        """
        通过设备地址连接指定的Smart USB Hub设备。
        
        **警告**: 由于设备地址默认为0，多个设备可能地址相同，此方法可能不够准确。
        建议使用 `scan_and_connect()` 并通过端口号来区分设备，或者先为每个设备设置不同的地址。
        
        Args:
            device_address (int): 要连接的设备地址（0x0000 - 0xFFFF）。
        
        Returns:
            SmartUSBHub or None: 如果找到匹配地址的设备则返回实例，否则返回None。
        """
        return cls.scan_and_connect(device_address=device_address)
    
    @classmethod
    def auto_connect(cls, exclude_ports=None, feature_filter=None):
        """
        自动扫描并连接第一个可用的Smart USB Hub设备。
        如果第一个设备被占用或连接失败，会自动尝试下一个设备，直到找到可用的设备。
        
        Args:
            exclude_ports (set, optional): 要排除的端口集合（已连接的端口）。如果为None，自动排除已连接的端口。
            feature_filter (str, optional): 功能过滤器。如果指定，只连接支持该功能的设备。
                可选值: "adc", "usb2_data_switch", "usb3_data_switch", "ilim_switch", "flexconnect"
        
        Returns:
            SmartUSBHub or None: 如果找到可用的设备则返回实例，否则返回None。
        
        Example:
            >>> # 连接任何可用的设备
            >>> hub = SmartUSBHub.auto_connect()
            
            >>> # 只连接FlexConnect设备
            >>> hub = SmartUSBHub.auto_connect(feature_filter="flexconnect")
            
            >>> # 排除已连接的端口
            >>> hub = SmartUSBHub.auto_connect(exclude_ports={"COM8"})
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()
        
        ports = cls.scan_available_ports()
        if not ports:
            logger.warning("No Smart USB Hub devices found")
            return None
        
        logger.info(f"Found {len(ports)} device(s): {ports}")
        
        for port in ports:
            # 跳过已连接的端口
            if port in exclude_ports:
                logger.debug(f"Skipping already connected port {port}")
                continue
            
            logger.info(f"Trying to connect to {port}...")
            try:
                hub = cls(port)
                logger.info(f"Successfully connected to {port}")
                
                # 如果指定了功能过滤器，检查设备是否支持该功能
                if feature_filter is not None:
                    if not hub._check_feature_support(feature_filter):
                        logger.info(f"Device on {port} does not support feature '{feature_filter}', trying next device...")
                        hub.disconnect()
                        continue
                    logger.info(f"Device on {port} supports feature '{feature_filter}'")
                
                return hub
            except ValueError as e:
                # 端口被占用或其他ValueError，尝试下一个
                if "already in use" in str(e).lower() or "already in use by another" in str(e).lower():
                    logger.info(f"Port {port} is already in use, trying next device...")
                else:
                    logger.warning(f"Failed to connect to {port}: {e}, trying next device...")
                continue
            except serial.SerialException as e:
                # 串口异常，尝试下一个
                logger.warning(f"Serial exception on {port}: {e}, trying next device...")
                continue
            except Exception as e:
                # 其他异常，尝试下一个
                logger.warning(f"Unexpected error connecting to {port}: {e}, trying next device...")
                continue
        
        logger.warning("All devices are unavailable (occupied or connection failed)")
        return None
    
    def _start(self):
        """
        Starts background threads and signal handlers for UART communication and SIGINT handling.
        """
        self.stop_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        self.uart_recv_thread = threading.Thread(target=self._uart_recv_task)
        self.uart_recv_thread.start()
    
    def disconnect(self):
        """
        Disconnects from the device and stops the UART receive thread.
        """
        self.stop_event.set()
        if hasattr(self, 'uart_recv_thread'):
            self.uart_recv_thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.flush()
            self.ser.close()
        
        # 从已连接端口列表中移除
        if self.port in SmartUSBHub._connected_ports:
            SmartUSBHub._connected_ports.discard(self.port)
        if self.port in SmartUSBHub._connected_addresses:
            del SmartUSBHub._connected_addresses[self.port]
        
        # 释放跨进程文件锁
        self._release_port_lock(self.port)
    def is_connected(self):
        """
        Check if the device's serial port is connected and open.

        Returns:
            bool: True if the serial port is open, False otherwise.
        """
        return self.ser.is_open if self.ser else False

    def _signal_handler(self, sig, frame):
        """
        Handles termination signals to cleanly shut down the UART thread and close the serial port.

        Args:
            sig (int): Signal number.
            frame (frame object): Current stack frame.
        """
        self.stop_event.set()
        self.uart_recv_thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.flush()
            self.ser.close()
        sys.exit(0)

    def _cal_crc16(self, data):
        """
        Calculate CRC16 (polynomial: 0x8005, initial: 0xFFFF)
        
        Args:
            data (bytes): Data to calculate CRC16 for
            
        Returns:
            int: CRC16 value
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x8005
                else:
                    crc = crc >> 1
        return crc & 0xFFFF

    def _parse_protocol_frame(self, data):
        """
        Processes a raw data frame from the device and delivers it to the correct handler.
        Supports V1, V2, and V3 protocols.

        Args:
            data (bytes): Raw bytes read from the device.

        Returns:
            tuple or None: Parsed command, channel, value, and length if valid, otherwise None.
            For V3 protocol: returns (cmd, 0, data_string, total_length)
        """

        # logger.debug(f"Received data: {data.hex()}")

        if len(data) < 6:
            return None

        # Check for V3 protocol (0x55 0xAB)
        if data[0] == 0x55 and data[1] == 0xAB:
            # V3 protocol format: [0x55, 0xAB, CRC16(2), cmd(2), length(2), data...]
            if len(data) < 8:  # Minimum header size
                return None
            
            # Read CRC16, cmd, and length (all little-endian)
            received_crc16 = data[2] | (data[3] << 8)
            cmd = data[4] | (data[5] << 8)
            data_length = data[6] | (data[7] << 8)
            
            # Check if we have enough data
            total_length = 8 + data_length
            if len(data) < total_length:
                return None
            
            # Calculate CRC16 for: cmd(2) + length(2) + data(data_length)
            crc_data = data[4:4+2+2+data_length]  # cmd + length + data
            calculated_crc16 = self._cal_crc16(crc_data)
            
            if calculated_crc16 != received_crc16:
                logger.debug(f"Invalid CRC16 for V3 protocol: calculated={calculated_crc16:04X}, received={received_crc16:04X}")
                return None
            
            # Extract data as string
            data_bytes = data[8:8+data_length]
            data_string = data_bytes.decode('utf-8', errors='ignore')
            
            logger.debug(f"Received V3 protocol: cmd={cmd:04X}, length={data_length}, data={data_string}")
            return (cmd, 0, data_string, total_length)
        
        # V1/V2 protocol (0x55 0x5A)
        if data[0] != 0x55 or data[1] != 0x5A:
            return None

        cmd = data[2]
        channel = data[3]

        if cmd in [CMD_GET_CHANNEL_VOLTAGE,
                    CMD_GET_CHANNEL_CURRENT,
                    CMD_SET_DEFAULT_POWER_STATUS,
                    CMD_SET_DEFAULT_DATALINE_STATUS,
                    CMD_GET_DEFAULT_POWER_STATUS,
                    CMD_GET_DEFAULT_DATALINE_STATUS]:
           
            logger.debug(f"Received protocol_v2 data for channel {self._convert_channel(channel)}")
            if len(data) < 7:
                return None
            value_0 = data[4]
            value_1 = data[5]
            checksum = data[6]
            cal_sum = (cmd + channel + value_0 + value_1) & 0xFF
            if cal_sum != checksum:
                logger.debug(f"Invalid checksum for protocol_v2 data for channel {channel},cal:{cal_sum},recv:{checksum}")
                return None
            # Combine two bytes into a single value
            return (cmd, channel, [value_0,value_1], 7)
        else:
            value = data[4]
            checksum = data[5]
            if ((cmd + channel + value) & 0xFF) != checksum:
                return None
            return (cmd, channel, value, 6)

    def _uart_recv_task(self):
        """
        Continuously reads from the UART and processes incoming data frames.
        """
        buffer = bytearray()
        while not self.stop_event.is_set():
            try:
                if self.ser is not None and self.ser.in_waiting > 0:
                    buffer.extend(self.ser.read(self.ser.in_waiting))
                    logger.debug(f"rx data: {buffer.hex()}")
                    # Check for V3 protocol minimum size (8 bytes) or V1/V2 (6 bytes)
                    min_size = 8 if len(buffer) >= 8 and buffer[0] == 0x55 and buffer[1] == 0xAB else 6
                    while len(buffer) >= min_size:
                        result = self._parse_protocol_frame(buffer)
                        if result is not None:
                            cmd, channel, value, length = result

                            logger.debug(f"Parsed CMD: {cmd:#04x}, Channel: {channel:#04x}, Value: {value}, Raw buffer: {buffer[:length].hex()}")

                            if cmd == CMD_SET_CHANNEL_POWER:
                                self._handle_set_channel_power_status()
                            if cmd == CMD_GET_CHANNEL_POWER_STATUS:
                                self._handle_get_channel_power_status(channel, value)
                            if cmd == CMD_SET_CHANNEL_POWER_INTERLOCK:
                                self._handle_power_interlock_control()
                            elif cmd == CMD_GET_CHANNEL_VOLTAGE:
                                self._handle_get_channel_voltage(channel, value)
                            elif cmd == CMD_GET_CHANNEL_CURRENT:
                                self._handle_get_channel_current(channel, value)
                            elif cmd == CMD_SET_CHANNEL_DATALINE:
                                self._handle_set_channel_dataline(channel, value)
                            elif cmd == CMD_GET_CHANNEL_DATALINE_STATUS:
                                self._handle_get_channel_dataline(channel, value)
                            elif cmd == CMD_SET_CHANNEL_USB3_DATALINE:
                                self._handle_set_channel_usb3_dataline(channel, value)
                            elif cmd == CMD_GET_CHANNEL_USB3_DATALINE_STATUS:
                                self._handle_get_channel_usb3_dataline(channel, value)
                            elif cmd == CMD_SET_CHANNEL_SLOW_CHARGE:
                                self._handle_set_channel_slow_charge(channel, value)
                            elif cmd == CMD_SET_CHANNEL_FAST_CHARGE:
                                self._handle_set_channel_fast_charge(channel, value)
                            elif cmd == CMD_GET_CHANNEL_CHARGE_MODE:
                                self._handle_get_channel_charge_mode(channel, value)
                            elif cmd == CMD_SET_BUTTON_CONTROL:
                                self._handle_set_button_control()
                            elif cmd == CMD_GET_BUTTON_CONTROL_STATUS:
                                self._handle_get_button_control(value)
                            elif cmd == CMD_SET_DEFAULT_POWER_STATUS:
                                self._handle_set_default_power_status(channel,value)
                            elif cmd == CMD_GET_DEFAULT_POWER_STATUS:
                                self._handle_get_default_power_status(channel,value)
                            elif cmd == CMD_SET_DEFAULT_DATALINE_STATUS:
                                self._handle_set_default_dataline_status(channel,value)
                            elif cmd == CMD_GET_DEFAULT_DATALINE_STATUS:
                                self._handle_get_default_dataline_status(channel,value)
                            elif cmd == CMD_SET_AUTO_RESTORE:
                                self._handle_set_auto_restore()
                            elif cmd == CMD_GET_AUTO_RESTORE_STATUS:
                                self._handle_get_auto_restore_status(value)
                            elif cmd == CMD_GET_OPERATE_MODE:
                                self._handle_get_operate_mode(value)
                            elif cmd == CMD_SET_OPERATE_MODE:
                                self._handle_set_operate_mode()
                            elif cmd == CMD_SET_DEVICE_ADDRESS:
                                self._handle_set_device_address()
                            elif cmd == CMD_GET_DEVICE_ADDRESS:
                                self._handle_get_device_address(channel,value)#msb lsb
                            elif cmd == CMD_REBOOT_MCU:
                                self._handle_reboot_mcu()
                            elif cmd == CMD_FACTORY_RESET:
                                self._handle_factory_reset()
                            elif cmd == CMD_GET_FIRMWARE_VERSION:
                                self._handle_firmware_version(value)
                            elif cmd == CMD_GET_HARDWARE_VERSION:
                                self._handle_hardware_version(value)
                            elif cmd == CMD_GET_PRODUCT_TYPE:
                                self._handle_product_type(value)
                            elif cmd == CMD_GET_MAX_CHANNELS:
                                logger.debug(f"CMD_GET_MAX_CHANNELS received: cmd={cmd:#04x}, channel={channel:#04x}, value={value}")
                                self._handle_get_max_channels(value)
                            elif cmd == CMD_GET_SERIAL_NO:
                                self._handle_serial_no(value)
                            elif cmd == CMD_SET_FLEXCONNECT_MODE:
                                self._handle_set_flexconnect_mode(value)
                            elif cmd == CMD_GET_FLEXCONNECT_MODE:
                                self._handle_get_flexconnect_mode(value)
                            elif cmd == CMD_GET_FLEXCONNECT_FAULT:
                                self._handle_get_flexconnect_fault(value)
                            elif cmd == CMD_SET_FLEXCONNECT_DEFAULT_MODE:
                                self._handle_set_flexconnect_default_mode()
                            elif cmd == CMD_GET_FLEXCONNECT_DEFAULT_MODE:
                                self._handle_get_flexconnect_default_mode(value)
                            if cmd in self.ack_events:
                                self._invoke_callback(cmd,channel,value)
                                self.ack_events[cmd].set()

                            del buffer[:length]
                        else:
                            buffer.pop(0)
            except (OSError, AttributeError,serial.SerialException) as e:
                # 检查是否是预期的断开（设备重启等）
                # errno 6 = ENXIO (Device not configured) 通常表示设备已断开
                # 如果 stop_event 已经设置，说明是主动断开，不应该记录为错误
                is_expected_disconnect = False
                if isinstance(e, OSError) and hasattr(e, 'errno'):
                    # errno 6 (ENXIO) 通常表示设备已断开，这在设备重启时是预期的
                    if e.errno == 6:  # Device not configured
                        is_expected_disconnect = True
                
                # 如果 stop_event 已经设置，说明是主动断开（disconnect() 被调用）
                if self.stop_event.is_set():
                    is_expected_disconnect = True
                
                if is_expected_disconnect:
                    logger.debug(f"UART disconnected (expected): {e}")
                else:
                    logger.error(f"Error reading from UART: {e}")
                
                self.ser = None
                if self.disconnect_callback:
                    self.disconnect_callback()
                self.stop_event.set()
                
                if not is_expected_disconnect:
                    logger.error("UART disconnected")
                break
            time.sleep(0.01)

    def _convert_channel(self, channel_mask):
        """
        Converts a channel bitmask into a list of individual channel numbers.

        Args:
            channel_mask (int): Bitmask representing which channels are included.

        Returns:
            list: A list of channel numbers (1, 2, 3, 4).
        """
        channels = []
        if channel_mask & CHANNEL_1:
            channels.append(1)
        if channel_mask & CHANNEL_2:
            channels.append(2)
        if channel_mask & CHANNEL_3:
            channels.append(3)
        if channel_mask & CHANNEL_4:
            channels.append(4)
        return channels

    def _send_packet(self, cmd, channels, data=None):
        """
        Builds and sends a packet to the device.

        Args:
            cmd (int): Command byte.
            channels (list[int]): List of channel numbers to include in the packet.
            data (list[int] or None): Extra data bytes to include.

        Returns:
            bytearray: The packet that was sent to the device.
        """
        if cmd is CMD_SET_DEVICE_ADDRESS:
            channel_mask = channels
        elif channels is None:
            channel_mask = 0
        else:
            # Convert channels to channel mask
            channel_mask = sum([1 << (ch - 1) for ch in channels])

        # Clean and normalize data
        if data is None:
            data = [0x00]
        elif not isinstance(data, list):
            data = [data]
        
        # Combine channel mask and data
        payload = [channel_mask] + data

        # Start with header bytes
        packet = bytearray([0x55, 0x5A, cmd])

        # Add data bytes
        packet.extend(payload)

        # Calculate checksum (cmd + all data bytes) & 0xFF
        checksum = (cmd + sum(payload)) & 0xFF

        # Add checksum to packet
        packet.append(checksum)

        # 串口发送同步：即使 ENABLE_SYNC_LOCK = False，也保护串口发送避免命令交错
        # 同时确保命令之间有最小间隔，并等待 MCU 响应（实现命令-响应同步）
        with self._send_lock:
            # 确保命令之间有最小间隔
            current_time = time.time()
            time_since_last_send = current_time - self._last_send_time
            if time_since_last_send < self._min_send_interval:
                # 如果距离上次发送时间太短，等待到最小间隔
                time.sleep(self._min_send_interval - time_since_last_send)
            
            # Send the packet
            if self.ser and self.ser.is_open:
                self.ser.write(packet)
            
            # 记录发送时间
            self._last_send_time = time.time()
            
            # 等待 MCU 开始响应（给 MCU 时间处理命令并开始发送 ACK）
            # 这是与 MCU 之间的同步机制：确保 MCU 有时间处理命令后再发送下一个
            time.sleep(self._mcu_response_wait)
            
            logger.debug(f"Sent command: {packet.hex()}")

        return packet
    
    def _wait_for_ack_with_recovery(self, cmd, timeout=None):
        """
        等待 ACK，如果连续失败则触发 MCU 状态机恢复机制。
        
        Args:
            cmd: 命令代码
            timeout: 超时时间，如果为 None 则使用 self.com_timeout
            
        Returns:
            bool: 如果收到 ACK 返回 True，否则返回 False
        """
        if timeout is None:
            timeout = self.com_timeout
        
        ack_event = self.ack_events.get(cmd)
        if not ack_event:
            return False
        
        # 先检查事件是否已经设置（ACK可能已经到达）
        if ack_event.is_set():
            # ACK已经到达，清除事件并返回成功
            ack_event.clear()
            self._consecutive_failures = 0
            return True
        
        # 清除事件，准备等待新的ACK
        ack_event.clear()
        # 再次检查（防止在clear()之后立即到达的ACK）
        time.sleep(0.001)  # 极短延迟，让可能的残留ACK到达
        if ack_event.is_set():
            # 残留ACK到达，清除并返回成功
            ack_event.clear()
            self._consecutive_failures = 0
            return True
        
        # 等待新的ACK
        success = ack_event.wait(timeout)
        
        if success:
            # 成功时重置失败计数
            self._consecutive_failures = 0
            return True
        else:
            # 失败时增加计数
            self._consecutive_failures += 1
            
            # 如果连续失败次数超过阈值，触发恢复机制
            if self._consecutive_failures >= self._max_consecutive_failures:
                logger.warning(f"Too many consecutive failures ({self._consecutive_failures}), triggering MCU recovery...")
                self._trigger_mcu_recovery()
                # 重置失败计数，给 MCU 一次恢复的机会
                self._consecutive_failures = 0
            
            return False
    
    def _trigger_mcu_recovery(self):
        """
        触发 MCU 状态机恢复机制：
        1. 等待足够时间让 MCU 自动恢复（MCU 的状态卡住检测是 100ms，超时检测是 20ms）
        2. 清空串口缓冲区
        """
        logger.debug("Triggering MCU state machine recovery...")
        time.sleep(0.15)  # 等待 150ms 让 MCU 状态机恢复
        
        # 清空输入缓冲区
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    self.ser.reset_input_buffer()
                    logger.debug("Cleared input buffer during recovery")
            except Exception as e:
                logger.warning(f"Failed to clear input buffer: {e}")

    def _handle_set_operate_mode(self):
        logger.debug("_handle_set_operate_mode ACK")

    def _handle_get_operate_mode(self, value):
        logger.debug("_handle_get_operate_mode ACK")
        self.operate_mode = value

    def _handle_set_channel_power_status(self):
        logger.debug("_handle_set_channel_power_status ACK")
        self.ack_events[CMD_SET_CHANNEL_POWER].set()

    def _handle_get_channel_power_status(self, channel, value):
        logger.debug("_handle_get_channel_power_status ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_power_status[ch] = value
            logger.info(f"CMD_GET_CHANNEL_POWER_STATUS acked: ch{ch} = {value}")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_GET_CHANNEL_POWER_STATUS].set()

    def _handle_power_interlock_control(self):
        logger.debug("_handle_power_interlock_control ACK")

    def _handle_get_channel_voltage(self, channel, value):
        logger.debug("_handle_get_channel_voltage ACK")
        if isinstance(value, list) and len(value) == 2:
            value_int = (value[0] << 8) | value[1]
            channels = self._convert_channel(channel)
            for ch in channels:
                self.channel_voltages[ch] = value_int
                logger.debug(f"Get Channel Voltage: ch{ch} = {value_int}")
        else:
            logger.error("Invalid voltage value received")

    def _handle_get_channel_current(self, channel, value):
        logger.debug("_handle_get_channel_current ACK")
        if isinstance(value, list) and len(value) == 2:
            value_int = (value[0] << 8) | value[1]
            channels = self._convert_channel(channel)
            for ch in channels:
                self.channel_currents[ch] = value_int
                logger.debug(f"Get Channel Current: ch{ch} = {value_int}")
        else:
            logger.error("Invalid current value received")

    def _handle_set_channel_dataline(self, channel, value):
        logger.debug("_handle_set_channel_dataline ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_dataline_status[ch] = value
            logger.debug(f"Set Channel Dataline: ch{ch} = {value}")

    def _handle_get_channel_dataline(self, channel, value):
        logger.debug("_handle_get_channel_dataline ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_dataline_status[ch] = value
            logger.debug(f"Get Channel Dataline: ch{ch} = {value}")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_GET_CHANNEL_DATALINE_STATUS].set()

    def _handle_set_channel_usb3_dataline(self, channel, value):
        logger.debug("_handle_set_channel_usb3_dataline ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_usb3_dataline_status[ch] = value
            logger.debug(f"Set Channel USB3 Dataline: ch{ch} = {value}")

    def _handle_get_channel_usb3_dataline(self, channel, value):
        logger.debug("_handle_get_channel_usb3_dataline ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_usb3_dataline_status[ch] = value
            logger.debug(f"Get Channel USB3 Dataline: ch{ch} = {value}")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_GET_CHANNEL_USB3_DATALINE_STATUS].set()

    def _handle_set_channel_slow_charge(self, channel, value):
        logger.debug("_handle_set_channel_slow_charge ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            logger.debug(f"Set Channel Slow Charge: ch{ch} = enabled")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_SET_CHANNEL_SLOW_CHARGE].set()

    def _handle_set_channel_fast_charge(self, channel, value):
        logger.debug("_handle_set_channel_fast_charge ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            logger.debug(f"Set Channel Fast Charge: ch{ch} = enabled")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_SET_CHANNEL_FAST_CHARGE].set()

    def _handle_get_channel_charge_mode(self, channel, value):
        logger.debug("_handle_get_channel_charge_mode ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_charge_modes[ch] = value
            mode_str = "off" if value == 0 else ("fast_charge" if value == 1 else "slow_charge")
            logger.debug(f"Get Channel Charge Mode: ch{ch} = {mode_str} ({value})")
        # 设置事件，通知等待的线程
        self.ack_events[CMD_GET_CHANNEL_CHARGE_MODE].set()

    def _handle_get_button_control(self, value):
        logger.debug("_handle_get_button_control ACK")
        self.button_control_status = value

    def _handle_set_button_control(self):
        logger.debug("_handle_set_button_control ACK")

    def _handle_set_default_power_status(self,channel,value):
        logger.debug("_handle_set_default_power_status ACK")
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            channels = self._convert_channel(channel)
            # 防御性检查：确保字典已初始化
            if self.channel_default_power_flag is None:
                self.channel_default_power_flag = {}
            if self.channel_default_power_status is None:
                self.channel_default_power_status = {}
            for ch in channels:
                self.channel_default_power_flag[ch] = enable
                self.channel_default_power_status[ch] = status
                logger.debug(f"Channel {ch} {'enable' if enable else 'disable'} default power status, value: {'on' if status else 'off'}")
        else:
            logger.error("Invalid data for _handle_set_default_power_status")
    
    def _handle_get_default_power_status(self,channel,value):
        logger.debug("_handle_get_default_power_status ACK")
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            channels = self._convert_channel(channel)
            # 防御性检查：确保字典已初始化
            if self.channel_default_power_flag is None:
                self.channel_default_power_flag = {}
            if self.channel_default_power_status is None:
                self.channel_default_power_status = {}
            for ch in channels:
                self.channel_default_power_flag[ch] = enable
                self.channel_default_power_status[ch] = status
                logger.debug(f"Channel {ch} {'enable' if enable else 'disable'} default power status, value: {'on' if status else 'off'}")
        else:
            logger.error("Invalid data for _handle_get_default_power_status")

    def _handle_set_default_dataline_status(self,channel,value):
        logger.debug("_handle_set_default_dataline_status ACK")
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            channels = self._convert_channel(channel)
            # 防御性检查：确保字典已初始化
            if self.channel_default_dataline_flag is None:
                self.channel_default_dataline_flag = {}
            if self.channel_default_dataline_status is None:
                self.channel_default_dataline_status = {}
            for ch in channels:
                self.channel_default_dataline_flag[ch] = enable
                self.channel_default_dataline_status[ch] = status
                logger.debug(f"Channel {ch} {'enable' if enable else 'disable'} default dataline status, value: {'on' if status else 'off'}")
        else:
            logger.error("Invalid data for _handle_set_default_dataline_status")
    
    def _handle_get_default_dataline_status(self,channel,value):
        logger.debug("_handle_get_default_dataline_status ACK")
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            channels = self._convert_channel(channel)
            # 防御性检查：确保字典已初始化
            if self.channel_default_dataline_flag is None:
                self.channel_default_dataline_flag = {}
            if self.channel_default_dataline_status is None:
                self.channel_default_dataline_status = {}
            for ch in channels:
                self.channel_default_dataline_flag[ch] = enable
                self.channel_default_dataline_status[ch] = status
                logger.debug(f"Channel {ch} {'enable' if enable else 'disable'} default dataline status, value: {'on' if status else 'off'}")
        else:
            logger.error("Invalid data for _handle_get_default_dataline_status")

    def _handle_set_device_address(self):
        logger.debug("_handle_set_device_address ACK")
    def _handle_get_device_address(self, msb,lsb):
        logger.debug("_handle_get_device_address ACK")
        self.device_address = (msb << 8) | lsb
        logger.debug(f"set device address: {self.device_address}")
    
    def _handle_reboot_mcu(self):
        logger.debug("_handle_reboot_mcu ACK")

    def _handle_factory_reset(self):
        logger.debug("_handle_factory_reset ACK")

    def _handle_firmware_version(self, value):
        logger.debug("_handle_firmware_version ACK")
        self.firmware_version = value

    def _handle_hardware_version(self, value):
        logger.debug("_handle_hardware_version ACK")
        self.hardware_version = value

    def _handle_product_type(self, value):
        logger.debug("_handle_product_type ACK")
        self.product_type = value

    def _handle_get_max_channels(self, value):
        logger.debug(f"_handle_get_max_channels ACK, value={value}")
        # 检查value是否合理（通道数量应该在1-16之间）
        if value == 0xFF or value > 16:
            logger.warning(f"Received suspicious max_channels value: {value} (0x{value:02X}). This might indicate an error response from the device.")
            # 如果返回0xFF，说明设备固件可能不支持此命令，尝试从产品类型推断
            if value == 0xFF and self.product_type is not None:
                product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
                if product_info is not None:
                    inferred_channels = product_info["channels"]
                    logger.info(f"Device firmware doesn't support CMD_GET_MAX_CHANNELS. Inferring max_channels={inferred_channels} from product_type={self.product_type} ({product_info['name']})")
                    self.max_channels = inferred_channels
                    return
            # 如果无法推断，保持原值（可能是0xFF）
            self.max_channels = value
        else:
            self.max_channels = value

    def _handle_serial_no(self, value):
        logger.debug("_handle_serial_no ACK")
        # value is a string for V3 protocol
        if isinstance(value, str):
            self.serial_no = value
        else:
            self.serial_no = None

    def _handle_set_flexconnect_mode(self, value):
        logger.debug("_handle_set_flexconnect_mode ACK")
        # value is the mode returned by the device (0=PC, 1=UDISK1, 2=UDISK2, 3=DISCONNECT, 0xFF=error)
        if value != 0xFF:
            self.flexconnect_mode = value
            if value == FLEXCONNECT_MODE_PC:
                mode_str = "PC"
            elif value == FLEXCONNECT_MODE_UDISK1:
                mode_str = "UDISK1"
            elif value == FLEXCONNECT_MODE_UDISK2:
                mode_str = "UDISK2"
            elif value == FLEXCONNECT_MODE_DISCONNECT:
                mode_str = "DISCONNECT"
            else:
                mode_str = f"Unknown({value})"
            logger.info(f"FlexConnect mode set to: {mode_str} ({value})")
        else:
            logger.error("FlexConnect mode set failed (device returned 0xFF)")

    def _handle_get_flexconnect_mode(self, value):
        logger.debug("_handle_get_flexconnect_mode ACK")
        self.flexconnect_mode = value
        if value == FLEXCONNECT_MODE_PC:
            mode_str = "PC"
        elif value == FLEXCONNECT_MODE_UDISK1:
            mode_str = "UDISK1"
        elif value == FLEXCONNECT_MODE_UDISK2:
            mode_str = "UDISK2"
        elif value == FLEXCONNECT_MODE_DISCONNECT:
            mode_str = "DISCONNECT"
        else:
            mode_str = f"Unknown({value})"
        logger.debug(f"FlexConnect current mode: {mode_str} ({value})")

    def _handle_get_flexconnect_fault(self, value):
        logger.debug("_handle_get_flexconnect_fault ACK")
        self.flexconnect_fault_status = value
        if value != 0:
            fault_desc = []
            if value & 0x01:
                fault_desc.append("DUT_VBUS_FAULT")
            if value & 0x02:
                fault_desc.append("UDISK1_VBUS_FAULT")
            if value & 0x04:
                fault_desc.append("UDISK2_VBUS_FAULT")
            logger.warning(f"FlexConnect fault detected: 0x{value:02X} ({', '.join(fault_desc)})")
        else:
            logger.debug("FlexConnect no fault detected")

    def _handle_set_flexconnect_default_mode(self):
        logger.debug("_handle_set_flexconnect_default_mode ACK")

    def _handle_get_flexconnect_default_mode(self, value):
        logger.debug(f"_handle_get_flexconnect_default_mode ACK, value:{value}")
        self.flexconnect_default_mode = value
        mode_names = {
            FLEXCONNECT_MODE_PC: "PC",
            FLEXCONNECT_MODE_UDISK1: "UDISK1",
            FLEXCONNECT_MODE_UDISK2: "UDISK2"
        }
        mode_str = mode_names.get(value, f"Unknown({value})")
        logger.debug(f"FlexConnect default mode: {mode_str} ({value})")

    def _handle_set_auto_restore(self):
        logger.debug("_handle_set_auto_restore ACK")

    def _handle_get_auto_restore_status(self,value):
        logger.debug(f"_handle_get_auto_restore_status ACK,value:{value}")
        self.auto_restore_status = value

    def _retry_get_info(self, get_func, info_name, max_retry_time=10.0):
        """
        重试获取设备信息，直到成功或超时（至少尝试10秒）
        
        Args:
            get_func: 获取信息的函数（无参数）
            info_name: 信息名称（用于日志）
            max_retry_time: 最大重试时间（秒），默认10秒
            
        Returns:
            获取到的信息值，如果超时则返回None
        """
        start_time = time.time()
        retry_count = 0
        
        while True:
            result = get_func()
            if result is not None:
                logger.debug(f"{info_name} retrieved successfully after {retry_count} retries, {time.time() - start_time:.2f}s")
                return result
            
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_retry_time:
                logger.error(f"{info_name} failed after {retry_count} retries, {elapsed_time:.2f}s - giving up")
                return None
            
            retry_count += 1
            # 重试间隔：前几次快速重试，之后逐渐增加间隔
            if retry_count <= 3:
                time.sleep(0.05)  # 50ms
            elif retry_count <= 10:
                time.sleep(0.1)    # 100ms
            else:
                time.sleep(0.2)    # 200ms
            
            logger.debug(f"{info_name} retry {retry_count}, elapsed: {elapsed_time:.2f}s")

    def get_device_info(self):
        """
        Returns the hub's ID, hardware version, firmware version, operate mode, and button control status.
        所有关键信息都会重试直到成功或至少尝试10秒。

        Returns:
            dict: A dictionary containing the hub's information.
        """
        # 重试获取所有关键信息，至少尝试10秒
        # 使用重试机制确保在设备初始化或恢复期间也能成功获取信息
        logger.info("Getting device info with retry mechanism (max 10s per item)...")
        
        self.hardware_version = self._retry_get_info(self.get_hardware_version, "hardware_version")
        self.firmware_version = self._retry_get_info(self.get_firmware_version, "firmware_version")
        self.product_type = self._retry_get_info(self.get_product_type, "product_type")
        
        # 根据产品类型设置ACK超时时间
        if self.product_type is not None:
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            if product_info is not None:
                ack_timeout = product_info.get("ack_timeout", 0.1)  # 默认100ms
                self.com_timeout = ack_timeout
                logger.info(f"Set ACK timeout to {ack_timeout}s for product {product_info['name']}")
        
        # 先尝试获取通道数量
        self.max_channels = self._retry_get_info(self.get_max_channels, "max_channels")
        # 如果返回无效值（0xFF），尝试从产品类型推断
        if self.max_channels == 0xFF and self.product_type is not None:
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            if product_info is not None:
                inferred_channels = product_info["channels"]
                logger.info(f"Device firmware doesn't support CMD_GET_MAX_CHANNELS. Inferring max_channels={inferred_channels} from product_type={self.product_type} ({product_info['name']})")
                self.max_channels = inferred_channels
        self.serial_no = self._retry_get_info(self.get_serial_no, "serial_no")
        self.operate_mode = self._retry_get_info(self.get_operate_mode, "operate_mode")
        self.auto_restore_status = self._retry_get_info(self.get_auto_restore_status, "auto_restore_status")
        self.button_control_status = self._retry_get_info(self.get_button_control_status, "button_control_status")
        self.device_address = self._retry_get_info(self.get_device_address, "device_address")
        
        # 获取默认状态，如果失败则保持原有值（不覆盖为None）
        # 这些不是关键信息，所以不强制重试
        # 注意：FlexConnect产品不支持默认电源状态和默认数据线状态功能
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type) if self.product_type is not None else None
        is_flexconnect = product_info.get("is_flexconnect", False) if product_info is not None else False
        
        if not is_flexconnect:
            # 只有非FlexConnect产品才支持默认状态功能
            default_power = self.get_default_power_status(1,2,3,4)
            if default_power is not None:
                self.channel_default_power_status = default_power
            
            default_dataline = self.get_default_dataline_status(1,2,3,4)
            if default_dataline is not None:
                self.channel_default_dataline_status = default_dataline
        else:
            # FlexConnect产品不支持这些功能，跳过
            logger.debug("FlexConnect product does not support default power/dataline status, skipping...")

        # 从产品类型表获取产品名称
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type) if self.product_type is not None else None
        product_type_name = product_info["name"] if product_info is not None else (f"Unknown({self.product_type})" if self.product_type is not None else "N/A")
        
        hub_info = {
            "id": self.port.split("/")[-1],
            "address": self.device_address,
            "hardware_version": self.hardware_version,
            "firmware_version": self.firmware_version,
            "product_type": product_type_name,
            "max_channels": self.max_channels if self.max_channels is not None else "N/A",
            "serial_no": self.serial_no if self.serial_no else "N/A",
            "operate_mode": "normal" if self.operate_mode == 0 else "interlock" if self.operate_mode == 1 else "N/A",
            "auto_restore": "enabled" if self.auto_restore_status == 1 else "disabled",
            "button_control_status": "enabled" if self.button_control_status == 1 else "disabled"
        }
        
        # 检查关键信息是否都获取成功
        if self.operate_mode is None:
            logger.error("Failed to get operate mode after retries - this is critical!")
        if self.hardware_version is None:
            logger.warning("Failed to get hardware_version after retries")
        if self.firmware_version is None:
            logger.warning("Failed to get firmware_version after retries")
        if self.product_type is None:
            logger.warning("Failed to get product_type after retries")
        if self.max_channels is None:
            logger.warning("Failed to get max_channels after retries")
        if self.serial_no is None:
            logger.warning("Failed to get serial_no after retries")
            
        return hub_info
        
    @synchronized
    def set_operate_mode(self, mode):
        """
        Set the device's operating mode.

        Args:
            mode (int): The desired operating mode.
        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        self._send_packet(CMD_SET_OPERATE_MODE, None, mode)
        if self._wait_for_ack_with_recovery(CMD_SET_OPERATE_MODE):
            logger.debug("set_operate_mode ACK")
            return True
        else:
            logger.error("set_operate_mode No ACK!")
            return False

    @synchronized
    def get_operate_mode(self):
        """
        Sends a command to verify the current operating mode of the device.

        Returns:
            bool: True if the device responds in the expected mode, otherwise False.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_OPERATE_MODE]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_OPERATE_MODE, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):  
            logger.debug("get_operate_mode ACK")
            logger.debug(f"operate_mode: {self.operate_mode}")
            if self.operate_mode is None:
                logger.warning("get_operate_mode No ACK!")
            return self.operate_mode
        else:
            self.operate_mode = None
            logger.warning("get_operate_mode No ACK!")
            return None

    @synchronized
    def set_channel_power(self, *channels, state):
        """
        Sets the power state of one or more USB channels.

        Args:
            *channels (int): Channel numbers (1-4) to be updated.
            state (int): 1 to turn on power, 0 to turn off.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        # 发送命令
        self._send_packet(CMD_SET_CHANNEL_POWER, channels, state)
        # 等待ACK（_wait_for_ack_with_recovery 内部会处理残留ACK的情况）
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
            logger.debug("set_channel_power ACK")
            return True
        else:
            logger.error("set_channel_power No ACK!")
            return False

    @synchronized
    def get_channel_power_status(self, *channels):
        """
        Requests the power status of specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or int or None: A dictionary with channel numbers as keys and power states as values if multiple channels are queried,
                                 the power state of the single channel if only one channel is queried,
                                 or None if timed out.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_POWER_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_POWER_STATUS, channels)
        
        # 如果是多通道查询，需要等待所有ACK都被解析
        if len(channels) > 1:
            # 等待第一个ACK到达
            if ack_event.wait(self.com_timeout):
                # 即使收到第一个ACK，也要继续等待一小段时间，确保所有ACK都被解析
                time.sleep(0.05)  # 等待50ms，给其他ACK时间到达并被解析
                logger.debug("get_channel_power_status ACK")
                logger.debug(f"get_channel_power_status: {self.channel_power_status}")
                # 只返回查询的通道，过滤掉其他通道
                result = {ch: self.channel_power_status.get(ch) for ch in channels if ch in self.channel_power_status}
                return result if result else None
            else:
                logger.error("get_channel_power_status No ACK!")
                return None
        else:
            # 单通道查询，使用原来的逻辑
            if ack_event.wait(self.com_timeout):  
                logger.debug("get_channel_power_status ACK")
                return self.channel_power_status.get(channels[0], None)
            else:
                logger.error("get_channel_power_status No ACK!")
                return None

    @synchronized
    def set_channel_power_interlock(self,channel):
        """
        Sets the interlock mode for a specified channel or all channels.

        Args:
            channel (int or None): The channel to set. If None, all channels will be turn off.

        Returns:
            bool: True if the command was acknowledged, False otherwise.
        """
        if channel is None:
            # If channel is None, set interlock mode for all channels
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, None,0)
        else:
            channels = [channel]
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, channels,1)

        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER_INTERLOCK):
            logger.debug("set_channel_power_interlock ACK")
            return True
        else:
            logger.error("set_channel_power_interlock No ACK!")
            return False

    @synchronized    
    def get_channel_voltage(self, channel):
        """
        Returns the voltage of a single channel.

        Args:
            channel (int): The channel to query.

        Returns:
            int or None: Voltage reading for the channel, or None if timed out or not supported.
            
        Raises:
            ValueError: 如果产品不支持电压检测功能
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_voltage only supports a single channel")
        
        # 检查产品是否支持ADC功能
        if not self._check_feature_support("adc"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} does not support voltage/current monitoring (ADC). "
                           f"This feature is not available on this device model.")

        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [channel])
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_voltage ACK")
            return self.channel_voltages.get(channel)
        else:
            logger.error("get_channel_voltage No ACK!")
            return None

    @synchronized
    def get_channel_current(self, channel):
        """
        Returns the current reading of a single channel.

        Args:
            channel (int): The channel to query.

        Returns:
            int or None: Current reading for the channel, or None if timed out or not supported.
            
        Raises:
            ValueError: 如果产品不支持电流检测功能
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_current only supports a single channel")
        
        # 检查产品是否支持ADC功能
        if not self._check_feature_support("adc"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} does not support voltage/current monitoring (ADC). "
                           f"This feature is not available on this device model.")

        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_CURRENT, [channel])
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_current ACK")
            return self.channel_currents.get(channel)
        else:
            logger.error("get_channel_current No ACK!")
            return None
            
    @synchronized
    def set_channel_usb2_dataline(self, *channels, state):
        """
        Sends a command to set the data line state of specific channels.

        Args:
            value (int): New data line state.
            *channels (int): Channels to update.
            state (int): 1 to enable data line, 0 to disable.
        """
        self._send_packet(CMD_SET_CHANNEL_DATALINE, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_DATALINE):
            logger.debug("set_channel_usb2_dataline ACK")
            return True
        else:
            logger.error("set_channel_usb2_dataline No ACK!")
            return False

    @synchronized
    def get_channel_usb2_dataline_status(self, *channels):
        """
        Requests the data line status for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: A dictionary with channel numbers as keys and data line states as values, or None if timed out.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_DATALINE_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_DATALINE_STATUS, channels)
        # 等待ACK
        if ack_event.wait(self.com_timeout):  
            logger.debug("get_channel_usb2_dataline_status ACK")
            return self.channel_dataline_status
        else:
            logger.error("get_channel_usb2_dataline_status No ACK!")
            return None

    @synchronized
    def set_channel_usb3_dataline(self, *channels, state):
        """
        Sends a command to set the USB3 data line state of specific channels.

        Args:
            *channels (int): Channels to update.
            state (int): 1 to enable USB3 data line, 0 to disable.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        self._send_packet(CMD_SET_CHANNEL_USB3_DATALINE, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_USB3_DATALINE):
            logger.debug("set_channel_usb3_dataline ACK")
            return True
        else:
            logger.error("set_channel_usb3_dataline No ACK!")
            return False

    @synchronized
    def get_channel_usb3_dataline_status(self, *channels):
        """
        Requests the USB3 data line status for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: A dictionary with channel numbers as keys and USB3 data line states as values, or None if timed out.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_USB3_DATALINE_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_USB3_DATALINE_STATUS, channels)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_usb3_dataline_status ACK")
            return self.channel_usb3_dataline_status
        else:
            logger.error("get_channel_usb3_dataline_status No ACK!")
            return None

    @synchronized
    def set_channel_slow_charge(self, *channels, disconnect_before_switch=False):
        """
        Enables slow charge mode for one or more channels.
        Slow charge mode limits the charging current (enables ilim).
        
        **重要**: 慢充模式保持连接的条件是之前电源必须是打开状态。如果通道之前是关闭状态，
        会先切换到快充模式3秒，然后再切换到慢充模式，以确保数据连接不断开。

        Args:
            *channels (int): Channel numbers (1-4) to be updated.
            disconnect_before_switch (bool): If True, disconnect channels for 3 seconds before enabling slow charge.
                                             Default is False.

        Returns:
            bool: True if command was acknowledged, False otherwise.

        set_channel_slow_charge(channels)
        ↓
        获取当前电源状态
        ↓
        ┌─────────────────┬─────────────────┐
        │  关闭状态         │   已打开状态     │
        │  (power=0)      │  (power=1)      │
        ├─────────────────┼─────────────────┤
        │ 1. 打开电源       │ 1. 如果disconnect│
        │ 2. 设置为快充     │    =True，断开3秒│
        │ 3. 等待3秒       │                 │
        │ 4. 切换到慢充     │ 2. 切换到慢充   │
        └─────────────────┴─────────────────┘

        """
        channels_list = list(channels)
        
        # 先获取当前状态（直接发送命令，避免调用@synchronized方法导致死锁）
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_POWER_STATUS]
        ack_event.clear()
        # 然后发送命令
        self._send_packet(CMD_GET_CHANNEL_POWER_STATUS, tuple(channels_list))
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_power_status ACK")
            power_status_dict = {}
            for ch in channels_list:
                status = self.channel_power_status.get(ch, 0)
                power_status_dict[ch] = status
            logger.debug(f"Power status retrieved: {power_status_dict}")
        else:
            logger.warning(f"Failed to get power status within {self.com_timeout}s timeout. "
                         f"Will try to read cached status or assume channels are off.")
            # 尝试使用缓存的状态（如果之前查询过）
            power_status_dict = {}
            for ch in channels_list:
                # 优先使用缓存的状态，如果没有则假设为关闭
                cached_status = self.channel_power_status.get(ch)
                if cached_status is not None:
                    power_status_dict[ch] = cached_status
                    logger.debug(f"Using cached power status for channel {ch}: {cached_status}")
                else:
                    power_status_dict[ch] = 0
                    logger.warning(f"No cached status for channel {ch}, assuming it's off")
        
        # 检查每个通道的当前状态
        need_fast_charge_first = []
        channels_already_on = []
        
        for channel in channels_list:
            # 检查电源状态
            power_status = power_status_dict.get(channel, 0)
            
            # 如果电源是关闭状态，需要先切换到快充模式
            if power_status == 0:
                need_fast_charge_first.append(channel)
                logger.debug(f"Channel {channel} is currently off, will enable fast charge first")
            else:
                channels_already_on.append(channel)
                logger.debug(f"Channel {channel} is already on")
        
        # 如果有通道需要先切换到快充模式（从关闭状态）
        if need_fast_charge_first:
            logger.debug(f"Channels {need_fast_charge_first} are off, enabling fast charge mode first for 3 seconds")
            # 先打开电源并设置为快充模式 (先建立数据连接)
            self._send_packet(CMD_SET_CHANNEL_POWER, tuple(need_fast_charge_first), 1)
            if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
                # 等待电源稳定
                time.sleep(0.1)
                # 设置为快充模式
                self._send_packet(CMD_SET_CHANNEL_FAST_CHARGE, tuple(need_fast_charge_first), 1)
                if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_FAST_CHARGE):
                    logger.debug(f"Fast charge enabled for channels {need_fast_charge_first}, waiting 3 seconds")
                    time.sleep(3.0)
                else:
                    logger.warning(f"Failed to enable fast charge for channels {need_fast_charge_first}. "
                                 f"Power is on but fast charge mode failed. Will continue to slow charge mode.")
                    # 即使快充模式设置失败，电源已经打开，仍然可以尝试切换到慢充模式
                    # 但可能无法保证数据连接不断开
            else:
                logger.warning(f"Failed to power on channels {need_fast_charge_first}. "
                             f"Cannot proceed to slow charge mode.")
                # 如果电源打开失败，无法继续执行慢充模式切换
                return False
        
        # 如果需要断开连接再切换（对于已经是打开状态的通道：快充或慢充）
        if disconnect_before_switch and channels_already_on:
            logger.debug(f"Disconnecting channels {channels_already_on} before setting slow charge mode")
            self._send_packet(CMD_SET_CHANNEL_POWER, tuple(channels_already_on), 0)
            if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
                time.sleep(3.0)
            else:
                logger.warning("Failed to disconnect channels before slow charge")

        # 切换到慢充模式
        # 检查上一个相关命令是否完成（避免在设备还在处理时发送新命令）
        # 检查快充命令是否完成，如果未完成则等待
        fast_charge_event = self.ack_events[CMD_SET_CHANNEL_FAST_CHARGE]
        if not fast_charge_event.is_set():
            logger.debug("Previous fast charge command not completed, waiting...")
            # 等待上一个命令完成，最多等待3秒（因为断开操作需要3秒）
            if not fast_charge_event.wait(3.1):
                logger.warning("Previous fast charge command timeout, proceeding anyway...")
        
        # 发送命令
        self._send_packet(CMD_SET_CHANNEL_SLOW_CHARGE, channels, 1)
        # 等待ACK（_wait_for_ack_with_recovery 内部会处理残留ACK的情况）
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_SLOW_CHARGE):
            logger.debug("set_channel_slow_charge ACK")
            return True
        else:
            logger.error("set_channel_slow_charge No ACK!")
            return False

    @synchronized
    def set_channel_fast_charge(self, *channels, disconnect_before_switch=True):
        """
        Enables fast charge mode for one or more channels.
        Fast charge mode provides full power (disables ilim, enables VBUS).

        Args:
            *channels (int): Channel numbers (1-4) to be updated.
            disconnect_before_switch (bool): If True, disconnect channels for 1 second before enabling fast charge.
                                            Default is True.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        if disconnect_before_switch:
            logger.debug(f"Disconnecting channels {channels} before setting fast charge mode")
            self._send_packet(CMD_SET_CHANNEL_POWER, channels, 0)
            if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
                time.sleep(3.0)
            else:
                logger.warning("Failed to disconnect channels before fast charge")

        # 检查上一个相关命令是否完成（避免在设备还在处理时发送新命令）
        # 检查慢充命令是否完成，如果未完成则等待
        slow_charge_event = self.ack_events[CMD_SET_CHANNEL_SLOW_CHARGE]
        if not slow_charge_event.is_set():
            logger.debug("Previous slow charge command not completed, waiting...")
            # 等待上一个命令完成，最多等待3秒（因为断开操作需要3秒）
            if not slow_charge_event.wait(3.1):
                logger.warning("Previous slow charge command timeout, proceeding anyway...")
        
        # 发送命令
        self._send_packet(CMD_SET_CHANNEL_FAST_CHARGE, channels, 1)
        # 等待ACK（_wait_for_ack_with_recovery 内部会处理残留ACK的情况）
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_FAST_CHARGE):
            logger.debug("set_channel_fast_charge ACK")
            return True
        else:
            logger.error("set_channel_fast_charge No ACK!")
            return False

    @synchronized
    def get_channel_charge_mode(self, *channels):
        """
        Requests the charge mode for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: A dictionary with channel numbers as keys and charge modes as values.
                          Charge mode values: 0=off, 1=fast_charge, 2=slow_charge.
                          Returns None if timed out.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_CHANNEL_CHARGE_MODE]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_CHANNEL_CHARGE_MODE, channels)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_charge_mode ACK")
            result = {}
            for ch in channels:
                mode = self.channel_charge_modes.get(ch)
                if mode is not None:
                    result[ch] = mode
            return result if result else None
        else:
            logger.error("get_channel_charge_mode No ACK!")
            return None

    @synchronized
    def set_button_control(self, enable: bool):
        """
        Enable or disable the hub's physical buttons.

        Args:
            enable (bool): True to enable buttons, False to disable.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        data_val = 1 if enable else 0

        self._send_packet(CMD_SET_BUTTON_CONTROL, None, data_val)
        if self._wait_for_ack_with_recovery(CMD_SET_BUTTON_CONTROL):
            logger.debug("set_button_control ACK")
            return True
        else:
            logger.error("set_button_control No ACK!")
            return False

    @synchronized
    def get_button_control_status(self):
        """
        Query whether the hub's physical buttons are enabled or disabled.

        Returns:
            int or None: 1 if enabled, 0 if disabled, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_BUTTON_CONTROL_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_BUTTON_CONTROL_STATUS, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_button_control_status ACK")
            return self.button_control_status
        else:
            logger.error("get_button_control_status No ACK!")
            return None

    @synchronized
    def set_default_power_status(self,*channels,enable,status=None):
        """
        Sets the default power status for one or more channels.

        Args:
            *channels (int): Channels to configure.
            enable (int): 1 to enable default power status, 0 to disable.
            status (int, optional): Default power state when enabled. 1 for ON, 0 for OFF. Defaults to 0.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        if status is None:
            status = 0
        self._send_packet(CMD_SET_DEFAULT_POWER_STATUS,channels,[enable,status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_POWER_STATUS):
            logger.debug("set_default_power_status ACK")
            return True
        else:
            logger.error("set_default_power_status No ACK!")
            return False

    @synchronized
    def get_default_power_status(self,*channels):
        """
        Retrieves the default power status configuration for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: Dictionary with enabled status and default value per channel, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_DEFAULT_POWER_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_DEFAULT_POWER_STATUS, channels,[0,0])
        # 等待ACK
        if ack_event.wait(self.com_timeout):  
            logger.debug("get_default_power_status ACK")
            result = {}
            for ch in channels:
                enable = self.channel_default_power_flag.get(ch)
                status = self.channel_default_power_status.get(ch)
                if enable is not None and status is not None:
                    result[ch] = {
                        "enabled": enable,
                        "value": status
                    }
                    logger.info(f"channel {ch} default power status: enabled={enable}, value={status}")
            return result
        else:
            logger.error("get_default_power_status No ACK!")
            return None

    @synchronized
    def set_default_dataline_status(self,*channels,enable,status=None):
        """
        Sets the default dataline status for one or more channels.

        Args:
            *channels (int): Channels to configure.
            enable (int): 1 to enable default dataline status, 0 to disable.
            status (int, optional): Default dataline state when enabled. 1 for Connected, 0 for Disconnected. Defaults to 0.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        if status is None:
            status = 0
        self._send_packet(CMD_SET_DEFAULT_DATALINE_STATUS,channels,[enable,status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_DATALINE_STATUS):
            logger.debug("set_default_dataline_status ACK")
            return True
        else:
            logger.error("set_default_dataline_status No ACK!")
            return False

    @synchronized
    def get_default_dataline_status(self,*channels):
        """
        Retrieves the default dataline status configuration for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: Dictionary with enabled status and default value per channel, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_DEFAULT_DATALINE_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_DEFAULT_DATALINE_STATUS, channels,[0,0])
        # 等待ACK
        if ack_event.wait(self.com_timeout):  
            logger.debug("get_default_dataline_status ACK")
            result = {}
            for ch in channels:
                enable = self.channel_default_dataline_flag.get(ch)
                status = self.channel_default_dataline_status.get(ch)
                if enable is not None and status is not None:
                    result[ch] = {
                        "enabled": enable,
                        "value": status
                    }
                    logger.info(f"channel {ch} default dataline status: enabled={enable}, value={status}")
            return result
        else:
            logger.error("get_default_dataline_status No ACK!")
            return None

    @synchronized    
    def set_auto_restore(self,enable:bool):
        """
        Enables or disables the auto-restore feature.
        
        Args:
            enable (bool): True to enable auto-restore; False to disable.
        
        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        data_val = 1 if enable else 0

        self._send_packet(CMD_SET_AUTO_RESTORE, None, data_val)
        if self._wait_for_ack_with_recovery(CMD_SET_AUTO_RESTORE):
            logger.debug("set_auto_restore ACK")
            return True
        else:
            logger.error("set_auto_restore No ACK!")
            return False

    @synchronized
    def get_auto_restore_status(self):
        """
        Queries whether auto-restore is enabled.
    
        Returns:
            int or None: 1 if auto-restore is enabled, 0 if disabled, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_AUTO_RESTORE_STATUS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_AUTO_RESTORE_STATUS, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_auto_restore_status ACK")
            return self.auto_restore_status
        else:
            logger.error("get_auto_restore_status No ACK!")
            return None

    @synchronized
    def set_device_address(self, address: int):
        """
        Set the device address (uint16) for this Hub.

        Args:
            address (int): 0x0000 - 0xFFFF
        
        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        if not (0 <= address <= 0xFFFF):
            raise ValueError("Address must be between 0x0000 and 0xFFFF")
        lsb = address & 0xFF
        msb = (address >> 8) & 0xFF
        self._send_packet(CMD_SET_DEVICE_ADDRESS,msb,lsb)
        ack_event = self.ack_events[CMD_SET_DEVICE_ADDRESS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
            logger.debug("set_device_address ACK")
            self.device_address = address
            return True
        else:
            logger.error("set_device_address No ACK!")
            return False

    @synchronized
    def get_device_address(self):
        """
        Get the current device address from the Hub.

        Returns:
            16-bit device address or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_DEVICE_ADDRESS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_DEVICE_ADDRESS, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_device_address ACK")
            return self.device_address
        else:
            logger.error("get_device_address No ACK!")
            return None

    @synchronized
    def reboot_mcu(self):
        """
        Sends a command to reboot the MCU.
        
        Note: After sending the reboot command, the MCU will reboot in approximately 100ms.
        The connection will be lost after reboot. You may need to reconnect after the device
        restarts.
    
        Returns:
            bool: True if the reboot command was acknowledged; False otherwise.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_REBOOT_MCU]
        ack_event.clear()
        # 等待一小段时间，让可能的残留ACK到达
        time.sleep(0.001)
        # 如果已经有残留ACK，直接返回成功
        if ack_event.is_set():
            ack_event.clear()
            logger.debug("reboot_mcu ACK (residual)")
            return True
        
        # 发送命令
        self._send_packet(CMD_REBOOT_MCU, None, None)
        # 等待ACK，使用更长的超时时间（200ms），因为MCU会在发送ACK后延迟100ms才重启
        # 这样可以确保有足够时间接收ACK
        if ack_event.wait(0.2):  # 200ms 超时
            logger.debug("reboot_mcu ACK")
            return True
        else:
            logger.error("reboot_mcu No ACK!")
            return False

    @synchronized
    def factory_reset(self):
        """
        Sends a command to reset the device to factory settings.
    
        Returns:
            bool: True if the reset command was acknowledged; False otherwise.
        """
        self._send_packet(CMD_FACTORY_RESET, None, None)
        ack_event = self.ack_events[CMD_FACTORY_RESET]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("factory_reset ACK")
            return True
        else:
            logger.error("factory_reset No ACK!")
            return False

    @synchronized
    def get_firmware_version(self):
        """
        Query the device's firmware version.

        Returns:
            int or None: The firmware version, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_FIRMWARE_VERSION]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_FIRMWARE_VERSION, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_firmware_version ACK")
            return self.firmware_version
        else:
            logger.error("get_firmware_version No ACK!")
            return None

    @synchronized
    def get_hardware_version(self):
        """
        Query the device's hardware version.

        Returns:
            int or None: The hardware version, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_HARDWARE_VERSION]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_HARDWARE_VERSION, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_hardware_version ACK")
            return self.hardware_version
        else:
            logger.error("get_hardware_version No ACK!")
            return None

    @synchronized
    def get_product_type(self):
        """
        Query the device's product type.

        Returns:
            int or None: The product type ID, or None if no response.
            
        Product types (see PRODUCT_TYPE_TABLE for details):
            - 0x00: HBP_USB2_4CH (USB2.0 4通道集线器)
            - 0x01: HBP_USB2_2CH (USB2.0 2通道集线器)
            - 0x02: HBP_USB3_4CH (USB3.0 4通道集线器)
            - 0x03: FLEX_3CH (FlexConnect 3通道集线器)
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_PRODUCT_TYPE]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_PRODUCT_TYPE, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_product_type ACK")
            return self.product_type
        else:
            # 旧固件不支持此功能，使用debug级别而不是error
            logger.debug("get_product_type No ACK (可能是不支持此功能的旧固件)")
            return None

    @synchronized
    def get_product_name(self):
        """
        Get the product name based on the device's product type.

        Returns:
            str or None: The product name (e.g., "HBP_USB2_4CH"), or None if product type is unknown or not available.
            
        Example:
            >>> hub = SmartUSBHub(port)
            >>> name = hub.get_product_name()
            >>> print(name)  # "HBP_USB2_4CH"
        """
        # 如果产品类型还未获取，先获取
        if self.product_type is None:
            self.product_type = self.get_product_type()
        
        # 如果产品类型仍然为None，返回None
        if self.product_type is None:
            return None
        
        # 从产品类型表获取产品名称
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        if product_info is not None:
            return product_info["name"]
        else:
            return f"Unknown({self.product_type:#02x})"

    @synchronized
    def get_max_channels(self):
        """
        Query the device's maximum channel count.

        Returns:
            int or None: The maximum number of channels supported by the device, or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_MAX_CHANNELS]
        ack_event.clear()
        # 发送命令
        self._send_packet(CMD_GET_MAX_CHANNELS, None, None)
        # 等待ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_max_channels ACK")
            return self.max_channels
        else:
            # 旧固件不支持此功能，使用debug级别而不是error
            logger.debug("get_max_channels No ACK (可能是不支持此功能的旧固件)")
            return None

    @synchronized
    def set_flexconnect_mode(self, mode):
        """
        Set FlexConnect working mode.
        
        Args:
            mode (int): The desired mode.
                - FLEXCONNECT_MODE_PC (0x00): PC mode (ADB debugging)
                - FLEXCONNECT_MODE_UDISK1 (0x01): U disk 1 mode
                - FLEXCONNECT_MODE_UDISK2 (0x02): U disk 2 mode
                - FLEXCONNECT_MODE_DISCONNECT (0x03): Disconnect all connections mode
        
        Returns:
            bool: True if command was acknowledged and mode was set successfully, False otherwise.
            
        Raises:
            ValueError: If the product is not a FlexConnect product or mode is invalid.
        """
        # Check if product is FlexConnect
        if not self._check_feature_support("flexconnect"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} is not a FlexConnect product. "
                           f"This method is only available for FlexConnect devices.")
        
        # Validate mode
        if mode not in [FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2, FLEXCONNECT_MODE_DISCONNECT]:
            raise ValueError(f"Invalid FlexConnect mode: {mode}. "
                           f"Valid modes are: FLEXCONNECT_MODE_PC (0), "
                           f"FLEXCONNECT_MODE_UDISK1 (1), FLEXCONNECT_MODE_UDISK2 (2), "
                           f"FLEXCONNECT_MODE_DISCONNECT (3)")
        
        # Send command
        self._send_packet(CMD_SET_FLEXCONNECT_MODE, None, mode)
        if self._wait_for_ack_with_recovery(CMD_SET_FLEXCONNECT_MODE):
            logger.debug("set_flexconnect_mode ACK")
            # Check if mode was set successfully (device returns 0xFF on error)
            if self.flexconnect_mode is not None and self.flexconnect_mode != 0xFF:
                return True
            else:
                logger.error("set_flexconnect_mode failed (device returned error)")
                return False
        else:
            logger.error("set_flexconnect_mode No ACK!")
            return False

    @synchronized
    def get_flexconnect_mode(self):
        """
        Get the current FlexConnect working mode.
        
        Returns:
            int or None: The current mode, or None if no response.
                - FLEXCONNECT_MODE_PC (0x00): PC mode (ADB debugging)
                - FLEXCONNECT_MODE_UDISK1 (0x01): U disk 1 mode
                - FLEXCONNECT_MODE_UDISK2 (0x02): U disk 2 mode
                - FLEXCONNECT_MODE_DISCONNECT (0x03): Disconnect all connections mode
                
        Raises:
            ValueError: If the product is not a FlexConnect product.
        """
        # Check if product is FlexConnect
        if not self._check_feature_support("flexconnect"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} is not a FlexConnect product. "
                           f"This method is only available for FlexConnect devices.")
        
        # Clear event to avoid stale ACK
        ack_event = self.ack_events[CMD_GET_FLEXCONNECT_MODE]
        ack_event.clear()
        # Send command
        self._send_packet(CMD_GET_FLEXCONNECT_MODE, None, None)
        # Wait for ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_flexconnect_mode ACK")
            return self.flexconnect_mode
        else:
            logger.error("get_flexconnect_mode No ACK!")
            return None

    @synchronized
    def get_flexconnect_fault(self):
        """
        Get FlexConnect fault status.
        
        Returns:
            int or None: Fault status byte, or None if no response.
                Bit 0: DUT_VBUS_FAULT
                Bit 1: UDISK1_VBUS_FAULT
                Bit 2: UDISK2_VBUS_FAULT
                0 = No fault
                
        Raises:
            ValueError: If the product is not a FlexConnect product or fault detection is not supported.
        """
        # Check if product is FlexConnect
        if not self._check_feature_support("flexconnect"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} is not a FlexConnect product. "
                           f"This method is only available for FlexConnect devices.")
        
        # Clear event to avoid stale ACK
        ack_event = self.ack_events[CMD_GET_FLEXCONNECT_FAULT]
        ack_event.clear()
        # Send command
        self._send_packet(CMD_GET_FLEXCONNECT_FAULT, None, None)
        # Wait for ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_flexconnect_fault ACK")
            return self.flexconnect_fault_status
        else:
            logger.error("get_flexconnect_fault No ACK!")
            return None

    @synchronized
    def set_flexconnect_default_mode(self, mode):
        """
        Set the FlexConnect default power-on mode.
        
        Args:
            mode (int): The default mode to set on power-on.
                - FLEXCONNECT_MODE_PC (0x00): PC mode (ADB debugging)
                - FLEXCONNECT_MODE_UDISK1 (0x01): U disk 1 mode
                - FLEXCONNECT_MODE_UDISK2 (0x02): U disk 2 mode
                
        Returns:
            bool: True if command was acknowledged, False otherwise.
                
        Raises:
            ValueError: If the product is not a FlexConnect product or mode is invalid.
        """
        # Check if product is FlexConnect
        if not self._check_feature_support("flexconnect"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} is not a FlexConnect product. "
                           f"This method is only available for FlexConnect devices.")
        
        # Validate mode (only PC, UDISK1, UDISK2 are valid for default mode, not DISCONNECT)
        if mode not in [FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1, FLEXCONNECT_MODE_UDISK2]:
            raise ValueError(f"Invalid FlexConnect default mode: {mode}. "
                           f"Valid modes are: FLEXCONNECT_MODE_PC (0), "
                           f"FLEXCONNECT_MODE_UDISK1 (1), FLEXCONNECT_MODE_UDISK2 (2)")
        
        # Send command
        self._send_packet(CMD_SET_FLEXCONNECT_DEFAULT_MODE, None, mode)
        if self._wait_for_ack_with_recovery(CMD_SET_FLEXCONNECT_DEFAULT_MODE):
            logger.debug("set_flexconnect_default_mode ACK")
            return True
        else:
            logger.error("set_flexconnect_default_mode No ACK!")
            return False

    @synchronized
    def get_flexconnect_default_mode(self):
        """
        Get the FlexConnect default power-on mode.
        
        Returns:
            int or None: The default mode, or None if no response.
                - FLEXCONNECT_MODE_PC (0x00): PC mode (ADB debugging)
                - FLEXCONNECT_MODE_UDISK1 (0x01): U disk 1 mode
                - FLEXCONNECT_MODE_UDISK2 (0x02): U disk 2 mode
                
        Raises:
            ValueError: If the product is not a FlexConnect product.
        """
        # Check if product is FlexConnect
        if not self._check_feature_support("flexconnect"):
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
            raise ValueError(f"Product {product_name} is not a FlexConnect product. "
                           f"This method is only available for FlexConnect devices.")
        
        # Clear event to avoid stale ACK
        ack_event = self.ack_events[CMD_GET_FLEXCONNECT_DEFAULT_MODE]
        ack_event.clear()
        # Send command
        self._send_packet(CMD_GET_FLEXCONNECT_DEFAULT_MODE, None, None)
        # Wait for ACK
        if ack_event.wait(self.com_timeout):
            logger.debug("get_flexconnect_default_mode ACK")
            return self.flexconnect_default_mode
        else:
            logger.error("get_flexconnect_default_mode No ACK!")
            return None

    @synchronized
    def get_serial_no(self):
        """
        Query the device's serial number (using V3 protocol).

        Returns:
            str or None: The serial number string (format: "XXXXXXXX-XXXXXXXX-XXXXXXXX"), or None if no response.
        """
        # 先清除事件，避免之前残留的ACK影响
        ack_event = self.ack_events[CMD_GET_SERIAL_NO]
        ack_event.clear()
        # 发送命令 (V1 protocol for request)
        self._send_packet(CMD_GET_SERIAL_NO, None, None)
        # 等待ACK (response will be V3 protocol)
        if ack_event.wait(self.com_timeout):
            logger.debug("get_serial_no ACK")
            return self.serial_no
        else:
            logger.error("get_serial_no No ACK!")
            return None