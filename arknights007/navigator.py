import os
import time
from collections import namedtuple

from adb import ADB
import cv2
import imgreco.imgops as imgops
import imgreco.template as template
import resource as res

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])


def is_main_menu():
    template_shortpath = "/main_menu/gear.png"
    img = ADB.screencap_mat(True)
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos("/main_menu/gear")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 255)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        return True
    else:
        return False


def is_terminal():
    template_shortpath = "/terminal/terminal_template.png"
    img = ADB.screencap_mat(True)
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos("/terminal/terminal_template")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        return True
    else:
        return False


# If not exist, return False.
# If succeed, return True.
def expand_menu_bar():
    template_shortpath = "/navigate_bar/nav_main.png"
    pos_shortpath = "/navigate_bar/nav_main"
    img = ADB.screencap_mat()
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        return True

    template_shortpath = "/navigate_bar/nav_menu.png"
    pos_shortpath = "/navigate_bar/nav_menu"
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) < 0.9:
        return False
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(0.8)
    return True


def menu_bar_press_main_menu():
    pos_shortpath = "/navigate_bar/nav_main"
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(pos_shortpath)))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(1)


def menu_bar_press_terminal():
    pos_shortpath = "/navigate_bar/nav_terminal"
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(pos_shortpath)))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(1)


def handle_back_button():
    template_shortpath = "/navigate_bar/back_black.png"
    pos_shortpath = "/navigate_bar/back_black"
    img = ADB.screencap_mat()
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    # cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
        return True

    template_shortpath = "/navigate_bar/back_white.png"
    pos_shortpath = "/navigate_bar/back_white"
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    # cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
        return True

    return False


def handle_reward_scene():
    pass


def handle_dialog():
    pass


def handle_unknown_scene():
    pass


def main_menu_press_terminal():
    pos_shortpath = "/main_menu/terminal"
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(pos_shortpath)))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(1)


def handle_close_button():
    # Use template match, find close button, mask needed.
    # https: // gregorkovalcik.github.io / opencv_contrib / tutorial_template_matching.html
    pass


def back_to_main_menu():
    error_counter = 0
    while not is_main_menu():
        if expand_menu_bar():
            menu_bar_press_main_menu()
            continue
        elif handle_back_button():
            continue
        elif handle_reward_scene():
            continue
        elif handle_dialog():
            continue
        elif handle_close_button():
            continue
        elif handle_unknown_scene():
            continue
        else:
            error_counter += 1
            time.sleep(1)
            if error_counter == 60:
                raise RuntimeError("Unhandled scene.")


def back_to_terminal():
    error_counter = 0
    while not is_terminal():
        if is_main_menu():
            main_menu_press_terminal()
        elif expand_menu_bar():
            menu_bar_press_terminal()
            continue
        elif handle_back_button():
            continue
        elif handle_reward_scene():
            continue
        elif handle_dialog():
            continue
        elif handle_close_button():
            continue
        elif handle_unknown_scene():
            continue
        else:
            error_counter += 1
            time.sleep(1)
            if error_counter == 60:
                raise RuntimeError("Unhandled scene.")


def goto_stage(stage: str):
    back_to_terminal()
    pass


if __name__ == '__main__':
    ADB.connect()
    print(back_to_terminal())
