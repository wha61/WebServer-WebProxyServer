#!/bin/python3
from socket import *
import os
import time
from email.utils import parsedate, formatdate
import threading

def handle_client(connectionSocket):
    print(f"Thread ID: {threading.get_ident()}")

    try:
        # Receive request message from client
        message = connectionSocket.recv(1024).decode('utf-8')
        print('The request message from client:', "\n", message)

        # case 400-Bad Request(not yet complete)
        message_parts = message.split("\r\n")
        message_part = message_parts[0] if message_parts else ''
        # test use:
        if not message_part or len(message_part.split()) != 3:
            raise ValueError("Invalid request line")
        request_method, request_path, request_protocol = message_part.split()
        # test use: curl -i -X BOGUS http://localhost:8080/test.html
        if request_method not in supported_methods:
            raise ValueError(f"Unsupported method: {request_method}")
        # test use:
        for header in message_parts[1:]:
            if header and ":" not in header:
                raise ValueError(f"Invalid header format: {header}")

        # From message get file name
        testFile = message_part.split()[1][1:]
        print('The test file request from client:', testFile, "\n")

        # Get metadata last modified of the testfile we have in our OS.
        lastModified = os.path.getmtime(testFile)
        lastModifiedString = formatdate(timeval = lastModified, localtime=False, usegmt=True)
        print("Last Modify time:", lastModifiedString, "\n")

        # case 304-Not Modified (implemented)
        # the last modfied time of modified.html is Sun, 19 Nov 2023 07:10:11 GMT
        # To test, run following 2 commands in cmd:
        # 1.modifiedTime < lastModified, should return 200 OK:
        # curl -i http://localhost:8080/modified.html -H "If-Modified-Since: Sat, 21 Oct 2023 07:28:00 GMT"
        # 2.modifiedTime >= lastModified, should return 304 Not Modified:
        # curl -i http://localhost:8080/modified.html -H "If-Modified-Since: Sat, 21 Dec 2023 07:28:00 GMT"
        if "If-Modified-Since:" in message:
            modifiedTimeString = message.split("If-Modified-Since:")[1]
            modifiedTime = parsedate(modifiedTimeString)
            if lastModified <= time.mktime(modifiedTime):
                connectionSocket.send("HTTP/1.1 304 Not Modified\r\n\r\n".encode())
                connectionSocket.close()
                return

        # case 403-Forbidden(implemented)
        if testFile in forbiddenList:
            connectionSocket.send("HTTP/1.1 403 Forbidden\r\n\r\n".encode())
            connectionSocket.close()
            return

        # case 411-Length Required(implemented)
        # To test, run following 2 commands in cmd:
        # 1.no content length: curl -i -X POST http://localhost:8080/test.html -H "Content-Type: application/x-www-form-urlencoded"
        # 2.with content length: curl -i -X POST http://localhost:8080/test.html -H "Content-Type: application/x-www-form-urlencoded" -d "test:value"
        requires_content_length = False
        request_method, request_path, request_protocol = message_part.split()
        print(f"Request Method: {request_method}")  # 添加这行来检查请求方法
        # GET usually do not have Content-Length section,
        # so check when get POST or PUT request
        requires_content_length = request_method in ["POST", "PUT"]
        content_length_present = "Content-Length:" in message
        if requires_content_length and not content_length_present:
            connectionSocket.send("HTTP/1.1 411 Length Required\r\n\r\n".encode())
            connectionSocket.close()
            return

        # Open file and get html data
        with open(testFile, 'rb') as file:
            testHTML = file.read()

        # case 200-OK(implemented)
        connectionSocket.send("HTTP/1.1 200 OK\r\n\r\n".encode())
        connectionSocket.send(testHTML)
        connectionSocket.close()

    except IOError:
        # Send HTTP response header for file not found to client
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
        connectionSocket.close()
        return
    except ValueError as e:
        # Log the error and send a 400 Bad Request response
        print(e)
        connectionSocket.send("HTTP/1.1 400 Bad Request\r\n\r\n".encode())
        connectionSocket.close()
        return


# Assign a Server Port
serverPort = 8080

# Create TCP welcoming socket
serverSocket = socket(AF_INET,SOCK_STREAM)

forbiddenList = ["secret.html"]

supported_methods = ["GET", "POST", "PUT", "DELETE"]

# Bind the server address & server port to the socket
# localhost/8080:
serverSocket.bind(('127.0.0.1',serverPort))

# Server begins listerning for incoming TCP connections
# set 1 for at most 1 connection at a time
serverSocket.listen(1)

while True:  # Loop forever

    print('-----------------------------------------------------\n The Server ready:')
    try:
        # Set up connection for the client, a new socket
        connectionSocket, addr = serverSocket.accept()
        #Make each connection a thread
        threading.Thread(target=handle_client, args=(connectionSocket,)).start()
    except KeyboardInterrupt:
        print("\nBye!")
        exit()
