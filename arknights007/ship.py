import os
import time
import typing
from collections import namedtuple

import numpy as np
from cnocr import CnOcr
from matplotlib import pyplot as plt

from adb import ADB
import cv2
import imgreco.imgops as imgops
import imgreco.template as template
import imgreco.ocr as ocr
import resource as res
import navigator
from arknights007 import main_menu

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def check_and_press_blue_button():
    img = ADB.screencap_mat(gray=False, std_size=True)

    color_white = Color(245, 245, 245)
    color_blue_when_red_pressed = Color(11, 145, 205)
    color_blue = Color(44, 166, 215)
    color_red = Color(204, 78, 86)
    color_red_when_blue_pressed = Color(186, 47, 56)

    path_up = "/ship/notification_button_1"
    path_down = "/ship/notification_button_2"

    rect_up = res.get_pos(path_up)
    img_up = imgops.mat_crop(img, Rect(*rect_up))
    img_up_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_white, tolerance=10))
    img_up_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue, tolerance=10))
    img_up_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red, tolerance=10))
    img_up_blue_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue_when_red_pressed, tolerance=14))
    img_up_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red_when_blue_pressed, tolerance=10))

    rect_down = res.get_pos(path_down)
    img_down = imgops.mat_crop(img, Rect(*rect_down))
    img_down_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_white, tolerance=10))
    img_down_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_blue, tolerance=10))
    img_down_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red, tolerance=10))
    img_down_blue_p = imgops.mat_bgr2gray(
        imgops.mat_pick_color_rgb(img_down, color_blue_when_red_pressed, tolerance=14))
    img_down_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red_when_blue_pressed, tolerance=10))

    plt.imshow(img_up)
    plt.show()

    if np.sum(img_up_blue) > 400000:  # 上蓝下空 未按
        navigator.press_std_rect(path_up)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_red) > 400000 and np.sum(img_down_blue > 400000):  # 上红下蓝 未按
        navigator.press_std_rect(path_down)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_blue_p) > 40000:  # 上蓝下空 已按蓝色
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_red_p) > 40000 and np.sum(
            img_down_blue_p) > 400000:  # 上红下蓝 已按红色
        navigator.press_std_rect(path_down)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_red_p) > 400000 and np.sum(img_down_white) > 1000000 and np.sum(img_down_blue_p) > 40000:
        return True


def reco_bottom_first_button():
    img = ADB.screencap_mat(gray=False, std_size=True)
    rect_1 = res.get_pos("/ship/bottom_1")
    img_1 = imgops.mat_crop(img, Rect(*rect_1))
    ocr_1 = ocr.ocr_rect_single_line(img, rect=Rect(*rect_1), ocr_dict='可收获订单交付干员信赖疲劳线索搜集', debug_show=True,
                                     bigger_box=5)
    return ocr_1.str


def reco_bottom_second_button():
    img = ADB.screencap_mat(gray=False, std_size=True)
    rect_2 = res.get_pos("/ship/bottom_2")
    img_2 = imgops.mat_crop(img, Rect(*rect_2))
    ocr_2 = ocr.ocr_rect_single_line(img, rect=Rect(*rect_2), ocr_dict='可收获订单交付干员信赖疲劳线索搜集', debug_show=True,
                                     bigger_box=5)
    return ocr_2.str


def check_and_press_bottom_button():
    while reco_bottom_first_button() in ['可收获', '订单交付', '干员信赖']:
        navigator.press_std_rect('/ship/bottom_1')
    res_dict = {reco_bottom_first_button(): True, reco_bottom_second_button(): True}
    return res_dict


def exist_new_daily_given_clue():
    img = ADB.screencap_mat(gray=False, std_size=True)

    color_new_red = Color(123, 1, 34)

    btn_daily = "/ship/meeting_room_in/new_daily_clue"
    btn_given = "/ship/meeting_room_in/new_given_clue"

    rect_up = res.get_pos(btn_daily)
    img_up = imgops.mat_crop(img, Rect(*rect_up))
    img_up = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_new_red, tolerance=5))

    rect_down = res.get_pos(btn_given)
    img_down = imgops.mat_crop(img, Rect(*rect_down))
    img_down = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_new_red, tolerance=5))

    plt.imshow(img_up)
    plt.show()
    plt.imshow(img_down)
    plt.show()

    return {"daily": np.sum(img_up) > 20000, "given": np.sum(img_down) > 20000}


def put_unputted_clue():
    img = ADB.screencap_mat(gray=False, std_size=True)
    result = {}
    delta_pos = res.get_pos('/ship/meeting_room_in/red_point_to_slot_middle')
    for i in range(1, 8):
        dot_path = '/ship/meeting_room_in/clue_slot_red_point/' + str(i)
        dot_pos = res.get_pos(dot_path)
        result[i] = (img[dot_pos[1]][dot_pos[0]] == np.array([1, 104, 255])).all()
        if result[i]:
            center_pos = Pos(dot_pos[0] + delta_pos[0], dot_pos[1] + delta_pos[1])
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), center_pos))
            time.sleep(1)
            navigator.press_std_pos('/ship/meeting_room_in/right_side_bar_first_clue')
            time.sleep(1)
            navigator.press_std_pos("/ship/enter_room_detail")
            time.sleep(1)


def give_out_one_clue():
    # Scene: meeting_room
    navigator.handle_close_button()
    time.sleep(1)
    navigator.press_std_pos("/ship/meeting_room_in/give_out_clue_button")
    time.sleep(2)
    navigator.press_std_pos("/ship/meeting_room_in/left_side_bar_first_clue")
    time.sleep(0.5)
    navigator.press_std_pos("/ship/meeting_room_in/give_out_first_people_button")
    time.sleep(3)
    navigator.press_std_pos("/ship/meeting_room_in/give_out_close_button")
    time.sleep(1)


def get_daily_clue():  # Suppose have "NEW" icon

    take_button_pos = res.get_pos("/ship/meeting_room_in/new_daily_clue_take_button")

    # Scene: meeting_room
    put_unputted_clue()
    new_reco = exist_new_daily_given_clue()
    if not new_reco['daily']:
        return

    navigator.press_std_rect("/ship/meeting_room_in/new_daily_clue")
    time.sleep(1)

    # Scene: daily_take_button
    img_take_scene = ADB.screencap_mat(gray=False, std_size=True)
    if (img_take_scene[take_button_pos[1]][take_button_pos[0]] == np.array([86, 86, 86])).all():
        # NEW, with autotake failed
        give_out_one_clue()
        new_reco = exist_new_daily_given_clue()
        if not new_reco['daily']:
            return
        else:
            navigator.press_std_rect("/ship/meeting_room_in/new_daily_clue")
            time.sleep(1)

    # Auto take succeeded, need to manually take
    # Scene: daily_take_button
    # Try to press
    navigator.press_std_pos("/ship/meeting_room_in/new_daily_clue_take_button")
    time.sleep(2)
    while True:
        # Scene: take_button
        img_take_scene = ADB.screencap_mat(gray=False, std_size=True)
        if (img_take_scene[take_button_pos[1]][take_button_pos[0]] == np.array([86, 86, 86])).all():
            # Successfully taken
            navigator.handle_close_button()
            time.sleep(0.5)
            break
        elif (img_take_scene[take_button_pos[1]][take_button_pos[0]] == np.array([0, 117, 168])).all():
            # Failed to take, try to give
            give_out_one_clue()
            new_reco = exist_new_daily_given_clue()
            if not new_reco['daily']:
                return
            else:
                navigator.press_std_rect("/ship/meeting_room_in/new_daily_clue")
                time.sleep(1)
                navigator.press_std_pos("/ship/meeting_room_in/new_daily_clue_take_button")
    # Scene: meeting_room


def get_given_clue():
    new_reco = exist_new_daily_given_clue()
    if not new_reco['given']:
        return
    navigator.press_std_rect("/ship/meeting_room_in/new_daily_clue")
    time.sleep(1.5)
    navigator.press_std_pos("/ship/meeting_room_in/given_clue_get_all")
    time.sleep(2)
    raise NotImplementedError("TODO: 点完之后会自动返回吗？")
    # TODO: 点完之后会自动返回吗？


def handle_clue(res_dict):
    if '线索搜集' not in res_dict:
        return
    navigator.press_std_rect('/ship/meeting_room')
    time.sleep(1.5)
    navigator.press_std_pos("/ship/enter_room_detail")
    time.sleep(1)
    put_unputted_clue()
    get_daily_clue()
    get_given_clue()


def handle_tired(res_dict):
    if '干员疲劳' not in res_dict:
        return
    # TODO: 最恐怖的……换班。


def main_to_ship():
    navigator.press_std_rect("/main_menu/ship")
    time.sleep(4.5)


def run_ship():
    navigator.back_to_main_menu()
    if main_menu.main_check_ship_remain():
        main_to_ship()
        check_and_press_blue_button()
        res_dict = check_and_press_bottom_button()
        handle_clue(res_dict)
        # TODO: handle_tired(res_dict)
        navigator.back_to_main_menu()


if __name__ == '__main__':
    run_ship()
