from collections import namedtuple

from matplotlib import pyplot as plt

import arknights007.adb as adb
from arknights007.adb import ADB

import cv2

from cnstd import CnStd
from cnocr import CnOcr

from PIL import Image

import arknights007.imgreco.imgops as imgops
import arknights007.resource as res
from arknights007.imgreco import template

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])


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


def ocr_all_text_box(img_pil=None, allow_tilt=False, ocr_dict=None, bigger_box_margin=0, str_limit: list[str] = None,
                     box_score_thresh=0.15, model_name="db_resnet18"):
    cn_std = CnStd(rotated_bbox=allow_tilt, model_name=model_name, context='cpu')
    cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    if img_pil is None:
        img_pil = ADB.screencap_pil(force=True)
    img_mat = imgops.pil_to_mat(img_pil)
    box_infos = cn_std.detect(img_pil, box_score_thresh=box_score_thresh)
    result_list: list[OCRSTDSingleResult] = []
    for box_info in box_infos['detected_texts']:
        box_rect_original = Rect(*box_info['box'])
        x1 = box_info['box'][0] - bigger_box_margin
        y1 = box_info['box'][1] - bigger_box_margin
        x2 = box_info['box'][2] + bigger_box_margin
        y2 = box_info['box'][3] + bigger_box_margin
        box_rect_bigger = Rect(x1, y1, x2, y2)
        ocr_result = ocr_rect_single_line(img_mat, box_rect_bigger, ocr_dict=ocr_dict)
        ocrstd_result = OCRSTDSingleResult(str=ocr_result.str, rect=box_rect_original, val=ocr_result.val)
        print(ocr_result.str, ocr_result.val)
        if str_limit is None or ocr_result.str in str_limit:
            result_list.append(ocrstd_result)
    return result_list


def extract_result(target: str, all_result: list[OCRSTDSingleResult]):
    for single_result in all_result:
        if single_result.str == target:
            return single_result
    return None


def ocr_rect_single_line(img_mat, rect: Rect = None, ocr_dict=None, debug_show=False) -> OCRSingleResult:
    if rect is not None:
        img_cropped = imgops.mat_crop(img_mat, rect)
    else:
        img_cropped = img_mat.copy()
    if debug_show:
        plt.imshow(img_cropped)
        plt.show()
    cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    ocr_res = cn_ocr.ocr_for_single_line(img_cropped)
    if debug_show:
        print('ocr result: %s' % str(ocr_res))
    return OCRSingleResult(''.join(ocr_res[0]), ocr_res[1])


def ocr_main_story_episode() -> int:
    path = "/main_story/ocr_episode_id"
    rect = Rect(*imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(path))))
    result = ocr_rect_single_line(ADB.screencap_mat(True), rect, ocr_dict='0123456789')
    return int(result.str)


def ocr_all_stage(stage_map):
    print("! Deprecated.  Use navigator.nav_get_all_stage_tag() instead.")
    img_screen = ADB.screencap_mat()
    img_screen = imgops.mat_bgr2gray(img_screen)
    img_screen = imgops.mat_size_real_to_std(img_screen)

    return ocr_all_text_box(ADB.screencap_pil(), allow_tilt=False, ocr_dict="ABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890",
                            bigger_box_margin=5, str_limit=stage_map, box_score_thresh=0)


def ocr_all_stage_tag_and_std_position(stage_map, debug_show=False, cn_ocr_object=None):
    img_screenshot = ADB.screencap_mat(force=True, std_size=True)
    screen = ADB.screencap_mat(std_size=True, gray=True)
    img_template_1 = res.get_img_gray("/stage_ocr/stage_icon_1.png")
    img_template_2 = res.get_img_gray("/stage_ocr/stage_icon_2.png")
    result: list[RectResult] = []
    result += template.match_template_all(screen, img_template_1)
    result += template.match_template_all(screen, img_template_2)
    ocr_result: list[OCRSTDSingleResult] = []
    ocr_dict = "0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if cn_ocr_object is None:
        cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    else:
        cn_ocr = cn_ocr_object
    for rect_result in result:
        rect_temp = rect_result.rect
        rect_temp = Rect(
            rect_temp.x1 + 47,
            rect_temp.y1 - 7,
            rect_temp.x1 + 220,
            rect_temp.y1 + 45)
        img_cropped = imgops.mat_crop(img_screenshot, rect_temp)
        if debug_show:
            plt.imshow(img_cropped)
            plt.show()
        if img_cropped.shape[1] < 80:
            continue
        try:
            ocr_res = cn_ocr.ocr_for_single_line(img_cropped)
        except RuntimeError:
            print("PyTorch RuntimeError, retry. ")
            ocr_res = cn_ocr.ocr_for_single_line(img_cropped)
        if debug_show:
            print('ocr result: %s' % str(ocr_res))
        single_result = OCRSTDSingleResult(''.join(ocr_res[0]), rect_temp, ocr_res[1])
        if single_result.str in stage_map:
            ocr_result.append(single_result)
        else:
            rect_temp = Rect(
                rect_temp.x1,
                rect_temp.y1,
                rect_temp.x2 - 45,
                rect_temp.y2)
            img_cropped = imgops.mat_crop(img_screenshot, rect_temp)
            if debug_show:
                plt.imshow(img_cropped)
            plt.show()
            ocr_res = cn_ocr.ocr_for_single_line(img_cropped)
            if debug_show:
                print('ocr result: %s' % str(ocr_res))
            single_result = OCRSTDSingleResult(''.join(ocr_res[0]), rect_temp, ocr_res[1])
            if single_result.str in stage_map:
                ocr_result.append(single_result)
    # TODO: auto correction using stage_map
    if debug_show:
        print(ocr_result)
    return ocr_result

