# Power Measurement Demo (Request/Response)

`examples/power_measurement_oneshot.py`

## What it does

Powers on all channels, then polls the voltage and current of every
channel in a loop and prints them in millivolts / milliamps. Optionally
logs the data to a CSV file. Press Ctrl-C to stop.

This demo uses the V2 request/response measurement: the script asks the
hub for one sample per channel each round. It works on all models with
measurement capability (ADC models).

## Prerequisites

- Python 3.7+, SDK installed or source checkout
- A measurement-capable SmartUSBHub connected over USB
- Something drawing current on the channels (a phone, a small load) makes
  the output meaningful; with nothing attached you will read ~0 mA

## Run

```shell
python examples/power_measurement_oneshot.py
python examples/power_measurement_oneshot.py --interval-ms 500
python examples/power_measurement_oneshot.py --csv data.csv
```

| Option | Default | Description |
| --- | --- | --- |
| `--interval-ms` | 200 | Poll interval between rounds, in ms |
| `--csv FILE` | off | Also write samples to a CSV file |

## Expected output

```
Product: SmartUSBHub Pro-4CH  Channels: [1, 2, 3, 4]
Polling every 200 ms - Ctrl-C to stop

CH1    5100 mV     420 mA
CH2    5098 mV       0 mA
CH3    5101 mV     180 mA
CH4    5099 mV       0 mA
```

The CSV file has one row per round: `timestamp_s, ch1_mV, ..., ch1_mA, ...`.

## Key APIs

| API | Purpose |
| --- | --- |
| `get_channel_voltage(ch)` | Instantaneous voltage of one channel, in mV |
| `get_channel_current(ch)` | Instantaneous current of one channel, in mA |
| `set_channel_power(ch, state=1)` | Power on before measuring |

## Notes

- Models without measurement hardware return an error for these calls;
  check `get_capability()` if you are unsure whether your model supports
  measurement.
- For continuous high-rate acquisition, see the streaming measurement
  section of the SDK documentation instead — this demo is intentionally
  simple.
