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


def main_to_credit_shop():
    navigator.press_std_rect("/main_menu/shopping_center")
    time.sleep(.7)
    navigator.press_std_rect("/shopping_center/bar/credit_shop")
    time.sleep(1)
    assert is_in_credit_shop()


def is_in_credit_shop():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(255, 104, 1))
    corner_rect = resource.navigator.get_pos("/shopping_center/bar/credit_shop")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 100000:
        return True
    else:
        return False


def get_daily_credit():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(224, 103, 21))
    corner_rect = resource.navigator.get_pos("/shopping_center/credit_shop/daily_credit_btn")
    img_cropped = imgops.mat_crop(img, Rect(*corner_rect))
    img_cropped = imgops.mat_bgr2gray(img_cropped)
    if np.sum(img_cropped) > 250000:
        navigator.press_std_rect("/shopping_center/credit_shop/daily_credit_btn")
        time.sleep(.7)
        navigator.handle_reward_scene()
        return True
    else:
        return False


def reco_credit_remain():
    img = ADB.screencap_mat(gray=False, std_size=True)
    img = imgops.mat_pick_color_rgb(img, Color(255, 255, 255), tolerance=100)
    num_rect = resource.navigator.get_pos("/shopping_center/credit_shop/credit_remain")
    img_cropped = imgops.mat_crop(img, Rect(*num_rect))
    # img_cropped = imgops.mat_bgr2gray(img_cropped)
    ocr_result = ocr.ocr_rect_single_line(img_cropped, ocr_dict='0123456789')
    try:
        return int(ocr_result.str)
    except ValueError:
        return 0


def reco_credict_product_cost(screen, pos):
    rect = Rect(pos.x - 57, pos.y + 207, pos.x + 263, pos.y + 247)
    img = imgops.mat_crop(screen, rect)
    img = imgops.mat_pick_color_rgb(img, Color(255, 255, 255), tolerance=20)
    ocr_result = ocr.ocr_rect_single_line(img, ocr_dict='0123456789')
    try:
        return int(ocr_result.str)
    except ValueError:
        return 999


def reco_credict_sales_discount(screen, pos):
    rect = Rect(pos.x - 77, pos.y - 38, pos.x + 18, pos.y + 12)
    img = imgops.mat_crop(screen, rect)
    img = imgops.mat_pick_color_rgb(img, Color(159, 233, 0), tolerance=30)
    img = img / np.amax(img) * 255
    ocr_result = ocr.ocr_rect_single_line(img, ocr_dict='-5790%')
    res_str = ocr_result.str.replace('-', '').replace('%', '')
    try:
        return int(res_str)
    except ValueError:
        return 50


def reco_credit_products(screen=None, debug_show=False):
    net, idx2id, id2idx, idx2name, idx2type = get_net_data()
    # screen = cv2.imread('demo.png')
    if screen is None:
        screen = ADB.screencap_mat(force=True, std_size=True, gray=False)

    x_base = 102
    y_base = 313
    x_delta = 380
    y_delta = 380
    width = 186
    height = 186

    items = []
    for j in range(2):
        for i in range(5):
            x_now = x_base + i * x_delta
            y_now = y_base + j * y_delta
            # 未被购买的物品
            if np.all(np.logical_and(screen[ y_now + 225, x_now - 65 ] <= np.array([95, 95, 95]), screen[ y_now + 225, x_now - 65 ] >= np.array([81, 81, 81]))):
                if np.all(screen[y_now - 30, x_now - 65] == np.array([0, 137, 93])):
                    sale_ratio = reco_credict_sales_discount(screen, Pos(x_now, y_now))
                else:
                    sale_ratio = 0
                item = {'item_img': screen[y_now:y_now + height, x_now:x_now + width],
                        'pos': Pos(x_now, y_now),
                        'on_sale': sale_ratio,
                        'cost': reco_credict_product_cost(screen, Pos(x_now, y_now))}
                prob, item_id, item_name, item_type = get_item_info(item['item_img'], 137, net, idx2id, id2idx,
                                                                    idx2name,
                                                                    idx2type)
                item['name'] = item_name
                items.append(item)
    return items

def credit_product_key(item, set_urgent, set_normal, set_excluded):
    if item['name'] in set_urgent:
        prior = 3
    elif item['name'] in set_normal:
        prior = 1
    elif item['name'] in set_excluded:
        return 999999
    else:
        prior = 0
    return - (item['on_sale'] * 10000 + prior)


def sort_credit_products(items: list[dict], set_urgent, set_normal, set_excluded):
    return sorted(items, key=lambda x: credit_product_key(x, set_urgent, set_normal, set_excluded))


def run_credit_store():
    path_config = get_config_path('credit_shop.yaml')
    with open(path_config, 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
    set_urgent = set(config['items']['urgent'])
    set_normal = set(config['items']['normal'])
    set_excluded = set(config['items']['excluded'])

    navigator.back_to_main_menu()
    main_to_credit_shop()
    get_daily_credit()
    items = reco_credit_products()
    items = sort_credit_products(items, set_urgent, set_normal, set_excluded)

    if not items:
        return

    for item in items:
        if item['name'] not in set_excluded:
            if reco_credit_remain() >= item['cost']:
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), item['pos']))
                time.sleep(.5)
                navigator.press_std_pos("/shopping_center/credit_shop/confirm_order")
                time.sleep(1)
                navigator.handle_reward_scene()
                assert is_in_credit_shop()
            else:
                break
        else:
            if reco_credit_remain() >= 300:
                ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), item['pos']))
                time.sleep(.5)
                navigator.press_std_pos("/shopping_center/credit_shop/confirm_order")
                time.sleep(1)
                navigator.handle_reward_scene()
                assert is_in_credit_shop()
            else:
                break

    navigator.back_to_main_menu()
