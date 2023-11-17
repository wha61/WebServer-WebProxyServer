# use python socket lib
from socket import *

# Assign a Server Port
serverPort = 3000

# Create TCP welcoming socket
serverSocket = socket(AF_INET,SOCK_STREAM)

# Bind the server address & server port to the socket
serverSocket.bind(('192.168.56.1',serverPort))

# Server begins listerning for incoming TCP connections
# set 1 for at most 1 connection at a time
serverSocket.listen(1)

while True:  # Loop forever
    print('The server ready:')

    # Set up connection for the client, a new socket
    connectionSocket, addr = serverSocket.accept()

    try:
        # Receive request message from client
        message = connectionSocket.recv(1024)
        print('The request message from client:', message)

        if not message:
            raise ValueError("Empty request received")

        message_parts = message.split()

        if len(message_parts) < 2:
            raise ValueError("Invalid HTTP request format")

        # From message get file name
        testFile = message_parts[1][1:]
        print('The test file from client:', testFile)

        # Open file and get html data
        with open(testFile, 'rb') as file:  # 'rb' is for reading in binary mode
            testHTML = file.read()

        # Send HTTP response header to client
        connectionSocket.send("HTTP/1.1 200 OK\r\n\r\n".encode())

        connectionSocket.send(testHTML)

        connectionSocket.close()
    
    except IOError:
        # Send HTTP response header for file not found to client
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
        connectionSocket.close()
    except ValueError as e:
        # Log the error and send a 400 Bad Request response
        print(e)
        connectionSocket.send("HTTP/1.1 400 Bad Request\r\n\r\n".encode())
        connectionSocket.close()
