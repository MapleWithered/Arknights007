# echo-client.py

import socket
import time

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

if __name__ == '__main__':

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            time.sleep(2)
            s.sendall(b"Hello, world")
            data = s.recv(1024)
            print(f"Received {data!r}")
