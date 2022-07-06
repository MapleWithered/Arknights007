import socket
#
# def decoder(data: bytes) -> dict:
#     data_str = data.decode('utf-8')


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)


if __name__ == '__main__':

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print('Waiting for connection')
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:        # The socket is lost
                    break
                else:
                    print(data.decode('utf-8'))
                    conn.sendall(data)