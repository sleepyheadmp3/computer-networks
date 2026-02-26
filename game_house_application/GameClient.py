#!/usr/bin/python3

from socket import *
import sys
import termios

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
    state = "command"

    try:
        while not authenticate_user(clientSocket):
            pass

        # client in game hall
        while True:
            if state == "command":
                clientSocket.send((input()).encode())
                serverResponse = clientSocket.recv(1024).decode()
                print(serverResponse)
                if serverResponse.split()[0] == "3012":
                    state = "ready"
                elif serverResponse.split()[0] == "4001":
                    break

            if state == "ready":
                # block input while waiting on game start message
                startMessage = clientSocket.recv(1024).decode()
                print(startMessage)
                if startMessage.split()[0] == "3013":
                    state = "playing"

            if state == "playing":
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
                clientSocket.send((input()).encode())
                print(clientSocket.recv(1024).decode())
                state = "command"

    except Exception as e:
        print("Connection to server lost, exiting program.")

    finally:
        clientSocket.close()

if __name__ == '__main__':
    main()