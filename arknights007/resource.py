import functools
import json
import os
import queue
import time
import typing
from collections import namedtuple
from threading import Thread

import cv2
import dpath.util
import requests
from ruamel import yaml

import arknights007.navigator
from arknights007 import adb
from multiprocessing import Process


StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])


@functools.lru_cache()
def load_yaml(path: str):
    assert os.path.exists(path), '未能检测到yaml文件.'
    with open(path, 'r', encoding='utf-8') as f:
        plan = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
    return plan


@functools.lru_cache()
def get_img_path_suffix():
    resolution = adb.ADB.get_resolution()
    hw_ratio = resolution.width / resolution.height
    return "%.2f" % hw_ratio


@functools.lru_cache()
def get_img_path(path: str) -> str:
    if path[0] == '/':
        path = path[1:]
    return os.path.join("resources/" + get_img_path_suffix(), path)


@functools.lru_cache()
def get_img_bgr(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_COLOR)
    return mat


@functools.lru_cache()
def get_img_gray(path: str):
    mat = cv2.imread(get_img_path(path), cv2.IMREAD_GRAYSCALE)
    return mat


@functools.lru_cache()
def get_pos(path: str):
    res = load_yaml("resources/navigator/pos.yaml")
    pos = dpath.util.get(res, "/" + get_img_path_suffix() + path)
    return pos


def get_game_data_path(filename: str, version: str):
    os.path.join("resources/game_data/" + version, filename)


server_url = [
    "https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel/FILENAME",
    "https://raw.fastgit.org/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/FILENAME",
    "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/FILENAME"
]


# noinspection PyBroadException
def download_url_to_bytes(url: str) -> typing.Optional[bytes]:
    try:
        resp = requests.get(url)
    except Exception:
        return None
    return resp.content


def download_game_data_from_all_server(filename: str) -> bytes:
    file_url = server_url

    que = queue.Queue(maxsize=len(file_url))
    threads_list = []

    for url in file_url:
        url = url.replace("FILENAME", filename)
        t = Thread(target=lambda q, arg1: q.put(download_url_to_bytes(arg1)), args=(que, url))
        t.start()
        threads_list.append(t)
    # for t in threads_list:
    #     t.join()   # If need to wait for thread to finish

    res = que.get()
    return res


def download_to_cache(filename: str):
    path = get_cache_path(filename)
    res = download_game_data_from_all_server(filename)
    with open(path, 'wb') as f:
        f.write(res)


def get_game_data_latest_version_number():
    res = download_game_data_from_all_server("data_version.txt").decode("utf-8")
    date_str = res[res.find("on ") + 3: res.find("\nVersionControl")].replace("/", '')
    print(date_str)
    return date_str


def get_cache_path(filename: str) -> str:
    return "resources/game_data/" + filename


def get_game_data_dict(filename: str, force_update=False):
    filepath = get_cache_path(filename)
    if not os.path.exists(filepath) or force_update:
        download_to_cache(filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)



def process_stages(stages):
    stage_code_map = {}
    zone_linear_map = {}
    for stage_id in stages.keys():
        stage = stages[stage_id]
        if stage_code_map.get(stage['code']) is not None:
            continue
        stage_code_map[stage['code']] = stage
        l = zone_linear_map.get(stage['zoneId'], [])
        l.append(stage['code'])
        zone_linear_map[stage['zoneId']] = l
    return stage_code_map, zone_linear_map


def get_stage_map_full_data(force_update=False):
    try:
        stages = get_game_data_dict('stage_table.json', force_update)['stages']
    except Exception:
        stages = get_game_data_dict('stage_table.json', True)['stages']

    return process_stages(stages)


def check_activity_available(zone_id):
    # noinspection PyBroadException
    def get_activities(force_update=False):
        try:
            activities_basic_info = get_game_data_dict('activity_table.json', force_update)['basicInfo']
        except Exception:
            activities_basic_info = get_game_data_dict('activity_table.json', True)['basicInfo']
        return activities_basic_info

    activity_id = zone_id.split('_')[0]
    activities = get_activities()
    if activity_id not in activities:
        activities = get_activities(force_update=True)
        if activity_id not in activities:
            return False
    cur_time = time.time()
    activity_info = activities[activity_id]
    return activity_info['startTime'] < cur_time < activity_info['endTime']


@functools.lru_cache()
def get_stage_map_local(stage: str) -> typing.Optional[list[str]]:
    path = ''
    res = load_yaml("resources/navigator/stage_map.yaml")
    if arknights007.navigator.stage_is_main_chapter(stage) is not None:
        episode = 'ep0' + str(arknights007.navigator.stage_is_main_chapter(stage))
        path = '/main_stage/' + episode
    elif arknights007.navigator.stage_is_resource(stage) is not None:
        part0 = '-'.join(stage.split('-')[:-1])
        path = '/resources/' + part0
    else:
        for other_map in res['other']:
            if stage in other_map:
                return other_map
        else:
            return None
    stage_map = dpath.util.get(res, path)
    return stage_map


def get_stage_info_full(stage: str):
    stage_code_map, zone_linear_map = get_stage_map_full_data()
    if stage not in stage_code_map:
        stage_code_map, zone_linear_map = get_stage_map_full_data(force_update=True)
        if stage not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {stage}')
    stage_info = stage_code_map[stage]
    # print(stage_info)
    if not check_activity_available(stage_info['zoneId']):
        # 活动复刻关卡的 zone id 会变化, 所以需要更新关卡信息
        stage_code_map, zone_linear_map = get_stage_map_full_data(force_update=True)
        if stage not in stage_code_map:
            raise RuntimeError(f'无效的关卡: {stage}')
        stage_info = stage_code_map[stage]
        # print(stage_info)  # Originally Commented
        # Original No comment below 2 code.
        # if not check_activity_available(stage_info['zoneId']):
        #     raise RuntimeError('活动未开放')
    stage_linear = zone_linear_map.get(stage_info['zoneId'])
    # print(stage_linear)
    return StageInfo(stage_info, stage_linear)


# Cache逻辑：
'''
启动时检查版本号，
定期检查版本号，
如果版本号有更新，则强制刷新游戏数据
'''
