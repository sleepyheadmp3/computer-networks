#!/usr/bin/python3

from socket import *
import threading
import sys

class ServerThread(threading.Thread):
	def __init__(self, client, server):
		threading.Thread.__init__(self)
		self.client = client
		self.server = server
		
	def run(self):
		connectionSocket, addr = self.client
		
		while True:
			message = connectionSocket.recv(1024).decode().split()
			command = message[0]
			if command == "/login":
				username, pwd = message[1], message[2]
				if self.server.userInfo.get(username) == pwd:
					connectionSocket.send(("1001 Authentication successful")
						   .encode())
					
					# TODO
					# enter game hall

				else:
					connectionSocket.send(("1002 Authentication failed")
						   .encode())
		
		connectionSocket.close()


class ServerMain:
	def __init__(self):
		self.userInfo = {}
		
	def parse_file(self, path):
		# parses and stores UserInfo.txt data
		# line format is user_name:password
		
		with open(path, "r") as f:
			for line in f:
				line = line.strip()
				username, password = line.split(":", 1)
				self.userInfo[username] = password

	def server_run(self):
		serverPort = int(sys.argv[1])
		self.parse_file(sys.argv[2])
		
		serverSocket = socket(AF_INET, SOCK_STREAM)
		serverSocket.bind(("", serverPort))
		serverSocket.listen(5)
		
		while True:
			client = serverSocket.accept()
			t = ServerThread(client, self)
			t.start()


if __name__ == '__main__':
	if len(sys.argv) != 3:
			print("Usage: GameServer.py [port] [UserInfo.txt path]")
			sys.exit(1)
			
	server = ServerMain()
	server.server_run()
	