# Description: 
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import time
sys.path.append('../')
from smartusbhub import SmartUSBHub

def main():
    hub_list = SmartUSBHub.scan_available_ports()# Scan all available ports
    print("available device:", hub_list)
    ch_count = 5 #todo change to get channel count
    
    hub = SmartUSBHub.scan_and_connect()# Scan and connect to the first SmartUSBHub found

    if hub is None:
        print("No SmartUSBHub found")
        sys.exit(1)

    device_info = hub.get_device_info()
    print("device info:", device_info)
    # Press Enter to toggle between full-speed charging (normal ILIM) and low-current mode.
    mode = "HIGH_POWER"  # or "LOW_CURRENT"

    print("\nInteractive battery test demo")
    print("- Press Enter to toggle mode")
    print("- Type 'q' then Enter to quit\n")

    try:
        while True:
            cmd = input(f"Current mode: {mode}. Press Enter to toggle (q to quit): ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                print("Exiting...")
                break

            # Toggle mode
            if mode == "HIGH_POWER":
                mode = "LOW_CURRENT"
                print("-> Switching to LOW_CURRENT (ilim mode)")

                # Ensure VBUS is on, then enable low-current mode
                hub.set_channel_low_current(1, 2, 3, 4, state=1)
            else:
                mode = "HIGH_POWER"
                print("-> Switching to HIGH_POWER (full-speed charging)")

                # Disable low-current mode, keep VBUS on
                hub.set_channel_power(1, 2, 3, 4, state=1)

            print(f"[STATE] mode={mode}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        hub.disconnect()
        
if __name__ == "__main__":
    main()
