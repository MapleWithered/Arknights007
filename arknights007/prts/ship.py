import os
import time
import typing
from collections import namedtuple

import cv2
import numpy as np

from .imgreco.inventory.reco import get_inventory_items_all_information
from . import main_menu
from . import navigator
from .resource import navigator as res_nav
from .resource import image as res_img
from .config import yaml as cfg_yaml
from . import ship_skill
from .adb import ADB
from .imgreco import imgops, inventory
from .imgreco import ocr
from .imgreco import template

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
    color_blue_when_red_pressed = Color(11, 145, 208)
    color_blue = Color(44, 166, 215)
    color_red = Color(204, 78, 86)
    color_red_when_blue_pressed = Color(186, 47, 56)

    path_up = "/ship/notification_button_1"
    path_down = "/ship/notification_button_2"

    rect_up = res_nav.get_pos(path_up)
    img_up = imgops.mat_crop(img, Rect(*rect_up))
    img_up_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_white, tolerance=10))
    img_up_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue, tolerance=10))
    img_up_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red, tolerance=10))
    img_up_blue_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue_when_red_pressed, tolerance=14))
    img_up_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red_when_blue_pressed, tolerance=10))

    rect_down = res_nav.get_pos(path_down)
    img_down = imgops.mat_crop(img, Rect(*rect_down))
    img_down_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_white, tolerance=10))
    img_down_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_blue, tolerance=10))
    img_down_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red, tolerance=10))
    img_down_blue_p = imgops.mat_bgr2gray(
        imgops.mat_pick_color_rgb(img_down, color_blue_when_red_pressed, tolerance=14))
    img_down_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red_when_blue_pressed, tolerance=10))

    # plt.imshow(img_up)
    # plt.show()

    if np.sum(img_up_blue) > 400000:  # ???????????? ??????
        navigator.press_std_rect(path_up)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_red) > 400000 and np.sum(img_down_blue) > 400000:  # ???????????? ??????
        navigator.press_std_rect(path_down)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_blue_p) > 40000:  # ???????????? ????????????
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_red_p) > 40000 and np.sum(
            img_down_blue_p) > 400000:  # ???????????? ????????????
        navigator.press_std_rect(path_down)
        time.sleep(0.5)
        assert check_and_press_blue_button()
        return True
    elif np.sum(img_up_red_p) > 400000 and np.sum(img_down_white) > 1000000 and np.sum(img_down_blue_p) > 40000:
        return True

    return False


def reco_bottom_first_button():
    img = ADB.screencap_mat(gray=False, std_size=True)
    rect_1 = res_nav.get_pos("/ship/bottom_1")
    img_1 = imgops.mat_crop(img, Rect(*rect_1))
    ocr_1 = ocr.ocr_rect_single_line(img, rect=Rect(*rect_1), ocr_dict='???????????????????????????????????????????????????', debug_show=False,
                                     bigger_box=5)
    return ocr_1.str


def reco_bottom_second_button():
    img = ADB.screencap_mat(gray=False, std_size=True)
    rect_2 = res_nav.get_pos("/ship/bottom_2")
    img_2 = imgops.mat_crop(img, Rect(*rect_2))
    ocr_2 = ocr.ocr_rect_single_line(img, rect=Rect(*rect_2), ocr_dict='???????????????????????????????????????????????????', debug_show=False,
                                     bigger_box=5)
    return ocr_2.str


def check_and_press_blue_bottom_button():
    while reco_bottom_first_button() in ['?????????', '????????????', '????????????']:
        navigator.press_std_rect('/ship/bottom_1')
    res_dict = {reco_bottom_first_button(): True, reco_bottom_second_button(): True}
    return res_dict


def exist_new_daily_given_clue():
    img = ADB.screencap_mat(gray=False, std_size=True)

    color_new_red = Color(123, 1, 34)

    btn_daily = "/ship/meeting_room_in/new_daily_clue"
    btn_given = "/ship/meeting_room_in/new_given_clue"

    rect_up = res_nav.get_pos(btn_daily)
    img_up = imgops.mat_crop(img, Rect(*rect_up))
    img_up = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_new_red, tolerance=5))

    rect_down = res_nav.get_pos(btn_given)
    img_down = imgops.mat_crop(img, Rect(*rect_down))
    img_down = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_new_red, tolerance=5))

    # plt.imshow(img_up)
    # plt.show()
    # plt.imshow(img_down)
    # plt.show()

    return {"daily": np.sum(img_up) > 20000, "given": np.sum(img_down) > 20000}


def put_unputted_clue():
    img = ADB.screencap_mat(gray=False, std_size=True)
    result = {}
    delta_pos = res_nav.get_pos('/ship/meeting_room_in/red_point_to_slot_middle')
    for i in range(1, 8):
        dot_path = '/ship/meeting_room_in/clue_slot_red_point/' + str(i)
        dot_pos = res_nav.get_pos(dot_path)
        result[i] = (img[dot_pos[1]][dot_pos[0]] == np.array([1, 104, 255])).all()
        if result[i]:
            center_pos = Pos(dot_pos[0] + delta_pos[0], dot_pos[1] + delta_pos[1])
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), center_pos))
            time.sleep(1)
            navigator.press_std_pos('/ship/meeting_room_in/right_side_bar_first_clue')
            time.sleep(1)
            navigator.press_std_pos("/ship/enter_room_detail")
            time.sleep(1)


def reco_clue_total_number():
    # Scene: before meeting_room
    img = ADB.screencap_mat(std_size=True, gray=False)
    rect_std = Rect(*res_nav.get_pos('/ship/meeting_room_in/clue_total_count'))
    ocr_result = ocr.ocr_rect_single_line(img, rect_std, '0123456789', debug_show=False, bigger_box=0)
    try:
        return int(ocr_result.str)
    except:
        raise RuntimeError("????????????????????? ???????????????????????????")


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

    take_button_pos = res_nav.get_pos("/ship/meeting_room_in/new_daily_clue_take_button")

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
        # ???NEW???????????????????????????
        give_out_one_clue()
        new_reco = exist_new_daily_given_clue()
        if not new_reco['daily']:
            return
        else:
            navigator.press_std_rect("/ship/meeting_room_in/new_daily_clue")
            time.sleep(1)
    else:
        # ???NEW??????????????????????????? ???????????????????????????????????????9????????????????????????
        navigator.press_std_pos("/ship/meeting_room_in/new_daily_clue_take_button")
        time.sleep(2)  # ????????????????????????????????????????????????
        return True


def get_given_clue():
    new_reco = exist_new_daily_given_clue()
    if not new_reco['given']:
        return
    navigator.press_std_rect("/ship/meeting_room_in/new_given_clue")
    time.sleep(1.5)
    navigator.press_std_pos("/ship/meeting_room_in/given_clue_get_all")
    time.sleep(2)
    navigator.press_std_pos("/ship/enter_room_detail")
    time.sleep(1)


def handle_clue():
    check_and_unpress_blue_button()
    path_zoom_out = res_img.get_img_path('/common_record/zoom_out.yaml')
    navigator.record_play(path_zoom_out)
    time.sleep(1)
    navigator.press_std_rect('/ship/meeting_room')
    time.sleep(1.5)
    try:
        clue_total = reco_clue_total_number()
    except RuntimeError:  # zoom out????????????????????????????????????
        navigator.press_std_rect('/ship/meeting_room')
        time.sleep(1.5)
        clue_total = reco_clue_total_number()
    navigator.press_std_pos("/ship/enter_room_detail")
    time.sleep(1)
    while clue_total >= 9:
        give_out_one_clue()
        clue_total -= 1
    put_unputted_clue()
    get_daily_clue()
    get_given_clue()
    put_unputted_clue()
    navigator.press_std_rect("/ship/meeting_room_in/unlock_clue")
    time.sleep(2)
    put_unputted_clue()
    while not ensure_and_press_summary(press=False):  # TODO: bugfix forever looped
        if navigator.is_main_menu():
            main_to_ship()
        elif check_and_unpress_blue_button():
            continue
        else:
            navigator.press_std_rect("/navigate_bar/back_black")
        time.sleep(3)


def check_and_unpress_blue_button():
    if ensure_and_press_summary(press=False):
        return True
    img = ADB.screencap_mat(gray=False, std_size=True)

    color_white = Color(245, 245, 245)
    color_blue_when_red_pressed = Color(11, 145, 208)
    color_blue = Color(44, 166, 215)
    color_red = Color(204, 78, 86)
    color_red_when_blue_pressed = Color(186, 47, 56)

    path_up = "/ship/notification_button_1"
    path_down = "/ship/notification_button_2"

    rect_up = res_nav.get_pos(path_up)
    img_up = imgops.mat_crop(img, Rect(*rect_up))
    img_up_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_white, tolerance=10))
    img_up_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue, tolerance=10))
    img_up_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red, tolerance=10))
    img_up_blue_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_blue_when_red_pressed, tolerance=14))
    img_up_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_up, color_red_when_blue_pressed, tolerance=10))

    rect_down = res_nav.get_pos(path_down)
    img_down = imgops.mat_crop(img, Rect(*rect_down))
    img_down_white = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_white, tolerance=10))
    img_down_blue = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_blue, tolerance=10))
    img_down_red = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red, tolerance=10))
    img_down_blue_p = imgops.mat_bgr2gray(
        imgops.mat_pick_color_rgb(img_down, color_blue_when_red_pressed, tolerance=14))
    img_down_red_p = imgops.mat_bgr2gray(imgops.mat_pick_color_rgb(img_down, color_red_when_blue_pressed, tolerance=10))

    # plt.imshow(img_up)
    # plt.show()

    if np.sum(img_up_blue) > 400000:  # ???????????? ??????
        return True
    elif np.sum(img_up_red) > 400000 and np.sum(img_down_blue) > 400000:  # ???????????? ??????
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_blue_p) > 40000:  # ???????????? ????????????
        navigator.press_std_rect(path_up)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_red_p) > 40000 and np.sum(
            img_down_blue_p) > 400000:  # ???????????? ????????????
        navigator.press_std_rect(path_up)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    elif np.sum(img_up_red_p) > 400000 and np.sum(img_down_white) > 1000000 and np.sum(img_down_blue_p) > 40000:
        # ???????????? ????????????
        navigator.press_std_rect(path_down)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    return False


def ensure_and_press_summary(press=True):
    template_shortpath = "/ship/summary.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res_nav.get_pos("/ship/summary")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res_img.get_img_path(template_shortpath)):
        cv2.imwrite(res_img.get_img_path(template_shortpath), cropped)
    gear_template = res_img.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        if press:
            navigator.press_std_rect("/ship/summary")
            time.sleep(2)
        return True
    else:
        if press:
            raise RuntimeError("???????????????")
        else:
            return False


def ensure_summary_scene():
    template_shortpath = "/ship/summary_scene/ensure.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res_nav.get_pos("/ship/summary_scene/ensure")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res_img.get_img_path(template_shortpath)):
        cv2.imwrite(res_img.get_img_path(template_shortpath), cropped)
    gear_template = res_img.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        return True
    else:
        return False


def summary_find_dormitory():
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    img_gray = imgops.mat_pick_grey(img_gray, 255)
    template_shortpath = '/ship/summary_scene/dormitory_icon.png'
    img_template = res_img.get_img_gray(template_shortpath)
    template.match_template_best(img_gray, img_template, show_result=False)


def is_dormitory_change_people_scene():
    template_shortpath = "/ship/dormitory/people_btn_pressed.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res_nav.get_pos("/ship/dormitory/people_btn")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res_img.get_img_path(template_shortpath)):
        cv2.imwrite(res_img.get_img_path(template_shortpath), cropped)
    img_template = res_img.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, img_template) > 0.9:
        return True
    else:
        return False


def handle_tired():
    dormitory_change_people()
    # ????????????
    put_up_new_people()

    while not ensure_and_press_summary(press=False):
        navigator.press_std_rect("/navigate_bar/back_black")
        time.sleep(3)


def main_to_ship():
    navigator.press_std_rect("/main_menu/ship")
    time.sleep(4.5)


def change_people_scene_detect_number_already() -> list[bool]:
    img_gray = ADB.screencap_mat(std_size=True, gray=True)
    img_gray = imgops.mat_pick_grey(img_gray, 255)
    list_exist = [None, False, False, False, False, False]
    for i in range(1, 6):
        temp = res_img.get_img_gray("/ship/change_scene/" + str(i) + ".png")
        result = template.match_template_best(img_gray, temp)
        if result.val < .1:
            list_exist[i] = True
        else:
            list_exist[i] = False
    return list_exist


def dormitory_change_people(upper_emotion=24, new_people_emotion_lower_or_equal_than=12):
    all_people_happy = False
    for i in range(1, 5):
        assert check_and_unpress_blue_button(), RuntimeError("????????????????????????")
        assert ensure_and_press_summary(press=False), RuntimeError("??????????????????")
        path_zoom_out = res_img.get_img_path('/common_record/zoom_out.yaml')
        navigator.record_play(path_zoom_out)
        navigator.press_std_pos('/ship/dormitory_' + str(i))
        navigator.press_std_pos('/ship/dormitory/info_btn')
        navigator.press_std_rect('/ship/dormitory/people_btn')
        assert is_dormitory_change_people_scene(), RuntimeError("????????????????????????")
        # ????????????????????????
        img_template = res_img.get_img_gray('/ship/dormitory/delete_people.png')
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_all(img_gray, img_template, None, cv2.TM_CCOEFF_NORMED, 0.95,
                                             show_result=False)
        for single_res in result:
            pos = (single_res.rect.x1 - 110, single_res.rect.y1 + 85)
            emotion_num_rect = Rect(pos[0], pos[1], pos[0] + 37, pos[1] + 27)
            ocr_result = ocr.ocr_rect_single_line(img_gray, emotion_num_rect, ocr_dict='0123456789', debug_show=False,
                                                  bigger_box=0)
            if int(ocr_result.str) >= upper_emotion:
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), single_res.rect))
                time.sleep(0.5)
        # ??????
        ADB.input_swipe_pos(
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/dormitory/right_swipe_1'))),
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/dormitory/right_swipe_2'))),
            200)
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_all(img_gray, img_template, None, cv2.TM_CCOEFF_NORMED, 0.95,
                                             show_result=False)
        for single_res in result:
            pos = (single_res.rect.x1 - 110, single_res.rect.y1 + 85)
            emotion_num_rect = Rect(pos[0], pos[1], pos[0] + 37, pos[1] + 27)
            ocr_result = ocr.ocr_rect_single_line(img_gray, emotion_num_rect, ocr_dict='0123456789', debug_show=False,
                                                  bigger_box=0)
            if int(ocr_result.str) >= upper_emotion:
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), single_res.rect))
                time.sleep(0.5)
        # ???????????? ?????????
        img_template = res_img.get_img_gray('/ship/dormitory/new_people.png')
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_best(img_gray, img_template, method=cv2.TM_CCOEFF_NORMED)
        if result.val < 0.9:
            # ?????????????????????????????????????????????
            ADB.input_swipe_pos(
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/dormitory/right_swipe_2'))),
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/dormitory/right_swipe_1'))),
                200)
            img_gray = ADB.screencap_mat(std_size=True, gray=True)
            result = template.match_template_best(img_gray, img_template, method=cv2.TM_CCOEFF_NORMED)
        if result.val >= 0.9:  # ?????????
            ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), result.rect))
            time.sleep(1.5)
            # ??????????????????
            path_sort_emotion = res_img.get_img_path('/ship/dormitory/sort_emotion.yaml')
            navigator.record_play(path_sort_emotion)
            time.sleep(1)
            reco_result = change_people_scene_detect_number_already()
            min_slot_available = 0
            for j in range(1, 6):
                if reco_result[j] == False:
                    min_slot_available = j
                    break
            assert min_slot_available != 0, "??????????????????????????????????????????"
            # ????????????
            for j in range(min_slot_available, 6):
                navigator.press_std_pos("/ship/change_scene/slot_" + str(j))
                time.sleep(0.5)
                img = ADB.screencap_mat(std_size=True)
                std_rect = Rect(*res_nav.get_pos("/ship/change_scene/now_emotion"))
                ocr_result = ocr.ocr_rect_single_line(img, std_rect, '0123456789', debug_show=False)
                if int(ocr_result.str) > new_people_emotion_lower_or_equal_than:
                    navigator.press_std_pos("/ship/change_scene/slot_" + str(j))
                    all_people_happy = True
                    break
                    # ????????????????????????
            navigator.press_std_pos("/ship/change_scene/yes_btn")
            time.sleep(1)
            navigator.press_std_pos("/ship/change_scene/yes_btn")
            time.sleep(2)
        navigator.press_std_rect("/navigate_bar/back_black")
        time.sleep(1)
        if all_people_happy:
            break
        else:
            continue


def dormitory_fill_people():
    ensure_and_press_summary()
    anchor_x = res_nav.get_pos("/ship/summary_scene/plus/x_anchor")
    anchor_dy = res_nav.get_pos("/ship/summary_scene/plus/dy_to_anchor")
    ocr_rect_size = res_nav.get_pos("/ship/summary_scene/plus/ocr_rect_two_char_size")
    swipe_counter = 0
    while swipe_counter <= 7:
        img = ADB.screencap_mat(std_size=True, gray=False)
        img_template = res_img.get_img_bgr("/ship/summary_scene/plus.png")
        tm_result = template.match_template_all(img, img_template, None, cv2.TM_CCOEFF_NORMED, 0.7, show_result=False,
                                                group_rectangle=1)
        task = ''
        task_plus_rect = None
        for sg_result in tm_result:
            ocr_rect = Rect(anchor_x, sg_result.rect.y1 + anchor_dy, anchor_x + ocr_rect_size[0],
                            sg_result.rect.y1 + anchor_dy + ocr_rect_size[1])
            ocr_result = ocr.ocr_rect_single_line(img, ocr_rect, "??????????????????????????????????????????????????????", debug_show=False)
            if ocr_result.str in ['??????']:
                task = "dorm"
                task_plus_rect = sg_result.rect
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), ocr_rect))
                time.sleep(0.5)
                break
        if task == '':  # ????????????????????????
            ADB.input_swipe_pos(
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/summary_scene/right_swipe_1'))),
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/summary_scene/right_swipe_2'))),
                500)
            time.sleep(3)
            swipe_counter += 1
            continue
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), task_plus_rect))
        # ????????????????????????
        time.sleep(1)

        while not ensure_summary_scene():
            navigator.press_std_pos("/ship/change_scene/yes_btn")
            time.sleep(1.5)


def reco_room_number():
    img = ADB.screencap_mat(std_size=True, gray=False)
    img = imgops.mat_pick_color_rgb(img, Color(100, 176, 210), 6)
    img_gray = imgops.mat_bgr2gray(img)
    room_list = ["B004", "B005", "B101", "B102", "B103", "B104", "B105", "B201", "B202", "B203", "B204", "B205", "B301",
                 "B302", "B303", "B304", "B305", "B404"]
    for room in room_list:
        pos = res_nav.get_pos("/ship/summary_scene/room_matrix/" + room)
        if img_gray[pos[1]][pos[0]]:
            return room
        else:
            continue


def room_number_to_category(room_number: typing.Optional[str] = None) -> int:
    if room_number is None:
        room_number = reco_room_number()
    room_category_dict: dict[str, int] = cfg_yaml.load_yaml("ship_manufactory_room.yaml")
    if room_number not in room_category_dict:
        return 0
    else:
        return room_category_dict[room_number]


def put_up_new_people():
    ensure_and_press_summary()
    anchor_x = res_nav.get_pos("/ship/summary_scene/plus/x_anchor")
    anchor_dy = res_nav.get_pos("/ship/summary_scene/plus/dy_to_anchor")
    ocr_rect_size = res_nav.get_pos("/ship/summary_scene/plus/ocr_rect_two_char_size")
    swipe_counter = 0
    while swipe_counter <= 7:
        img = ADB.screencap_mat(std_size=True, gray=False)
        img_template = res_img.get_img_bgr("/ship/summary_scene/plus.png")
        tm_result = template.match_template_all(img, img_template, None, cv2.TM_CCOEFF_NORMED, 0.7, show_result=False,
                                                group_rectangle=1)
        task = ''
        task_plus_rect = None
        for sg_result in tm_result:
            ocr_rect = Rect(anchor_x, sg_result.rect.y1 + anchor_dy, anchor_x + ocr_rect_size[0],
                            sg_result.rect.y1 + anchor_dy + ocr_rect_size[1])
            ocr_result = ocr.ocr_rect_single_line(img, ocr_rect, "??????????????????????????????????????????????????????", debug_show=False)
            if ocr_result.str in ['??????', '??????', '??????', '??????', '??????', '??????']:
                task = ['ctrl', 'meet', 'tra', 'man', 'pow', 'hire'][
                    ['??????', '??????', '??????', '??????', '??????', '??????'].index(ocr_result.str)]
                task_plus_rect = sg_result.rect
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), ocr_rect))
                time.sleep(0.5)
                break
        if task == '':  # ????????????????????????
            ADB.input_swipe_pos(
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/summary_scene/right_swipe_1'))),
                imgops.from_std_pos(ADB.get_resolution(), Pos(*res_nav.get_pos('/ship/summary_scene/right_swipe_2'))),
                500)
            time.sleep(3)
            swipe_counter += 1
            continue
        if task == 'man':  # ????????? ???????????????
            man_category = room_number_to_category()
        else:
            man_category = 0
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), task_plus_rect))
        time.sleep(1.5)
        ship_skill.choose_skill(task, man_category)
        while not ensure_summary_scene():
            navigator.press_std_pos("/ship/change_scene/yes_btn")
            time.sleep(1.5)


def handle_drone():
    drone_config: dict[str, str] = cfg_yaml.load_yaml("drone_config.yaml")

    path_handle_drone = ''

    if drone_config['drone_mode'] == 'auto':
        navigator.back_to_main_menu()
        my_inventory = get_inventory_items_all_information()
        gold_count = my_inventory.get('3003', {}).get('quantity', 0)
        if gold_count < drone_config['drone_auto_gold_threshold']:
            operation = drone_config['drone_auto_operation_when_few_gold']
        else:
            operation = drone_config['drone_auto_operation_when_much_gold']
        navigator.back_to_main_menu()
        main_to_ship()
        path_handle_drone = res_img.get_img_path('/common_record/' + operation + '.yaml')
    elif drone_config['drone_mode'] == 'manual':
        path_handle_drone = res_img.get_img_path('/common_record/' + drone_config['drone_manual_operation'] + '.yaml')

    check_and_unpress_blue_button()
    assert ensure_and_press_summary(press=False), RuntimeError("??????????????????")
    path_zoom_out = res_img.get_img_path('/common_record/zoom_out.yaml')
    navigator.record_play(path_zoom_out)

    if not os.path.exists(path_handle_drone):
        print("???????????????????????????????????????")
        navigator.record_new(path_handle_drone, False)
    else:
        navigator.record_play(path_handle_drone)
    time.sleep(3)

    while not ensure_and_press_summary(press=False):  # TODO: bugfix forever looped
        if navigator.is_main_menu():
            main_to_ship()
        elif check_and_unpress_blue_button():
            continue
        else:
            navigator.press_std_rect("/navigate_bar/back_black")
        time.sleep(3)


def run_ship(force=False):
    navigator.back_to_main_menu()
    if main_menu.main_check_ship_remain() or force:
        main_to_ship()
        time.sleep(9)  # ??????????????????????????????????????????
        check_and_press_blue_button()
        check_and_press_blue_bottom_button()
        time.sleep(4)  # ???????????????????????????
        handle_clue()
        handle_tired()
        check_and_press_blue_button()
        check_and_press_blue_bottom_button()
        time.sleep(4)  # ???????????????????????????
        handle_drone()
        navigator.back_to_main_menu()


if __name__ == '__main__':
    while True:
        try:
            run_ship(True)
        except Exception as e:
            navigator.back_to_main_menu()
            run_ship(True)
        time.sleep(900)
    # TODO: Feat. ???????????????????????????????????????????????????
