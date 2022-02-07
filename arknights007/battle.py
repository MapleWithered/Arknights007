import os
import time
import typing
from collections import namedtuple

from cnocr import CnOcr
from matplotlib import pyplot as plt

from adb import ADB
import cv2
import imgreco.imgops as imgops
import imgreco.template as template
import imgreco.ocr as ocr
import resource as res
import navigator

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])

STATUS_IN_BATTLE = 1
STATUS_FINISHED = 2
STATUS_ERROR = -1
STATUS_FAILED = -2
STATUS_UNKNOWN = 0


def before_battle_reco_stage_code(screenshot_gray=None):
    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    pos_rect = res.get_pos("/before_battle/stage_code_small_noise_square")
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect))

    img_gray[pos_rect.y1:pos_rect.y2, pos_rect.x1:pos_rect.x2] = 0

    pos_rect = res.get_pos("/before_battle/stage_code")
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect))

    cropped = imgops.mat_crop(img_gray, pos_rect)
    cropped = imgops.mat_pick_grey(cropped, 235, 20)

    ocrresult = ocr.ocr_rect_single_line(cropped, None, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789')
    return ocrresult.str


def before_battle_reco_sanity_cost(screenshot_gray=None):
    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    pos_rect = res.get_pos("/before_battle/sanity_cost")
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect))

    cropped = imgops.mat_crop(img_gray, pos_rect)
    cropped = imgops.mat_pick_grey(cropped, 200, 100)

    ocr_result = ocr.ocr_rect_single_line(cropped, None, '-0123456789')
    return int(ocr_result.str.replace('-', ''))


def before_battle_reco_sanity_remain(screenshot_gray=None):
    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    pos_rect = res.get_pos("/before_battle/sanity_remain")
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect))

    cropped = imgops.mat_crop(img_gray, pos_rect)
    cropped = imgops.mat_pick_grey(cropped, 200, 100)

    ocr_result = ocr.ocr_rect_single_line(cropped, None, '/0123456789')
    return int(ocr_result.str[:ocr_result.str.find('/')])


def before_battle_check_tickbox(screenshot_gray=None):
    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    result = is_tickbox_ticked(img_gray)
    if result is None:
        return False
    elif result == 1:
        return True
    elif result == 0:
        navigator.press_std_rect("/before_battle/tickbox")
        return True


def is_tickbox_ticked(screenshot_gray=None):
    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    template_shortpath = "/before_battle/tickbox_ticked.png"
    pos_rect = res.get_pos("/before_battle/tickbox")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)

    if template.compare_mat(cropped, gear_template) > 0.9:
        return 1

    template_shortpath = "/before_battle/tickbox_not_ticked.png"
    pos_rect = res.get_pos("/before_battle/tickbox")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)

    if template.compare_mat(cropped, gear_template) > 0.9:
        return 0
    else:
        return None


def is_team_scene(screenshot_gray=None):

    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    template_shortpath = "/before_battle/team_start.png"
    pos_rect = res.get_pos("/before_battle/team_start")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)

    if template.compare_mat(cropped, gear_template) > 0.9:
        return 1
    else:
        return 0


def is_finished(screenshot_gray=None):

    if screenshot_gray is None:
        img_gray = ADB.screencap_mat(gray=True)
    else:
        img_gray = screenshot_gray.copy()

    template_shortpath = "/battle/finished.png"
    pos_rect = res.get_pos("/battle/finished")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 230, 30)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)

    if template.compare_mat(cropped, gear_template) > 0.9:
        return 1
    else:
        return 0


def start_battle(ensure_stage_code: str = ''):

    if not navigator.is_battle_start_button_visible():
        print("无法看到开始按钮")
        return False

    img_gray = ADB.screencap_mat(force=True, gray=True)

    if ensure_stage_code != '':
        if before_battle_reco_stage_code(img_gray) != ensure_stage_code:
            print("当前关卡非目标关卡 ( now: "+ensure_stage_code+" != "+before_battle_reco_stage_code(img_gray)+" )")
            return False

    before_battle_check_tickbox(img_gray)

    if before_battle_reco_sanity_cost(img_gray) > before_battle_reco_sanity_remain(img_gray):
        print("理智不足 ( now: "+str(before_battle_reco_sanity_remain(img_gray))+" < "+str(before_battle_reco_sanity_cost(img_gray))+" )")
        return False

    navigator.press_std_rect("/before_battle/start_button")
    time.sleep(2)

    if not is_team_scene():
        raise RuntimeError("非编队选择界面")
        return False

    navigator.press_std_rect("/before_battle/team_start")

    # TODO: bugfix. handle unexpecccted scene
    # After battle, handle unknown scene, if timeout , return False
    # For robust

    while not is_finished():
        time.sleep(1)

    time.sleep(8)
    navigator.press_std_rect("/battle/finished")
    time.sleep(3)
    while not navigator.is_battle_start_button_visible():
        navigator.press_std_rect("/battle/finished")
        time.sleep(5)

    return True


