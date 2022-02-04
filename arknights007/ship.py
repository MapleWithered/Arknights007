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
    color_blue_when_red_pressed = Color(11, 145, 208)
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
    elif np.sum(img_up_red) > 400000 and np.sum(img_down_blue) > 400000:  # 上红下蓝 未按
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

    return False


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


def check_and_press_blue_bottom_button():
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


def reco_clue_total_number():
    # Scene: before meeting_room
    img = ADB.screencap_mat(std_size=True, gray=False)
    rect_std = Rect(*res.get_pos('/ship/meeting_room_in/clue_total_count'))
    ocr_result = ocr.ocr_rect_single_line(img, rect_std, '0123456789', debug_show=True, bigger_box=0)
    return int(ocr_result.str)


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
        # Todo: ensure!
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
    navigator.press_std_rect("/ship/meeting_room_in/new_given_clue")
    time.sleep(1.5)
    navigator.press_std_pos("/ship/meeting_room_in/given_clue_get_all")
    time.sleep(2)
    navigator.press_std_pos("/ship/enter_room_detail")
    time.sleep(1)
    # TODO: 点完之后会自动返回吗？


def handle_clue():
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
    while not ensure_and_press_summary(press=False):
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
        return True
    elif np.sum(img_up_red) > 400000 and np.sum(img_down_blue) > 400000:  # 上红下蓝 未按
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_blue_p) > 40000:  # 上蓝下空 已按蓝色
        navigator.press_std_rect(path_up)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    elif np.sum(img_up_white) > 1000000 and np.sum(img_up_red_p) > 40000 and np.sum(
            img_down_blue_p) > 400000:  # 上红下蓝 已按红色
        navigator.press_std_rect(path_up)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    elif np.sum(img_up_red_p) > 400000 and np.sum(img_down_white) > 1000000 and np.sum(img_down_blue_p) > 40000:
        # 上红下蓝 已按蓝色
        navigator.press_std_rect(path_down)
        time.sleep(0.7)
        assert check_and_unpress_blue_button()
        return True
    return False


def ensure_and_press_summary(press=True):
    template_shortpath = "/ship/summary.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res.get_pos("/ship/summary")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        if press:
            navigator.press_std_rect("/ship/summary")
            time.sleep(2)
        return True
    else:
        if press:
            raise RuntimeError("未找到按钮")
        else:
            return False


def ensure_summary_scene():
    template_shortpath = "/ship/summary_scene/ensure.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res.get_pos("/ship/summary_scene/ensure")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        return True
    else:
        return False


def summary_find_dormitory():
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    img_gray = imgops.mat_pick_grey(img_gray, 255)
    template_shortpath = '/ship/summary_scene/dormitory_icon.png'
    img_template = res.get_img_gray(template_shortpath)
    template.match_template_best(img_gray, img_template, show_result=True)


def is_dormitory_change_people_scene():
    template_shortpath = "/ship/dormitory/people_btn_pressed.png"
    img_gray = ADB.screencap_mat(gray=True, std_size=True)
    pos_rect = res.get_pos("/ship/dormitory/people_btn")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    img_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, img_template) > 0.9:
        return True
    else:
        return False


def handle_tired():
    # TODO: 最恐怖的……换班。
    dormitory_change_people()
    put_up_new_people()


def main_to_ship():
    navigator.press_std_rect("/main_menu/ship")
    time.sleep(4.5)


def change_people_scene_detect_number_already() -> list[bool]:
    img_gray = ADB.screencap_mat(std_size=True, gray=True)
    img_gray = imgops.mat_pick_grey(img_gray, 255)
    list_exist = [None, False, False, False, False, False]
    for i in range(1, 6):
        temp = res.get_img_gray("/ship/change_scene/" + str(i) + ".png")
        result = template.match_template_best(img_gray, temp)
        if result.val < .1:
            list_exist[i] = True
        else:
            list_exist[i] = False
    return list_exist


def dormitory_change_people(upper_emotion=24, new_people_emotion_lower_or_equal_than=1):
    all_people_happy = False
    for i in range(1, 5):
        assert check_and_unpress_blue_button(), RuntimeError("无法回到基建首页")
        assert ensure_and_press_summary(press=False), RuntimeError("不在基建首页")
        path_zoom_out = res.get_img_path('/common_record/zoom_out.yaml')
        navigator.record_play(path_zoom_out)
        navigator.press_std_pos('/ship/dormitory_' + str(i))
        navigator.press_std_pos('/ship/dormitory/info_btn')
        navigator.press_std_rect('/ship/dormitory/people_btn')
        assert is_dormitory_change_people_scene(), RuntimeError("不在进驻信息界面")

        img_template = res.get_img_gray('/ship/dormitory/delete_people.png')
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_all(img_gray, img_template, None, cv2.TM_CCOEFF_NORMED, 0.95, True)
        for single_res in result:
            pos = (single_res.rect.x1 - 110, single_res.rect.y1 + 85)
            emotion_num_rect = Rect(pos[0], pos[1], pos[0] + 37, pos[1] + 27)
            ocr_result = ocr.ocr_rect_single_line(img_gray, emotion_num_rect, ocr_dict='0123456789', debug_show=True,
                                                  bigger_box=0)
            if int(ocr_result.str) >= upper_emotion:
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), single_res.rect))
        ADB.input_swipe_pos(
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos('/ship/dormitory/right_swipe_1'))),
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos('/ship/dormitory/right_swipe_2'))),
            200)
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_all(img_gray, img_template, None, cv2.TM_CCOEFF_NORMED, 0.95, True)
        for single_res in result:
            pos = (single_res.rect.x1 - 110, single_res.rect.y1 + 85)
            emotion_num_rect = Rect(pos[0], pos[1], pos[0] + 37, pos[1] + 27)
            ocr_result = ocr.ocr_rect_single_line(img_gray, emotion_num_rect, ocr_dict='0123456789', debug_show=True,
                                                  bigger_box=0)
            if int(ocr_result.str) >= upper_emotion:
                ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), single_res.rect))
        ADB.input_swipe_pos(
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos('/ship/dormitory/right_swipe_1'))),
            imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos('/ship/dormitory/right_swipe_2'))),
            200)
        img_template = res.get_img_gray('/ship/dormitory/new_people.png')
        img_gray = ADB.screencap_mat(std_size=True, gray=True)
        result = template.match_template_best(img_gray, img_template, method=cv2.TM_CCOEFF_NORMED)
        if result.val > 0.9:  # 有空位
            ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), result.rect))
            time.sleep(1.5)
            # 换新干员
            # 确认心情排序
            path_sort_emotion = res.get_img_path('/ship/dormitory/sort_emotion.yaml')
            navigator.record_play(path_sort_emotion)
            time.sleep(1)
            reco_result = change_people_scene_detect_number_already()
            min_slot_available = 0
            for j in range(1, 6):
                if reco_result[j] == False:
                    min_slot_available = j
                    break
            assert min_slot_available != 0, "不是说好的有空位的吗（疑惑）"
            for j in range(min_slot_available, 6):
                navigator.press_std_pos("/ship/change_scene/slot_" + str(j))
                time.sleep(0.5)
                img = ADB.screencap_mat(std_size=True)
                std_rect = Rect(*res.get_pos("/ship/change_scene/now_emotion"))
                ocr_result = ocr.ocr_rect_single_line(img, std_rect, '0123456789', True)
                if int(ocr_result.str) > new_people_emotion_lower_or_equal_than:
                    navigator.press_std_pos("/ship/change_scene/slot_" + str(j))
                    all_people_happy = True
                    break
                    # 选好了，去点确定
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
    pass


def put_up_new_people():
    pass  # TODO: now


def run_ship():
    navigator.back_to_main_menu()
    if main_menu.main_check_ship_remain():
        main_to_ship()
        check_and_press_blue_button()
        check_and_press_blue_bottom_button()
        handle_clue()
        handle_tired()
        navigator.back_to_main_menu()


if __name__ == '__main__':
    run_ship()
