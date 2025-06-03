#!/usr/bin/env python3
"""
vm_router.py

User-space router for 2 VMs + gateway via TAP interfaces and a dummy router interface.
- Learns L2 (MAC) and L3 (IP) tables
- Replies ARP for the gateway IP
- Replies ICMP echo for the gateway IP
- Forwards all IPv4 (including ICMP) between VM taps and to/from the gateway
- Logs each packet transaction
"""

import threading
import time
from scapy.all import sniff, sendp, Ether, ARP, IP, ICMP, get_if_hwaddr
import os
import fcntl
import struct

def claim_tap_interface(ifname):
    TUNSETIFF = 0x400454ca
    IFF_TAP   = 0x0002
    IFF_NO_PI = 0x1000
    fd = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", ifname.encode(), IFF_TAP | IFF_NO_PI)
    fcntl.ioctl(fd, TUNSETIFF, ifr)
    return fd

def tap_loop(fd):
    while True:
        pkt_data = os.read(fd, 2048)
        pkt = Ether(pkt_data)
        forward_packet(pkt, "router0")

# Interfaces: VM taps and the dummy router interface
taps = ["tap0", "tap1", "router0"]

# Gateway definition
GATEWAY_IP = "172.24.100.1"
ROUTER_IF  = "monitor0"
ROUTER_MAC = get_if_hwaddr(ROUTER_IF)

### CREATE STATIC IP AND MAC TABLES !!!

# L2 and L3 tables
ip_table = {
    "172.24.100.1" : "router0",             # IP  -> iface
    "172.24.100.11": "tap0",
    "172.24.100.12": "tap1",
}

mac_table = {
    "172.24.100.1" : "3a:19:e8:1d:be:c1",   # IP -> MAC
    "172.24.100.11": "ee:7c:ad:d5:1d:63",
    "172.24.100.12": "86:b0:d6:7e:3d:31",
}
#mac_table = {ROUTER_MAC: ROUTER_IF}   
#ip_table  = {GATEWAY_IP: ROUTER_IF}    
last_seen = {}                              # MAC -> timestamp                         

# Entry aging (seconds)
ENTRY_TIMEOUT = 300
lock = threading.Lock()


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")



## REMOVE THIS BLOCK FOR LEARNING TABLES' ENTRIES !!!! 
def learn(eth, iface):
    """Learn source MAC/IP and expire stale entries."""
    now = time.time()
    mac_table[eth.src] = iface
    last_seen[eth.src] = now
    if eth.haslayer(IP):
        log(f"LEARN {eth[IP].src}, {iface}")
        if eth[IP].src != "255.255.255.255" and eth[IP].src != "0.0.0.0" and eth[IP].src!=GATEWAY_IP:
            ip_table[eth[IP].src] = iface
            log(f"Learned IP {eth[IP].src} on {iface}")
    log(f"Learned MAC {eth.src} on {iface}")
    # expire old
    for mac, ts in list(last_seen.items()):
        if now - ts > ENTRY_TIMEOUT:
            log(f"Aged out MAC {mac} from {mac_table.get(mac)}")
            mac_table.pop(mac, None)
            last_seen.pop(mac, None)
            # remove IP entries for that MAC
            for ip_addr, ifc in list(ip_table.items()):
                if ifc == iface and ip_addr != GATEWAY_IP:
                    log(f"Aged out IP {ip_addr} from {iface}")
                    ip_table.pop(ip_addr, None)


def handle_arp(pkt, iface):
    """Reply to ARP requests for the gateway IP."""
    if  pkt.op == 1:
        log(f"[HANDLE ARP]:: {pkt.pdst} |||| {iface}")
    if pkt.op == 1 and pkt.pdst == GATEWAY_IP:
        log(f"ARP request for gateway on {iface} from {pkt.psrc}/{pkt.hwsrc}")
        """
        arp_reply = (
            Ether(src=ROUTER_MAC, dst=pkt.hwsrc)/
            ARP(op=2, hwsrc=ROUTER_MAC, psrc=GATEWAY_IP,
                hwdst=pkt.hwsrc, pdst=pkt.psrc)
        )
        """
        arp_reply = Ether(
                src=ROUTER_MAC,
                dst=pkt.hwsrc
            ) / ARP(
                hwtype=0x0001,           # Ethernet
                ptype=0x0800,            # IPv4
                hwlen=6,
                plen=4,
                op=2,                    # ARP reply
                hwsrc=ROUTER_MAC,        # Our MAC
                psrc=GATEWAY_IP,         # Our IP (gateway)
                hwdst=pkt.hwsrc,         # Requester's MAC
                pdst=pkt.psrc            # Requester's IP
            )
        sendp(arp_reply, iface=iface, verbose=False)
        log(f"Sent ARP reply for {GATEWAY_IP} to {pkt.hwsrc} on {iface}")
        return True
    return False


def handle_icmp_to_gateway(pkt, iface):
    """Reply to ICMP echo requests sent to the gateway IP."""
    if pkt.haslayer(ICMP):
        log(f"[HANDLE ICMP] {pkt[IP].src} {pkt[IP].dst}")
    if pkt.haslayer(ICMP) and pkt[ICMP].type == 8 and pkt[IP].dst == GATEWAY_IP:
        eth = pkt[Ether]
        ip = pkt[IP]
        echo = pkt[ICMP]
        log(f"ICMP echo request for gateway from {ip.src} on {iface} (id={echo.id}, seq={echo.seq})")
        """
        icmp_reply = (
            Ether(src=ROUTER_MAC, dst=eth.src)/
            IP(src=GATEWAY_IP, dst=ip.src)/
            ICMP(type=0, id=echo.id, seq=echo.seq)/
            echo.payload
        )
        """
        icmp_reply = (
            Ether(src=ROUTER_MAC, dst=eth.src)/
            IP(src=GATEWAY_IP, dst=ip.src)/
            ICMP(type=0, id=echo.id, seq=echo.seq)/
            echo.payload
        )
        sendp(icmp_reply, iface=iface, verbose=False)
        log(f"Sent ICMP echo reply to {ip.src} on {iface}")
        return True
    return False


def forward_packet(pkt, in_iface):
    """Sniff callback: learn, ARP, ICMP gateway, then IPv4 forwarding."""
    if not pkt.haslayer(Ether):
        print(f"Packet has not Ether {pkt[IP].src}")
        return
    eth = pkt[Ether]
    #with lock:
    #    learn(eth, in_iface)

    if pkt.haslayer(IP):
        log(f"[IP DETECTED] {pkt[IP].src} → {pkt[IP].dst}")
    if pkt.haslayer(ICMP):
        log(f"[ICMP DETECTED] {pkt[IP].src} → {pkt[IP].dst}, type={pkt[ICMP].type}")


    # ARP for gateway
    if pkt.haslayer(ARP) and handle_arp(pkt[ARP], in_iface):
        return 
    # ICMP echo to gateway
    if handle_icmp_to_gateway(pkt, in_iface):
        return
    print(f"No ICMP, No ARP\n {ip_table}")
    # Forward all IPv4 (including ICMP) between taps/gateway
    if pkt.haslayer(IP):
        dst_ip = pkt[IP].dst
        out_iface = ip_table.get(dst_ip)# or mac_table.get(eth.dst)
        log(f"Packet forwarding. {in_iface} TO {out_iface} ||| {pkt[IP].src}--->{dst_ip}")
        #if pkt.haslayer(ICMP):
        #    log(f"Forwarding ICMP packet {pkt[IP].src} -> {dst_ip} via {out_iface}")
        #    sendp(pkt, iface=out_iface, verbose=False)
        if out_iface and out_iface != in_iface:
            log(f"Forwarding IP packet {pkt[IP].src} -> {dst_ip} via {out_iface}")
            sendp(pkt, iface=out_iface, verbose=False)
        else:
            log(f"Dropping IP packet {pkt[IP].src} -> {dst_ip} on {in_iface}")
        return


def start_sniff(iface):
    sniff(iface=iface, prn=lambda p: forward_packet(p, iface), store=False)


def main():
    for iface in ["router0"]: #taps:
    #for iface in taps:
        threading.Thread(target=start_sniff, args=(iface,), daemon=True).start()
        log(f"Sniffing started on {iface}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopping vm_router.")


if __name__ == "__main__":
    # Call this before sniffing
    #tap_fd = claim_tap_interface("router0")
    #main()
    tap_fd = claim_tap_interface("monitor0")
    #log("TAP interface router0 claimed and active.")
    #threading.Thread(target=tap_loop, args=(tap_fd,), daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopping vm_router.")

