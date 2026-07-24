# USB Channel Power Monitor — per-port voltage & current.
# Project website: https://www.mixedsignallab.com
#
# Automatically detects the connected hub, reads channel count from the
# device, and checks whether voltage/current monitoring is supported.
# Falls back to a clear error message if the product does not have ADC.
#
# Usage:
#   python ina3221_poll.py
#   python ina3221_poll.py --csv output.csv
#   python ina3221_poll.py --interval-ms 20
#   python ina3221_poll.py --request-response

import sys
import os
import time
import argparse
import csv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

DEFAULT_INTERVAL_MS = 10


def _measurements_to_rows(measurements, channels):
    if measurements is None:
        return [(ch, None, None, False, False) for ch in channels]
    return [
        (
            ch,
            measurements.get(ch, {}).get("voltage"),
            measurements.get(ch, {}).get("current"),
            measurements.get(ch, {}).get("fresh", False),
            measurements.get(ch, {}).get("valid", False),
        )
        for ch in channels
    ]


def main():
    parser = argparse.ArgumentParser(description="USB channel voltage/current monitor")
    parser.add_argument("--csv", metavar="FILE", help="log data to CSV file")
    parser.add_argument("--settle-ms", type=int, default=0,
                        help="wait N ms after power-on before first read")
    parser.add_argument("--interval-ms", type=int, default=DEFAULT_INTERVAL_MS,
                        help="poll interval in ms (stream mode, default 10)")
    parser.add_argument("--request-response", action="store_true",
                        help="use V3 request/response per sweep instead of streaming")
    args = parser.parse_args()

    # ── Connect ──────────────────────────────────────────────────────────────
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found. Check USB connection.")
        sys.exit(1)

    # ── Check ADC support ────────────────────────────────────────────────────
    product_info = SmartUSBHub.get_product_info(hub.product_type)
    if not product_info:
        print(f"Unknown product type (0x{hub.product_type:02X}). Cannot continue.")
        hub.disconnect()
        sys.exit(1)

    if not product_info.get("enable_adc", False):
        print(
            f"Product '{product_info['name']}' does not support voltage/current monitoring.\n"
            f"This feature requires a hub with INA3221 (e.g. HBP_USB2_7CH)."
        )
        hub.disconnect()
        sys.exit(1)

    # ── Resolve channel list from device ────────────────────────────────────
    n_ch = hub.max_channels
    if not isinstance(n_ch, int) or n_ch <= 0:
        n_ch = product_info["channels"]
    channels = list(range(1, n_ch + 1))

    print(
        f"Connected: {product_info['name']}  "
        f"({product_info['description']})  "
        f"| {n_ch} channels"
    )

    # ── Power on and settle ──────────────────────────────────────────────────
    hub.set_channel_power(*channels, state=1)
    if args.settle_ms > 0:
        time.sleep(args.settle_ms / 1000)

    if not args.request_response:
        hub.set_channel_measurement_stream(*channels, enabled=True)
        print(f"Stream started. Polling every {args.interval_ms} ms — Ctrl-C to stop.\n")
    else:
        print("Request-response mode — Ctrl-C to stop.\n")

    # ── CSV setup ────────────────────────────────────────────────────────────
    csv_file = None
    writer = None
    if args.csv:
        csv_file = open(args.csv, "w", newline="")
        writer = csv.writer(csv_file)
        writer.writerow(
            ["timestamp_s"] +
            [f"ch{c}_mV" for c in channels] +
            [f"ch{c}_mA" for c in channels]
        )

    # ── Display header ───────────────────────────────────────────────────────
    t_prev = time.perf_counter()
    sweep  = 0
    header = f"{'CH':<4} {'Voltage':>10} {'Current':>10} {'FV':>3}    {'Interval':>10} {'Sweep':>8}"
    print(header)
    print("-" * len(header))
    for _ in channels:
        print()
    UP = f"\x1b[{len(channels)}A"

    # ── Main loop ────────────────────────────────────────────────────────────
    try:
        while True:
            t0 = time.perf_counter()

            if args.request_response:
                measurements = hub.get_channel_measurements(*channels)
            else:
                # Non-blocking: background receiver keeps the cache fresh.
                # Commands (set_channel_power etc.) can be called here freely.
                measurements = hub.get_latest_measurements(*channels)

            data = _measurements_to_rows(measurements, channels)

            t1 = time.perf_counter()
            interval_ms = (t1 - t_prev) * 1000
            sweep_ms    = (t1 - t0) * 1000
            t_prev = t1
            sweep += 1

            v_vals = [d[1] if d[1] is not None else -1 for d in data]
            i_vals = [d[2] if d[2] is not None else -1 for d in data]

            lines = []
            for idx, (ch, v, i, fresh, valid) in enumerate(data):
                v  = v if v is not None else -1
                i  = i if i is not None else -1
                fv = ("F" if fresh else "-") + ("V" if valid else "-")
                stat = f"  Δ{interval_ms:6.1f}ms  {sweep_ms:5.1f}ms" if idx == 0 else ""
                lines.append(f"CH{ch}  {v:8d} mV  {i:8d} mA {fv:>3}{stat}")

            sys.stdout.write(UP + "\n".join(lines) + "\n")
            sys.stdout.flush()

            if writer:
                writer.writerow([f"{t1:.6f}"] + v_vals + i_vals)
                csv_file.flush()

            elapsed_ms = (time.perf_counter() - t0) * 1000
            sleep_ms = args.interval_ms - elapsed_ms
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000)

    except KeyboardInterrupt:
        print(f"\nStopped after {sweep} sweeps.")
    finally:
        if not args.request_response:
            hub.set_channel_measurement_stream(*channels, enabled=False)
        if csv_file:
            csv_file.close()
        hub.disconnect()


if __name__ == "__main__":
    main()
