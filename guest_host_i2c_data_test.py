from smbus2 import SMBus

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

if __name__ == "__main__":
    HOST_BUS   = 13        # e.g. /dev/i2c-13 if that’s your stub
    SLAVE_ADDR = 0x1C      # decimal 28
    #PAYLOAD    = bytes([0xDE, 0xAF, 0xFA, 0xEE])
    PAYLOAD_STR = "PAULO LINARES"#"NTU RULES!"
    PAYLOAD    = bytes([ord(p) for p in PAYLOAD_STR])

    send_data(HOST_BUS, SLAVE_ADDR, PAYLOAD)