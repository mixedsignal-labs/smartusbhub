# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""
Sets every channel to power ON and data line connected by default, then
reads the settings back. These defaults are stored on the hub and applied
at every power-on.

Run:
    python examples/extras/power_on_defaults.py
"""

import os
import sys

# Allow running from a source checkout: add the package root to sys.path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub


def main():
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    channels = hub.get_channels()

    print("set defaults: power ON, data line connected")
    hub.set_default_power_status(*channels, enable=1, status=1)
    hub.set_default_dataline_status(*channels, enable=1, status=1)

    print(f"default power status : {hub.get_default_power_status(*channels)}")
    print(f"default dataline     : {hub.get_default_dataline_status(*channels)}")

    hub.disconnect()


if __name__ == "__main__":
    main()
