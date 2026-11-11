# Quick Start Demo

`examples/quick_start.py`

## What it does

Connects to the first SmartUSBHub found and demonstrates the three most
common things you do with the device:

1. **Device report** — product name, hardware/firmware version, channel
   list, capability flags, current power status and USB2 data line status
   of every channel.
2. **Power control** — turn a single channel on/off, turn all channels
   on/off at once, and run interlock mode (only one channel powered at a
   time), then restore normal mode.
3. **Device address** — read the current device address and write it back.

## Prerequisites

- Python 3.7+
- The SDK installed (`pip install smartusbhub`) or run from a source
  checkout (the script adds the package root to `sys.path` automatically)
- One SmartUSBHub connected over USB

## Run

```shell
python examples/quick_start.py
```

To target a specific serial port instead of scanning:

```python
hub = SmartUSBHub("/dev/cu.usbmodem132301")
```

## Expected output

```
=== Device Info ===
  Product name      : SmartUSBHub Pro-4CH
  Hardware version  : V1.2
  ...
=== Power control ===
turn on channel 1
turn off channel 1
turn on all channels [1, 2, 3, 4] at once
...
=== Device address ===
current device address: 0
device address set to: 0
```

## Key APIs

| API | Purpose |
| --- | --- |
| `SmartUSBHub.scan_and_connect()` | Scan all serial ports and connect to the first hub found |
| `get_product_name() / get_hardware_version() / get_firmware_version()` | Device identity |
| `get_channels()` | Tuple of controllable channel numbers |
| `get_capability()` | Feature flags of this model |
| `get_channel_power_status(*channels)` | Current power state per channel |
| `get_channel_usb2_dataline_status(*channels)` | Current data line state per channel |
| `set_channel_power(ch, state=1/0)` | Power a channel on/off (multiple channels allowed) |
| `set_channel_power_interlock(ch)` / `set_channel_power_interlock(None)` | Interlock mode: exactly one channel on at a time; `None` restores normal mode |
| `get_device_address()` / `set_device_address(addr)` | Read/write the device address |

## Notes

- The device address demo writes the address it just read back, so running
  the demo never changes your device configuration.
- Interlock mode is useful when the downstream devices must never draw
  power simultaneously (e.g. shared power budget).
