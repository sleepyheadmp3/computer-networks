#!/usr/bin/python3

from socket import *
import sys
import struct
import random
from enum import IntEnum


class Checksum(IntEnum):
    Intact = 0
    Corrupted = 1


# simulate ack loss
def lostACK(seq_num, bound):
    prob = random.random()
    if prob < bound:
        print(f"ACK {seq_num} lost")
        return True
    else:
        return False


# simulate ack corruption
def corruptedACK(seq_num, bound):
    prob = random.random()
    if prob < bound:
        print(f"ACK {seq_num} corrupted")
        return True
    else:
        return False


class RDTReceive:
    def __init__(
        self,
        receiver_socket,
        f,
        SEND_IP,
        SEND_PORT,
        packer,
        unpacker,
        lost_bound,
        corrupt_bound,
    ) -> None:
        self.receiver_socket = receiver_socket
        self.f = f
        self.SEND_IP = SEND_IP
        self.SEND_PORT = SEND_PORT
        self.packer = packer
        self.unpacker = unpacker
        self.lost_bound = lost_bound
        self.corrupt_bound = corrupt_bound

        # please refer to Page 10 of the lecture slides, this corresponds to
        # event: null (initial state)
        # action: expectedseqnum=1 ...
        self.expt_seq_num = 1

    def recv_data(self):

        packed_data = None
        while True:
            try:
                data, _ = self.receiver_socket.recvfrom(1024)
            except timeout:
                print("Socket timeout, terminate the receiver program.")
                break

            # unpack received data
            try:
                seq_num, checksum, content = self.unpacker.unpack(data)
                content = content.decode()
            except struct.error as emsg:
                print("Unpack data error: ", emsg)
                sys.exit(1)

            # if packet received is not corrupted and has expected seq_num,
            # decode and write the content into the above opened file
            #
            # please refer to Page 10 of the lecture slides, this if block corresponds to
            # event: rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && hasseqnum(rcvpkt,expectedseqnum)
            # action: extract(rcvpkt,data) deliver_data(data) ...
            if checksum == Checksum.Intact and seq_num == self.expt_seq_num:

                # write the content into a file
                try:
                    self.f.write(content)
                except IOError as emsg:
                    print("File IO error: ", emsg)
                    sys.exit(1)

                print(f"Receive expected packet with seq num: {self.expt_seq_num}")

                # skip sending to simulate packet loss if lostACK returns True
                if not lostACK(self.expt_seq_num, self.lost_bound):

                    # simulate ACK packet corruption
                    ACK_checksum = Checksum.Intact
                    if corruptedACK(self.expt_seq_num, self.corrupt_bound):
                        ACK_checksum = Checksum.Corrupted

                    # send ACK to the sender
                    try:
                        packed_data = self.packer.pack(self.expt_seq_num, ACK_checksum)
                        self.receiver_socket.sendto(
                            packed_data, (self.SEND_IP, self.SEND_PORT)
                        )
                    except struct.error as emsg:
                        print("Pack data error: ", emsg)
                        sys.exit(1)
                    except error as emsg:
                        print("Socket send error: ", emsg)
                        sys.exit(1)
                    print(f"Cumulative ACK {self.expt_seq_num} sent to the Sender")

                # update the expected received sequence number for next packet
                self.expt_seq_num += 1

            # please refer to Page 10 of the lecture slides, this else block corresponds to
            # event: default
            # action: udt_send(sndpkt)
            else:  # for any other cases, resend the previous ack
                if checksum == Checksum.Corrupted:
                    print("Receive corrupted packet from the sender, resending latest ACK ...")
                else:
                    print(
                        f"Receive unexpected packet with wrong seq_num {seq_num}, resending latest ACK ..."
                    )

                # skip sending ACK to simulate packet loss
                if lostACK(self.expt_seq_num - 1, self.lost_bound):
                    continue

                # simulate ACK packet corruption
                ACK_checksum = Checksum.Intact
                if corruptedACK(self.expt_seq_num - 1, self.corrupt_bound):
                    ACK_checksum = Checksum.Corrupted
                # send ACK to the sender
                try:
                    packed_data = self.packer.pack(self.expt_seq_num - 1, ACK_checksum)
                    self.receiver_socket.sendto(
                        packed_data, (self.SEND_IP, self.SEND_PORT)
                    )
                except struct.error as emsg:
                    print("Pack data error: ", emsg)
                    sys.exit(1)
                except error as emsg:
                    print("Socket send error: ", emsg)
                    sys.exit(1)
                print(f"Latest ACK {self.expt_seq_num - 1} resent to the Sender" )

        self.f.close()
        self.receiver_socket.close()


def main(argv):
    SEND_IP = "127.0.0.1"
    SEND_PORT = 6666

    RECV_IP = "127.0.0.1"
    RECV_PORT = 7777
    LOST_BOUND = 0.05
    CORRUPT_BOUND = 0.05

    try:
        receiver_socket = socket(AF_INET, SOCK_DGRAM)
        receiver_socket.bind((RECV_IP, RECV_PORT))
    except error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)

    # define the format of received/sent packets
    try:
        packer = struct.Struct("I I")        # seq_num, checksum
        unpacker = struct.Struct("I I 32s")  # seq_num, checksum, content
    except struct.error as emsg:
        print("Struct error: ", emsg)
        sys.exit(1)

    try:
        f = open("recv.txt", "w")
    except IOError as emsg:
        print("File IO error: ", emsg)
        sys.exit(1)

    # terminate the program if timeout - 10 seconds
    receiver_socket.settimeout(10)

    receiver = RDTReceive(
        receiver_socket,
        f,
        SEND_IP,
        SEND_PORT,
        packer,
        unpacker,
        LOST_BOUND,
        CORRUPT_BOUND,
    )

    # start receiving data
    receiver.recv_data()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Usage: python3 RDTReceive.py")
        sys.exit(1)
    main(sys.argv)
