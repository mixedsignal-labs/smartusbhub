# Description: Python class to control Smart USB Hub with serial communication.
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com
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

import logging
import colorlog

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

CMD_SET_CHANNEL_LOW_CURRENT         = 0x13
CMD_GET_CHANNEL_LOW_CURRENT         = 0x14

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

    def __init__(self, port):
        """
        Initializes the Smart USB Hub.

        Args:
            port (str): The serial port name to connect to the device.
        """
        self.port = port
        self.ser = serial.Serial(port, 115200,timeout = 0.5)
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
            CMD_SET_CHANNEL_LOW_CURRENT: threading.Event(),
            CMD_GET_CHANNEL_LOW_CURRENT: threading.Event(),
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
            CMD_FACTORY_RESET:threading.Event(),
            CMD_GET_FIRMWARE_VERSION: threading.Event(),
            CMD_GET_HARDWARE_VERSION: threading.Event(),
        }
        
        self.lock = threading.Lock()  # 用于串口操作的互斥锁

        self.callbacks = {cmd: None for cmd in self.ack_events.keys()}
        
        self.poweroff_recover = None
        self.hardware_version = None
        self.firmware_version = None
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
        self.channel_low_current_status = {}

        self.device_address = None

        self.disconnect_callback = None

        self._start()
        self.get_device_info()
        
        if self.get_operate_mode is None:
            logger.error("Failed to get operate mode.")
            sys.exit(1)
            
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
    def scan_and_connect(cls):
        """
        Searches for available Smart USB Hub devices and connects to the first valid one.

        Returns:
            SmartUSBHub or None: An instance of SmartUSBHub if found, otherwise None.
        """
        for port_info in serial.tools.list_ports.comports():
            port_name = port_info.device
            logger.debug(f"Trying to connect to port {port_name}")
            if port_info.vid == 0x1A86 and port_info.pid == 0xfe0c:
                hub = cls(port_name)
                port_suffix = port_name.split("/")[-1]
                hub.name = f"smarthub_id:{port_suffix}"
                return hub

        logger.error("No Smart USB Hub found.")
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
        self.uart_recv_thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.flush()
            self.ser.close()
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

    def _parse_protocol_frame(self, data):
        """
        Processes a raw data frame from the device and delivers it to the correct handler.

        Args:
            data (bytes): Raw bytes read from the device.

        Returns:
            tuple or None: Parsed command, channel, value, and length if valid, otherwise None.
        """

        # logger.debug(f"Received data: {data.hex()}")

        if len(data) < 6:
            return None

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
                    while len(buffer) >= 6:
                        result = self._parse_protocol_frame(buffer)
                        if result is not None:
                            cmd, channel, value, length = result

                            logger.debug(f"Parsed CMD: {cmd:#04x}, Channel: {channel:#04x}, Value: {value}")

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
                            elif cmd == CMD_SET_CHANNEL_LOW_CURRENT:
                                self._handle_set_channel_low_current(channel, value)
                            elif cmd == CMD_GET_CHANNEL_LOW_CURRENT:
                                self._handle_get_channel_low_current(channel, value)
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
                            elif cmd == CMD_FACTORY_RESET:
                                self._handle_factory_reset()
                            elif cmd == CMD_GET_FIRMWARE_VERSION:
                                self._handle_firmware_version(value)
                            elif cmd == CMD_GET_HARDWARE_VERSION:
                                self._handle_hardware_version(value)
                            if cmd in self.ack_events:
                                self._invoke_callback(cmd,channel,value)
                                self.ack_events[cmd].set()

                            del buffer[:length]
                        else:
                            buffer.pop(0)
            except (OSError, AttributeError,serial.SerialException) as e:
                logger.error(f"Error reading from UART: {e}")
                self.ser = None
                if self.disconnect_callback:
                    self.disconnect_callback()
                self.stop_event.set()
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

        # Send the packet
        if self.ser and self.ser.is_open:
            self.ser.write(packet)

        logger.debug(f"Sent command: {packet.hex()}")

        return packet

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

    def _handle_set_channel_low_current(self, channel, value):
        logger.debug("_handle_set_channel_low_current ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_low_current_status[ch] = value
            logger.debug(f"Set Channel Low Current: ch{ch} = {value}")

    def _handle_get_channel_low_current(self, channel, value):
        logger.debug("_handle_get_channel_low_current ACK")
        channels = self._convert_channel(channel)
        for ch in channels:
            self.channel_low_current_status[ch] = value
            logger.debug(f"Get Channel Low Current: ch{ch} = {value}")

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
            for ch in channels:
                self.channel_default_power_flag[ch] = enable
                self.channel_default_power_status[ch] = status
                logger.debug(f"Channel {ch} {'enable' if enable else 'disable'} default power status, value: {'on' if status else 'off'}")
        else:
            logger.error("Invalid data for _handle_set_default_power_status")

    def _handle_set_default_dataline_status(self,channel,value):
        logger.debug("_handle_set_default_dataline_status ACK")
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            channels = self._convert_channel(channel)
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
    def _handle_factory_reset(self):
        logger.debug("_handle_factory_reset ACK")

    def _handle_firmware_version(self, value):
        logger.debug("_handle_firmware_version ACK")
        self.firmware_version = value

    def _handle_hardware_version(self, value):
        logger.debug("_handle_hardware_version ACK")
        self.hardware_version = value

    def _handle_set_auto_restore(self):
        logger.debug("_handle_set_auto_restore ACK")

    def _handle_get_auto_restore_status(self,value):
        logger.debug(f"_handle_get_auto_restore_status ACK,value:{value}")
        self.auto_restore_status = value

    def get_device_info(self):
        """
        Returns the hub's ID, hardware version, firmware version, operate mode, and button control status.

        Returns:
            dict: A dictionary containing the hub's information.
        """
        self.hardware_version = self.get_hardware_version()
        self.firmware_version =  self.get_firmware_version()
        self.operate_mode = self.get_operate_mode()
        self.auto_restore_status = self.get_auto_restore_status()
        self.button_control_status = self.get_button_control_status()
        self.device_address = self.get_device_address()
        self.channel_default_power_status = self.get_default_power_status(1,2,3,4)
        self.channel_default_dataline_status = self.get_default_dataline_status(1,2,3,4)

        hub_info = {
            "id": self.port.split("/")[-1],
            "address": self.device_address,
            "hardware_version": self.hardware_version,
            "firmware_version": self.firmware_version,
            "operate_mode": "normal" if self.operate_mode == 0 else "interlock" if self.operate_mode == 1 else "N/A",
            "auto_restore": "enabled" if self.auto_restore_status == 1 else "disabled",
            "button_control_status": "enabled" if self.button_control_status == 1 else "disabled"
        }
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
        ack_event = self.ack_events[CMD_SET_OPERATE_MODE]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
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
        command = self._send_packet(CMD_GET_OPERATE_MODE, None, None)
        ack_event = self.ack_events[CMD_GET_OPERATE_MODE]
        ack_event.clear()
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
        self._send_packet(CMD_SET_CHANNEL_POWER, channels, state)
        ack_event = self.ack_events[CMD_SET_CHANNEL_POWER]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
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
        self._send_packet(CMD_GET_CHANNEL_POWER_STATUS, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_POWER_STATUS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
            logger.debug("get_channel_power_status ACK")

            if len(channels) == 1:
                return self.channel_power_status.get(channels[0], None)
            logger.debug(f"get_channel_power_status: {self.channel_power_status}")
            return self.channel_power_status
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

        ack_event = self.ack_events[CMD_SET_CHANNEL_POWER_INTERLOCK]
        ack_event.clear()
        if ack_event.wait(timeout=self.com_timeout): 
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
            int or None: Voltage reading for the channel, or None if timed out.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_voltage only supports a single channel")

        self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [channel])
        ack_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
        ack_event.clear()
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
            int or None: Current reading for the channel, or None if timed out.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_voltage only supports a single channel")

        self._send_packet(CMD_GET_CHANNEL_CURRENT, [channel])
        ack_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
        ack_event.clear()
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
        ack_event = self.ack_events[CMD_SET_CHANNEL_DATALINE]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
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
        self._send_packet(CMD_GET_CHANNEL_DATALINE_STATUS, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_DATALINE_STATUS]
        ack_event.clear()
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
        ack_event = self.ack_events[CMD_SET_CHANNEL_USB3_DATALINE]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
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
        self._send_packet(CMD_GET_CHANNEL_USB3_DATALINE_STATUS, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_USB3_DATALINE_STATUS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_usb3_dataline_status ACK")
            return self.channel_usb3_dataline_status
        else:
            logger.error("get_channel_usb3_dataline_status No ACK!")
            return None
    @synchronized
    def set_channel_low_current(self, *channels, state):
        """ 
        Enables or disables low-current mode for one or more channels.

        Args:
            *channels (int): Channel numbers (1-4) to be updated.
            state (int): True to enable low-current mode; False to disable.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        self._send_packet(CMD_SET_CHANNEL_LOW_CURRENT, channels, state)
        ack_event = self.ack_events[CMD_SET_CHANNEL_LOW_CURRENT]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("set_channel_low_current ACK")
            return True
        else:
            logger.error("set_channel_low_current No ACK!")
            return False
    @synchronized
    def get_channel_low_current_status(self, *channels):
        """
        Requests low-current mode status for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: A dictionary with channel numbers as keys and low-current states as values, or None if timed out.
        """
        self._send_packet(CMD_GET_CHANNEL_LOW_CURRENT, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_LOW_CURRENT]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_low_current_status ACK")
            return self.channel_low_current_status
        else:
            logger.error("get_channel_low_current_status No ACK!")
            return None
    @synchronized
    def set_button_control(self, enable: bool):
        """
        Sends a command to set the USB3 data line state of specific channels.

        Args:
            enable (bool): True to enable buttons, False to disable.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        self._send_packet(CMD_SET_CHANNEL_USB3_DATALINE, channels, state)
        ack_event = self.ack_events[CMD_SET_CHANNEL_USB3_DATALINE]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
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
        self._send_packet(CMD_GET_CHANNEL_USB3_DATALINE_STATUS, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_USB3_DATALINE_STATUS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_usb3_dataline_status ACK")
            return self.channel_usb3_dataline_status
        else:
            logger.error("get_channel_usb3_dataline_status No ACK!")
            return None
    @synchronized
    def set_channel_low_current(self, *channels, state):
        """ 
        Enables or disables low-current mode for one or more channels.

        Args:
            *channels (int): Channel numbers (1-4) to be updated.
            state (int): True to enable low-current mode; False to disable.

        Returns:
            bool: True if command was acknowledged, False otherwise.
        """
        self._send_packet(CMD_SET_CHANNEL_LOW_CURRENT, channels, state)
        ack_event = self.ack_events[CMD_SET_CHANNEL_LOW_CURRENT]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("set_channel_low_current ACK")
            return True
        else:
            logger.error("set_channel_low_current No ACK!")
            return False
    @synchronized
    def get_channel_low_current_status(self, *channels):
        """
        Requests low-current mode status for specified channels.

        Args:
            *channels (int): Channels to query.

        Returns:
            dict or None: A dictionary with channel numbers as keys and low-current states as values, or None if timed out.
        """
        self._send_packet(CMD_GET_CHANNEL_LOW_CURRENT, channels)
        ack_event = self.ack_events[CMD_GET_CHANNEL_LOW_CURRENT]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_channel_low_current_status ACK")
            return self.channel_low_current_status
        else:
            logger.error("get_channel_low_current_status No ACK!")
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
        ack_event = self.ack_events[CMD_SET_BUTTON_CONTROL]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
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
        self._send_packet(CMD_GET_BUTTON_CONTROL_STATUS, None, None)
        ack_event = self.ack_events[CMD_GET_BUTTON_CONTROL_STATUS]
        ack_event.clear()
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
        ack_event = self.ack_events[CMD_SET_DEFAULT_POWER_STATUS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
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
        self._send_packet(CMD_GET_DEFAULT_POWER_STATUS, channels,[0,0])
        ack_event = self.ack_events[CMD_GET_DEFAULT_POWER_STATUS]
        ack_event.clear()
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
        ack_event = self.ack_events[CMD_SET_DEFAULT_DATALINE_STATUS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):  
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
        self._send_packet(CMD_GET_DEFAULT_DATALINE_STATUS, channels,[0,0])
        ack_event = self.ack_events[CMD_GET_DEFAULT_DATALINE_STATUS]
        ack_event.clear()
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
        ack_event = self.ack_events[CMD_SET_AUTO_RESTORE]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
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
        self._send_packet(CMD_GET_AUTO_RESTORE_STATUS, None, None)
        ack_event = self.ack_events[CMD_GET_AUTO_RESTORE_STATUS]
        ack_event.clear()
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
        self._send_packet(CMD_GET_DEVICE_ADDRESS, None, None)

        ack_event = self.ack_events[CMD_GET_DEVICE_ADDRESS]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_device_address ACK")
            return self.device_address
        else:
            logger.error("get_device_address No ACK!")
            return None        
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
        self._send_packet(CMD_GET_FIRMWARE_VERSION, None, None)
        ack_event = self.ack_events[CMD_GET_FIRMWARE_VERSION]
        ack_event.clear()
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
        self._send_packet(CMD_GET_HARDWARE_VERSION, None, None)
        ack_event = self.ack_events[CMD_GET_HARDWARE_VERSION]
        ack_event.clear()
        if ack_event.wait(self.com_timeout):
            logger.debug("get_hardware_version ACK")
            return self.hardware_version
        else:
            logger.error("get_hardware_version No ACK!")
            return None