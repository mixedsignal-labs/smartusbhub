# Alert Demo (Overcurrent)

`examples/extras/alerts.py`

## What it does

Sets an overcurrent alert rule on one channel (threshold in mA), registers
an event callback, subscribes to alert events, and polls the alert status
once per second. To see it fire, draw more current than the threshold on
the watched channel.

The demo action is `power_off_lock`: when the threshold is exceeded the
hub cuts power to that channel and locks it — a real protection response,
not just a notification.

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- A SmartUSBHub connected over USB, with a device/load on the watched
  channel

## Run

```shell
python examples/extras/alerts.py
python examples/extras/alerts.py --channel 2 --threshold 200
```

| Option | Default | Description |
| --- | --- | --- |
| `--channel` | 1 | Channel to watch |
| `--threshold` | 500 | Overcurrent threshold in mA |

## Expected output

```
alert rule: {'channel': 1, 'type': 'overcurrent', 'threshold': 500, 'action': 'power_off_lock'}
watching CH1 for overcurrent > 500 mA - Ctrl-C to stop

alert status: [...]
ALERT on CH1: {...}          <- when the threshold is exceeded
alert status: [...]          <- channel now shows an alert / power locked
```

## Key APIs

| API | Purpose |
| --- | --- |
| `set_alert_config(channel, "overcurrent", threshold_ma, action=...)` | Create an alert rule; `threshold` is in mA |
| `register_callback(CMD_ALERT_EVENT, fn)` | Register a callback invoked when an alert event arrives |
| `subscribe_alert_events(True/False)` | Start/stop pushing alert events to the host |
| `get_alert_status()` | Poll the current alert status |

## Notes

- After `power_off_lock` triggers, the channel stays locked; clear the
  lock (from the app or via the SDK) before reusing the channel.
- The callback runs when the device pushes the event; the one-second poll
  in the demo is a belt-and-suspenders way to also see the status field.
