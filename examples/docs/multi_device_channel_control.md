# Multi-Device Channel Control Demo

`examples/multi_device_channel_control.py`

## What it does

Scans and connects **every** SmartUSBHub attached to the computer, then
runs a "chasing light": each channel of each device turns on for 0.1 s in
sequence, driven by the channel indicator LEDs. Press Ctrl-C to stop; all
channels are switched off and every device is disconnected on exit.

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- One or more SmartUSBHub devices connected over USB

## Run

```shell
python examples/multi_device_channel_control.py
```

## Expected output

```
Device 1: SmartUSBHub Pro-4CH (port: /dev/cu.usbmodem132301)
Device 2: SmartUSBHub Pro-4CH (port: /dev/cu.usbmodem132302)
Found 2 device(s), 8 channels total. Ctrl-C to stop.
```

Then the channel LEDs chase across all devices until you stop it.

## Key APIs

| API | Purpose |
| --- | --- |
| `SmartUSBHub.scan_and_connect(exclude_ports=...)` | Scan and connect, skipping ports already taken |
| `hub.port` / `hub.name` | Serial port path and device name |
| `set_channel_power(ch, state=1/0)` | Power a channel on/off |
| `hub.disconnect()` | Release the serial port |

## Notes

- `exclude_ports` is the trick to enumerate multiple identical devices:
  keep a set of ports already connected and pass it to the next scan, until
  the scan returns `None`.
- Only one channel is on at any moment, so total power draw stays low even
  with many devices.
