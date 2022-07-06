import socket
import json

'''
主动回传以下种类的信息：
日志
理智
计划清单
物品清单

'''  # TODO: 剩下的见Xd


# Message format:
# {
#     "operation": "POST/GET",
#     "api": "textlog",
#     "data": {
#         xxxxxxxxxxx
#     }
# }


class SocketLogger:

    @classmethod
    def wait_json(cls):
        if not Socket.is_connected():
            Socket.connect_client()
        data = json.loads(Socket.recv(1024).decode('utf-8'))
        Socket.send(json.dumps({'success': True}).encode('utf-8'))
        return data

    @classmethod
    def send_json(cls, data: dict):
        if not Socket.is_connected():
            return {'success': False, 'message': 'No connection'}
        Socket.send(json.dumps(data).encode('utf-8'))
        ret = json.loads(Socket.recv(1024).decode('utf-8'))
        assert ret['success']
        return ret

    @classmethod
    def log_text(cls, text: str):
        if not Socket.is_connected():
            print(text)
        data = {}  # TODO
        ret = SocketLogger.send_json(data)
        assert ret['success']


class Socket:
    _socket: socket.socket = None
    _conn: socket.socket = None
    _addr: tuple = None

    @classmethod
    def connect_client(cls, port: int = 65432):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.bind(('127.0.0.1', port))
        _socket.listen()
        print('Waiting for socket connection')
        _conn, _addr = _socket.accept()
        print(f'Connected by {_addr[0]}:{_addr[1]}')

    @classmethod
    def send(cls, data: bytes):
        if cls._conn is None:
            return False
        cls._conn.sendall(data)
        return True

    @classmethod
    def recv(cls, size: int):
        if cls._conn is None:
            return None
        return cls._conn.recv(size)

    @classmethod
    def is_connected(cls):
        return cls._conn is not None
