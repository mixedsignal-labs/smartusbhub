# Power-On Defaults Demo

`examples/extras/power_on_defaults.py`

## What it does

Configures every channel's power-on default to "power ON + data line
connected", then reads the settings back to confirm.

These defaults are stored in the hub's non-volatile memory and applied
automatically every time the hub powers up (or a channel is re-enabled).
It is a one-time configuration, not something you need to run repeatedly.

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- A SmartUSBHub connected over USB

## Run

```shell
python examples/extras/power_on_defaults.py
```

## Expected output

```
set defaults: power ON, data line connected
default power status : [{'channel': 1, 'enable': 1, 'status': 1}, ...]
default dataline     : [{'channel': 1, 'enable': 1, 'status': 1}, ...]
```

## Key APIs

| API | Purpose |
| --- | --- |
| `set_default_power_status(*channels, enable=1, status=1)` | Default power state applied at power-on; `enable` controls whether the rule is active, `status` is ON/OFF |
| `set_default_dataline_status(*channels, enable=1, status=1)` | Default data line state applied at power-on |
| `get_default_power_status(*channels)` / `get_default_dataline_status(*channels)` | Read back the stored defaults |

## Notes

- The write goes to flash memory — settings survive power cycles.
- To make channels default to OFF at power-on, run the same script with
  `status=0`.
- These settings can also be changed from the SmartUSBHub app; this demo
  shows how to do it programmatically.
