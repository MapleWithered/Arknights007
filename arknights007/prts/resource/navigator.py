import functools
import os
import time
import typing
from collections import namedtuple

import dpath.util

from .. import navigator
from .game_data_json import get_game_data_dict
from .image import get_img_path_suffix
from .import resource_path
from .yaml import load_yaml


@functools.lru_cache()
def get_pos(path: str):
    file_path = os.path.join(resource_path, 'navigator', 'pos.yaml')
    res = load_yaml(file_path)
    pos = dpath.util.get(res, "/" + get_img_path_suffix() + path)
    return pos


StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])


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
    if activity_id in ['main', 'weekly']:
        return True
    if activity_id not in activities:
        activities = get_activities(force_update=True)
        if activity_id not in activities:
            return False
    cur_time = time.time()
    activity_info = activities[activity_id]
    return activity_info['startTime'] < cur_time < activity_info['endTime']


@functools.lru_cache()
def get_stage_map_local(stage: str) -> typing.Optional[list[str]]:
    res = load_yaml("navigator/stage_map.yaml")
    if navigator.stage_is_main_chapter(stage) is not None:
        episode = 'ep' + str(navigator.stage_is_main_chapter(stage)).rjust(2, '0')
        path = '/main_stage/' + episode
    elif navigator.stage_is_resource(stage) is not None:
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


def get_stage_info_and_map(stage: str):
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


def get_stage_sanity_cost(stage_code: str):
    stage_code.replace('$', '')
    stages = get_game_data_dict('stage_table.json')['stages']
    for stage in stages:
        if stages[stage].get('code', '') == stage_code:
            return stages[stage].get('apCost', -1)
    return 18