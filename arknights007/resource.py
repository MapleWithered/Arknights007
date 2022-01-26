import functools
import os

import cv2
import dpath.util
from ruamel import yaml

from arknights007 import adb


@functools.lru_cache()
def load_yaml(path: str):
    assert os.path.exists(path), '未能检测到刷图计划文件.'
    with open(path, 'r', encoding='utf-8') as f:
        plan = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
    return plan


@functools.lru_cache()
def get_img_path_suffix():
    resolution = adb.ADB.get_resolution()
    hw_ratio = resolution.width / resolution.height
    return "%.2f" % hw_ratio


@functools.lru_cache()
def get_img_path(path: str) -> str:
    if path[0] == '/':
        path = path[1:]
    return os.path.join("resources/" + get_img_path_suffix(), path)


@functools.lru_cache()
def get_img_bgr(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_COLOR)
    return mat


@functools.lru_cache()
def get_img_gray(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_GRAYSCALE)
    return mat


@functools.lru_cache()
def get_pos(path: str):
    res = load_yaml("resources/navigator/pos.yaml")
    pos = dpath.util.get(res, "/" + get_img_path_suffix() + path)
    return pos
