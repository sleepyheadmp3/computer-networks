#!/usr/bin/python3

from socket import *
import sys

def authenticate_user(clientSocket):
    # sends user input credentials to server for validation
    username = input("Please input your user name:\n")
    pwd = input("Please input your password:\n")
    clientSocket.send(("/login " + username + " " + pwd).encode())

    response = clientSocket.recv(1024).decode()
    print(response)
    status = response.split()[0]

    if status == "1001":
        return True
    else:
        return False
    

def main(): 
    if len(sys.argv) != 3:
        print("Usage: GameClient.py [hostname / server IP] [port]")
        sys.exit(1)
                        
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    while not authenticate_user(clientSocket):
        pass

    # client in game hall
    while True:
        clientSocket.send((input()).encode())
        serverResponse = clientSocket.recv(1024).decode()
        print(serverResponse)

        # waiting for game start
        if serverResponse.split()[0] == "3012":
            print(clientSocket.recv(1024).decode())                         # TODO: timeout??
            break
    
    # client in auctioning state
    clientSocket.send((input()).encode())
    print(clientSocket.recv(1024).decode())








    clientSocket.close()

if __name__ == '__main__':
    main()