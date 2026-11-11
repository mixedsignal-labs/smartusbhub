# Aging / Burn-In Cycle Demo

`examples/extras/aging_cycle.py`

## What it does

Power-cycles each channel on and off repeatedly, one channel at a time —
a quick burn-in or factory production test. Press Ctrl-C to stop early;
all channels are switched off before exit.

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- A SmartUSBHub connected over USB; optionally with loads attached to the
  channels under test

## Run

```shell
python examples/extras/aging_cycle.py
python examples/extras/aging_cycle.py --cycles 50 --on-ms 1000
python examples/extras/aging_cycle.py --cycles 100 --on-ms 2000 --off-ms 300
```

| Option | Default | Description |
| --- | --- | --- |
| `--cycles` | 10 | Power on/off cycles per channel |
| `--on-ms` | 500 | Power-on duration per cycle, in ms |
| `--off-ms` | 500 | Power-off duration per cycle, in ms |

## Expected output

```
Product: SmartUSBHub Pro-4CH  Channels: [1, 2, 3, 4]
10 cycles x 4 channels - Ctrl-C to stop

cycle 1/10  CH1  ON
cycle 1/10  CH2  ON
...
```

## Key APIs

| API | Purpose |
| --- | --- |
| `set_channel_power(ch, state=1/0)` | Power a single channel on/off |
| `set_channel_power(*channels, state=0)` | Switch everything off at the end |

## Notes

- Channels are cycled one at a time; combined with the measurement demo
  (`power_measurement_oneshot.py`) you can log voltage/current during
  burn-in.
- Total duration is roughly `cycles × channels × (on_ms + off_ms)` — the
  defaults finish 10 cycles × 4 channels in about 4 seconds.
