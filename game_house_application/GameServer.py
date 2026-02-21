#!/usr/bin/python3

from socket import *
import threading
import sys

class ServerThread(threading.Thread):
	def __init__(self, client):                        # constructor for ServerThread obj!!
		threading.Thread.__init__(self)                # constructs parent class Thread
		self.client = client

	def run(self):
		connectionSocket, addr = self.client           # creates new socket specifically for client
		sentence = connectionSocket.recv(1024)
		
        # TODO

		connectionSocket.close()

class ServerMain:
	def parse_file(path):
		# UserInfo.txt file formatted as user_name:password
		# TODO:
		# 1) read all .txt data into memory
		# 2) authenticate new clients using said data
		# maintain list of players in each room (?)


	def server_run(self):
		# usage: python3 GameServer.py [port] [UserInfo.txt path]
		serverPort = sys.argv[1]
		
		parse_file(sys.argv[2])
		
		serverSocket = socket(AF_INET, SOCK_STREAM)    # creates socket (reused)
		serverSocket.bind(("", serverPort))            # associates socket obj with server IP addr and port #
		serverSocket.listen(5)                         # prepares incoming queue
		
		while True:
			client = serverSocket.accept()             # ready for client connection, blocked until connect() request received
			t = ServerThread(client)
			t.start()


if __name__ == '__main__':
	server = ServerMain()
	server.server_run()