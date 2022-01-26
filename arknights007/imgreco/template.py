import cv2
import numpy as np

from . import imgops


def match_template(screenshot, template):
    ...


def compare_mat(img1, img2):
    temp1 = np.asarray(img1)
    temp2 = np.asarray(img2)
    if not img1.shape == img2.shape:
        temp1, temp2 = imgops.uniform_size(img1, img2)
    result = cv2.matchTemplate(temp1, temp2, cv2.TM_CCOEFF_NORMED)[0, 0]
    return result
