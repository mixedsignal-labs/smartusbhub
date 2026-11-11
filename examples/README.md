# SmartUSBHub Examples

Runnable examples for the SmartUSBHub Python library. Each script is
self-contained, connects to the first hub it finds, and documents what it does
in its top-of-file docstring.

[简体中文](./README_cn.md)

## Prerequisites

- A SmartUSBHub connected over USB. The examples auto-detect it via
  `SmartUSBHub.scan_and_connect()`; no port name is required.
- Make sure the serial port is not held open by another program.
- The SDK itself only requires `pyserial`; the examples have no extra
  dependencies.

Choose one setup method:

1. Install the released package:

```bash
pip install smartusbhub
```

2. Use this source checkout:

```bash
cd smartusbhub
python -m pip install -r requirements.txt
python examples/quick_start.py
```

## Quick start

Run the examples in this order:

| Step | Example | What it shows | Guide |
| --- | --- | --- | --- |
| 1 | [quick_start.py](./quick_start.py) | Print a full device report (identity, capabilities, runtime status), then demonstrate channel power control: single channel, all channels at once, interlock mode, and device address get/set | [en](./docs/quick_start.md) / [cn](./docs/quick_start_cn.md) |
| 2 | [power_measurement_oneshot.py](./power_measurement_oneshot.py) | Continuously print per-port voltage/current via V2 request/response measurement; `--csv` export, `--interval-ms` | [en](./docs/power_measurement_oneshot.md) / [cn](./docs/power_measurement_oneshot_cn.md) |
| 3 | [multi_device_channel_control.py](./multi_device_channel_control.py) | Discover and control several hubs at once | [en](./docs/multi_device_channel_control.md) / [cn](./docs/multi_device_channel_control_cn.md) |

```bash
python examples/quick_start.py
python examples/power_measurement_oneshot.py
python examples/multi_device_channel_control.py
```

## Extras

Additional demos for less common needs, in [extras/](./extras/):

| Example | What it shows | Guide |
| --- | --- | --- |
| [extras/dataline_control.py](./extras/dataline_control.py) | Disconnect/reconnect a channel's data line while power stays on | [en](./docs/extras_dataline_control.md) / [cn](./docs/extras_dataline_control_cn.md) |
| [extras/power_on_defaults.py](./extras/power_on_defaults.py) | Configure power-on defaults: power ON, data line connected | [en](./docs/extras_power_on_defaults.md) / [cn](./docs/extras_power_on_defaults_cn.md) |
| [extras/aging_cycle.py](./extras/aging_cycle.py) | Power-cycle every channel N times - burn-in / production test | [en](./docs/extras_aging_cycle.md) / [cn](./docs/extras_aging_cycle_cn.md) |
| [extras/alerts.py](./extras/alerts.py) | Configure an overcurrent alert rule, subscribe and watch events | [en](./docs/extras_alerts.md) / [cn](./docs/extras_alerts_cn.md) |
