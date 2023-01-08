import os
import re
import time
from collections import namedtuple

import cv2
from cnocr import CnOcr
from ruamel import yaml

from .. import battle, navigator
from ..resource import navigator as res_nav
from ..resource import image as res_img
from ..resource import yaml as res_yaml
from .. import config
from ..adb import ADB
from ..imgreco import imgops
from ..imgreco import ocr
from ..imgreco import template
from ..resource.image import get_img_path, get_img_gray
from ..navigator import is_terminal, back_to_terminal, press_std_pos


def back_to_rogue_menu():
    try:
        assert is_terminal()
    except AssertionError:
        back_to_terminal()
        assert is_terminal()
    press_std_pos("/terminal/rogue")
    time.sleep(8)


def enter_rogue(rogue_name):
    img_pattern = get_img_gray(f"/rogue/{rogue_name}/terminal_rogue_choose.png")
    # Screenshot
    img = imgops.mat_threshold(ADB.screencap_mat(std_size=True, gray=True), 10)
    # Find the pattern
    result = template.match_template_best(img, img_pattern)
    if result.val > 0.1:
        raise RuntimeError("Cannot find the desired rogue on the screen.")
    # Click
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), result.rect))
    time.sleep(2)
    navigator.press_std_pos("/rogue/enter_theme")
    time.sleep(5)


def run(rogue_name):
    import importlib

    rogue = importlib.import_module(f".{rogue_name}.run", package="arknights007.prts.rogue")

    if not rogue.is_main_menu():
        back_to_rogue_menu()
        enter_rogue(rogue_name)

    rogue.run()
