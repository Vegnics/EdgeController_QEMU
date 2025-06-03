#!/bin/bash
set -e

sudo bridge fdb flush dev br0 || true

echo "[*] Bringing down interfaces (ignore if not present)..."
sudo ip link set tap0 down || true
sudo ip link set tap1 down || true
sudo ip link set monitor0 down || true
sudo ip link set br0 down || true

echo "[*] Deleting TAP interfaces..."
sudo ip tuntap del dev tap0 mode tap || true
sudo ip tuntap del dev tap1 mode tap || true
sudo ip tuntap del dev monitor0 mode tap || true

echo "[*] Deleting bridge..."
sudo ip link delete br0 type bridge || true

echo "[*] Disabling IP forwarding..."
echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward

echo "[*] Removing NAT rule (if it exists)..."
sudo iptables -t nat -D POSTROUTING -s 172.24.100.0/24 -o wlo1 -j MASQUERADE || true

echo "[✓] Cleanup complete. Virtual switch and networking reverted."