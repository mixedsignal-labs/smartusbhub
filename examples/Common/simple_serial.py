# Description: a very simple serial communication example to control the power of each channel of the SmartUSBHub
# copyright: (c) 2026 makerlabtools
# license: Apache-2.0
# version: 1.0
# author: makerlabtools
# email: makerlabtools@outlook.com

import serial
import time

serial_port = "/dev/cu.usbmodem142101"  # Replace with your actual serial port
baud_rate = 115200  # Baud rate

# Commands
get_mode_cmd = "55 5A 07 00 00 07" # Query working mode
ch1_on_cmd = "55 5A 01 01 01 03"  # Turn on channel 1
ch1_off_cmd = "55 5A 01 01 00 02"  # Turn off channel 1

def hex_str_to_bytes(hex_str):
    """
    Convert hex string to byte array.
    """
    return bytes.fromhex(hex_str)

def bytes_to_hex_str(byte_data):
    """
    Convert byte array to hex string.
    """
    return " ".join(f"{b:02X}" for b in byte_data)

try:
    # Open serial port
    s = serial.Serial(serial_port, baudrate=baud_rate, timeout=1)
    # Close previous connection if open
    if s.is_open:
        s.close()
    s.open()

    print("device connected")

    # Send counter
    send_count = 0
    current_cmd = ch1_off_cmd  # Initial state: send OFF command

    while True:
        # Convert command to bytes
        byte_cmd = hex_str_to_bytes(current_cmd)

        # Send command
        bytes_written = s.write(byte_cmd)
        send_count += 1  # Increment counter each time a command is sent

        # Receive response
        response = s.read(len(byte_cmd))  # Assume response length equals command length
        if response:
            response_str = bytes_to_hex_str(response)
            if response_str == current_cmd:  # Verify response data
                status = f"sent {send_count} times: {current_cmd} | ack: {response_str}"
            else:
                status = f"sent {send_count} times: {current_cmd} | ack: {response_str}"
                raise ValueError(f"send failed, sent: {current_cmd}, ack: {response_str}")
        else:
            status = f"sent {send_count}: {current_cmd} | no ack!"

        # Print status in the same line and flush
        print(f"\r{status}", end="", flush=True)

        # Toggle command
        current_cmd = ch1_on_cmd if current_cmd == ch1_off_cmd else ch1_off_cmd

        # Send every 500ms
        time.sleep(0.001)

except serial.SerialException as e:
    print(f"\nserial error: {e}")
except ValueError as e:
    print(f"\nerror: {e}")
    print("program exit")
except KeyboardInterrupt:
    print("\nprogram interrupted")
except Exception as e:
    print(f"\nother error: {e}")
finally:
    # Close serial port
    if 's' in locals() and s.is_open:
        s.close()
        print("\nserial is closed")
