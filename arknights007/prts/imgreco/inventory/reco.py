import subprocess
import time
from random import randint

import cv2
import numpy as np
from matplotlib import pyplot as plt

from .. import ocr
from ... import adb
from ...resource.image import get_img_path
from ...resource.inventory_reco import get_net_data
from ... import navigator

# 720p
item_circle_radius = 64
itemreco_box_size = 142
half_box = itemreco_box_size // 2
pixel_x_between_center_720p = 155.71
pixel_y_between_center_720p = 190


def get_circles(gray_img, min_radius=55, max_radius=65):
    circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 100, param1=50,
                               param2=30, minRadius=min_radius, maxRadius=max_radius)
    return circles[0]


def crop_item_middle_img(cv_item_img):
    # radius 60
    img_h, img_w = cv_item_img.shape[:2]
    ox, oy = img_w // 2, img_h // 2
    y1 = int(oy - 40)
    y2 = int(oy + 20)
    x1 = int(ox - 30)
    x2 = int(ox + 30)
    return cv_item_img[y1:y2, x1:x2]


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def get_item_img(cv_screen, dbg_screen, center_x, center_y, ratio):
    itemreco_box_size_ratioed = round(itemreco_box_size * ratio)
    half_box_ratioed = round(half_box * ratio)
    img_h, img_w = cv_screen.shape[:2]
    x, y = int(center_x - half_box_ratioed), int(center_y - half_box_ratioed)
    if x < 0 or x + itemreco_box_size_ratioed > img_w:
        return None
    cv_item_img = cv_screen[y:y + itemreco_box_size_ratioed, x:x + itemreco_box_size_ratioed]

    cv2.rectangle(dbg_screen, (x, y), (x + itemreco_box_size_ratioed, y + itemreco_box_size_ratioed), (255, 0, 0), 2)
    return {'item_img': cv_item_img,
            'item_pos': (center_x, center_y)}


def get_all_item_img_in_screen(cv_screen, debug_show=False):
    h, w = cv_screen.shape[:2]
    ratio = h / 720
    # if h != 720:
    #     cv_screen = cv2.resize(cv_screen, (int(w * ratio), int(h * ratio)))
    gray_screen = cv2.cvtColor(cv_screen, cv2.COLOR_BGR2GRAY)
    dbg_screen = cv_screen.copy()
    # cv2.HoughCircles seems works fine for now
    circles: np.ndarray = get_circles(gray_screen, min_radius=round(55 * ratio), max_radius=round(65 * ratio))
    if circles is None:
        return []

    min_x = 500 * ratio
    min_y = 500 * ratio
    for center_x, center_y, r in circles:
        if center_x < min_x:
            min_x = center_x
        if center_y < min_y:
            min_y = center_y

    x_sum = 0
    y_sum = 0
    r_sum = 0

    pixel_x_between_center = pixel_x_between_center_720p * ratio
    pixel_y_between_center = pixel_y_between_center_720p * ratio

    for center_x, center_y, r in circles:
        x_n = round((center_x - min_x) / pixel_x_between_center)
        y_n = round((center_y - min_y) / pixel_y_between_center)
        x_sum += center_x - x_n * pixel_x_between_center
        y_sum += center_y - y_n * pixel_y_between_center
        r_sum += r

    x_lu_avg = round(x_sum / len(circles))
    y_lu_avg = round(y_sum / len(circles))
    r_avg = round(r_sum / len(circles))

    for i in range(len(circles)):
        circles[i][0] = round(
            x_lu_avg + round((circles[i][0] - x_lu_avg) / pixel_x_between_center) * pixel_x_between_center)
        circles[i][1] = round(
            y_lu_avg + round((circles[i][1] - y_lu_avg) / pixel_y_between_center) * pixel_y_between_center)
        circles[i][2] = half_box * ratio

    res = []

    for center_x, center_y, r in circles:
        cv2.circle(dbg_screen, (round(center_x), round(center_y)), round(half_box * ratio), (0, 0, 255), 2)
        cv2.circle(dbg_screen, (round(center_x), round(center_y)), radius=5, color=(255, 0, 0), thickness=-1)
        item_img = get_item_img(cv_screen, dbg_screen, center_x, center_y, ratio)
        if item_img:
            res.append(item_img)
    if debug_show:
        plt.imshow(dbg_screen)
        plt.show()
    # cv2.imwrite('demo-dbg.png', dbg_screen)
    return res


def get_item_info(cv_img, box_size, net, idx2id, id2idx, idx2name, idx2type):
    cv_img = cv2.resize(cv_img, (box_size, box_size))
    mid_img = crop_item_middle_img(cv_img)
    blob = cv2.dnn.blobFromImage(mid_img)
    net.setInput(blob)
    out = net.forward()

    # Get a class with a highest score.
    out = out.flatten()
    probs = softmax(out)
    classId = np.argmax(out)
    return probs[classId], idx2id[classId], idx2name[classId], idx2type[classId]


def _bumper_cropper(thimg, x_threshold=None, debug_show=False):
    height = thimg.shape[0]
    width = thimg.shape[1]

    if debug_show:
        plt.imshow(thimg)
        plt.show()

    if x_threshold is None:
        x_threshold = int(height * 0.25)
    y_threshold = 16
    mat = np.asarray(thimg)
    right = -1
    for x in range(width - 1, -1, -1):
        col = mat[:, x]
        if np.any(col):
            right = x + 1
            break
    left = right
    emptycnt = 0
    for x in range(right - 1, -1, -1):
        col = mat[:, x]
        if np.any(col):
            left = x
            print(emptycnt) if emptycnt > 0 and debug_show else None
            emptycnt = 0
        else:
            emptycnt += 1
            if emptycnt >= x_threshold:
                break
    top = 0
    for y in range(height):
        row = mat[y, left:right + 1]
        if np.any(row):
            top = y
            break
    bottom = top
    emptycnt = 0
    for y in range(top, height):
        row = mat[y, left:right + 1]
        if np.any(row):
            bottom = y + 1
            emptycnt = 0
        else:
            emptycnt += 1
            if emptycnt >= y_threshold:
                break

    return thimg[int(top - 3):int(bottom + 3), int(left - 3):int(right + 3)]


def get_quantity_ocr(ori_img, debug_show=False):
    img_h, img_w = ori_img.shape[:2]
    l, t, r, b = tuple(map(int, (img_w * 0.2, img_h * 0.69, img_w * 0.82, img_h * 0.87)))

    # to gray
    gray_img = cv2.cvtColor(ori_img, cv2.COLOR_BGR2GRAY)

    # 二值化
    half_img = gray_img[t:b, l:r]
    half_img[half_img < 173] = 0

    # 裁剪数字区
    half_img = _bumper_cropper(half_img, 7)

    res = ocr.ocr_rect_single_line(img_mat=half_img, rect=None, ocr_dict='.0123456789万', debug_show=debug_show,
                                   bigger_box=0)
    res_str = res.str
    val = 0
    if res_str.find('万') != -1:
        res_str = res.str.replace('万', '')
        try:
            val = int(float(res_str) * 10000)
        except Exception:
            val = None
    else:
        try:
            val = int(res_str)
        except Exception:
            val = None
    return val


def get_all_item_details_in_screen(screen=None, debug_show=False):
    net, idx2id, id2idx, idx2name, idx2type = get_net_data()
    # screen = cv2.imread('demo.png')
    if screen is None:
        screen = adb.ADB.screencap_mat(force=True, std_size=False, gray=False)

    item_images = get_all_item_img_in_screen(screen)

    res = []
    for item_img in item_images:
        if item_img['item_pos'][0]-half_box < 0 or item_img['item_pos'][0]+half_box>screen.shape[1]:
            continue
        # prob 识别结果置信度
        # item_id, item_name, item_type 见 Kengxxiao/ArknightsGameData 的解包数据
        # https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/item_table.json
        prob, item_id, item_name, item_type = get_item_info(item_img['item_img'], 137, net, idx2id, id2idx, idx2name,
                                                            idx2type)
        quantity = get_quantity_ocr(item_img['item_img'])
        if quantity is None:
            continue
        if debug_show:
            plt.imshow(item_img['item_img'])
            plt.show()
            print(f"name: {item_name}, quantity: {quantity}, pos: {item_img['item_pos']}, prob: {prob}")
        # name: 中级作战记录, quantity: 8416, pos: (235, 190), prob: 0.9656420946121216
        res.append({'itemId': item_id, 'itemName': item_name, 'itemType': item_type,
                    'quantity': quantity, 'itemPos': item_img['item_pos']})
        # show_img(item_img['item_img'])
    return res


def get_inventory_items_all_information(show_item_name=False, debug_show=False):
    navigator.back_to_main_menu()
    navigator.press_std_rect("/main_menu/inventory")

    time.sleep(1.5)

    # First detection
    screen_items = {item['itemId']: item for item in get_all_item_details_in_screen()}
    items = screen_items
    if debug_show:
        for item_id in screen_items:
            print(f"new item: {items[item_id]}")

    while True:
        navigator.record_play(get_img_path('/common_record/swipe_left_with_break.yaml'), no_delay=True)

        screen_items = {item['itemId']: item for item in get_all_item_details_in_screen()}

        if len(set(screen_items) - set(items)) == 0:
            break

        for item_id in screen_items:
            if item_id not in items:
                items[item_id] = screen_items[item_id]
                if debug_show:
                    print(f"new item: {items[item_id]}")

    if debug_show:
        print(items)

    return {item_id: items[item_id] for item_id in items}
