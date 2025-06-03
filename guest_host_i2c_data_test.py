from smbus2 import SMBus
import argparse

def send_data(bus_num: int, slave_addr: int, data: bytes) -> None:
    """
    Use an SMBus block write to send `data` to `slave_addr`
    on bus `bus_num`.
    """
    with SMBus(bus_num) as bus:
        # The "command" byte can be 0 if you don't have a register concept.
        # SMBus limits blocks to 32 bytes; for longer data you'd need to chunk.
        bus.write_i2c_block_data(slave_addr, 0x00, list(data))
        print(f"Sent {list(data)} to 0x{slave_addr:02X} on bus {bus_num}")

parser = argparse.ArgumentParser(
                    prog='Host to Guest I2C test',
                    description='test for i2c comm',
                    epilog='nothing')
parser.add_argument("--host-bus",default=None)
parser.add_argument("--slave-addr",default=None)

if __name__ == "__main__":
    args = parser.parse_args()
    if not args.host_bus:
        raise Exception("Host bus (i2c stub) must be specified") 
    if not args.slave_addr:
        raise Exception("I2C slave address must be specified")
    HOST_BUS   = int(args.host_bus)        # e.g. /dev/i2c-13 if that’s your stub
    SLAVE_ADDR = int(args.slave_addr)      # decimal 28
    #PAYLOAD    = bytes([0xDE, 0xAF, 0xFA, 0xEE])
    PAYLOAD_STR = "PAULO LINARES"#"NTU RULES!"
    PAYLOAD    = bytes([ord(p) for p in PAYLOAD_STR])

    send_data(HOST_BUS, SLAVE_ADDR, PAYLOAD)