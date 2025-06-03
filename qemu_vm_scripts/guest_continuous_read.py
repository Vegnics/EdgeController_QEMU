#!/usr/bin/env python3
"""
i2c_listener_safe.py

Continuously polls an I²C device by reading each byte register
individually (via SMBus read_byte_data) to avoid hangs or unsupported
ioctls, and prints whenever a new payload appears.
"""

import time
import sys
import argparse

# Try importing SMBus, instruct if missing
try:
    from smbus2 import SMBus
except ImportError:
    print("Error: 'smbus2' module not found. Please install it with:\n\n    pip install smbus2\n")
    sys.exit(1)



def read_bytes(bus):
    """Read LENGTH bytes, one register at a time."""
    data = []
    for reg in range(LENGTH):
        try:
            byte = bus.read_byte_data(ADDR, reg)
        except OSError:
            # NACK or bus error; no valid data right now
            return None
        data.append(byte)
    return data

def clear_buffer(bus):
    """Write zeroes to all registers to clear the buffer."""
    for reg in range(LENGTH):
        try:
            bus.write_byte_data(ADDR, reg, 0x00)
        except OSError:
            # Ignore write errors
            pass

# Configuration
BUS = 0              # I²C bus number (/dev/i2c-0)
ADDR = 0x1C          # I²C slave 
LENGTH = 4           # Number of bytes to read (registers 0x00 .. 0x03)
POLL_INTERVAL = 0.5  # Seconds between polls

parser = argparse.ArgumentParser(prog='Guest I2C continuous reading',
                    description='test for i2c comm',
                    epilog='nothing')

parser.add_argument("--slave-addr",default=None)
parser.add_argument("--msg-length",default=None)
parser.add_argument("--slave-bus",default="0")


def main():
    args = parser.parse_args()
    if not args.slave_addr:
        raise Exception("I2C slave address must be specified")
    if not args.msg_length:
        raise Exception("I2C message length must be specified")  
    
    BUS = int(args.slave_bus)              # I²C bus number (/dev/i2c-0)
    ADDR = int(args.slave_addr)          # I²C slave 
    LENGTH = int(args.msg_length)           # Number of bytes to read (registers 0x00 .. 0x03)
    POLL_INTERVAL = 0.5  # Seconds between polls

    prev = None

    with SMBus(BUS) as bus:
        print(f"Listening for new data on I2C bus {BUS}, address 0x{ADDR:02X} (poll every {POLL_INTERVAL}s)...")
        while True:
            data = read_bytes(bus)
            if data is not None:
                if any(data):
                    print("Received data:", [f"0x{b:02X}" for b in data])
                    prev = data
                    clear_buffer(bus)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()