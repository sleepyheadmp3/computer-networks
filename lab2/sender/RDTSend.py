#!/usr/bin/python3

from socket import *
import threading
import struct
import sys
import random
from enum import IntEnum


class Checksum(IntEnum):
    Intact = 0
    Corrupted = 1


# simulate packet loss
def lostPacket(seq_num, bound):
    prob = random.random()
    if prob < bound:
        print(f"Packet sent from Sender with seq_num {seq_num} lost")
        return True
    else:
        return False


# simulate packet corruption
def corruptedPacket(seq_num, bound):
    prob = random.random()
    if prob < bound:
        print(f"Packet sent from Sender with seq_num {seq_num} corrupted")
        return True
    else:
        return False


class RDTSend:

    def __init__(
        self,
        sender_socket,
        pkt_data,
        RECV_IP,
        RECV_PORT,
        packer,
        unpacker,
        lost_bound,
        corrupt_bound,
        window_size,
    ) -> None:
        self.sender_socket = sender_socket
        self.pkt_data = pkt_data
        self.RECV_IP = RECV_IP
        self.RECV_PORT = RECV_PORT
        self.packer = packer
        self.unpacker = unpacker
        self.lost_bound = lost_bound
        self.corrupt_bound = corrupt_bound
        self.window_size = window_size

        self.timer = None
        self.stop = False

        # please refer to Page 9 of the lecture slides, this corresponds to
        # event: null (initial state)
        # action: base=1, nextseqnum=1
        self.base = 1
        self.next_seq_num = 1

    # please refer to Page 9 of the lecture slides, this function corresponds to
    # event: timeout
    # action: start_timer, udt_send(sndpkt[base]) ... udt_send(sndpkt[nextseqnum-1])
    def funcTimeout(self):
        self.timer = threading.Timer(2, self.funcTimeout)
        self.timer.start()

        # TODO: retransmit unacked packets from base to next_seq_num-1 (inclusive)
        for seq_num in range(self.base, self.next_seq_num):
            if not lostPacket(self.next_seq_num, self.lost_bound):
                pkt = self.pkt_data[seq_num - 1]

                # simulate packet corruption
                checksum = Checksum.Intact
                if corruptedPacket(self.next_seq_num, self.corrupt_bound):
                    checksum = Checksum.Corrupted

                try:
                    # pack data into binary
                    packed_data = self.packer.pack(
                        self.next_seq_num, checksum, bytes(pkt, encoding="utf-8")
                    )
                except struct.error as emsg:
                    print("Pack data error: ", emsg)
                    sys.exit(1)

                try:
                    self.sender_socket.sendto(
                        packed_data, (self.RECV_IP, self.RECV_PORT)
                    )
                    print(f"Packet (seq num: {self.next_seq_num}) is sent")
                except error as emsg:
                    print("Socket send error: ", emsg)
                    sys.exit(1)

    def send_data(self):
        recv_task = threading.Thread(target=self.recvAck, args=(2,))
        recv_task.start()
        self.sendPacket()
        recv_task.join()
        self.sender_socket.close()

    # set timer to receive ACK
    def recvAck(self, t):
        # self.stop is set to True before self.sendPacket() returns, i.e.,
        # the while loop keeps receiving ACKs until all packets are sent
        # and acked (self.base > len(self.pkt_data))
        while not self.stop:
            try:
                data_recv, _ = self.sender_socket.recvfrom(1024)
            except timeout:
                continue

            try:
                seq_num, checksum = self.unpacker.unpack(data_recv)
            except struct.error as emsg:
                print("Unpack data error: ", emsg)
                sys.exit(1)

            # please refer to Page 9 of the lecture slides, this corresponds to
            # event: rdt_rcv(rcvpkt) && corrupt(rcvpkt)
            # action: null
            if checksum == Checksum.Corrupted:
                print("Receive corrupted ACK")
                continue

            # please refer to Page 9 of the lecture slides, this corresponds to
            # event: rdt_rcv(rcvpkt) && notcorrupt(rcvpkt)
            # action: base=getacknum(rcvpkt)+1, if(base == nextseqnum) ...
            #
            # update base pointer
            self.base = max(self.base, seq_num + 1)

            self.timer.cancel()
            # reset timer if there are unacked packets
            if self.base < self.next_seq_num:
                self.timer = threading.Timer(t, self.funcTimeout)
                self.timer.start()

    # send packet with seq_num and checksum
    def sendPacket(self):
        while self.base <= len(self.pkt_data):
            while self.next_seq_num < self.base + self.window_size and \
                self.next_seq_num <= len(self.pkt_data):

                # please refer to Page 9 of the lecture slides, the following corresponds to
                # event: rdt_send(data)
                # action: if(nextseqnum<base+N) { sndpkt[nextseqnum]= ... } else refuse_data(data)
                if not lostPacket(self.next_seq_num, self.lost_bound):
                    pkt = self.pkt_data[self.next_seq_num - 1]

                    # simulate packet corruption
                    checksum = Checksum.Intact
                    if corruptedPacket(self.next_seq_num, self.corrupt_bound):
                        checksum = Checksum.Corrupted

                    try:
                        # pack data into binary
                        packed_data = self.packer.pack(
                            self.next_seq_num, checksum, bytes(pkt, encoding="utf-8")
                        )
                    except struct.error as emsg:
                        print("Pack data error: ", emsg)
                        sys.exit(1)

                    try:
                        self.sender_socket.sendto(
                            packed_data, (self.RECV_IP, self.RECV_PORT)
                        )
                        print(f"Packet (seq num: {self.next_seq_num}) is sent")
                    except error as emsg:
                        print("Socket send error: ", emsg)
                        sys.exit(1)

                # start the timer if the base equals the next_seq_num
                if self.base == self.next_seq_num:
                    self.timer = threading.Timer(2, self.funcTimeout)
                    self.timer.start()

                # update next_seq_num
                self.next_seq_num += 1

        self.stop = True


def main(argv):
    SEND_IP = "127.0.0.1"
    SEND_PORT = 6666

    RECV_IP = "127.0.0.1"
    RECV_PORT = 7777
    LOST_BOUND = 0.00       # changeable!!
    CORRUPT_BOUND = 0.00
    WINDOW_SIZE = 5

    try:
        sender_socket = socket(AF_INET, SOCK_DGRAM)
        sender_socket.bind((SEND_IP, SEND_PORT))
        sender_socket.settimeout(5)
    except error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)

    # define the format of send/receive packets
    try:
        packer = struct.Struct("I I 32s")  # seq_num, checksum, content
        unpacker = struct.Struct("I I")    # seq_num, checksum
    except struct.error as emsg:
        print("Struct error: ", emsg)
        sys.exit(1)

    with open(argv[1], 'r') as f:
        contents = f.read()
        pkt_data = [contents[i : i + 32] for i in range(0, len(contents), 32)]

    # GBN (Go-Back-N) protocol
    sender = RDTSend(
        sender_socket,
        pkt_data,
        RECV_IP,
        RECV_PORT,
        packer,
        unpacker,
        LOST_BOUND,
        CORRUPT_BOUND,
        WINDOW_SIZE,
    )

    # start sending data
    sender.send_data()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 RDTSend.py <filename>")
        sys.exit(1)
    main(sys.argv)
