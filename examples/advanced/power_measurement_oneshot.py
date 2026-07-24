"""
@file power_measurement_oneshot.py
@brief USB Channel Power Measurement — V2 request/response monitor.
@copyright (c) 2026 MixedSignalLab
@license Apache-2.0
@author zhang <mixedsignallab@outlook.com>
@website https://www.mixedsignallab.com

Run:
    python examples/advanced/power_measurement_oneshot.py
"""

import sys
import os
import time
import argparse
import csv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

DEFAULT_INTERVAL_MS = 200


def _read_v2_measurements(hub, channels):
    rows = []
    for ch in channels:
        voltage = hub.get_channel_voltage(ch)
        current = hub.get_channel_current(ch)
        rows.append((ch, voltage, current))
    return rows


def _resolve_product_and_channels(hub):
    product_info = SmartUSBHub.get_product_info(hub.product_type)
    if not product_info:
        if hub.product_type is None:
            print("Unknown product type. Cannot continue.")
        else:
            print(f"Unknown product type (0x{hub.product_type:02X}). Cannot continue.")
        sys.exit(1)

    if not product_info.get("enable_adc", False):
        print(
            f"Product '{product_info['name']}' does not support voltage/current monitoring.\n"
            f"This feature requires a hub with INA3221 (e.g. HBP_USB2_7CH)."
        )
        sys.exit(1)

    channels = list(hub.get_channels())
    return product_info, channels


def main():
    parser = argparse.ArgumentParser(description="USB channel voltage/current V2 request-response monitor")
    parser.add_argument("--csv", metavar="FILE", help="log data to CSV file")
    parser.add_argument("--settle-ms", type=int, default=0,
                        help="wait N ms after power-on before first read")
    parser.add_argument("--interval-ms", type=int, default=DEFAULT_INTERVAL_MS,
                        help="poll interval in ms (default 200)")
    args = parser.parse_args()

    # ── Connect ──────────────────────────────────────────────────────────────
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found. Check USB connection.")
        sys.exit(1)

    csv_file = None
    try:
        product_info, channels = _resolve_product_and_channels(hub)

        print(
            f"Connected: {product_info['name']}  "
            f"({product_info['description']})  "
            f"| {len(channels)} channels"
        )

        # ── Power on and settle ──────────────────────────────────────────────
        hub.set_channel_power(*channels, state=1)
        if args.settle_ms > 0:
            time.sleep(args.settle_ms / 1000)

        print(f"V2 request/response mode. Polling every {args.interval_ms} ms — Ctrl-C to stop.\n")

        # ── CSV setup ────────────────────────────────────────────────────────
        writer = None
        if args.csv:
            csv_file = open(args.csv, "w", newline="")
            writer = csv.writer(csv_file)
            writer.writerow(
                ["timestamp_s"] +
                [f"ch{c}_mV" for c in channels] +
                [f"ch{c}_mA" for c in channels]
            )

        # ── Display header ───────────────────────────────────────────────────
        t_prev = time.perf_counter()
        sweep = 0
        header = f"{'CH':<4} {'Voltage':>10} {'Current':>10}    {'Interval':>10} {'Sweep':>8}"
        print(header)
        print("-" * len(header))
        for _ in channels:
            print()
        up = f"\x1b[{len(channels)}A"

        # ── Main loop ────────────────────────────────────────────────────────
        while True:
            t0 = time.perf_counter()
            data = _read_v2_measurements(hub, channels)
            t1 = time.perf_counter()

            interval_ms = (t1 - t_prev) * 1000
            sweep_ms = (t1 - t0) * 1000
            t_prev = t1
            sweep += 1

            lines = []
            for idx, (ch, voltage, current) in enumerate(data):
                v = voltage if voltage is not None else -1
                i = current if current is not None else -1
                stat = f"  Δ{interval_ms:6.1f}ms  {sweep_ms:5.1f}ms" if idx == 0 else ""
                lines.append(f"CH{ch}  {v:8d} mV  {i:8d} mA{stat}")

            sys.stdout.write(up + "\n".join(lines) + "\n")
            sys.stdout.flush()

            if writer:
                v_vals = [row[1] if row[1] is not None else -1 for row in data]
                i_vals = [row[2] if row[2] is not None else -1 for row in data]
                writer.writerow([f"{t1:.6f}"] + v_vals + i_vals)
                csv_file.flush()

            elapsed_ms = (time.perf_counter() - t0) * 1000
            sleep_ms = args.interval_ms - elapsed_ms
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if csv_file:
            csv_file.close()
        hub.disconnect()


if __name__ == "__main__":
    main()
