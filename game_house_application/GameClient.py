#!/usr/bin/python3

from socket import *
import sys

def authenticate_user(clientSocket):
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


    # TODO




    clientSocket.close()

if __name__ == '__main__':
    main()