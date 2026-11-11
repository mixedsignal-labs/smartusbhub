# Data Line Control Demo

`examples/extras/dataline_control.py`

## What it does

Disconnects the data lines of the first channel, waits 2 seconds, then
reconnects them — while **power stays on the whole time**. Watch the
downstream device: it re-enumerates (disconnect/reconnect sound on the
host) without ever losing power.

This is the signature capability that separates SmartUSBHub from a plain
USB hub: software control of the data lines independent of power.

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- A SmartUSBHub with something plugged into channel 1 (so you can see the
  re-enumeration)

## Run

```shell
python examples/extras/dataline_control.py
```

## Expected output

```
Product: SmartUSBHub Pro-4CH  Channel under test: 1
disconnect data line (power stays on)
data line status: [{'channel': 1, 'dataline': 0}]
reconnect data line
data line status: [{'channel': 1, 'dataline': 1}]
```

## Key APIs

| API | Purpose |
| --- | --- |
| `set_channel_dataline(ch, state=0/1)` | Disconnect/reconnect the channel's data lines |
| `get_channel_dataline_status(ch)` | Read back the data line state |
| `set_channel_power(ch, state=1)` | Power on first — the demo keeps power on throughout |

## Notes

- On USB2 models this toggles the D+/D- pair; on USB3 models it also
  covers the SuperSpeed pairs, so the whole data path drops.
- Typical uses: force a USB device to re-enumerate without physically
  replugging it, recover a hung device remotely, or scripted device
  toggling in test benches.
