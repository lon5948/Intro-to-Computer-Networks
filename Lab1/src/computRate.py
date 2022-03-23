from scapy.config import conf
conf.ipv6_enabled = False
from scapy.all import *
import sys
import time

# get path of pcap file
Th3 = "../out/TCP_h3.pcap"
Th4 = "../out/TCP_h4.pcap"
Uh3 = "../out/UDP_h3.pcap"
Uh4 = "../out/UDP_h4.pcap"

# read pcap
packetsTh3 = rdpcap(Th3)
packetsTh4 = rdpcap(Th4)
packetsUh3 = rdpcap(Uh3)
packetsUh4 = rdpcap(Uh4) 

print("---TCP---")

size = 0
for packet in packetsTh4[TCP]:
    size += len(packet) 

print("Flow1(h1->h4): ",size*8/5000000, " Mbps")

size = 0
for packet in packetsTh3[TCP]:
    size += len(packet)

print("Flow3(h2->h3): ",size*8/5000000, " Mbps")

print("\n---UDP---")


size = 0
for packet in packetsUh4[UDP]:
    size += len(packet)

print("Flow1(h1->h4): ",size*8/5000000, " Mbps")

size = 0
for packet in packetsUh3[UDP]:
    size += len(packet) 

print("Flow3(h2->h3): ",size*8/5000000, " Mbps")



