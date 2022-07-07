import os
import time
from collections import namedtuple
from functools import lru_cache

from .adb import ADB
from .imgreco import imgops
from .penguin_stats import arkplanner
from .resource.inventory_reco import get_item_index

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def save_screenshot_after_battle(stage: str):
    img = ADB.screencap_mat(force=True, std_size=False)
    # generate file path with timestamp
    date_str = time.strftime("%Y%m%d", time.localtime())
    time_str = time.strftime("%H%M%S", time.localtime())
    file_name = f"{date_str}_{time_str}_{stage}.png"
    folder_path = os.path.join("battle_screenshot", f"{date_str}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    # save image
    imgops.save_image(img, file_path)


@lru_cache()
def item_id_to_name(id):
    data = get_item_index()
    if id in data['id2idx']:
        return data["idx2name"][data['id2idx'][id]]
    else:
        return None


@lru_cache()
def item_name_to_id(name):
    special_support = {'净龙门币': 'net_lmb', '总作战记录': 'total_exp'}
    if name in special_support:
        return special_support[name]

    if '技巧概要' in name or '技能书' in name:
        if '合成' in name:
            if '1' in name:
                return item_name_to_id('技巧概要·卷1')
            elif '2' in name:
                return 'skill_book_compose_2'
            elif '3' in name:
                return 'skill_book_compose_3'
        else:
            if '1' in name:
                return '3301'
            if '2' in name:
                return '3302'
            if '3' in name:
                return '3303'

    data = get_item_index()
    for item_idx in range(len(data["idx2name"])):
        if data["idx2name"][item_idx] == name:  # and item['rarity'] == 2
            return data["idx2id"][item_idx]


@lru_cache()
def item_id_to_type(id):
    data = get_item_index()
    if id in data['id2idx']:
        return data["idx2type"][data['id2idx'][id]]
    else:
        return None


material_white_list = {
    "源岩", "固源岩", "固源岩组", "提纯源岩",
    "代糖", "糖", "糖组", "糖聚块",
    "酯原料", "聚酸酯", "聚酸酯组", "聚酸酯块",
    "异铁碎片", "异铁", "异铁组", "异铁块",
    "双酮", "酮凝集", "酮凝集组", "酮阵列",
    "破损装置", "装置", "全新装置", "改量装置",
    "扭转醇", "白马醇",
    "轻锰矿", "三水锰矿",
    "研磨石", "五水研磨石",
    "RMA70-12", "RMA70-24",
    "聚合剂", "双极纳米片", "D32钢", "晶体电子单元",
    "凝胶", "聚合凝胶",
    "炽合金", "炽合金块",
    "晶体元件", "晶体电路",
    "半自然溶剂", "精炼溶剂",
    "化合切削液", "切削原液"
}

material_not_avail = {
    "采购凭证",
    "赤金",
    "龙骨",
    "碳", "碳素", "碳素组",
    "基础加固建材", "进阶加固建材", "高级加固建材",
    "源石碎片",
    "芯片助剂",
    "先锋芯片", "先锋芯片组", "先锋双芯片",
    "近卫芯片", "近卫芯片组", "近卫双芯片",
    "重装芯片", "重装芯片组", "重装双芯片",
    "狙击芯片", "狙击芯片组", "狙击双芯片",
    "术师芯片", "术师芯片组", "术师双芯片",
    "医疗芯片", "医疗芯片组", "医疗双芯片",
    "辅助芯片", "辅助芯片组", "辅助双芯片",
    "特种芯片", "特种芯片组", "特种双芯片",
    "技巧概要·卷1", "技巧概要·卷2",
    "技巧概要·卷3",
    "家具零件",
    "模组数据块", "数据增补条", "数据增补仪",
}


@lru_cache()
def item_id_is_material_avail(id):
    name = item_id_to_name(id)
    if name in material_white_list:
        return True
    if name in material_not_avail:
        return False
    if item_id_to_type(id) == 'MATERIAL':
        return True
    else:
        return False
