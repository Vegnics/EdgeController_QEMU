# 1) Create a dummy interface called “router0”
sudo ip tuntap add dev router0 mode tap user $USER

# 2) Assign the gateway IP on your VM subnet (e.g. 172.24.100.1/24)
sudo ip addr add 172.24.100.1/24 dev router0
sudo ip link set dev router0 address 3a:19:e8:1d:be:c1

# 3) Bring it up
sudo ip link set dev router0 up

# 1) Enable IPv4 forwarding (so you can NAT out to eth0)
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 2) (Optional) NAT VM Internet traffic via your uplink (eth0)
sudo iptables -t nat -A POSTROUTING -s 172.24.100.0/24 -o wlo1 -j MASQUERADE

# 3) Create each TAP for your VMs (but DO NOT attach to any bridge)
sudo ip tuntap add dev tap0 mode tap user $USER
sudo ip link set dev tap0 up

sudo ip tuntap add dev tap1 mode tap user $USER
sudo ip link set dev tap1 up



# Enable forwarding
#echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# If you want the VMs to talk out to the Internet via NAT:
#sudo iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -j MASQUERADE

# Replace tap0 with tap1, tap2, etc. for additional VMs
#sudo ip tuntap add dev tap0 mode tap user $USER
#sudo ip link set tap0 up

#ip tuntap add dev tap1 mode tap user $USER
#ip link set tap1 up

#sudo ip tuntap add dev tap0 mode tap user $USER
#sudo ip link set dev tap0 master br0
#sudo ip link set dev tap0 up