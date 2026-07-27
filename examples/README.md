# SmartUSBHub Examples

Runnable examples for the SmartUSBHub Python library. Each script is
self-contained, connects to the first hub it finds, and documents what it does
in its top-of-file docstring.

[简体中文](./README_cn.md)

## Prerequisites

- A SmartUSBHub connected over USB. The examples auto-detect it via
  `SmartUSBHub.scan_and_connect()`; no port name is required.
- Make sure the serial port is not held open by another program.

Choose one setup method:

1. Install the released package:

```bash
pip install smartusbhub
```

2. Use this source checkout:

```bash
cd smartusbhub
python -m pip install -r requirements.txt
python examples/power_control_example.py
```

The SDK itself only installs `pyserial`. The oscilloscope GUI demos require
separate, optional dependencies:

```bash
python -m pip install -r examples/requirements.txt
```

## Running

Run any script from the package root or from this source checkout:

```bash
python examples/power_control_example.py
```

## Basics

| Example | What it shows |
| --- | --- |
| [device_report.py](./device_report.py) | Read the hub's identity + runtime status; `--info-only`, `--json`, `--port` |
| [power_control_example.py](./power_control_example.py) | Turn channels on/off, individually and in groups; interlock mode |
| [setting_example.py](./setting_example.py) | Read device info; configure default states, address, operate mode and buttons; factory reset |
| [cycle_all_channels.py](./cycle_all_channels.py) | Power-cycle every controllable channel in sequence |
| [set_default_power_dataline_on.py](./set_default_power_dataline_on.py) | Configure power-on defaults (power ON, USB2 data line connected) |

## Monitoring (models with voltage/current sensing)

| Example | What it shows |
| --- | --- |
| [advanced/power_measurement_oneshot.py](./advanced/power_measurement_oneshot.py) | Continuously print per-port voltage/current via V2 request/response |
| [advanced/power_measurement_stream.py](./advanced/power_measurement_stream.py) | Continuously print per-port voltage/current via the V3 measurement stream |
| [advanced/oscilloscope.py](./advanced/oscilloscope.py) | Real-time GUI plot of voltage/current (needs PyQt5 + pyqtgraph) |
| [advanced/oscilloscope_stream.py](./advanced/oscilloscope_stream.py) | Same plot, driven by the V3 measurement streaming protocol |
| [advanced/oc_monitor_usb2_7p.py](./advanced/oc_monitor_usb2_7p.py) | Poll overcurrent active/latch status on USB2 7P models only |

## Advanced

| Example | What it shows |
| --- | --- |
| [advanced/dataline_control_example.py](./advanced/dataline_control_example.py) | Disconnect/reconnect a channel's USB2.0 data line while power stays on |
| [advanced/user_callback_example.py](./advanced/user_callback_example.py) | Register callbacks invoked when a command is acknowledged |
| [advanced/multi_device_channel_control.py](./advanced/multi_device_channel_control.py) | Discover and control several hubs at once |
