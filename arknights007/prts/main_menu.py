from collections import namedtuple

import numpy as np

from .navigator import is_main_menu
from . import resource as res
from .adb import ADB
from .imgreco import imgops
from .imgreco import ocr

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def main_menu_reco_sanity(force=False):
    assert is_main_menu()
    img = ADB.screencap_mat(gray=False, std_size=True, force=force)
    img = imgops.mat_pick_color_rgb(img, Color(51, 51, 51))
    img[img != 0] = 255
    corner_rect = res.navigator.get_pos("/main_menu/sanity_remain")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    # plt.imshow(img_cropped)
    # plt.show()
    ocr_result = ocr.ocr_rect_single_line(img_cropped, ocr_dict='0123456789')
    return int(ocr_result.str)


def main_check_task_remain():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(230, 98, 41))
    corner_rect = res.navigator.get_pos("/main_menu/task_number")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 50000:
        return True
    else:
        return False


def main_check_ship_remain():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(35, 159, 214))
    corner_rect = res.navigator.get_pos("/main_menu/ship_info")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    # plt.imshow(img_cropped)
    # plt.show()
    if np.sum(img_cropped) > 80000:
        return True
    else:
        return False


def main_check_shop_remain():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(255, 104, 1))
    corner_rect = res.navigator.get_pos("/main_menu/shop_corner_notification")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 7000:
        return True
    else:
        return False


if __name__ == '__main__':
    main_check_shop_remain()