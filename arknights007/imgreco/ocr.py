from collections import namedtuple

import arknights007.adb as adb
from arknights007.adb import ADB

import cv2

from cnstd import CnStd
from cnocr import CnOcr

from PIL import Image

import arknights007.imgreco.imgops as imgops
import arknights007.resource as res

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])


def debug_main():
    cn_std = CnStd(rotated_bbox=False)
    cn_ocr = CnOcr(cand_alphabet="0123456789终端当前理智编队干员采购中心公开招募角色管理寻访任务基建仓库好友档案/+-")
    device = adb.auto_connect()
    img = device.screencap_cv()
    img = Image.fromarray(img)
    # print(img, type(img))
    img.show()
    box_infos = cn_std.detect(img)
    for box_info in box_infos['detected_texts']:
        # print(box_info['box'])
        cropped_img = box_info['cropped_img']
        cv2.imshow("", cropped_img)
        ocr_res = cn_ocr.ocr_for_single_line(cropped_img)
        # print('ocr result: %s' % str(ocr_res))
        cv2.waitKey(0)


def ocr_rect_single_line(img, rect: Rect = None, ocr_dict=None) -> OCRSingleResult:
    if rect is not None:
        img_cropped = imgops.mat_crop(img, rect)
    else:
        img_cropped = img.copy()
    cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    ocr_res = cn_ocr.ocr_for_single_line(img_cropped)
    # print('ocr result: %s' % str(ocr_res))
    return OCRSingleResult(''.join(ocr_res[0]), ocr_res[1])


def ocr_main_story_episode() -> int:
    path = "/main_story/ocr_episode_id"
    rect = Rect(*imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(path))))
    result = ocr_rect_single_line(ADB.screencap_mat(True), rect, ocr_dict='0123456789')
    return int(result.str)

