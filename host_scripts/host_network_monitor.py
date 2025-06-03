#!/usr/bin/env python3
"""
tap_switch.py

Host-side learning switch/router for VM tap interfaces.
Maintains a MAC-to-interface table and forwards each Ethernet
frame only to its learned destination (or floods if unknown).
"""

import threading
import time
from scapy.all import (sniff, sendp, Ether, ARP, IP, ICMP, TCP, UDP, get_if_hwaddr)

# List your tap interfaces here
#TAP_IFACES = ["tap0", "tap1"]  # extend as needed
TAP_IFACES = ["tap0","tap1","router0"]  # extend as needed

GATEWAY_IP  = "172.24.100.1"
ROUTER_IF   = "router0"
ROUTER_MAC  = "3a:19:e8:1d:be:c1"  # must match the dummy you set abov

# MAC address table: maps MAC -> interface name
mac_table = { ROUTER_MAC: ROUTER_IF }  
ip_table  = { GATEWAY_IP: ROUTER_IF }
last_seen = {}

table_lock = threading.Lock()

# Entry aging (seconds) before a MAC is forgotten
ENTRY_TIMEOUT = 300
# Track insert times to expire entries
insert_times = {}

# ICMP duplicate‐suppression state
seen_icmp = set()
icmp_times = {}
ICMP_ENTRY_TIMEOUT = 10  # ICMP key aging (seconds)
ICMP_TYPES = {"0":"Echo Reply", "8":"Echo Request"}


def learn(pkt, iface):
    now = time.time()
    # learn L2
    mac_table[pkt.src] = iface
    last_seen[pkt.src] = now

    # learn L3 if IPv4
    if IP in pkt:
        ip_table[pkt[IP].src] = iface

    # expire old entries
    for key, t in list(last_seen.items()):
        if now - t > ENTRY_TIMEOUT:
            mac_table.pop(key, None)
            # also pop from ip_table if value matches
            for ip, ifc in list(ip_table.items()):
                if mac_table.get(key) == ifc:
                    ip_table.pop(ip, None)
            last_seen.pop(key, None)

def handle_icmp_echo(pkt, iface):
    if pkt.haslayer(ICMP) and pkt[ICMP].type == 8: # and pkt[IP].dst == GATEWAY_IP:
        ip = pkt[IP]; icmp = pkt[ICMP]
        print(f"[ICMP] \t Src: {ip.src} -->> Dst: {ip.dst} | ICMP ID: {icmp.id} | SEQ_NUM: {icmp.seq} | TYPE: {ICMP_TYPES[f"{icmp.type}"]}")
        """
        reply = (
            Ether(src=ROUTER_MAC, dst=pkt[Ether].src) /
            IP(src=GATEWAY_IP,       dst=ip.src)        /
            ICMP(type=0, id=icmp.id, seq=icmp.seq)     /
            icmp.payload
        )
        """
        reply = (
            Ether(src=pkt[Ether].dst, dst=pkt[Ether].src) /
            IP(src=ip.dst,       dst=ip.src)        /
            ICMP(type=0, id=icmp.id, seq=icmp.seq)     /
            icmp.payload
        )
        sendp(reply, iface=iface, verbose=False)
        return True
    return False


def handle_arp(pkt, iface):
    # ARP request for one of our VM IPs?
    if pkt.op==1 and pkt.pdst in ip_table:
        # craft reply: say q our source MAC is this tap’s MAC
        resp = Ether(dst=pkt.hwsrc, src=ROUTER_MAC)/\
               ARP(op=2,
                   hwsrc=pkt.hwdst,
                   psrc=pkt.pdst,
                   hwdst=pkt.hwsrc,
                   pdst=pkt.psrc)
            
        """
        ARP(op=2,
            hwsrc=ROUTER_MAC,
            psrc=GATEWAY_IP,
            hwdst=pkt.hwsrc,
            pdst=pkt.psrc)
        """
        sendp(resp, iface=iface, verbose=False)
        return True
    return False


def forward_packet(pkt, in_iface):
    """
    Forward a captured packet from in_iface to the correct out_iface.
    Learns the source MAC and consults the MAC table for dest.
    """
    global mac_table, insert_times, seen_icmp, icmp_times, ip_table, last_seen

    if not pkt.haslayer(Ether):
        return

    # learn first
    learn(pkt[Ether], in_iface)

    # if ARP, maybe answer it
    if ARP in pkt and handle_arp(pkt[ARP], in_iface):
        return

    # ICMP Echo Request?
    if handle_icmp_echo(pkt, in_iface):
        return

    src_mac = pkt[Ether].src
    dst_mac = pkt[Ether].dst

    with table_lock:
        # Learn source MAC
        mac_table[src_mac] = in_iface
        insert_times[src_mac] = time.time()
        # Expire old entries
        now = time.time()
        for mac, ts in list(insert_times.items()):
            if now - ts > ENTRY_TIMEOUT:
                mac_table.pop(mac, None)
                insert_times.pop(mac, None)
        
    # ICMP duplicate suppression
    if pkt.haslayer(IP):
        dst_ip = pkt[IP].dst
        # choose by IP first, then by destination MAC
        out_iface = ip_table.get(dst_ip) or mac_table.get(dst_mac)
        if out_iface and out_iface != in_iface:
            sendp(pkt, iface=out_iface, verbose=False)
        return


    if pkt.haslayer(IP) and pkt.haslayer(ICMP):
        ip = pkt[IP]
        icmp = pkt[ICMP]
        key = (ip.src, ip.dst, icmp.id, icmp.seq)
        ts = time.time()
        # expire old icmp entries
        for k, t in list(icmp_times.items()):
            if ts - t > ICMP_ENTRY_TIMEOUT:
                seen_icmp.discard(k)
                icmp_times.pop(k, None)
        print(f"[ICMP] \t Src: {ip.src} -->> Dst: {ip.dst} | ICMP ID: {icmp.id} | SEQ_NUM: {icmp.seq} | TYPE: {ICMP_TYPES[f"{icmp.type}"]}")
        #return
        #check for duplicate
        #if key in seen_icmp:
        #    return  # drop duplicate
        #seen_icmp.add(key)
        #icmp_times[key] = ts

        out_iface = None
        if IP in pkt:
            out_iface = ip_table.get(pkt[IP].dst)
        # fallback: L2 lookup
        if not out_iface:
            #Determine out interface
            out_iface = mac_table.get(dst_mac)

        if in_iface!=out_iface and in_iface and out_iface:
            print(f"[Packet Fordwarding] Src: {in_iface} \t -->> Dst: {out_iface}")
            sendp(pkt, iface=out_iface, verbose=False)
        else:
            return
            # Flood to all except source
            print(f"[Flooding] Src: {in_iface}")
            for iface in TAP_IFACES:
                if iface != in_iface:
                    sendp(pkt, iface=iface, verbose=False)
       
            

def start_sniff(iface):
    """
    Start sniffing on the given interface and forward packets.
    """
    sniff(iface=iface,
          prn=lambda pkt: forward_packet(pkt, iface),
          store=False)

def main():
    threads = []
    for iface in TAP_IFACES:
        t = threading.Thread(target=start_sniff, args=(iface,), daemon=True)
        t.start()
        threads.append(t)
        print(f"[+] Started switch thread on {iface}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping tap_switch.")

if __name__ == "__main__":
    main()