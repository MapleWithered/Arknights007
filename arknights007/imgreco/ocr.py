import arknights007.adb as adb

import cv2

from cnstd import CnStd
from cnocr import CnOcr

from PIL import Image

cn_std = CnStd(rotated_bbox=False)
cn_ocr = CnOcr(cand_alphabet="0123456789终端当前理智编队干员采购中心公开招募角色管理寻访任务基建仓库好友档案/+-")

if __name__ == '__main__':
    device = adb.auto_connect()
    img = device.screencap_cv()
    img = Image.fromarray(img)
    print(img, type(img))
    img.show()
    box_infos = cn_std.detect(img)
    for box_info in box_infos['detected_texts']:
        print(box_info['box'])
        cropped_img = box_info['cropped_img']
        cv2.imshow("", cropped_img)
        ocr_res = cn_ocr.ocr_for_single_line(cropped_img)
        print('ocr result: %s' % str(ocr_res))
        cv2.waitKey(0)


def ocr_all_text(screenshot) -> list:
    ...


def ocr_multi_line(img) -> list[str]:
    ...


def ocr_single_line(img) -> str:
    ...


def ocr_all_text_regional(screenshot, region: list[int]) -> list:
    ...
