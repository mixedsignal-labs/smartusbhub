#!/usr/bin/env python3
# Description: full SmartUSBHub report - device identity plus runtime status
# copyright: (c) 2026 MixedSignalLab
# license: Apache-2.0
# version: 1.0
# author: zhang <mixedsignallab@outlook.com>
# email: mixedsignallab@outlook.com
# website: https://www.mixedsignallab.com
"""
Get a full report from a SmartUSBHub.

Reads the hub's identity/configuration via ``get_device_info()`` and, unless
``--info-only`` is given, also reads its capabilities and runtime status
(power, data lines, overcurrent, measurements). Without ``--port`` every
SmartUSBHub serial port found is reported.

Usage:
    python examples/device_report.py
    python examples/device_report.py --port /dev/tty.usbmodemXXX
    python examples/device_report.py --info-only          # identity only
    python examples/device_report.py --json               # raw JSON output
"""

import argparse
import json
import os
import sys
from pprint import pprint

# Add project root to sys.path so we can import smartusbhub from any location.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import FeatureNotSupportedError, PRODUCT_TYPE_TABLE, SmartUSBHub


# Human-readable labels for the fields returned by get_device_info().
INFO_LABELS = [
    ("id", "Port / ID"),
    ("address", "Device address"),
    ("device_alias", "Alias"),
    ("serial_no", "Serial number"),
    ("product_type", "Product type"),
    ("max_channels", "Channel count"),
    ("hardware_version", "Hardware version"),
    ("firmware_version", "Firmware version"),
    ("operate_mode", "Operate mode"),
    ("auto_restore", "Auto restore"),
    ("button_control_status", "Button control"),
]


def _safe_call(func, *args, default=None, **kwargs):
    """Call an SDK getter, turning unsupported/error cases into dict markers."""
    try:
        return func(*args, **kwargs)
    except (FeatureNotSupportedError, NotImplementedError) as exc:
        return {"unsupported": str(exc)}
    except Exception as exc:
        return {"error": str(exc)}


def _capabilities(hub):
    info = PRODUCT_TYPE_TABLE.get(hub.product_type, {})
    return {
        "adc": bool(info.get("enable_adc")),
        "usb2_data_switch": bool(info.get("enable_usb2_data_switch")),
        "usb3_data_switch": bool(info.get("enable_usb3_data_switch")),
        "ilim_switch": bool(info.get("enable_ilim_switch")),
    }


def read_report(port, info_only=False):
    """Read identity (+ optionally capabilities and runtime status) from one hub."""
    with SmartUSBHub(port) as hub:
        info = hub.get_device_info() or {}
        report = {"port": port, "device": info}
        if info_only:
            return report

        channels = tuple(hub.get_channels())
        caps = _capabilities(hub)
        report["capabilities"] = caps
        report["parameters"] = {
            "channel_names": _safe_call(hub.get_channel_names, *channels),
            "device_address": _safe_call(hub.get_device_address),
            "device_alias": _safe_call(hub.get_device_alias),
            "operate_mode": _safe_call(hub.get_operate_mode),
            "auto_restore": _safe_call(hub.get_auto_restore_status),
            "button_control": _safe_call(hub.get_button_control_status),
            "defaults": {
                "power": _safe_call(hub.get_default_power_status, *channels),
                "usb2_dataline": _safe_call(hub.get_default_dataline_status, *channels),
            },
        }
        runtime = {
            "power": _safe_call(hub.get_channel_power_status, *channels),
            "usb2_dataline": _safe_call(hub.get_channel_usb2_dataline_status, *channels),
            "overcurrent": _safe_call(hub.get_channel_oc_status),
        }
        if caps["adc"]:
            runtime["measurements"] = _safe_call(hub.get_channel_measurements, *channels)
        else:
            runtime["measurements"] = {"unsupported": "ADC not supported by this product"}
        report["runtime"] = runtime
        return report


def print_info(info):
    print("\n=== Device Info ===")
    width = max(len(label) for _, label in INFO_LABELS)
    for key, label in INFO_LABELS:
        value = info.get(key, "N/A")
        if key in ("hardware_version", "firmware_version") and isinstance(value, int):
            value = f"V1.{value}"
        elif value in (None, ""):
            value = "N/A"
        print(f"  {label:<{width}} : {value}")


def print_human(report):
    print(f"\n########## {report['port']} ##########")
    print_info(report["device"])
    if "capabilities" not in report:  # info-only
        print()
        return
    print("\n=== Capabilities ===")
    pprint(report["capabilities"], sort_dicts=False)
    print("\n=== Parameters ===")
    pprint(report["parameters"], sort_dicts=False)
    print("\n=== Runtime status ===")
    pprint(report["runtime"], sort_dicts=False)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Read SmartUSBHub device info and runtime status.")
    parser.add_argument("--port", action="append",
                        help="Serial port to read. Can be used more than once. "
                             "When omitted, all matching SmartUSBHub ports are scanned.")
    parser.add_argument("--info-only", action="store_true",
                        help="Print only the device identity, skip runtime status.")
    parser.add_argument("--json", action="store_true",
                        help="Print JSON instead of human-readable output.")
    args = parser.parse_args()

    ports = args.port or SmartUSBHub.scan_available_ports()
    if not ports:
        print("No SmartUSBHub serial ports found.", file=sys.stderr)
        return 1

    results = []
    for port in ports:
        try:
            results.append(read_report(port, info_only=args.info_only))
        except Exception as exc:
            results.append({"port": port, "error": str(exc)})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            if "error" in result:
                print(f"\n########## {result['port']} ##########")
                print(f"ERROR: {result['error']}")
            else:
                print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
