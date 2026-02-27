#!/usr/bin/python3

import random
import socket
import threading

class ServerThread(threading.Thread):
    def __init__(self, client, secret):
        threading.Thread.__init__(self)
        self.client = client
        self.secret = secret

    def compare_guess(self, guess):
        # Step 4: compare the client's guess against the secret,
        # then generate and return a feedback accordingly.
        feedback = ''
        secret_l = list(self.secret)
        guess_l = list(guess)

        for i in range(4):
            if guess_l[i] == secret_l[i]:
                feedback += 'b'
                secret_l[i] = 'x'   # nullify matched numbers
                guess_l[i] = 'x'
        
        for i in range(4):
            if (guess_l[i] != 'x') and (guess_l[i] in secret_l):
                feedback += 'w'
                secret_l[secret_l.index(guess_l[i])] = 'x'
        
        for i in range(4 - len(feedback)):
            feedback += '-'

        return feedback
        
    def run(self):
        connectionSocket, addr = self.client
        player_IP, player_port = addr

        try:
            remain_attempts = 10

            while True:
                # Step 4: read the client's guesses and send responses
                # until the client guesses correctly or remaining attempts count reaches 0.

                guess = connectionSocket.recv(1024).decode()
                print("Player " + str(player_port) + "'s guess is: " + guess + ".")
                feedback = self.compare_guess(guess)

                if feedback == 'bbbb':
                    connectionSocket.send((feedback + " Secret cracking success!").encode())
                    break
                if remain_attempts <= 1:
                    connectionSocket.send((feedback + " Secret cracking failed.").encode())
                    break

                remain_attempts -= 1
                connectionSocket.send((feedback + " Your remaining attempts are " + str(remain_attempts) + ".").encode())
            
        finally:
            connectionSocket.close()


class ServerMain:
    def __init__(self):
        self.secret = ''
        for i in range(4):
            self.secret += str(random.randrange(1, 7))

    def server_run(self):
        # Step 3: set up `serverSocket` that listens for TCP connections on port 12000.
        # Hint: refer to socketprog_examples/TCPSocket-5.

        serverPort = 12000
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(("", serverPort))
        serverSocket.listen(5) 

        print(f"Game starts! The secret is {self.secret}")

        while True:
            # Step 3: accept a connection and launch a thread to handle the connection.
            # Pass appropriate arguments to the thread constructor.

            client = serverSocket.accept()
            t = ServerThread(client, self.secret)
            t.start()



if __name__ == '__main__':
    server = ServerMain()
    server.server_run()
