# Ping application

# Import necessary modules
from socket import *
import os
import struct
import time
import select

# echo request
REQUEST_CODE = 8
# Initialize variables to track the number of packets sent and received, as well as the round trip times for each packet
pack_sent = 0
pack_rec = 0
round_trip_times = []
target_host = ""


# Function to calculate checksum for icmp header with the help of dummy header and the data
def get_checksum(packet):
    cs = 0  # checksum
    packget_len = (len(packet) // 2) * 2  # if length is odd then subtracting one
    count = 0

# Processing a packet, byte by byte
    while count < packget_len:
        thisVal = int(packet[count + 1]) * 256 + int(packet[count])
        cs = cs + thisVal
        cs = cs & 0xffffffff
        count = count + 2

# packet length was odd then condition becomes true
    if packget_len < len(packet):
        cs = cs + int(packet[len(packet) - 1])
        cs = cs & 0xffffffff

# Handling of checksum to be 2 bytes
    cs = (cs >> 16) + (cs & 0xffff)
    cs = cs + (cs >> 16)
    output = ~cs  # complement
    output = output & 0xffff
    output = output >> 8 | (output << 8 & 0xff00)
    return output

# Function that receives the ping response and print required data
def receive(sock, ID, timeout, sequence_no):
    global pack_rec, round_trip_times
    timeLeft = timeout

    while 1:
        start_time = time.time()
        isready = select.select([sock], [], [], timeLeft)  # waiting for I/O completion- read/write/exception
        howLongInSelect = (time.time() - start_time)

        if isready[0] == []:  # indicates timeout
            return "\tRequest timed out for icmp_seq " + str(sequence_no)

        message, addr = sock.recvfrom(1024)
        timeReceived = time.time()
        icmp_header = message[20:28]  # 1-20 is network layer header and 20-28 is icmp header
        type, code, checksum, p_id, sequence = struct.unpack('bbHHh', icmp_header)  # getting things from icmp header

        if (p_id == ID):  # confirming about process id
            pack_rec += 1
            rtt = int((timeReceived - start_time) * 100)
            round_trip_times.append(rtt)
            data_length = len(message)
            network_header = message[0:20]
            timetolive = network_header[8]
            src_ip = str(network_header[12]) + "." + str(network_header[13]) + "." + str(
                network_header[14]) + "." + str(network_header[15])
            return "\t{} bytes from {}: icmp_seq={} ttl={} time={} ms".format(str(data_length), src_ip, str(sequence),
                                                                              str(timetolive), str(rtt))

        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:  # indicates timeout
            return "\tRequest timed out for icmp_seq " + str(sequence_no)

# Function that prepares the packet = header+data after getting checksum
def send_packet(sock, destAddr, ID, sequence_no):
    global pack_sent
    cs = 0  # checksum
    header = struct.pack("bbHHh", REQUEST_CODE, 0, cs, ID, sequence_no)  # header with checksum = 0
    data = struct.pack("f", time.time())
    cs = get_checksum(header + data)
    cs = htons(cs)  # host byte order to network byte order
    header = struct.pack("bbHHh", REQUEST_CODE, 0, cs, ID, sequence_no)
    packet = header + data
    sock.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str
    pack_sent += 1

# Function that creates socket and call send_packet function to send a single ping
def single_ping(destAddr, timeout, sequence_no):
    icmp = getprotobyname("icmp")  # for icmp it returns 1
    sock = socket(AF_INET, SOCK_RAW, icmp)
    PID = os.getpid()  # process id of current process
    send_packet(sock, destAddr, PID, sequence_no)
    message = receive(sock, PID, timeout, sequence_no)
    sock.close()
    return message


# Function that calls the required functions for 4 times to send the ping
def ping(host, timeout=1):
    global target_host
    dest = gethostbyname(host)
    target_host = dest
    print("Pinging " + dest + " with 32 bytes of data using Python:")

    for i in range(4):  # pings 4 times
        message = single_ping(dest, timeout, i)
        print(message)
        time.sleep(1)  # waiting for 1 second

# Function that prints the summary of all the pings
def get_stats():
    global target_host, pack_sent, pack_rec, round_trip_times
    loss = pack_sent - pack_rec
    percent_loss = int((loss / pack_sent) * 100)
    min_rtt = min(round_trip_times)
    max_rtt = max(round_trip_times)
    avg_rtt = sum(round_trip_times) / len(round_trip_times)
    print("Ping stats for " + target_host + ":")
    print("\tPackets: Sent = {}, Received = {}, Lost = {} ({}% loss)".format(str(pack_sent), str(pack_rec), str(loss),
                                                                             str(percent_loss)))
    print("Approximate round trip times in milli-seconds:")
    print("\tMinimium = {}ms, Maximum = {}ms, Average = {}ms ".format(str(min_rtt), str(max_rtt), str(avg_rtt)))


# ---------------------Main---------------------------------------
def main():
    while True:
        choice = input("Enter choice (1-Ping, 2-Quit) ")
        if choice == "1":
            hostname = input("Enter the host name you want to ping : ")
            ping(hostname)
            get_stats()
        elif choice == "2":
            print("Thankyou!")
            break
        else:
            print("Invalid input, try again!")


if __name__ == "__main__":
    main()
