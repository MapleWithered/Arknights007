from functools import lru_cache

import socketio

from .config.yaml import load_yaml

import requests


def log(msg: str):
    if if_config_use_cli():
        print(msg)
    if if_config_use_server():
        SocketIO.emit('log', msg)


def log_v(msg: str, *args, **kwargs):
    if if_config_use_cli():
        print(msg, *args, **kwargs)


def info(msg: str):
    if if_config_use_cli():
        print(msg)
    if if_config_use_server():
        SocketIO.emit('log', msg)


def warning(msg: str):
    if if_config_use_cli():
        print(msg)
    if if_config_use_server():
        SocketIO.emit('log', msg)


@lru_cache(maxsize=1)
def if_config_use_server():
    cfg = load_yaml('logging.yaml')
    if cfg['use_server']:
        return True
    return False


@lru_cache(maxsize=1)
def if_config_use_cli():
    cfg = load_yaml('logging.yaml')
    if cfg['use_cli']:
        return True
    return False


class SocketIO:
    _sio: socketio.Client = socketio.Client()

    @classmethod
    def connected(cls):
        return cls._sio.connected

    @classmethod
    def connect(cls, host: str = "127.0.0.1", port: int = 9019):
        cls._sio.connect(f'http://{host}:{port}', namespaces=['/prts'])

    @classmethod
    def emit(cls, event: str, data):
        if not cls.connected():
            cls.connect()
        cls._sio.emit(event, data, namespace='/prts')
