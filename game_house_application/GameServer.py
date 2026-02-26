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
        self.room = 0       # rooms use 1-indexing, 0 before joined


    def authenticate_bid(self, connectionSocket):
        # checks bid input validity, returns int bid list or empty if invalid

        try:
            response = connectionSocket.recv(1024).decode().split()
            if not response:
                return [0]

            if response[0] != "/bids" or len(response) != 7:
                connectionSocket.send(("4002 Unrecognized message").encode())
                return []

            response.pop(0)
            bidList = [int(x) for x in response]
            if sum(bidList) > 30 or any(x < 0 for x in bidList):
                connectionSocket.send(("3022 You lost this game").encode())
                return []

            return bidList
        except Exception as e:
            return [0]


    def run(self):
        connectionSocket, addr = self.client
        authenticated = False

        try:
            while True:
                clientQuery = (connectionSocket.recv(1024)).decode().split()
                if not clientQuery:
                    self.server.disconnect(self.playerID, self.room)
                    print(f"Client {addr} disconnected.")
                    break

                command = clientQuery[0]
                if command == "/login":
                    if authenticated:
                        connectionSocket.send(("4002 Unrecognized message")
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

                    elif command == "/enter" and len(clientQuery) == 2:
                        roomNumber = int(clientQuery[1])
                        code = self.server.attempt_entry(roomNumber,
                               self.playerID, connectionSocket)
                        if code == 3011:
                            self.room = roomNumber
                            connectionSocket.send((
                                "3011 In room, not ready").encode())
                            print(self.playerID, "entered room", roomNumber, ".")
                        elif code == 3014:
                            connectionSocket.send((
                                "3014 The room is playing a game").encode())
                            print("Room entry rejected.")
                        else:
                            connectionSocket.send((
                                "4002 Unrecognized message").encode())

                    elif command == "/ready":
                        if self.room == 0:      # no room entered
                            connectionSocket.send((
                                "4002 Unrecognized message").encode())
                            continue

                        self.server.update_player(self.playerID, self.room)
                        self.server.update_room(self.room)

                        # wait for game to start

                        # player enters "playing" state
                        bidList = self.authenticate_bid(connectionSocket)
                        if bidList:
                            self.server.submit_bid(
                                bidList, self.playerID, self.room)
                        elif bidList == [0]:
                            self.server.disconnect(self.playerID, self.room)
                        else:
                            self.server.remove_player(
                                [self.playerID], self.room)

                        self.room = 0

                    elif command == "/exit":
                        connectionSocket.send(("4001 Bye bye").encode())

                    else:
                        connectionSocket.send((
                            "4002 Unrecognized message").encode())
                else:
                    connectionSocket.send((
                        "4002 Unrecognized message").encode())

        except (ConnectionResetError, BrokenPipeError) as e:
            self.server.disconnect(self.playerID, self.room)
            print(f"Connection error from client {addr}, "
                  f" may have disconnected forcibly: {e}")

        except Exception as e:
            self.server.disconnect(self.playerID, self.room)
            print(f"Other error occurred with client: {e}")

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
        self.lock = threading.RLock()


    def remove_player(self, playerList, room):
        # removes player(s) in playerList from corresponding room
        with self.lock:
            roomMembers = self.playerStatus.get(room)
            for player in playerList:
                roomMembers.pop(player)
                self.activeUsers.pop(player)
            print("after removing: ", self.playerStatus.get(room))                              # debug


    def submit_bid(self, playerBids, playerID, room):
        # aggregates player bids and determines winner
        # sends corresponding results to each player

        with (self.lock):
            for i in range(6):
                self.allBids[i][playerID] = playerBids[i]

            # if all player bids submitted, calculate winner
            if len(self.allBids.get(0)) == len(self.playerStatus.get(room)):
                print("calculating winner")
                wins = {player: 0 for player in self.allBids.get(0).keys()}
                for i in range(6):
                    current = self.allBids.get(i)
                    max_bid = max(current.values())
                    winners = [p for p, b in current.items() if b == max_bid]
                    for winner in winners:
                        wins[winner] += 1

                # multiple winners if tie for overall score
                max_win = max(wins.values())
                gameWinners = [x for x, w in wins.items() if w == max_win]

                losers = self.playerStatus.get(room).copy()
                # send winning / losing notifications
                for winner in gameWinners:
                    self.activeUsers.get(winner).send((
                        "3021 You are the winner").encode())
                    print(f"Congrats to {winner} in room {room} :D")
                    losers.pop(winner)

                for player in losers:
                    self.activeUsers.get(player).send((
                        "3022 You lost this game").encode())
                print(f"Losers: {losers}")                                            # DEBUG

                # clears room and resets bid data
                self.remove_player(gameWinners, room)
                self.remove_player(losers, room)
                self.roomStatus[room] = "available"
                print(f"Active users: {list(self.activeUsers)}")                     # DEBUG
                print(f"Room statuses: {self.roomStatus}")                          # DEBUG
                self.allBids = {i: {} for i in range(6)}


    def update_room(self, room):
        # checks if game start qualifications are met, and
        # notifies all room members when game begins

        with self.lock:
            if all(self.playerStatus[room].values()) and \
                    len(self.playerStatus[room]) >= 2:
                self.roomStatus[room] = "playing"
                print("Room", room, "is now playing.")
                for player in self.playerStatus[room]:
                    self.activeUsers.get(player).send((
                    "3013 Game starts. Please submit your bids").encode())
            else:
                self.roomStatus[room] = "available"


    def update_player(self, playerID, room):
        # updates player status to ready (True)
        with self.lock:
            self.playerStatus[room][playerID] = True
            self.activeUsers.get(playerID).send(("3012 Ready").encode())


    def attempt_entry(self, room, playerID, connectionSocket):
        # returns corresponding error or success codes
        with (self.lock):
            if playerID in self.activeUsers:
                return 4002

            if self.roomStatus[room] == "available":
                # default player state: not ready
                self.playerStatus[room][playerID] = False
                self.activeUsers[playerID] = connectionSocket
                return 3011
            else:
                return 3014


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

    def disconnect(self, playerID, room):
        # handles client disconnect by updating server based on client state

        # "not ready" state: update room info
        with self.lock:
            if room != 0:
                self.remove_player([playerID], room)

            # playing state: reevaulates auction
            if self.roomStatus[room] == "playing":
                remaining = self.playerStatus.get(room)
                if len(remaining) == 1:
                    self.activeUsers[remaining[0]].send(
                        ("3021 You are the winner").encode())
                    self.remove_player(remaining, room)
                    self.allBids = {i: {} for i in range(6)}
            self.update_room(room)


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
        print("Server connected.")
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
