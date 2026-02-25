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
		self.playerID = ""
		self.room = 0       # rooms use 1-indexing
		self.state = "not ready"                                        # TODO required?? or
		

	def authenticate_bid(self, connectionSocket):
		# checks bid input validity, returns int bid list or empty if invalid
		
		response = connectionSocket.recv(1024).decode().split()
		if response[0] != "/bid" or len(response) != 7:
			connectionSocket.send(("4002 Unrecognized message").encode())
			return []
		
		response.pop(0)
		bidList = [int(x) for x in response]
		if sum(bidList) > 30 or any(x < 0 for x in bidList):
			connectionSocket.send(("3022 You lost this game").encode())
			return []
		
		return bidList


	def run(self):
		connectionSocket, addr = self.client
		activeplayerStatus = {}
		authenticated = False
	
		try:
			while True:
				clientQuery = connectionSocket.recv(1024).decode().split()
				command = clientQuery[0]

				if command == "/login":
					if authenticated:
						connectionSocket.send(("User already logged in.")
							.encode())
						continue
					
					username, pwd = clientQuery[1], clientQuery[2]
					if self.server.userLogins.get(username) == pwd:
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
						if self.server.attempt_entry(roomNumber, 
							   self.playerID, connectionSocket) == 0:
							self.room = roomNumber
							connectionSocket.send((
								"3011 In room, not ready").encode())
							print(f"{self.playerID} entered room {str(roomNumber)}.")
						else:
							connectionSocket.send((
								"3014 The room is playing a game").encode())
							print("Room entry rejected.")

					elif command == "/ready":
						if self.room == 0:
							connectionSocket.send((
								"Please enter a room first.").encode())
							continue
						
						self.server.update_room(self.playerID, self.room)
						self.state = "ready"						
								
						# player enters auctioning state
						bidList = self.authenticate_bid(connectionSocket)
						if bidList:
							self.server.submit_bid(bidList, self.playerID, self.room)
						else:
							self.server.remove_player([self.playerID], self.room)
								
							    
                        # TODO exit stuff



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
		self.userLogins = {}
		self.activeUsers = {}       # player ID : socket
		self.playerStatus = {}
		self.roomStatus = {}
		for i in range(TOTAL_ROOMS):
			# {room number : {player ID : isReady}}
			self.playerStatus[i + 1] = {}
			self.roomStatus[i + 1] = "available"
			
        # {auction number : {player ID : bid amount}}
		self.allBids = {i: {} for i in range(6)}
		self.lock = threading.Lock()
		

	def remove_player(self, playerList, room):
		# removes player(s) from their respective room
		with self.lock:
			roomMembers = self.playerStatus.get(room)
			for player in playerList:
				roomMembers.pop(player)
				

    def submit_bid(self, playerBids, playerID, room):
		# aggregates player bids and determines winner
		# sends corresponding results to each player

		with self.lock:
			for auction in self.allBids:
			    auction[playerID] = playerBids[auction]
		
            # if all player bids submitted, calculate winner
            if len(self.allBids.get(0)) == len(self.playerStatus.get(room)):
                wins = {player: 0 for player in self.allBids.get(0).keys()}
                for i in range(6):
                    current = self.allBids.get(0)
                    winner = max(current, key=current.get)
                    wins[winner] += 1
                gameWinner = max(wins, key=wins.get)
				
                # send winning / losing notifications
				self.activeUsers.get(gameWinner).send((
					"3021 You are the winner").encode())
				self.remove_player([gameWinner], room)
				
				for player in self.playerStatus.get(room):
					self.activeUsers.get(player).send((
					"3022 You lost this game").encode())
					self.remove_player([gameWinner], room)


    def attempt_entry(self, room, playerID, connectionSocket):
		# returns success or failure (currently playing game)
		
		with self.lock:
			if self.roomStatus[room] == "available":
				# default player state: not ready
				self.playerStatus[room][playerID] = False
				self.activeUsers[playerID] = connectionSocket
				return 0
			else:
				return 1


	def update_room(self, playerID, room):
		# updates player status to ready (True),
		# checks if game start qualifications are met, and
		# notifies all room members when game begins
		
		with self.lock:
			self.playerStatus[room][playerID] = True
			self.activeUsers.get(playerID).send(("3012 Ready").encode())
			
			if all(self.playerStatus[room].values()) and \
			        len(self.playerStatus[room]) >= 2:
				self.roomStatus[room] = "playing"
				print(self.playerStatus[room].keys())                               # FOR DEBUGGINGGGGGG
				for player in self.playerStatus[room].keys():
					self.activeUsers.get(player).send((
						"3013 Game starts. Please submit your bids").encode())
					

	def format_list(self):
		# displays total rooms, as well as
		# number of playerStatus and status of each room
		
		roomsData = "3001 " + str(TOTAL_ROOMS) + " "
		with self.lock:
			for i in range(TOTAL_ROOMS):
				roomsData = roomsData + \
					str(len(self.playerStatus[i + 1])) + ":" + \
					self.roomStatus[i + 1] + " "

		return roomsData


	def parse_file(self, path):
		# UserInfo.txt line format is user_name:password
		
		with open(path, "r") as f:
			for line in f:
				line = line.strip()
				username, password = line.split(":", 1)
				self.userLogins[username] = password


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
	