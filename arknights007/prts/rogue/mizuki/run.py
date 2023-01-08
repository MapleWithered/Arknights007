import os
import re
import time
from collections import namedtuple

import cv2
from cnocr import CnOcr
from ruamel import yaml
import numpy as np
import difflib

from ... import battle, navigator
from ...resource import navigator as res_nav
from ...resource import image as res_img
from ...resource import yaml as res_yaml
from ... import config
from ...adb import ADB
from ...imgreco import imgops
from ...imgreco import ocr
from ...imgreco import template
from ...resource.image import get_img_path, get_img_gray, get_img_bgr
from ...navigator import is_terminal, back_to_terminal, press_std_pos

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])

battle_stages = [
    '蓄水池',
    '虫群横行',
    '射手部队',
    '共生',
    '无声呼号',
    '海神的信者',
    '病症',
    '征兆',
    '回溯',
    '除暴安良',
    '原始部落',
    '精酿杀手',
    '据险固守',
    '巢穴',
    '漩涡',
    '大君遗脉',
    '地下天途',
    '火之骄子',
    '领地意识',
    '海窟沙暴',
    '溟痕乐园',
    '狩猎场',
    '崇敬深海',
    '机械之灾',
    '教徒居所',
    '失控',
    '吹笛人的号召',
    '好梦在何方',
    '育生池',
    '蔓延',
    '水火相容',
    '深度认知',
]

battle_stages_ocr_dict = ''.join(set(''.join(battle_stages)))

boss_stages = [
    '永恒安息',
    '分离与统一',
    '纠错',
    '永恒愤怒',
    '异体同心',
    '订正',
    '认知即重担',
    '“命运的宠儿”',
    '大群所向',
    '荒地群猎',
    '寒灾之咒',
    '险路勿近',
]

stage2skill = {
    '蓄水池': {'shuichen': 1, 'bandian': 1, 'shiduhuade': 1},
    '虫群横行': {'shuichen': 1, 'bandian': 1, 'shiduhuade': 1},
    '射手部队': {'shuichen': 1, 'bandian': 1, 'shiduhuade': 1},
    '共生': {'shuichen': 1, 'bandian': 1, 'shiduhuade': 1},
}


def is_main_menu():
    img_pattern = get_img_bgr("/rogue/mizuki/mizuki_main_menu_assert.png")
    img = ADB.screencap_mat(std_size=True, gray=False)
    navigator.press_pattern_color('/rogue/mizuki/exit_rogue.png')
    result = template.match_template_best(img, img_pattern)
    # print(result.val)
    return result.val < 0.1


def filter_contour(contour):
    width = np.max(contour[:, :, 0]) - np.min(contour[:, :, 0])
    height = np.max(contour[:, :, 1]) - np.min(contour[:, :, 1])
    block_area = width * height
    contour_area = cv2.contourArea(contour)
    similar = contour_area / block_area
    # print(np.min(contour[:, :, 0]), np.max(contour[:, :, 0]), np.min(contour[:, :, 1]), np.max(contour[:, :, 1]),
    #       height, block_area, contour_area, similar)
    if similar > 0.6 and block_area > 7000:
        return True
    return False


def find_and_press_node(first_node=False):
    img = ADB.screencap_mat(std_size=True, gray=False)
    # to HSV
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_battle = imgops.mat_bgr2gray(imgops.mat_pick_color_hsv(img_hsv, Color(253, 52, 88), Color(2, 7, 6)))
    img_event = imgops.mat_bgr2gray(imgops.mat_pick_color_hsv(img_hsv, Color(181, 88, 78), Color(2, 7, 6)))
    img_emergency = imgops.mat_bgr2gray(imgops.mat_pick_color_hsv(img_hsv, Color(333, 52, 70), Color(2, 4, 6)))
    img_shop = imgops.mat_bgr2gray(imgops.mat_pick_color_hsv(img_hsv, Color(168, 83, 61), Color(2, 7, 6)))

    kernel = np.ones((20, 20), dtype=np.uint8)

    dilate = img_battle  # np.uint8(cv2.dilate(img_battle, kernel, 1))  # 膨胀。 1:迭代次数，也就是执行几次膨胀操作
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 获取轮廓及层级关系
    pass_rects = []
    for contour in contours:
        if filter_contour(contour):
            if first_node or np.min(contour[:, :, 0]) > 800:
                pass_rects.append(Rect(np.min(contour[:, :, 0]),
                                       np.min(contour[:, :, 1]),
                                       np.max(contour[:, :, 0]),
                                       np.max(contour[:, :, 1])))

    if pass_rects:
        pass_rects.sort(key=lambda x: -x.x1)
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), pass_rects[0]))  # 有节点可点
        time.sleep(1.8)
        return "BATTLE"

    dilate = img_event  # np.uint8(cv2.dilate(img_event, kernel, 1))  # 膨胀。 1:迭代次数，也就是执行几次膨胀操作
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 获取轮廓及层级关系
    pass_rects = []
    for contour in contours:
        if filter_contour(contour):
            if first_node or np.min(contour[:, :, 0]) > 800:
                pass_rects.append(Rect(np.min(contour[:, :, 0]),
                                       np.min(contour[:, :, 1]),
                                       np.max(contour[:, :, 0]),
                                       np.max(contour[:, :, 1])))

    if pass_rects:
        pass_rects.sort(key=lambda x: -x.x1)
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), pass_rects[0]))  # 有节点可点
        time.sleep(1.8)
        return "EVENT"

    dilate = img_emergency  # np.uint8(cv2.dilate(img_emergency, kernel, 1))  # 膨胀。 1:迭代次数，也就是执行几次膨胀操作
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 获取轮廓及层级关系
    pass_rects = []
    for contour in contours:
        if filter_contour(contour):
            if first_node or np.min(contour[:, :, 0]) > 800:
                pass_rects.append(Rect(np.min(contour[:, :, 0]),
                                       np.min(contour[:, :, 1]),
                                       np.max(contour[:, :, 0]),
                                       np.max(contour[:, :, 1])))

    if pass_rects:
        pass_rects.sort(key=lambda x: -x.x1)
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), pass_rects[0]))  # 有节点可点
        time.sleep(1.8)
        return "EMERGENCY"

    dilate = img_shop  # np.uint8(cv2.dilate(img_shop, kernel, 1))  # 膨胀。 1:迭代次数，也就是执行几次膨胀操作
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 获取轮廓及层级关系
    pass_rects = []
    for contour in contours:
        if filter_contour(contour):
            if first_node or np.min(contour[:, :, 0]) > 800:
                pass_rects.append(Rect(np.min(contour[:, :, 0]),
                                       np.min(contour[:, :, 1]),
                                       np.max(contour[:, :, 0]),
                                       np.max(contour[:, :, 1])))

    if pass_rects:
        pass_rects.sort(key=lambda x: -x.x1)
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), pass_rects[0]))  # 有节点可点
        time.sleep(1.8)
        return "SHOP"

    else:
        return None


def reco_battle_name():
    img = ADB.screencap_mat(std_size=True, gray=False)
    img = imgops.mat_pick_color_rgb(img, Color(255, 255, 255), 128)
    res = (ocr.ocr_rect_single_line(img, Rect(1410, 265, 1860, 345), ocr_dict=battle_stages_ocr_dict))
    res = difflib.get_close_matches(res.str, battle_stages)
    if res:
        # print(str(res[0]))
        return str(res[0])
    else:
        return ''


def choose_operator():
    img = ADB.screencap_mat(std_size=True, gray=True)
    img = imgops.mat_pick_grey(img, 255, 1)
    img_pattern = get_img_gray('/rogue/operator_empty_plus.png')
    img_cropped = imgops.mat_crop(img, Rect(0, 0, 605, 345))
    result = template.match_template_best(img_cropped, img_pattern)
    if result.val < 0.1:  # 第一位干员为空位
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1367, 60)))
        time.sleep(1.8)
        navigator.press_pattern_color('/rogue/mizuki/operator/juji/shuichen.png')
        navigator.press_pattern_color('/rogue/mizuki/operator/zhongzhuang/bandian.png')
        navigator.press_pattern_color('/rogue/mizuki/operator/shushi/shiduhuade.png')
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1700, 1015)))
        time.sleep(1)


def in_battle():
    img = ADB.screencap_mat(std_size=True, gray=True, force=True)
    img = imgops.mat_pick_grey(img, 255, 2)
    img_cropped = imgops.mat_crop(img, Rect(1740, 740, 1800, 800))
    img_pattern = get_img_gray('/rogue/in_battle_cost_icon.png')
    result = template.match_template_best(img_cropped, img_pattern)
    if result.val < 0.1:
        return True
    else:
        return False


def handle_battle(battle_name: str):
    Pos_2x_speed = imgops.from_std_pos(ADB.get_resolution(), Pos(1640, 85))
    Pos_Op_L1 = imgops.from_std_pos(ADB.get_resolution(), Pos(1475, 985))
    Pos_Op_L2 = imgops.from_std_pos(ADB.get_resolution(), Pos(1655, 985))
    Pos_Op_L3 = imgops.from_std_pos(ADB.get_resolution(), Pos(1835, 985))
    if battle_name == '共生':
        # 初始10费
        time.sleep(4)
        # 14费
        ADB.input_press_pos(Pos_2x_speed)
        time.sleep(3)
        # 20费
        ADB.input_swipe_pos(Pos_Op_L1,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1260, 740)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1260, 740)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(800, 765)), 200)
        # 1费
        time.sleep(16)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1245, 585)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1245, 585)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(800, 620)), 200)
        # 1费
        time.sleep(8.5)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1079, 345)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1079, 345)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1105, 745)), 200)
    elif battle_name == '射手部队':
        # 初始10费
        time.sleep(4)
        # 14费
        ADB.input_press_pos(Pos_2x_speed)
        time.sleep(3)
        # 20费
        ADB.input_swipe_pos(Pos_Op_L1,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1535, 435)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1535, 435)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1610, 720)), 200)
        # 1费
        time.sleep(16)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1380, 435)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1380, 435)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1783, 388)), 200)
        # 1费
        time.sleep(8.2)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1217, 334)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1217, 334)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(848, 362)), 200)
    elif battle_name == '虫群横行':
        # 初始10费
        time.sleep(4)
        # 14费
        ADB.input_press_pos(Pos_2x_speed)
        time.sleep(1)
        # 20费
        ADB.input_swipe_pos(Pos_Op_L1,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1401, 573)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1401, 573)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1476, 955)), 200)
        # 1费
        time.sleep(16)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1232, 453)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1232, 453)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1653, 400)), 200)
        # 1费
        time.sleep(8.2)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(943, 472)), 200)
        time.sleep(.2)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(943, 472)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(943, 175)), 200)
    elif battle_name == '蓄水池':
        # 初始10费
        time.sleep(4)
        # 14费
        ADB.input_press_pos(Pos_2x_speed)
        time.sleep(1)
        # 20费
        ADB.input_swipe_pos(Pos_Op_L1,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1432, 672)), 500)
        time.sleep(.5)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1432, 672)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1000, 672)), 500)
        # 1费
        time.sleep(16)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1412, 500)), 500)
        time.sleep(.5)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1412, 500)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(997, 547)), 500)
        # 1费
        time.sleep(8.5)
        ADB.input_swipe_pos(Pos_Op_L3,
                            imgops.from_std_pos(ADB.get_resolution(), Pos(1390, 385)), 500)
        time.sleep(.5)
        ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1390, 385)),
                            imgops.from_std_pos(ADB.get_resolution(), Pos(935, 440)), 500)
    return


def run():
    assert is_main_menu()
    if navigator.press_pattern_color('/rogue/mizuki/abandon_exploration.png'):
        time.sleep(4)
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1267, 741)))  # 确认放弃
        time.sleep(2)
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1847, 549)))
        time.sleep(2)
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 976)))
        while not is_main_menu():
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 976)))
            time.sleep(3)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1754, 888)))  # 开始探索
    time.sleep(3)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1113, 510)))  # 以人为本
    time.sleep(1)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1113, 879)))  # 确认以人为本
    time.sleep(2)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(745, 495)))  # 稳扎稳打
    time.sleep(1)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(745, 879)))  # 确认稳扎稳打
    time.sleep(2)

    # Handle 上次层数奖励
    img = ADB.screencap_mat(std_size=True, gray=True)
    if img[296, 1350] != 255:
        pass  # Handle needed

    # 选初始干员 重装 术师 狙击
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1392, 352)))  # 狙击
    time.sleep(2)
    error_cnt = 0
    while not navigator.press_pattern_color('/rogue/mizuki/operator/juji/shuichen.png'):  # 水陈
        ADB.input_swipe(1755, 521, 1170, 521, 200, 300)
        time.sleep(1)
        error_cnt += 1
        if error_cnt > 15:
            raise RuntimeError("Cannot find 水陈")
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1750, 1010)))  # 确认
    time.sleep(1)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1870, 50)))  # skip
    time.sleep(.5)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1865, 55)))  # 关闭立绘
    time.sleep(2)

    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(970, 345)))  # 术师
    time.sleep(2)
    error_cnt = 0
    while not navigator.press_pattern_color('/rogue/mizuki/operator/shushi/shiduhuade.png'):  # 史图华德
        ADB.input_swipe(1755, 521, 1170, 521, 200, 300)
        time.sleep(1)
        error_cnt += 1
        if error_cnt > 15:
            raise RuntimeError("Cannot find 史图华德")
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1750, 1010)))  # 确认
    time.sleep(1)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1870, 50)))  # skip
    time.sleep(.5)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1865, 55)))  # 关闭立绘
    time.sleep(2)

    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(520, 345)))  # 重装
    time.sleep(2)
    error_cnt = 0
    while not navigator.press_pattern_color('/rogue/mizuki/operator/zhongzhuang/bandian.png'):  # 斑点
        ADB.input_swipe(1755, 521, 1170, 521, 200, 300)
        time.sleep(1)
        error_cnt += 1
        if error_cnt > 15:
            raise RuntimeError("Cannot find 斑点")
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1750, 1010)))  # 确认
    time.sleep(1)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1870, 50)))  # skip
    time.sleep(.5)
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1865, 55)))  # 关闭立绘
    time.sleep(2)

    assert navigator.press_pattern_color('/rogue/mizuki/explore_ocean.png')  # 探索海洋
    time.sleep(8)

    first_node = True

    while True:
        # 选关，打关
        stage_category = find_and_press_node(first_node)
        # print(stage_category)
        if stage_category is not None:
            first_node = False
        elif first_node is False:
            navigator.press_pattern_color('/rogue/mizuki/exit_rogue.png')
            time.sleep(1)
            break

        if stage_category == "BATTLE" or stage_category == "EMERGENCY":
            battle_name = reco_battle_name()
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1695, 775)))  # 出发前往
            time.sleep(1)
            choose_operator()
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1783, 1004)))  # 开始行动
            while not in_battle():
                time.sleep(0.1)
            handle_battle(battle_name)
            time.sleep(3)
            while in_battle():
                time.sleep(1)
            time.sleep(15)
            if navigator.press_pattern_bw('/rogue/mizuki/connection_lost.png', 253):
                time.sleep(5)
                break

            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1783, 1004)))  # 关闭结算画面
            time.sleep(3)
            img = ADB.screencap_mat()
            while (
                    navigator.press_pattern_color('/rogue/mizuki/originum_jewel.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/dice_chance.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/take_away_blue.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/take_away_cyan.png', screen=img)
            ):
                img = ADB.screencap_mat()
            while not navigator.press_pattern_color('/rogue/mizuki/red_tick_small.png', tolerance=0.2):
                navigator.press_pattern_bw('/rogue/mizuki/abandon.png', 128, 0.1, True)
                time.sleep(3)
            time.sleep(2)

        if stage_category == "EVENT":
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1695, 775)))  # 出发前往
            time.sleep(10)
            img = ADB.screencap_mat()
            if (
                    navigator.press_pattern_color('/rogue/mizuki/event_escape.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/event_close_terminal.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/event_take_armour.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/event_take_something.png', screen=img)
                    or navigator.press_pattern_color('/rogue/mizuki/event_dice_chance.png', screen=img)
            ):
                navigator.press_pattern_bw('/rogue/mizuki/event_confirm_tick.png', 253)
                navigator.press_pattern_color('/rogue/mizuki/event_sure.png')
                time.sleep(5)
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 985)))  # 关闭事件
            elif (
                    navigator.press_pattern_color('/rogue/mizuki/event_throw_dice_random.png')
            ):
                navigator.press_pattern_bw('/rogue/mizuki/event_confirm_tick.png', 253)
                navigator.press_pattern_color('/rogue/mizuki/event_sure.png')
                time.sleep(5)
                while not navigator.press_pattern_color('/rogue/mizuki/hope_icon.png'):
                    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 985)))  # 关闭事件
                    time.sleep(3)
            else:
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1783, 503)))  # 中间选项
                time.sleep(1)
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1783, 503)))  # 中间选项

                # TODO: Handle Recruitment

                while not navigator.press_pattern_color('/rogue/mizuki/hope_icon.png'):
                    if navigator.press_pattern_color('/rogue/mizuki/recruitment_abandon.png'):
                        time.sleep(1)
                        navigator.press_pattern_color('/rogue/mizuki/recruitment_abandon_confirm.png')
                        time.sleep(2)
                    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 985)))  # 关闭事件
                    time.sleep(3)
            time.sleep(5)
            if not navigator.press_pattern_color('/rogue/mizuki/hope_icon.png'):
                break

        if stage_category == "SHOP":
            ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1695, 775)))  # 出发前往
            time.sleep(4)
            if navigator.press_pattern_color('/rogue/mizuki/shop_investment_system.png'):
                time.sleep(1)
                if navigator.press_pattern_color('/rogue/mizuki/shop_investment_entrypoint.png'):
                    time.sleep(1)
                    while navigator.press_pattern_color('/rogue/mizuki/shop_investment_confirm.png'):
                        pass
                    navigator.press_pattern_color('/rogue/mizuki/shop_investment_abandon.png')
                    time.sleep(1)
                navigator.press_pattern_color('/rogue/mizuki/shop_investment_abandon.png')
                time.sleep(1)
            navigator.press_pattern_color('/rogue/mizuki/shop_leave.png')
            time.sleep(0.5)
            navigator.press_pattern_color('/rogue/mizuki/shop_confirm_leave.png')
            time.sleep(5)
            navigator.press_pattern_color('/rogue/mizuki/dice_confirm.png')
            time.sleep(5)
            navigator.press_pattern_color('/rogue/mizuki/exit_rogue.png')
            time.sleep(2)
            # navigator.press_pattern_color('/rogue/mizuki/abandon_exploration.png')
            # time.sleep(2)
            # ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1267, 741)))  # 确认放弃
            # time.sleep(2)
            break

    # ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(1847, 549)))
    # time.sleep(2)
    # ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 976)))

    while not is_main_menu():
        ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 976)))
        time.sleep(3)
