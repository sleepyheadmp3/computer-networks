#!/usr/bin/python3

import socket

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverName = "localhost" # on local machine

serverPort = 12000

clientSocket.connect( (serverName, serverPort) )

try:
    print("Game starts! Your remaning attempts are 10.")
    while True:
        move = input("Make your guess: ")

        clientSocket.send(move.encode())

        response = clientSocket.recv(1024).decode()

        print(response)

        # success! or failed.
        if response[-3:] == 'ss!' or response[-3:] == 'ed.':
            break
finally:
    clientSocket.close()
