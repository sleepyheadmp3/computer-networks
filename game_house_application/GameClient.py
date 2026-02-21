#!/usr/bin/python3

from socket import *
import sys

def authenticate_user():
    username = input("Please input your user name:\n")
    pwd = input("Please input your password:\n")

def main(): 
    # usage: python3 GameClient.py [hostname / server IP] [port]
    serverName = sys.argv[1]
    serverPort = sys.argv[2]
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    # TODO
    # if authenticate_user()


    clientSocket.close()