import os
import time
from collections import namedtuple

import cv2

from . import main_menu as main_menu
from . import navigator as navigator
from .adb import ADB
from .imgreco import imgops
from .imgreco import template

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
    navigator.press_std_rect("/task/get_all")

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