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
from scapy.all import *
import struct
import threading

# Try importing SMBus, instruct if missing
try:
    from smbus2 import SMBus
except ImportError:
    print("Error: 'smbus2' module not found. Please install it with:\n\n    pip install smbus2\n")
    sys.exit(1)


MONITOR_IP = "172.24.100.9"
MONITOR_PORT = 5555


def read_bytes(bus,length,addr):
    """Read LENGTH bytes, one register at a time."""
    data = []
    for reg in range(length):
        try:
            byte = bus.read_byte_data(addr, reg)
        except OSError:
            # NACK or bus error; no valid data right now
            return None
        data.append(byte)
    return data


def clear_buffer(bus,length,addr):
    """Write zeroes to all registers to clear the buffer."""
    for reg in range(length):
        try:
            bus.write_byte_data(addr, reg, 0x00)
        except OSError:
            # Ignore write errors
            pass

def send_data_udp_monitor(payload):
    pkt = (
    IP(dst=MONITOR_IP) /
    UDP(sport=12345, dport=MONITOR_PORT) /
    Raw(load=payload)
    )   
    sendp(pkt, iface="eth0", verbose=False)
    return

class FakeSensorI2C():
    def __init__(self,alpha,timeout):
        self.buffer = []
        self.alpha = alpha
        self.scale = 2**16 - 1  # 65535
        self.min_val = -6.0
        self.max_val = 6.0
        self.timeout = timeout
        self.readtime = time.time()
        self.lock = threading.Lock()
        self.result_ready = threading.Event()
        self.started = False
    def filter(self,data_bytes):
        dataraw = float(struct.unpack('<H', data_bytes)[0])
        data = (dataraw / self.scale) * (self.max_val - self.min_val) + self.min_val
        with self.lock:
            if self.buffer:
                prev = self.buffer[-1]
                filtered = self.alpha * prev + (1.0 - self.alpha) * data
            else:
                filtered = data

            self.buffer.append(filtered)
            self.readtime = time.time()

            if not self.started:
                self.started = True
                self.thread = threading.Thread(target=self._monitor, daemon=True)
                self.thread.start()
        self.result_ready.set()

    def _monitor(self):
        while True:
            triggered = self.result_ready.wait(timeout=self.timeout)
            with self.lock:
                now = time.time()
                if now - self.readtime > self.timeout and self.buffer:
                    payload = ",".join(f"{v:.4f}" for v in self.buffer).encode()
                    print(f"[TIMEOUT] Sending buffer: {self.buffer}")
                    send_data_udp_monitor(payload)
                    self.buffer.clear()
            self.result_ready.clear()




# Configuration
#BUS = 0              # I²C bus number (/dev/i2c-0)
#ADDR = 0x1C          # I²C slave 
#LENGTH = 4           # Number of bytes to read (registers 0x00 .. 0x03)
#POLL_INTERVAL = 0.5  # Seconds between polls

parser = argparse.ArgumentParser(prog='Guest I2C continuous reading',
                    description='test for i2c comm',
                    epilog='nothing')

parser.add_argument("--addr",default=None)
parser.add_argument("--len",default=None)
parser.add_argument("--bus",default="0")
parser.add_argument("--srate",default=None)


def main():
    args = parser.parse_args()
    if not args.slave_addr:
        raise Exception("I2C slave address must be specified")
    if not args.msg_length:
        raise Exception("I2C message length must be specified")
    if not args.sampling_rate:
        raise Exception("Sampling rate must be specified")   
    
    BUS = int(args.bus)              # I²C bus number (/dev/i2c-0)
    ADDR = int(args.addr)          # I²C slave 
    LENGTH = int(args.len)           # Number of bytes to read (registers 0x00 .. 0x03)
    POLL_INTERVAL = float(1/(float(args.srate)+2))  # Seconds between polls

    prev = None

    sensor1 = FakeSensorI2C(alpha=0.86,timeout=1.0)
    sensor2 = FakeSensorI2C(alpha=0.86,timeout=1.0)

    with SMBus(BUS) as bus:
        print(f"Listening for new data on I2C bus {BUS}, address 0x{ADDR:02X} (poll every {POLL_INTERVAL}s)...")
        while True:
            data = read_bytes(bus,LENGTH,ADDR)
            if data is not None:
                if any(data):
                    sensor1.filter(data[0:2])
                    sensor2.filter(data[2:4])
                    print("Received data:", [f"0x{b:02X}" for b in data])
                    prev = data
                    clear_buffer(bus,LENGTH,ADDR)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()