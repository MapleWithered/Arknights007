import os
import time
import typing
from collections import namedtuple

import cv2

import numpy as np
from cnocr import CnOcr
from matplotlib import pyplot as plt

from .adb import ADB
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


def main_to_task():
    navigator.press_std_rect("/main_menu/task")
    time.sleep(1)

def press_weekly_button():
    navigator.press_std_rect("/task/weekly")
    time.sleep(1)

def check_and_get_all_reward():
    img_gray = ADB.screencap_mat(gray=True)

    template_shortpath = "/task/get_all.png"
    pos_rect = res.get_pos("/task/get_all")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)

    if template.compare_mat(cropped, gear_template) > 0.9:
        navigator.press_std_rect("/task/get_all")
        time.sleep(2)

def run_task():
    navigator.back_to_main_menu()
    if main_menu.main_check_task_remain():
        main_to_task()
        check_and_get_all_reward()
        navigator.handle_reward_scene()
        press_weekly_button()
        check_and_get_all_reward()
        navigator.handle_reward_scene()
        navigator.back_to_main_menu()

if __name__ == '__main__':
    run_task()