from scapy.all import IP, ICMP, sr1, conf

#IFACE   = "monitor0"           # the interface you want to “own”
#TARGET  = "172.24.100.11"        # where to ping
#TIMEOUT = 2.0                  # seconds to wait for reply


conf.iface = "monitor0"          # or any managed/TAP interface
reply = sr1(IP(dst="172.24.100.11")/ICMP(), timeout=2, verbose=False)
if reply:
    print("reply from", reply.src)