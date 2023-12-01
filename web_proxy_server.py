import socket
import os
import time
from email.utils import formatdate,parsedate

# Proxy Server Configuration
proxy_server_port = 80
originator_server_port = 8080
originator_server_address = '127.0.0.1'

# Create TCP socket for Proxy Server
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.bind(('127.0.0.1', proxy_server_port))
proxy_socket.listen(1)

# Cache for storing web pages
cache = {}

while True:
    print('-----------------------------------------------------\n The Proxy Server ready:')

    # Accepting connection from client
    connection_socket, client_address = proxy_socket.accept()

    try:
        # Receiving request from client
        request_message = connection_socket.recv(1024).decode('utf-8')
        request_line = request_message.split("\r\n")[0]
        request_method, requested_resource, _ = request_line.split()
        requested_resource = requested_resource[1:]
        # print("requested_resource: ", requested_resource)
        # print("cache: ", cache)

        # Request Handling: determine 200 and 304 response
        # To test, run following 2 commands in cmd:
        # 1.checked modifiedTime < lastModified, cache is out date, should go to server and return 200 OK:
        # curl -i http://localhost/proxy_test.html -H "If-Modified-Since: Sat, 21 Oct 2023 07:28:00 GMT"
        # 2.checked modifiedTime >= lastModified, cache is up to date, should not go to server and return 304 Not Modified:
        # curl -i http://localhost/proxy_test.html -H "If-Modified-Since: Sat, 21 Dec 2023 07:28:00 GMT"
        if "If-Modified-Since:" in request_message:
            modifiedTimeString = request_message.split("If-Modified-Since:")[1]
            modifiedTime = parsedate(modifiedTimeString)
            # Check cache for the requested resource
            if requested_resource in cache:
                # Check if the cached copy is up to date
                cached_copy, last_modified = cache[requested_resource]
                # Format the time to a string in the RFC 2822 format, e.g., "Thu, 30 Nov 2023 22:48:17 GMT"
                last_modified_time = formatdate(timeval=last_modified, localtime=False, usegmt=True)
                print("Last Modify time: ", last_modified_time)
                last_modified_time = parsedate(last_modified_time)
                if time.mktime(last_modified_time) <= time.mktime(modifiedTime):
                    connection_socket.send("HTTP/1.1 304 Not Modified\r\n\r\n".encode())
                    connection_socket.close()
                    continue
        else:
            # check modify time in cache
            if requested_resource in cache:
                    # Check if the cached copy is up to date
                    cached_copy, last_modified = cache[requested_resource]
                    # Format the time to a string in the RFC 2822 format, e.g., "Thu, 30 Nov 2023 22:48:17 GMT"
                    last_modified_time = formatdate(timeval=last_modified, localtime=False, usegmt=True)
                    print("Last Modify time1: ", last_modified_time)
                    if time.time() - last_modified < 60:  # Assume 60 seconds cache validity for simplicity
                        connection_socket.send("HTTP/1.1 304 Not Modified\r\n\r\n".encode())
                        connection_socket.close()
                        continue  

        # Forwarding Requests: Forwarding HTTP Request to Originator Server
        originator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        originator_socket.connect((originator_server_address, originator_server_port))
        http_request = f"GET /{requested_resource} HTTP/1.1\r\nHost: {originator_server_address}\r\n\r\n"
        originator_socket.send(http_request.encode())

        # Receiving response from originator server
        # Initialize response variable
        response = b''
        # receive response head
        while True:
            part = originator_socket.recv(8000)
            response += part
            if len(part) < 8000:  # No more data
                break
        # receive response body
        while True:
            part = originator_socket.recv(8000)
            response += part
            if len(part) < 8000:  # No more data
                break
        originator_socket.close()

        # Extract status code and content
        response_lines = response.decode().split("\r\n")
        print("response_lines: ", response_lines)

        status_line = response_lines[0]
        status_code = int(status_line.split(" ")[1])

        # Handle response
        if status_code == 200:
            # Caching Mechanism:  store copies of requested web pages
            body = "\r\n".join(response_lines[response_lines.index("") + 1:])
            cache[requested_resource] = (body.encode(), time.time())

            # Send response to client
            connection_socket.send("HTTP/1.1 200 OK\r\n\r\n".encode())
            connection_socket.send(body.encode())
        else:
            # Send error response to client, like 
            connection_socket.send(f"HTTP/1.1 {status_code} {status_line.split(' ', 2)[2]}\r\n\r\n".encode())

        connection_socket.close()

    except Exception as e:
        print(f"Error: {e}")
        connection_socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode())
        connection_socket.close()
