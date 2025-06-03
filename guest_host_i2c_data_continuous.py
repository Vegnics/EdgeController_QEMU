from smbus2 import SMBus
import argparse
import numpy as np
from matplotlib import pyplot as plt
from time import sleep
from scapy.all import *

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

def quantize_data_16(data:np.ndarray,min_val,max_val):
    scale = (2**16-1)
    quantized = np.clip(np.floor(scale*(data-min_val)/(max_val - min_val)),0,2**32-1)
    return np.uint32(quantized)  

def qdata_to_bytes(qdata:np.ndarray):
    return qdata.astype('<u2').tobytes()



parser = argparse.ArgumentParser(
                    prog='Host to Guest I2C test',
                    description='test for i2c comm',
                    epilog='nothing')
parser.add_argument("--host-bus",default=None)
parser.add_argument("--slave-addr",default=None)

N_points = 101 

x_signal = np.linspace(0,3,N_points)
y_signal1 = 3.0*np.sin(2*3.141592*0.5*x_signal) + 0.4*np.random.uniform(-1.0,1.0,x_signal.shape)
y_signal1 = np.clip(y_signal1,-6.0,6.0)
y_signal2 = 5.0*np.sin(2*3.141592*2.0*x_signal) + 0.1*np.random.normal(0.0,6.0,x_signal.shape) + 0.2*np.random.uniform(-1.0,1.0,x_signal.shape) 
shot_noise = np.random.binomial(1,0.92,x_signal.shape)
salt_pep = np.random.binomial(1,0.5,x_signal.shape)
y_signal2_salt = np.where(np.logical_and(shot_noise==0,salt_pep==1),6.0,y_signal2)
y_signal2_salt_pepper = np.where(np.logical_and(shot_noise==0,salt_pep==0),-6.0,y_signal2_salt)
y_signal2 = np.clip(y_signal2_salt_pepper,-6.0,6.0)

quantized_1 = quantize_data_16(y_signal1,-6.0,6.0)
quantized_2 = quantize_data_16(y_signal2_salt_pepper,-6.0,6.0)

bytes_s1 = qdata_to_bytes(quantized_1)
bytes_s2 = qdata_to_bytes(quantized_2)



if __name__ == "__main__":
    args = parser.parse_args()
    if not args.host_bus:
        raise Exception("Host bus (i2c stub) must be specified") 
    if not args.slave_addr:
        raise Exception("I2C slave address must be specified")
    HOST_BUS   = int(args.host_bus)        # e.g. /dev/i2c-13 if that’s your stub
    SLAVE_ADDR = int(args.slave_addr)      # decimal 28
    #PAYLOAD    = bytes([0xDE, 0xAF, 0xFA, 0xEE])
    PAYLOAD_STR = "PABLO LINARES"#"NTU RULES!"
    PAYLOAD    = bytes([ord(p) for p in PAYLOAD_STR])
    for k in range(len(bytes_s2)//2):
        PAYLOAD= bytes_s1[2*k:2*(k+1)]+bytes_s2[2*k:2*(k+1)]
        send_data(HOST_BUS, SLAVE_ADDR, PAYLOAD)
        sleep(0.6)
    plt.plot(x_signal,y_signal2)
    plt.show()