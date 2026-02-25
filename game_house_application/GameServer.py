#!/usr/bin/python3

from socket import *
import threading
import sys

TOTAL_ROOMS = 7

class ServerThread(threading.Thread):
	def __init__(self, client, server):
		threading.Thread.__init__(self)
		self.playerID = ""
		self.client = client
		self.server = server

	def run(self):
		connectionSocket, addr = self.client
		authenticated = False
		try:
			while True:
				clientQuery = connectionSocket.recv(1024).decode().split()      # TODO if client disconnects?
				command = clientQuery[0]

				if command == "/login":
					if authenticated:
						connectionSocket.send(("User already logged in.")
							.encode())
						continue
					
					username, pwd = clientQuery[1], clientQuery[2]
					if self.server.userInfo.get(username) == pwd:
						self.playerID = username
						connectionSocket.send(("1001 Authentication successful")
							.encode())
						print("New user", self.playerID, "logged in!")
						authenticated = True    # player enters game hall
					else:
						connectionSocket.send(("1002 Authentication failed")
							.encode())
						print("Failed login attempt.")
					continue

				# game hall state actions:
				if authenticated:
					if command == "/list":
						connectionSocket.send((self.server.format_list())
							.encode())

					elif command == "/enter":
						roomNumber = int(clientQuery[1])
						if self.server.attempt_entry(roomNumber, self.playerID) \
						    == 0:
							connectionSocket.send((
								"3011 In room, not ready").encode())
							print(self.playerID + " entered room " + 
			                    str(roomNumber) + ".")
							print(self.server.players) # take outtttttt for debug :p
						else:
							connectionSocket.send((
								"3014 The room is playing a game").encode())
							print("Room entry rejected.")

					elif command == "/ready":
						pass

					else:
						connectionSocket.send((
							"\nInvalid command. Game hall command usage:\n\n" \
								"/login                 User authentication\n" \
								"/list                  Display room info and availibility\n" \
								"/enter [room number]   Enter specified room\n" \
								"/ready                 User status ready for game start\n")
								.encode())

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
			# {room number : {player ID : isReady}}
			self.players[i + 1] = {}
			self.roomStatus[i + 1] = "available"
		self.lock = threading.Lock()        # TODO: locking errors / nonblock / timeout???

	def attempt_entry(self, room, playerID):
		# returns 0 if entry successful, 1 on failure (currently playing game)
		with self.lock:
			if self.roomStatus[room] == "available":
				# default player state: not ready
				self.players[room][playerID] = False
				return 0
			else:
				return 1

	def update_room(self, room):
		# checks if game start qualifications are met
		# returns status for specified room
		with self.lock:
			if all(self.players[room].values()) and len(self.players[room]) \
			    >= 2:
				self.roomStatus[room] = "playing"
			else:
				self.roomStatus[room] = "available"

		return self.roomStatus[room]

	def format_list(self):
		# displays total rooms, as well as
		# number of players and status of each room
		roomsData = "3001 " + str(TOTAL_ROOMS) + " "
		with self.lock:
			for i in range(TOTAL_ROOMS):
				roomsData = roomsData + \
					str(len(self.players[i + 1])) + ":" + \
					self.roomStatus[i + 1] + " "

		return roomsData

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
		print("Server connected!")
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
	