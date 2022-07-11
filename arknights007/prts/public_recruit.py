import functools
import json
import os
import time
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt
from bitarray import bitarray
from ruamel import yaml
import itertools

from .config import get_config_path
from .imgreco.inventory.reco import get_item_info, get_quantity_ocr
from .navigator import is_main_menu
from . import resource
from .adb import ADB
from .imgreco import imgops
from .imgreco import ocr
from .imgreco.inventory import reco as inventory_reco
from . import navigator
from .resource.game_data_json import get_game_data_dict
from .resource.inventory_reco import get_net_data

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def main_to_pub_recruit():
    navigator.back_to_main_menu()
    navigator.press_std_rect("/main_menu/public_recruit")
    time.sleep(.7)
    assert is_in_pub_recruit()


def is_in_pub_recruit():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(242, 152, 0), tolerance=8)
    rect = resource.navigator.get_pos("/public_recruit/flag")
    img_cropped = imgops.mat_crop(img, Rect(*rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 100000:
        return True
    else:
        return False


def reco_pub_recruit_refresh_ticket():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(255, 255, 255), tolerance=100)
    num_rect = resource.navigator.get_pos("/public_recruit/refresh_remain_num")
    img_cropped = imgops.mat_crop(img, Rect(*num_rect))
    # img_cropped = imgops.mat_bgr2gray(img_cropped)
    ocr_result = ocr.ocr_rect_single_line(img_cropped, ocr_dict='0123')
    try:
        return int(ocr_result.str)
    except ValueError:
        return 3


def reco_empty_slots_handle_finish_slots():
    assert is_in_pub_recruit()

    screen = ADB.screencap_mat(gray=False, std_size=True)

    x_base = [55, 1005]
    y_base = [525, 940]
    x_delta = 95
    y_delta = 25
    width = 30
    height = 30

    empty_slots = []

    for j in range(2):
        for i in range(2):
            img_cropped = imgops.mat_crop(screen,
                                          Rect(x_base[i] + x_delta,
                                               y_base[j] + y_delta,
                                               x_base[i] + x_delta + width,
                                               y_base[j] + y_delta + height))
            bgr = np.array([np.sum(img_cropped[:, :, 0]),
                            np.sum(img_cropped[:, :, 1]),
                            np.sum(img_cropped[:, :, 2])])
            bgr = bgr / np.amax(bgr)

            if bgr[2] < 0.1:
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(),
                                                        Pos(x_base[i] + x_delta, y_base[j] + y_delta)))
                time.sleep(1.5)
                navigator.press_std_pos("/public_recruit/buttons/skip")
                time.sleep(5)
                navigator.press_std_pos("/public_recruit/buttons/skip", sleep=False)
                time.sleep(0.3)
                empty_slots.append(j * 2 + i)
                continue
            if 100000 < np.sum(img_cropped) < 190000:
                continue
            else:
                empty_slots.append(j * 2 + i)
    return empty_slots


def is_in_labels_menu():
    screen = ADB.screencap_mat(gray=False, std_size=True)
    img_cropped = imgops.mat_crop(screen, Rect(*resource.navigator.get_pos("/public_recruit/labels_menu_yes_rect")))
    bgr = np.array([np.sum(img_cropped[:, :, 0]),
                    np.sum(img_cropped[:, :, 1]),
                    np.sum(img_cropped[:, :, 2])])
    bgr = bgr / np.amax(bgr)
    if bgr[2] < 0.05:
        return True
    else:
        return False


def reco_labels(debug_show=False):
    x_base = [563, 814, 1064]
    y_base = [541, 648]
    width = 216
    height = 70

    color_avail = Color(49, 49, 49)
    color_empty = Color(179, 179, 179)
    color_chosen = Color(0, 152, 220)

    screen = ADB.screencap_mat(force=True, gray=False, std_size=True)

    assert is_in_labels_menu()

    labels = []

    for j in range(2):
        for i in range(3):
            label = {}
            label_rect = Rect(x_base[i], y_base[j], x_base[i] + width, y_base[j] + height)
            label_cropped = imgops.mat_crop(screen, label_rect)

            label_cropped_color_empty = imgops.mat_pick_color_rgb(label_cropped, color_empty, tolerance=5)
            label_cropped_color_empty = imgops.mat_bgr2gray(label_cropped_color_empty)
            if np.sum(label_cropped_color_empty) > 70000:  # 这个slot里没有标签
                continue

            # 有标签，四种状态：普通（黑），普通选中（蓝），高级（黑黄），高级选中（黄）
            bgr = np.array([np.sum(label_cropped[:, :, 0]),
                            np.sum(label_cropped[:, :, 1]),
                            np.sum(label_cropped[:, :, 2])])
            bgr = bgr / np.amax(bgr)

            if bgr[0] < 0.9:  # 黄色标签
                label['yellow'] = True
                if bgr[0] < 0.15:
                    label['chosen'] = True
                else:
                    label['chosen'] = False
            else:
                label['yellow'] = False
                label['chosen'] = (bgr[2] < 0.2)

            # OCR
            ocr_result = ocr.ocr_rect_single_line(label_cropped,
                                                  ocr_dict='高级资深干员新手支援机械近卫狙击重装医疗辅助术师特种先锋战远程控场爆发治费用回复输出生存群攻防护减速削弱快活位移召唤',
                                                  bigger_box=-10)
            if ocr_result.str == '':
                raise RuntimeError("OCR识别标签错误")
            label['text'] = ocr_result.str
            if debug_show:
                print(label)

            label['rect'] = label_rect

            labels.append(label)

    return labels


@functools.lru_cache()
def gen_char_matrix():
    config_path = get_config_path('public_recruit.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.RoundTripLoader)

    char_data = get_game_data_dict('character_table.json')

    tags = set()
    tags2char = {}
    name2rarity = {}

    profession2tag = {'PIONEER': '先锋干员',
                      'WARRIOR': '近卫干员',
                      'SNIPER': '狙击干员',
                      'TANK': '重装干员',
                      'MEDIC': '医疗干员',
                      'SUPPORT': '辅助干员',
                      'CASTER': '术师干员',
                      'SPECIAL': '特种干员'}

    # O(n)
    name2idx = {}
    idx2name = []
    for char_name in config['pool']:
        idx2name.append(char_name)
        name2idx[char_name] = len(idx2name) - 1
    idx2id = [None] * len(idx2name)
    id2idx = {}
    idx2tags = [set()] * len(idx2name)
    for char_id in char_data:
        if char_data[char_id]['name'] in name2idx:
            idx2id[name2idx[char_data[char_id]['name']]] = char_id
            id2idx[char_id] = name2idx[char_data[char_id]['name']]
            idx2tags[name2idx[char_data[char_id]['name']]] = set(char_data[char_id]['tagList'])
            if char_data[char_id]['position'] == 'MELEE':
                idx2tags[name2idx[char_data[char_id]['name']]].add('近战位')
            else:
                idx2tags[name2idx[char_data[char_id]['name']]].add('远程位')
            if char_data[char_id]['rarity'] == 5:
                idx2tags[name2idx[char_data[char_id]['name']]].add('高级资深干员')
            elif char_data[char_id]['rarity'] == 4:
                idx2tags[name2idx[char_data[char_id]['name']]].add('资深干员')
            elif char_data[char_id]['rarity'] == 0:
                idx2tags[name2idx[char_data[char_id]['name']]].add('支援机械')
            idx2tags[name2idx[char_data[char_id]['name']]].add(
                profession2tag[char_data[char_id]['profession']])
            tags = tags | idx2tags[name2idx[char_data[char_id]['name']]]
            for tag in idx2tags[name2idx[char_data[char_id]['name']]]:
                tags2char[tuple([tag])] = tags2char.get(tuple([tag]), set()) | set([char_data[char_id]['name']])
            name2rarity[char_data[char_id]['name']] = char_data[char_id]['rarity'] + 1

    return tags2char, name2rarity


def gen_matrix_with_labels(labels):
    tags2char, name2rarity = gen_char_matrix()
    tags2char_new = {}
    for tag in labels:
        name = tag['text']
        tags2char_new[tuple([name])] = tags2char[tuple([name])]
    for tag1, tag2 in itertools.combinations(labels, 2):
        name1 = tag1['text']
        name2 = tag2['text']
        temp = tags2char[tuple([name1])] & tags2char[tuple([name2])]
        if temp:
            tags2char_new[tuple(sorted([name1, name2]))] = temp
    for tag1, tag2, tag3 in itertools.combinations(labels, 3):
        name1 = tag1['text']
        name2 = tag2['text']
        name3 = tag3['text']
        temp = tags2char[tuple([name1])] & \
               tags2char[tuple([name2])] & \
               tags2char[tuple([name3])]
        if temp:
            tags2char_new[tuple(sorted([name1, name2, name3]))] = temp
    for key, value in tags2char_new.items():
        if '高级资深干员' not in key:
            tags2char_new[key] -= tags2char[tuple(['高级资深干员'])]
    for key in list(tags2char_new):
        if len(tags2char_new[key]) == 0:
            del tags2char_new[key]
    tags2lowest_rarity = {}
    max_rarity = 0
    max_rarity_labels = []
    robot_label = None
    for key, value in tags2char_new.items():
        if '高级资深干员' in key:
            tags2lowest_rarity[key] = 6
        else:
            lowest_rarity = 5
            for name in value:
                if name2rarity[name] < lowest_rarity:
                    lowest_rarity = name2rarity[name]
            tags2lowest_rarity[key] = lowest_rarity
        if tags2lowest_rarity[key] > max_rarity:
            max_rarity = tags2lowest_rarity[key]
            max_rarity_labels = []
            for label in labels:
                if label['text'] in key:
                    max_rarity_labels.append(label)
        if '支援机械' in key:
            for label in labels:
                if label['text'] == '支援机械':
                    robot_label=label
    return tags2char, tags2lowest_rarity, max_rarity, max_rarity_labels, robot_label


def reco_ticket_remain():
    screen = ADB.screencap_mat(force=True, std_size=True, gray=False)
    bumper_x = 1900
    bumper_y = 41

    screen_gray = imgops.mat_pick_color_rgb(screen, Color(98, 98, 98))
    screen_darkgray = imgops.mat_pick_color_rgb(screen, Color(49, 49, 49))
    screen_white = imgops.mat_pick_color_rgb(screen, Color(255, 255, 255), tolerance=100)

    bumper_count = 0
    while bumper_count < 5:
        bumper_x -= 1
        if np.any(screen_gray[bumper_y, bumper_x] != np.array([0, 0, 0])):
            bumper_count += 1
        else:
            bumper_count = 0

    while np.all(screen_darkgray[bumper_y, bumper_x] == np.array([0, 0, 0])):
        bumper_x += 1

    box_x1 = bumper_x
    box_y1 = 37

    while np.any(screen_darkgray[bumper_y, bumper_x] != np.array([0, 0, 0])):
        bumper_x += 1

    box_x2 = bumper_x
    box_y2 = 80

    ocr_res = ocr.ocr_rect_single_line(screen, Rect(box_x1, box_y1, box_x2, box_y2), ocr_dict='0123456789')
    try:
        return int(ocr_res.str)
    except ValueError:
        return 0


def press_slot(slot_id):
    x_base = [26, 974]
    y_base = [273, 690]
    x_delta = 272
    y_delta = 26
    width = 16
    height = 38

    empty_slots = []
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(),
                                              Rect(x_base[slot_id % 2] + x_delta,
                                                   y_base[slot_id // 2] + y_delta,
                                                   x_base[slot_id % 2] + x_delta + width,
                                                   y_base[slot_id // 2] + y_delta + height)))
    time.sleep(0.5)


def use_label(labels, hour, minute):
    for _ in range(hour-1):
        navigator.press_std_pos("/public_recruit/buttons/hour_up", sleep=False)
    for _ in range(minute):
        navigator.press_std_pos("/public_recruit/buttons/minute_up", sleep=False)
    if not reco_ticket_remain():
        navigator.press_std_pos("/public_recruit/buttons/no")
    for label in labels:
        if not label['chosen']:
            ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), label['rect']))
            time.sleep(0.1)
    navigator.press_std_pos("/public_recruit/buttons/yes")


def refresh_labels():
    navigator.press_std_pos("/public_recruit/buttons/refresh")
    time.sleep(0.3)
    navigator.press_std_pos("/public_recruit/buttons/refresh_confirm")
    time.sleep(0.5)


def run_public_recruit():
    config_path = get_config_path('public_recruit.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.RoundTripLoader)

    navigator.back_to_main_menu()
    main_to_pub_recruit()

    empty_slots = reco_empty_slots_handle_finish_slots()

    while True:
        if not empty_slots:
            navigator.back_to_main_menu()
            return
        if not reco_ticket_remain() and not reco_pub_recruit_refresh_ticket():
            navigator.back_to_main_menu()
            return

        press_slot(empty_slots[0])

        while True:
            labels = reco_labels()
            tags2char, tags2lowest_rarity, max_rarity, max_rarity_labels, robot_label = gen_matrix_with_labels(labels)
            if (max_rarity >= 4) or (robot_label is not None) or (not reco_pub_recruit_refresh_ticket()):
                break
            else:
                refresh_labels()

        if max_rarity >= 5:     # 有五六星保底组合
            print(f"公招有{max_rarity}星保底组合！")
            print(f"Slot: {empty_slots[0]}")
            for tags in tags2char:
                if tags2lowest_rarity[tags] >= 5:
                    print(f"{tags} ({tags2lowest_rarity[tags]}★) : {tags2char[tags]}")
            navigator.press_std_pos("/public_recruit/buttons/no")
            empty_slots = empty_slots[1:]
            continue

        if robot_label is not None:
            if config['1or4'] in [1, '1', 'one'] or max_rarity <= 3:
                use_label([robot_label], 3, 5)
                print("上次公招获得了支援机械词条！")
                empty_slots = empty_slots[1:]
                continue

        if max_rarity >= 4:
            use_label(max_rarity_labels, 9, 0)
            print("上次公招获得了四星词条！")
            empty_slots = empty_slots[1:]
            continue

        if config['strategy'] in ['fast', 'Fast']:
            use_label([], 7, 4)
        else:
            navigator.press_std_pos("/public_recruit/buttons/no")
        empty_slots = empty_slots[1:]
        continue

