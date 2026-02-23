#!/usr/bin/python3

from socket import *
import threading
import sys

TOTAL_ROOMS = 7

class ServerThread(threading.Thread):
	def __init__(self, client, server):
		threading.Thread.__init__(self)
		self.client = client
		self.server = server
	
	def attempt_entry(self, room):
		pass
	
	def update_room(self, room):
		# checks if game start qualifications are met
		# returns status for specified room
		# TODO: locking thread??
		
		if all(self.server.players[room].values()) and \
			len(self.server.players[room]) >= 2:
			self.server.roomStatus[room] = "playing"
		else:
			self.server.roomStatus[room] = "available"
		
		return self.server.roomStatus[room]
	
	def run(self):
		connectionSocket, addr = self.client
		authenticated = False
		
		try:
			while True:
				clientQuery = connectionSocket.recv(1024).decode().split()      # TODO if client disconnects?
				command = clientQuery[0]
				
				if command == "/login":
					username, pwd = clientQuery[1], clientQuery[2]
					if self.server.userInfo.get(username) == pwd:
						connectionSocket.send(("1001 Authentication successful")
							.encode())
						authenticated = True    # player enters game hall
					else:
						connectionSocket.send(("1002 Authentication failed")
							.encode())
					continue
								
				if authenticated:
					if command == "/list":
						# display total rooms, as well as
                        # number of players and status of each room
						# TODO: locking thread?
						roomsData = "3001 " + TOTAL_ROOMS + " "
						for i in range(TOTAL_ROOMS):
							roomsData = roomsData + \
							    len(self.server.players[i + 1]) + ":" + \
								self.server.roomStatus[i + 1] + " "
						connectionSocket.send((roomsData).encode())
					
					elif command == "/enter":
						roomNumber = int(clientQuery[1])
						attempt_entry(roomNumber)
						
						

					elif command == "/ready":
						pass
					else:
						connectionSocket.send((
							"Invalid command. Game hall command usage:\n\n" \
								"/login                 User authentication\n" \
								"/list                  Display room info and availibility\n" \
								"/enter [room number]   Enter specified room\n" \
								"/ready                 User status ready for game start").encode())

				else:
					connectionSocket.send((
						"Please login first using command '/login'.").encode())

		finally:
			connectionSocket.close()


class ServerMain:
	def __init__(self):
		self.userInfo = {}
		self.players = {}
		self.roomStatus = {}
		for i in range(TOTAL_ROOMS):
			# {room number : {player name : isReady}}
			self.players[i + 1] = {}
			self.roomStatus[i + 1] = "available"
		
	def parse_file(self, path):
		# UserInfo.txt line format is user_name:password
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
	