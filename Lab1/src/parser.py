from scapy.config import conf
conf.ipv6_enabled = False
from scapy.all import *
import sys

# get path of pcap file
INPUTPATH = sys.argv[1] 

# read pcap
packets = rdpcap(INPUTPATH) 

print ("***Print all packets in this pcap file***")
print (packets.show())
print ("***Print all TCP packets in this pcap file***")
print (packets[TCP].show())
print ("***Print the first TCP packet content***")
print (packets[TCP][0].show())
print ("***Get data of this packet***")
print ("src IP: ", packets[TCP][0][1].src) # in IP layer
print ("dst IP: ", packets[TCP][0][1].dst) # in IP layer
print ("src port: ", packets[TCP][0][2].sport) # in TCP layer
print ("dst port: ", packets[TCP][0][2].dport) # in TCP layer
print ("packet size: ", len(packets[TCP][0]), " bytes")
print ("***Count number of TCP packets***")
count = 0
for packet in packets[TCP]:
    count += 1
print ("number of TCP packets: ", count)


