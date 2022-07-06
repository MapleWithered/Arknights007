import functools
import os

import cv2

from .. import adb
from .. import resource

@functools.lru_cache()
def get_img_path_suffix():
    resolution = adb.ADB.get_resolution()
    hw_ratio = resolution.width / resolution.height
    return "%.2f" % hw_ratio


@functools.lru_cache()
def get_img_path(path: str) -> str:
    if path[0] == '/':
        path = path[1:]
    return os.path.join(resource.get_resource_path(), get_img_path_suffix(), path)


@functools.lru_cache()
def get_img_bgr(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_COLOR)
    return mat


@functools.lru_cache()
def get_img_gray(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_GRAYSCALE)
    return mat
