# Create the bridge
sudo ip link add br0 type bridge
sudo ip link set br0 up

# Create TAP interfaces for VMs
sudo ip tuntap add dev tap0 mode tap user $USER
sudo ip tuntap add dev tap1 mode tap user $USER
sudo ip link set tap0 up
sudo ip link set tap1 up

# Add TAPs to bridge
sudo ip link set tap0 master br0
sudo ip link set tap1 master br0

# Optional: disable bridge port isolation (this is important!)
sudo bridge link set dev tap0 isolated off
sudo bridge link set dev tap1 isolated off


echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 2) (Optional) NAT VM Internet traffic via your uplink (eth0)
sudo iptables -t nat -A POSTROUTING -s 172.24.100.0/24 -o wlo1 -j MASQUERADE

# Create host TAP interface to join the bridge
sudo ip tuntap add dev monitor0 mode tap user $USER
sudo ip link set monitor0 master br0
sudo ip link set monitor0 up

# Assign host-side IP to the bridge (correct!)
sudo ip addr add 172.24.100.1/24 dev br0
ip link set br0 promisc on ## Setting the bridge to promiscuous mode
sudo bridge fdb flush dev br0
