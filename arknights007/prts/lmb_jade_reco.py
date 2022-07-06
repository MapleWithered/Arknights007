from collections import namedtuple

from cnocr import CnOcr

from . import navigator as navigator
from . import resource as res
from .adb import ADB
from .imgreco import imgops
from .imgreco import template

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def reco_all():
    navigator.nav_to_public_recruit()
    screen = ADB.screencap_mat(force=True, std_size=True)
    img_template_r1 = res.image.get_img_bgr("/public_recruit/R1.png")
    img_template_r2 = res.image.get_img_bgr("/public_recruit/R2.png")
    img_template_r3 = res.image.get_img_bgr("/public_recruit/R3.png")
    img_template_r4 = res.image.get_img_bgr("/public_recruit/R4.png")
    logo_rect_r1 = template.match_template_best(screen, img_template_r1).rect
    logo_rect_r2 = template.match_template_best(screen, img_template_r2).rect
    logo_rect_r3 = template.match_template_best(screen, img_template_r3).rect
    logo_rect_r4 = template.match_template_best(screen, img_template_r4).rect
    data_rect_l1 = Rect(logo_rect_r4.x2 + 75 + 10, logo_rect_r4.y1, logo_rect_r3.x1 - 28, logo_rect_r4.y1 + 41)
    data_rect_l2 = Rect(logo_rect_r3.x2 + 75 + 10, logo_rect_r3.y1, logo_rect_r2.x1 - 28, logo_rect_r3.y1 + 41)
    data_rect_l4 = Rect(logo_rect_r1.x2 + 75 + 10, logo_rect_r1.y1, ADB.get_resolution().width - 30,
                        logo_rect_r1.y1 + 41)
    ocr_dict = "0123456789"
    cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    data_mat_l1 = imgops.mat_crop(screen, data_rect_l1)
    data_mat_l2 = imgops.mat_crop(screen, data_rect_l2)
    data_mat_l4 = imgops.mat_crop(screen, data_rect_l4)
    num_l1 = int(''.join(cn_ocr.ocr_for_single_line(data_mat_l1)[0]))
    num_l2 = int(''.join(cn_ocr.ocr_for_single_line(data_mat_l2)[0]))
    num_l4 = int(''.join(cn_ocr.ocr_for_single_line(data_mat_l4)[0]))
    return {'lmb': num_l1, 'recruit_ticket': num_l2, 'jade': num_l4}


if __name__ == '__main__':
    print(reco_all())
