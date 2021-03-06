import functools
import os.path
import subprocess
import time
import typing
from collections import namedtuple
from pathlib import Path

import PIL
import cv2
import numpy as np
import ppadb.device
from PIL import Image
from ppadb.client import Client

from .imgreco import imgops

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])


def get_adb_path() -> str:
    return os.path.join(os.path.join(str(Path(__file__).parent.parent.parent), "adb"), "adb.exe")


def start_server():
    p = subprocess.Popen([get_adb_path(), 'start-server'])
    while p.wait():
        time.sleep(0.5)


def start_client(host: str = "127.0.0.1", port: int = 5037) -> Client:
    client = Client(host, port)
    try:
        client.version()  # 尝试进行实际通讯
    except RuntimeError:
        start_server()
        client = Client(host, port)
        client.version()
    return client


def connect_remote(client: Client = None, host: str = "127.0.0.1", port: int = 7555) -> bool:
    if client is None:
        client = start_client()
    return client.remote_connect(host, port)


def device(client: Client = None, device_id: int = 0) -> ppadb.device.Device:
    if client is None:
        client = start_client()
    devices = client.devices()
    if len(devices) == 0:
        raise RuntimeError("No devices found.")
    else:
        if len(devices) <= device_id:
            raise RuntimeError("Device id out of range. (0-" + str(len(devices)) + ") (get: " + str(device_id))
        return devices[device_id]


def auto_connect(host: str = "127.0.0.1", port: int = 7555):
    connect_remote(None, host, port)
    return device()


# Static class(?)
class ADB:
    _device: ppadb.device.Device = None
    _prev_screenshot_raw = None
    _prev_screenshot_timestamp = 0

    @classmethod
    def connect(cls, host: str = "127.0.0.1", port: int = 7555):
        cls._device = auto_connect()

    @classmethod
    @functools.lru_cache()
    def get_resolution(cls) -> typing.Optional[Size]:
        if cls._device is None:
            cls.connect()
        size = cls._device.wm_size()
        if size is not None:
            if size[0] > size[1]:
                long = size[0]
                short = size[1]
            else:
                long = size[1]
                short = size[0]
            return Size(int(long), int(short))
        else:
            return None

    @classmethod
    def screencap_raw(cls, force: bool = False) -> str:
        screenshot_ttl = 0.2
        if cls._device is None:
            cls.connect()
        if time.monotonic() - cls._prev_screenshot_timestamp > screenshot_ttl or force:
            cls._prev_screenshot_raw = cls._device.screencap()
            cls._prev_screenshot_timestamp = time.monotonic()
            return cls._prev_screenshot_raw
        else:
            return cls._prev_screenshot_raw

    @classmethod
    def screencap_mat(cls, force: bool = False, std_size: bool = False, gray=False) -> np.array:
        if cls._device is None:
            cls.connect()
        img_np = np.frombuffer(cls.screencap_raw(force), dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        if std_size:
            img = imgops.mat_size_real_to_std(img)
        if gray:
            img = imgops.mat_bgr2gray(img)
        return img

    @classmethod
    def screencap_pil(cls, force: bool = False, std_size: bool = False) -> PIL.Image.Image:
        if cls._device is None:
            cls.connect()
        img = Image.fromarray(cls.screencap_mat(force=force, std_size=std_size))
        return img

    @classmethod
    def get_top_activity(cls):
        if cls._device is None:
            cls.connect()
        # TODO: feat. Ensure arknights is running
        return cls._device.get_top_activity()

    @classmethod
    def input_text(cls, string: str):
        if cls._device is None:
            cls.connect()
        return cls._device.input_text(string)

    @classmethod
    def input_keyevent(cls, keycode, long_press=False):
        if cls._device is None:
            cls.connect()
        return cls._device.input_keyevent(keycode, long_press)

    @classmethod
    def input_tap(cls, x, y):
        if cls._device is None:
            cls.connect()
        return cls._device.input_tap(x, y)

    @classmethod
    def input_swipe(cls, start_x, start_y, end_x, end_y, duration_ms):
        if cls._device is None:
            cls.connect()
        return cls._device.input_swipe(start_x, start_y, end_x, end_y, duration_ms)

    @classmethod
    def input_press_pos(cls, pos: Pos):
        cls.input_tap(pos.x, pos.y)

    @classmethod
    def input_press_rect(cls, rect: Rect):
        cls.input_tap(int((rect.x1 + rect.x2) / 2), int((rect.y1 + rect.y2) / 2))

    @classmethod
    def input_swipe_pos(cls, pos1: Pos, pos2: Pos, duration_ms: int):
        cls.input_swipe(int(pos1.x), int(pos1.y), int(pos2.x), int(pos2.y), duration_ms)

    @classmethod
    def input_roll(cls, dx, dy):
        if cls._device is None:
            cls.connect()
        return cls._device.input_roll(dx, dy)

    @classmethod
    def run_activity(cls):
        if cls._device is None:
            cls.connect()
        # TODO: feat. Restart arknights when crashed
        pass

    @classmethod
    def create_connection(cls):
        if cls._device is None:
            cls.connect()
        conn = cls._device.create_connection()
        return conn

    @classmethod
    def get_device_object(cls):
        if cls._device is None:
            cls.connect()
        return cls._device
