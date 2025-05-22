import time

# Attempt to import SMBus and provide instruction if missing
try:
    from smbus2 import SMBus
except ImportError:
    print("Error: 'smbus2' module not found. Please install it with:\n\n    pip install smbus2\n")
    exit(1)

# Configuration
BUS = 0            # I2C bus number (/dev/i2c-0)
ADDR = 0x1C        # I2C slave address
REGISTER = 0x00    # Register to read from
LENGTH = 4         # Number of bytes to read
POLL_INTERVAL = 0.1  # Seconds between polls

def read_data(bus):
    """Read a block of bytes from the I2C device."""
    return bus.read_i2c_block_data(ADDR, REGISTER, LENGTH)

def main():
    prev_data = None
    with SMBus(BUS) as bus:
        print(f"Listening for data on I2C bus {BUS}, address 0x{ADDR:02X}...")
        while True:
            try:
                data = read_data(bus)
                if data != prev_data or True:
                    print("Received data:", [hex(b) for b in data])
                    prev_data = list(data)
                time.sleep(POLL_INTERVAL)
            except OSError:
                # Bus not ready or NACK; wait and retry
                print("nothing!!")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
