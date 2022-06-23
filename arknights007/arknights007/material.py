
import os
import time
import typing
from collections import namedtuple

import numpy as np
from cnocr import CnOcr
from matplotlib import pyplot as plt

from .adb import ADB
import cv2
import arknights007.imgreco.imgops as imgops
import arknights007.imgreco.template as template
import arknights007.imgreco.ocr as ocr
import arknights007.resource as res
import arknights007.navigator as navigator
import arknights007.main_menu as main_menu

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def save_screenshot_after_battle(stage: str):
    img = ADB.screencap_mat(force=True, std_size=False)
    # generate file path with timestamp
    date_str = time.strftime("%Y%m%d", time.localtime())
    time_str = time.strftime("%H%M%S", time.localtime())
    file_name = f"{date_str}_{time_str}_{stage}.png"
    folder_path = os.path.join("../battle_screenshot", f"{date_str}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    # save image
    imgops.save_image(img, file_path)