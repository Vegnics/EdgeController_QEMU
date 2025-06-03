import os, fcntl, struct, select, sys
from scapy.all import Ether, IP, ICMP, sendp, get_if_hwaddr, UDP
from ipaddress import ip_address, ip_network
from matplotlib import pyplot as plt
import numpy as np

TUNSETIFF = 0x400454ca
IFF_TAP   = 0x0002
IFF_NO_PI = 0x1000

IFACE       =   "monitor0"          # the bridge slave you created
IP_MONITOR  =   "172.24.100.9"
MTU         =   1600                # a bit larger than 1500

VM_SUBNET = ip_network("172.24.100.0/24")

def log(msg):
    print(f"[+] {msg}")

def claim_tap_interface(ifname: str) -> int:
    """Attach to existing TAP device"""
    fd = os.open("/dev/net/tun", os.O_RDWR | os.O_NONBLOCK)
    ifr = struct.pack("16sH", ifname.encode(), IFF_TAP | IFF_NO_PI)
    fcntl.ioctl(fd, TUNSETIFF, ifr)
    return fd

def ensure_up_hairpin(ifname: str):
    os.system(f"sudo ip link set {ifname} up")
    os.system(f"sudo bridge link set dev {ifname} isolated off")
    os.system(f"sudo bridge link set dev {ifname} hairpin on")

def handle_icmp(pkt, iface, hwsrc):
    if pkt.haslayer(ICMP) and pkt[ICMP].type == 8 and pkt[IP].dst == IP_MONITOR:
        eth = pkt[Ether]
        ip = pkt[IP]
        echo = pkt[ICMP]
        log(f"ICMP echo request from {ip.src} (id={echo.id}, seq={echo.seq})")

        reply = (
            Ether(src=hwsrc, dst=eth.src) /
            IP(src=IP_MONITOR, dst=ip.src) /
            ICMP(type=0, id=echo.id, seq=echo.seq) /
            echo.payload
        )
        sendp(reply, iface=iface, verbose=False)
        log(f"Sent ICMP echo reply to {ip.src}")
        return True
    return False

def handle_packet(pkt):
    if pkt.haslayer(IP) and pkt.haslayer(UDP):
        src = pkt[IP].src
        dst = pkt[IP].dst
        src_ip = ip_address(src)
        log(f"PKT UDP VMSUBNET {src_ip}  {src}") 
        if src_ip in VM_SUBNET:
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
            log(f"{dport}")
            data = bytes(pkt[UDP].payload)
            log(f"[UDP] {src}:{sport} → {dst}:{dport} | Payload: {data!r}")
            try:
                decoded = data.decode("utf-8")
                float_list = [float(x) for x in decoded.strip().split(",")]
                arr = np.array(float_list, dtype=np.float32)
                log(f"Converted to NumPy array: {arr} {arr.shape}")
                plt.plot(arr)
                plt.title("Sensor Data (Filtered - Received over Ethernet)")
                plt.xlabel("Sample idx")
                plt.ylabel("Signal")
                plt.grid(True)
                plt.show()
            except Exception as e:
                log(f"Failed to decode/convert payload: {e}")
            return True
        else: 
            return False
    return False

def tap_loop(fd: int, iface: str):
    poller = select.poll()
    poller.register(fd, select.POLLIN)
    hwsrc = get_if_hwaddr(iface)
    log(f"Listening on {iface} ({hwsrc}) … Ctrl+C to stop")
    while True:
        for _fd, _ev in poller.poll():
            frame = os.read(fd, MTU)
            if not frame:
                continue
            try:
                pkt = Ether(frame)
                if handle_icmp(pkt, iface, hwsrc):
                    continue
                handle_packet(pkt)
            except Exception as e:
                log(f"Failed to parse frame: {e}")

if __name__ == "__main__":
    ensure_up_hairpin(IFACE)
    tap_fd = claim_tap_interface(IFACE)
    try:
        tap_loop(tap_fd, IFACE)
    except KeyboardInterrupt:
        print("\n[!] Stopped.")
    finally:
        os.close(tap_fd)