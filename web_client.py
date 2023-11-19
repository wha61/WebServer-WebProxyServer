from socket import *

serverName = '127.0.0.1'
serverPort = 8080

clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))

requestOne = "GET /test.html HTTP/1.1\r\nHost: '127.0.0.1'\r\n"
byteLength = len(requestOne.encode("utf-8"))
contentLength = f"Content-Length:{byteLength}\r\n"
requestList = [requestOne, contentLength]
fullRequest = " ".join(requestList)
print(fullRequest)

clientSocket.send(fullRequest.encode())

responseOne = clientSocket.recv(1024)

while responseOne:
    print(responseOne.decode())
    responseOne = clientSocket.recv(1024)

clientSocket.close()
