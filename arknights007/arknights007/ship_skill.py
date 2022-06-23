import os
import time
import typing
from collections import namedtuple

import numpy as np
from cnocr import CnOcr
from matplotlib import pyplot as plt

from .adb import ADB
import cv2
import arknights007.imgreco.imgops as imgops
import arknights007.imgreco.template as template
import arknights007.imgreco.ocr as ocr
import arknights007.resource as res
import arknights007.navigator as navigator
import arknights007.main_menu as main_menu
import arknights007.ship as ship

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])

SkillSingleResult = namedtuple("SkillSingleResult", ["rect", "name", "val", "icon_index"])
SkillRect = namedtuple("SkillRect", ['rect', 'side', 'people_id'])


def download_skill_icon():
    # s = requests.Session()

    # r = s.get("https://prts.wiki/w/%E5%90%8E%E5%8B%A4%E6%8A%80%E8%83%BD%E4%B8%80%E8%A7%88")
    # assert r.status_code == 200

    # from bs4 import BeautifulSoup

    # soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')

    # img_all = soup.find_all('img', class_='lazyload')
    # img_bskill = []
    # for img in img_all:
    #     if 'Bskill' in img.attrs['data-src'] and '.png' in img.attrs['data-src']:
    #         img_bskill.append("https://prts.wiki" + img.attrs['data-src'])

    # for i in img_bskill:
    #     r = s.get(i)
    #     assert r.status_code == 200
    #     with open("./download/720p" + i.split('/')[-1].replace('%26', '&'), "wb") as f_dl:
    #         f_dl.write(r.content)

    print("完成")
    pass


def gen_rect_matrix(img, bigger_rect=1) -> list[SkillRect]:
    anchor_delta = res.get_pos("/ship/change_scene/skill_matrix/anchor_delta")

    bumper_start_x = res.get_pos("/ship/change_scene/skill_matrix/bumper_start_x")
    bumper_y = res.get_pos("/ship/change_scene/skill_matrix/bumper_y")

    bumper = bumper_start_x

    img_gray = imgops.mat_bgr2gray(img)
    img_gray = imgops.mat_pick_grey(img_gray, 51, 0) + imgops.mat_pick_grey(img_gray, 64, 0)

    while img_gray[bumper_y][bumper] == 51 or img_gray[bumper_y][bumper] == 64:
        bumper += 1
    while img_gray[bumper_y][bumper] != 51 and img_gray[bumper_y][bumper] != 64:
        bumper += 1

    pos_anchor = [bumper + anchor_delta[0], bumper_y + anchor_delta[1]]

    dx_small = res.get_pos("/ship/change_scene/skill_matrix/dx_small")
    dx = res.get_pos("/ship/change_scene/skill_matrix/dx")
    dy = res.get_pos("/ship/change_scene/skill_matrix/dy")
    size = res.get_pos("/ship/change_scene/skill_matrix/size")
    rect_list = []
    people_id = 0
    while pos_anchor[0] + size + size + dx_small + bigger_rect < img.shape[1]:
        rect_list.append(SkillRect(Rect(pos_anchor[0] - bigger_rect,
                                        pos_anchor[1] - bigger_rect,
                                        pos_anchor[0] + size + 2 * bigger_rect,
                                        pos_anchor[1] + size + 2 * bigger_rect), 0, people_id))
        rect_list.append(SkillRect(Rect(pos_anchor[0] + dx_small - bigger_rect,
                                        pos_anchor[1] - bigger_rect,
                                        pos_anchor[0] + dx_small + size + 2 * bigger_rect,
                                        pos_anchor[1] + size + 2 * bigger_rect), 1, people_id))
        people_id += 1
        rect_list.append(SkillRect(Rect(pos_anchor[0] - bigger_rect,
                                        pos_anchor[1] + dy - bigger_rect,
                                        pos_anchor[0] + size + 2 * bigger_rect,
                                        pos_anchor[1] + dy + size + 2 * bigger_rect), 0, people_id))
        rect_list.append(SkillRect(Rect(pos_anchor[0] + dx_small - bigger_rect,
                                        pos_anchor[1] + dy - bigger_rect,
                                        pos_anchor[0] + dx_small + size + 2 * bigger_rect,
                                        pos_anchor[1] + dy + size + 2 * bigger_rect), 1, people_id))
        people_id += 1
        pos_anchor[0] += dx
    return rect_list


def read_all_skill_icon_resource():
    skill_list = []
    icon_path = "resources/game_data/ship_skill/icon"
    mask_path = "resources/game_data/ship_skill/mask"
    for path, dir_list, file_list in os.walk("resources/game_data/ship_skill/icon"):
        for file_name in file_list:
            img_icon = cv2.imread(os.path.join(icon_path, file_name), cv2.IMREAD_UNCHANGED)
            img_alpha = (img_icon[:, :, 3] / 255.0)
            img_icon = (img_icon[:, :, :3] * np.stack((img_alpha,) * 3, axis=-1)).astype(np.uint8)
            img_mask = cv2.imread(os.path.join(mask_path, file_name), cv2.IMREAD_COLOR)
            skill_list.append([file_name.replace('.png', ''), img_icon, img_mask])
    return skill_list


def reco_matrix(img_gray, skillrect_list, skill_list, score_above_than=0.8):
    reco_result = []
    for rect in skillrect_list:
        img_cropped = imgops.mat_crop(img_gray, rect.rect)
        val_list = []
        reco_result_rect_list = []
        for skill in skill_list:
            match_result = template.match_masked_template_best(img_cropped, skill[1], skill[2],
                                                               method=cv2.TM_CCOEFF_NORMED)
            val_list.append(match_result.val)
            reco_result_rect_list.append(match_result.rect)
        max_val = max(val_list)
        max_val_skill_index = val_list.index(max_val)
        corresponding_rect = reco_result_rect_list[max_val_skill_index]
        precise_rect = SkillRect(Rect(rect.rect.x1 + corresponding_rect.x1,
                                      rect.rect.y1 + corresponding_rect.y1,
                                      rect.rect.x1 + corresponding_rect.x2,
                                      rect.rect.y1 + corresponding_rect.y2), rect.side, rect.people_id)
        if max_val > score_above_than:
            reco_result.append(
                SkillSingleResult(precise_rect, skill_list[max_val_skill_index][0], max_val, max_val_skill_index))
    return reco_result


def num_people_already():
    reco_result = ship.change_people_scene_detect_number_already()
    for j in range(5, 0, -1):
        if reco_result[j]:
            return j
    else:
        return 0


SinglePeople = namedtuple('SinglePeople', ['priority', "data"])


def choose_skill(scene, category_limit=0):
    if scene == 'ctrl':
        choose_skill_generic(scene_skill_keyword='ctrl', category_limit=0,
                             self_conflict_skill=['Bskill_ctrl_p_spd', 'Bskill_ctrl_t_spd', 'Bskill_ctrl_token_p_spd'],
                             max_people=5, num_chosen=num_people_already())
    elif scene == 'meet':
        choose_skill_generic(scene_skill_keyword='meet', category_limit=0,
                             self_conflict_skill=[],
                             max_people=2, num_chosen=num_people_already())
    elif scene == 'tra':
        choose_skill_generic(scene_skill_keyword='tra', category_limit=0,
                             self_conflict_skill=[],
                             max_people=3, num_chosen=num_people_already())
    elif scene == 'man':
        choose_skill_generic(scene_skill_keyword='man', category_limit=category_limit,
                             self_conflict_skill=[],
                             max_people=3, num_chosen=num_people_already())
    elif scene == 'pow':
        choose_skill_generic(scene_skill_keyword='pow', category_limit=0,
                             self_conflict_skill=[],
                             max_people=1, num_chosen=num_people_already())
    elif scene == 'hire':
        choose_skill_generic(scene_skill_keyword='hire', category_limit=0,
                             self_conflict_skill=[],
                             max_people=1, num_chosen=num_people_already())


def choose_skill_generic(scene_skill_keyword, category_limit, self_conflict_skill, max_people, num_chosen):
    priority_dict: dict[str, int] = res.load_yaml("resources/game_data/ship_skill/priority.yaml")['priority']
    category_dict = res.load_yaml("resources/game_data/ship_skill/manufactory_category.yaml")[
        'manufactory_category']
    skill_visible = reco_skills(debug_show=False)
    all_people_dict: dict[int, SinglePeople] = {}
    for single_result in skill_visible:
        if scene_skill_keyword not in single_result.name:
            continue
        try:
            priority = priority_dict[single_result.name]
        except:
            continue
        if single_result.rect.people_id not in all_people_dict:
            all_people_dict[single_result.rect.people_id] = SinglePeople(priority, single_result)
        elif priority < all_people_dict[single_result.rect.people_id].priority:
            all_people_dict[single_result.rect.people_id] = SinglePeople(priority, single_result)
    all_people_dict = dict(sorted(all_people_dict.items(), key=lambda item: item[1]))
    to_choose_people_dict: dict[int, SinglePeople] = {}
    pop_key_list: list[int] = []
    conflict_skill_list = {}
    for str_skill in self_conflict_skill:
        conflict_skill_list[str_skill] = False
    # 事先已经存在的干员的冲突技能列表
    for people in all_people_dict:
        if all_people_dict[people].data.rect.people_id < num_chosen and \
                all_people_dict[people].data.name in \
                self_conflict_skill:
            conflict_skill_list[all_people_dict[people].data.name] = True
    # 按优先级选择新干员
    for people in all_people_dict:
        # 优先级为负1 或是已选择的干员 直接跳过
        if all_people_dict[people].priority == -1 or all_people_dict[people].data.rect.people_id < num_chosen:
            continue
        # 不符合当前分类的干员也直接跳过
        elif category_limit != 0:  # 场景要求分类限制
            if all_people_dict[people].data.name in category_dict:  # 技能有分类限定
                if category_dict[all_people_dict[people].data.name] not in [0, category_limit]:  # 技能分类不为0且不为场景限制分类
                    continue
        # 未选择的合理干员，若是拥有冲突技能
        if all_people_dict[people].data.name in ['Bskill_ctrl_p_spd', 'Bskill_ctrl_t_spd',
                                                 'Bskill_ctrl_token_p_spd']:
            # 冲突技能已被选择的
            if conflict_skill_list[all_people_dict[people].data.name]:
                continue
            # 技能有冲突性但未曾被选择
            else:
                # 加入备选字典中
                to_choose_people_dict[people] = all_people_dict[people]
                conflict_skill_list[all_people_dict[people].data.name] = True
        else:
            to_choose_people_dict[people] = all_people_dict[people]
    for people in to_choose_people_dict:
        if num_chosen >= max_people:
            break
        ADB.input_press_rect(
            imgops.from_std_rect(ADB.get_resolution(), to_choose_people_dict[people].data.rect.rect))
        num_chosen += 1
        time.sleep(0.5)



def reco_skills(debug_show=False):
    img_gray = ADB.screencap_mat(std_size=True, gray=False)
    skill_rect_list = gen_rect_matrix(img_gray)
    skill_mat = read_all_skill_icon_resource()
    reco_result = reco_matrix(img_gray, skill_rect_list, skill_mat)
    if debug_show:
        for i in reco_result:
            img_cropped = imgops.mat_crop(img_gray, i.rect.rect)
            f = plt.figure()
            f.add_subplot(1, 2, 1)
            plt.imshow(((img_cropped * (skill_mat[i.icon_index][2] / 255.0)).astype(np.uint8))[:, :, ::-1])
            f.add_subplot(1, 2, 2)
            plt.imshow(skill_mat[i.icon_index][1][:, :, ::-1])
            plt.show()
            pass
    return reco_result


if __name__ == '__main__':
    choose_skill('man')
