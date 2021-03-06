import datetime
import os
import time
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt
from ruamel import yaml

from .config import get_config_path
from .imgreco.inventory.reco import get_item_info, get_quantity_ocr
from .navigator import is_main_menu
from . import resource
from .adb import ADB
from .imgreco import imgops
from .imgreco import ocr
from .imgreco.inventory import reco as inventory_reco
from . import navigator
from .resource.inventory_reco import get_net_data

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def is_in_friend_list():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(215, 215, 215), tolerance=8)
    btn_rect = resource.navigator.get_pos("/friends/left_side_rect")
    img_cropped = imgops.mat_crop(img, Rect(*btn_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 4000000:
        return True
    else:
        return False


def main_to_friend_list():
    navigator.press_std_rect("/main_menu/friends")
    time.sleep(.7)
    navigator.press_std_rect("/friends/left_side_rect")
    time.sleep(1.2)
    assert is_in_friend_list()


def exist_more_friend_to_visit():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(209, 88, 6), tolerance=8)
    btn_rect = resource.navigator.get_pos("/friends/next_friend_btn")
    img_cropped = imgops.mat_crop(img, Rect(*btn_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 200000:
        return True
    else:
        return False


def reco_friend_credit():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(255, 255, 255), tolerance=100)
    num_rect = resource.navigator.get_pos("/friends/credit_remain")
    img_cropped = imgops.mat_crop(img, Rect(*num_rect))
    # img_cropped = imgops.mat_bgr2gray(img_cropped)
    ocr_result = ocr.ocr_rect_single_line(img_cropped, ocr_dict='0123456789')
    try:
        return int(ocr_result.str)
    except ValueError:
        return None




def get_today_fuse():
    fuse_path = resource.get_resource_path('friend/fuse.yaml')

    if not os.path.exists(fuse_path):
        fuse = {'status': False, 'timestamp': time.time()}
        with open(fuse_path, 'w', encoding='utf-8') as f:
            yaml.dump(fuse, f, Dumper=yaml.RoundTripDumper, indent=2, allow_unicode=True, encoding='utf-8')
        return False

    with open(fuse_path, 'r', encoding='utf-8') as f:
        fuse = yaml.load(f, Loader=yaml.RoundTripLoader)

    prev_update_time = datetime.datetime.now().replace(hour=4, minute=0, second=0, microsecond=0).timestamp()
    if prev_update_time > time.time():
        prev_update_time = prev_update_time - 24 * 60 * 60

    if fuse.get('timestamp', 0) < prev_update_time:
        fuse['status'] = False
        fuse['timestamp'] = time.time()
        with open(fuse_path, 'w', encoding='utf-8') as f:
            yaml.dump(fuse, f, Dumper=yaml.RoundTripDumper, indent=2, allow_unicode=True, encoding='utf-8')
        return False

    return fuse.get('status', False)


def fuse_up():
    fuse_path = resource.get_resource_path('friend/fuse.yaml')
    fuse = {'status': True, 'timestamp': time.time()}
    with open(fuse_path, 'w', encoding='utf-8') as f:
        yaml.dump(fuse, f, Dumper=yaml.RoundTripDumper, indent=2, allow_unicode=True, encoding='utf-8')


def run_friend():
    if get_today_fuse():
        return
    navigator.back_to_main_menu()
    main_to_friend_list()
    navigator.press_std_pos("/friends/first_friend")
    time.sleep(5)
    credit = reco_friend_credit()
    last_credit = credit - 30
    while True:
        if not exist_more_friend_to_visit():
            break
        credit = reco_friend_credit()
        if credit == last_credit:   # ????????????????????????
            fuse_up()
            break
        last_credit = credit
        navigator.press_std_rect("/friends/next_friend_btn")
        time.sleep(5)
    navigator.back_to_main_menu()