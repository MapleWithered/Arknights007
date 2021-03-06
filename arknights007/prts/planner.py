import copy
import os
import time
import datetime
from math import ceil, floor

import requests
import ruamel.yaml as yaml

from .config import get_config_path
from .navigator import goto_stage, back_to_main_menu
from .battle import start_battle
from .item_material import item_id_to_name, item_name_to_id, item_id_is_material_avail
from .penguin_stats import arkplanner
from .resource.navigator import get_stage_sanity_cost
from .imgreco.inventory.reco import get_inventory_items_all_information
from .arkplanner.MaterialPlanning import MaterialPlanning
from . import logger

_stages_not_open = []
_stages_not_open_date_last_write_timestamp = 0

_aog_data = None
_aog_data_timestamp = 0

mp = MaterialPlanning(update=False)


def get_stages_not_open():
    global _stages_not_open
    global _stages_not_open_date_last_write_timestamp
    # get the time of today 4:00 AM
    update_time = datetime.datetime.now().replace(hour=4, minute=0, second=0, microsecond=0).timestamp()
    if _stages_not_open_date_last_write_timestamp < update_time < time.time():
        _stages_not_open_date_last_write_timestamp = time.time()
        _stages_not_open = []
    return _stages_not_open


def push_stages_not_open(stage: str):
    global _stages_not_open
    global _stages_not_open_date_last_write_timestamp
    _stages_not_open = get_stages_not_open() + [stage]
    _stages_not_open_date_last_write_timestamp = time.time()


def dump_plan_yaml(plan):
    path_plan = get_config_path('plan.yaml')
    with open(path_plan, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, Dumper=yaml.RoundTripDumper, indent=2, allow_unicode=True, encoding='utf-8')


def load_config():
    config = {}
    path_config = get_config_path()
    with open(os.path.join(path_config, 'item_excluded.yaml'), 'r', encoding='utf-8') as f:
        config['item_excluded'] = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
        if config['item_excluded'] is None:
            config['item_excluded'] = []
    with open(os.path.join(path_config, 'stage_unavailable.yaml'), 'r', encoding='utf-8') as f:
        config['stage_unavailable'] = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
        if config['stage_unavailable'] is None:
            config['stage_unavailable'] = []
    return config


def load_local_plan():
    path_plan = get_config_path('plan.yaml')
    assert os.path.exists(path_plan), '?????????????????????????????????.'
    with open(path_plan, 'r', encoding='utf-8') as f:
        plan = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
    # ??????????????????
    need_dump = False
    for priority in plan['plan']:
        if list(priority)[0] == 'stages':
            stages_same_prior = priority['stages']
            for i in range(len(stages_same_prior)):
                stage_data = stages_same_prior[i]
                if '//' not in list(stage_data):
                    need_dump = True
                    stage_data['//'] = ' '
                if 'sanity' not in list(stage_data):
                    need_dump = True
                    stage_data['sanity'] = get_stage_sanity_cost(list(stage_data)[0])
                if 'remain' not in list(stage_data):
                    need_dump = True
                    stage_data['remain'] = stage_data[list(stage_data)[0]]
    if need_dump:
        dump_plan_yaml(plan)
    return plan


def calc_experience(inventory):  # lmb/exp????????????1:1
    exp_sum = 0
    if '2004' in inventory:
        exp_sum += inventory['2004'] * 2000
    if '2003' in inventory:
        exp_sum += inventory['2003'] * 1000
    if '2002' in inventory:
        exp_sum += inventory['2002'] * 400
    if '2001' in inventory:
        exp_sum += inventory['2001'] * 200
    return exp_sum


def load_inventory():  # load simple inventory
    my_inventory = get_inventory_items_all_information()
    for item in my_inventory:
        if my_inventory[item] is None:
            my_inventory[item] = 0
        else:
            my_inventory[item] = my_inventory[item].get('quantity', 0)
    my_inventory['total_exp'] = calc_experience(my_inventory)
    my_inventory['net_lmb'] = my_inventory.get('4001', 0) - my_inventory['total_exp']
    my_inventory['skill_book_compose_2'] = floor(my_inventory.get('3301', 0) / 3 * 1.17) + my_inventory.get('3302', 0)
    my_inventory['skill_book_compose_3'] = floor(my_inventory.get('skill_book_compose_2', 0) / 3 * 1.17) + \
                                           my_inventory.get('3303', 0)
    return my_inventory


def create_plan_by_material(wish_list, my_inventory=None):
    required = {}
    owned = {}

    global mp

    for item_need in wish_list:
        if item_id_is_material_avail(item_name_to_id(item_need[0])):
            required[item_need[0]] = item_need[1]

    if len(required) == 0:
        return [], 0

    if my_inventory is None:
        my_inventory = load_inventory()

    for item_had in my_inventory:
        if item_id_to_name(item_had) is not None and item_id_is_material_avail(item_had):
            owned[item_id_to_name(item_had)] = my_inventory[item_had]

    config = load_config()
    excluded = config['stage_unavailable']

    b_need_plan = False
    for item in required:
        if owned.get(item, 0) < required.get(item, 0):
            b_need_plan = True
            break
    if not b_need_plan:
        return [], 0

    plan = mp.get_plan(required, owned, print_output=False, outcome=True, convertion_dr=0.17,
                       input_lang='zh', output_lang='zh', exclude=excluded)

    stage_task_list = []

    sanity = 0

    for stage in plan['stages']:
        stage_name = stage['stage']
        count = ceil(float(stage['count']))
        single_sanity = get_stage_sanity_cost(stage_name)
        sanity += count * single_sanity
        stage_task_list.append({'stage': stage_name, 'count': count, 'cost': single_sanity})

    return stage_task_list, sanity


def create_plan_by_non_material(wish_list, my_inventory=None):
    required = {}
    owned = {}

    if my_inventory is None:
        my_inventory = load_inventory()

    for item_had in my_inventory:
        if item_id_to_name(item_had) is not None:
            owned[item_id_to_name(item_had)] = my_inventory[item_had]
        else:
            owned[item_had] = my_inventory[item_had]

    stage_task_list = []
    sanity = 0

    chip_stage = ['PR-A', 'PR-B', 'PR-C', 'PR-D']
    chip_idx = {'??????': 0, '??????': 1, '??????': 2, '??????': 3, '??????': 4, '??????': 5, '??????': 6, '??????': 7}  # AABBCCDD
    chip_wish = [[0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0]]  # small, large, duo

    lmb_need = 0

    book_need = [0, 0, 0]

    for item_need in wish_list:
        if item_need[0] == '?????????':
            lmb_need = max(lmb_need, 0, item_need[1] - owned.get('?????????', 0))
        elif item_need[0] == '????????????':
            lmb_need = max(lmb_need, 0, item_need[1] - owned.get('net_lmb', owned.get('?????????', 0) - owned.get('total_exp',
                                                                                                            calc_experience(
                                                                                                                my_inventory))))
        elif item_need[0] in {'????????????', '??????', '??????', '?????????', '?????????', '?????????', '?????????', '?????????', '??????'}:
            count = max(0, ceil((item_need[1] - owned.get('total_exp', 0)) / 10000))
            if count != 0:
                stage_task_list.append({'stage': 'LS-6', 'count': count, 'cost': 36})
                sanity += count * 36
        elif item_need[0] in {'????????????', '??????'}:
            count = max(0, ceil((item_need[1] - owned.get('????????????', 0)) / 20))
            if count != 0:
                stage_task_list.append({'stage': 'AP-5', 'count': count, 'cost': 30})
                sanity += count * 30
        elif '????????????' in item_need[0] or '?????????' in item_need[0]:
            if '1' in item_need[0]:
                book_need[0] = max(book_need[0], 0, item_need[1] - owned.get('?????????????????1', 0))
            if '2' in item_need[0]:
                if '??????' in item_need[0]:
                    book_need[1] = max(book_need[1], 0,
                                       item_need[1] - owned.get('?????????????????2', 0) -
                                       floor(owned.get('?????????????????1', 0) / 3 * 1.17))
                else:
                    book_need[1] = max(book_need[1], 0,
                                       item_need[1] - owned.get('?????????????????2', 0))
            if '3' in item_need[0]:
                if '??????' in item_need[0]:
                    book_need[2] = max(book_need[2], 0, item_need[1] - owned.get('?????????????????3', 0) -
                                       floor((floor(owned.get('?????????????????1', 0) / 3 * 1.17) +
                                              owned.get('?????????????????2', 0)) / 3 * 1.17))
                else:
                    book_need[2] = max(book_need[2], 0, item_need[1] - owned.get('?????????????????3', 0))
        elif '??????' in item_need[0] and \
                item_need[0][0:2] in chip_idx:
            if len(item_need[0]) == 5 and item_need[0].endswith('?????????'):
                chip_wish[1][chip_idx[item_need[0][0:2]]] += item_need[1]
            elif item_need[0].endswith('?????????'):
                chip_wish[2][chip_idx[item_need[0][0:2]]] += item_need[1]
            elif len(item_need[0]) == 4 and item_need[0].endswith('??????'):
                chip_wish[0][chip_idx[item_need[0][0:2]]] += item_need[1]
            # if len(item_need[0]) == 5 and item_need[0].endswith('?????????') and \
            #         item_need[0][0:2] in {"??????", "??????", "??????", "??????", "??????", "??????", "??????", "??????"}:
            #     count = max(0, (item_need[1] - owned.get(item_need[0], 0)) * 2)
            #     if count != 0:
            #         stage_task_list.append(
            #             {'stage': f'{chip_stage[item_need[0][0:2]]}-2',
            #              'count': count,
            #              'cost': 36}
            #         )
            #         sanity += count * 36
            # elif item_need[0].endswith('?????????'):
            #     raise NotImplementedError('?????????????????????????????????')
            # elif len(item_need[0]) == 4 and item_need[0].endswith('??????') and \
            #         item_need[0][0:2] in {"??????", "??????", "??????", "??????", "??????", "??????", "??????", "??????"}:
            #     count = max(0, (item_need[1] - owned.get(item_need[0], 0)) * 2)
            #     if count != 0:
            #         stage_task_list.append(
            #             {'stage': f'{chip_stage[item_need[0][0:2]]}-1',
            #              'count': count,
            #              'cost': 18}
            #         )
            #         sanity += count * 18

    # ?????????/??????????????????
    lmb_stage_count = max(0, ceil(lmb_need / 10000))
    if lmb_stage_count != 0:
        stage_task_list.append({'stage': 'CE-6', 'count': lmb_stage_count, 'cost': 36})
        sanity += lmb_stage_count * 36

    # ???????????????
    chip_owned = [[0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0]]
    for chip_cat in chip_idx:
        chip_owned[0][chip_idx[chip_cat]] = owned.get(f'{chip_cat}??????', 0)
        chip_owned[1][chip_idx[chip_cat]] = owned.get(f'{chip_cat}?????????', 0)
        chip_owned[2][chip_idx[chip_cat]] = owned.get(f'{chip_cat}?????????', 0)
    # ?????????????????????
    chip_need = copy.deepcopy(chip_wish)
    for i in range(2, -1, -1):
        for j in range(8):
            chip_need[i][j] = chip_wish[i][j] - chip_owned[i][j]
    for i in range(8):
        if chip_need[1][i] < 0 and chip_need[2][i] > 0:
            compose_num = min(chip_need[2][i], (-chip_need[1][i]) // 2)
            chip_need[1][i] += compose_num * 2
            chip_need[2][i] -= compose_num
    # ????????????????????????
    for i in range(4):
        count = max(0, chip_need[0][i * 2], chip_need[0][i * 2 + 1]) * 2
        if count != 0:
            stage_task_list.append(
                {'stage': f'{chip_stage[i]}-1',
                 'count': count,
                 'cost': 18}
            )
            sanity += count * 18
        count = 2 * max(0,
                        max(0, chip_need[2][i * 2]) * 2 + chip_need[1][i * 2],
                        max(0, chip_need[2][i * 2 + 1]) * 2 + chip_need[1][i * 2 + 1])
        if count != 0:
            stage_task_list.append(
                {'stage': f'{chip_stage[i]}-2',
                 'count': count,
                 'cost': 36}
            )
            sanity += count * 36

    # ???????????????
    book_stage_count = ceil(max(book_need[0]/1.5, book_need[1]/1.5, book_need[2]/2))
    if book_stage_count != 0:
        stage_task_list.append(
            {'stage': 'CA-5',
             'count': book_stage_count,
             'cost': 30}
        )

    return stage_task_list, sanity


def aog_order_stage(item_data):
    list_stages = []
    for stage in item_data['lowest_ap_stages']['normal']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    for stage in item_data['lowest_ap_stages']['event']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    for stage in item_data['balanced_stages']['normal']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    for stage in item_data['balanced_stages']['event']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    for stage in item_data['drop_rate_first_stages']['normal']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    for stage in item_data['drop_rate_first_stages']['event']:
        if [stage['code'], stage['efficiency']] not in list_stages:
            list_stages.append([stage['code'], stage['efficiency']])
    list_stages.sort(reverse=True, key=(lambda x: x[1]))
    return list_stages


def get_aog_data():
    global _aog_data
    global _aog_data_timestamp
    # get the time of today 14:00
    update_time = datetime.datetime.now().replace(hour=14, minute=0, second=0, microsecond=0).timestamp()
    if _aog_data_timestamp < update_time < time.time() or _aog_data is None:
        _aog_data_timestamp = time.time()
        headers = {'Referer': 'https://aog.wiki/'}
        _aog_data = requests.get('https://api.aog.wiki/v2/data/total/CN', headers=headers).json()
    return _aog_data


def get_min_blue_item_stage(item_excluded=None, stage_unavailable=None, my_items=None, aog_data=None):
    config = load_config()
    if item_excluded is None:
        item_excluded = config['item_excluded']
    if stage_unavailable is None:
        stage_unavailable = config['stage_unavailable']
    if aog_data is None:
        aog_data = get_aog_data()
    if my_items is None:
        my_items = load_inventory()
    all_items = arkplanner.get_all_items()
    list_my_blue_item = []
    for item in all_items:
        if item['itemType'] in ['MATERIAL'] and item['name'] not in item_excluded and item['rarity'] == 2 \
                and len(item['itemId']) > 4:
            if item['name'] == '????????????':
                list_my_blue_item.append({'name': item['name'],
                                          'itemId': item['itemId'],
                                          'count': my_items.get(item['itemId'], 0) + my_items.get('30012', 0) / 5,
                                          'rarity': item['rarity']})
            else:
                list_my_blue_item.append({'name': item['name'],
                                          'itemId': item['itemId'],
                                          'count': my_items.get(item['itemId'], 0),
                                          'rarity': item['rarity']})
    list_my_blue_item = sorted(list_my_blue_item, key=lambda x: x['count'])
    # print('require item: %s, owned: %s, need ' % (list_my_blue_item[0]['name'], list_my_blue_item[0]['count']))
    second_count = list_my_blue_item[0]['count']
    for i in range(len(list_my_blue_item)):
        if list_my_blue_item[i]['count'] > list_my_blue_item[0]['count']:
            second_count = list_my_blue_item[i]['count']
            break
    else:
        second_count += 9999
    # return [list_my_blue_item[0]['name'], list_my_blue_item[0]['count'], (second_count-list_my_blue_item[0]['count'])]

    # ????????????????????????????????? ????????????????????????

    blue_items_data = aog_data['tier']['t3']
    stage_todo = None
    i = 0
    while i < len(list_my_blue_item):  # ???????????????????????????????????????????????????
        if list_my_blue_item[i]['name'] == '????????????':
            logger.info('?????????: ' + '????????????' +
                        ', ????????????(?????????????????????): ' + str(list_my_blue_item[i]['count']) +
                        ', ??????: ' + '1-7' +
                        ', ??????: ' + '1.000')
            return '1-7'
        for aog_blue_item in blue_items_data:
            if aog_blue_item['name'] == list_my_blue_item[i]['name']:  # ?????????????????????????????????
                stage_info = aog_order_stage(aog_blue_item)
                for stage in stage_info:  # ????????????????????????
                    if stage[0] not in stage_unavailable:  # ????????????????????????
                        stage_todo = stage[0]
                        logger.info('?????????: ' + list_my_blue_item[i]['name'] +
                                    ', ????????????: ' + str(list_my_blue_item[i]['count']) +
                                    ', ??????: ' + stage_todo,
                                    ', ??????: ' + str(stage[1]))
                        return stage_todo
        i += 1
    return stage_todo


def get_good_stage_id(stages_same_prior):
    config = load_config()
    stage_ok_id = -1
    max_remain_ratio = 0
    for i in range(len(stages_same_prior)):
        stage_data = stages_same_prior[i]
        stage_name = list(stage_data)[0]
        stage_count = stage_data[list(stage_data)[0]]
        if 'remain' not in list(stage_data):
            stage_data['remain'] = copy.deepcopy(stage_count)
        remain_ratio = stage_data['remain'] / stage_count
        if stage_name not in get_stages_not_open() + config['stage_unavailable'] and stage_data['remain'] > 0 \
                and remain_ratio > max_remain_ratio:
            stage_ok_id = i
            max_remain_ratio = remain_ratio
    return stage_ok_id


def get_planner_good_stage_id(stages_same_prior):
    config = load_config()
    stage_ok_id = -1
    max_remain_ratio = 0
    for i in range(len(stages_same_prior)):
        stage_data = stages_same_prior[i]
        stage_name = stage_data['stage']
        stage_count = stage_data['count']
        if stage_name not in get_stages_not_open() + config['stage_unavailable'] and stage_count > 0:
            stage_ok_id = i
            return stage_ok_id
    return stage_ok_id


def get_my_item_count(item_name, my_items=None):
    if my_items is None:
        my_items = load_inventory()
    # logger.info("?????????????????????????????????????????????")
    if item_name_to_id(item_name) in list(my_items):
        return my_items[item_name_to_id(item_name)]
    else:
        return 0


def print_sanity_usage(sanity):
    hour_rest = sanity / 240 * 24
    hour_rest_monthly = sanity // 300 * 24 + sanity % 300 / 10
    if hour_rest >= 24:
        str_hour_rest = str(int(hour_rest // 24)) + " ??? " + str(int(hour_rest % 24) + 1) + " ??????"
    else:
        str_hour_rest = str(int(hour_rest % 24) + 1) + " ??????"
    if hour_rest_monthly >= 24:
        str_hour_rest_monthly = str(int(hour_rest_monthly // 24)) + " ??? " + str(
            int(hour_rest_monthly % 24) + 1) + " ??????"
    else:
        str_hour_rest_monthly = str(int(hour_rest_monthly % 24) + 1) + " ??????"
    logger.info("????????????????????? " + str(sanity) + " ??????  -  " + str_hour_rest + " / " + str_hour_rest_monthly + " (Prime)")


def print_exp_lmb_info(my_inventory):
    logger.info(
        f"????????? {my_inventory.get('4001', 0)} - ???????????? {my_inventory['total_exp']} = {my_inventory['net_lmb']} ??????????????????")


def print_plan_with_plan(plan=None, my_inventory=None, print_priority=None):
    back_to_main_needed = False
    if plan is None:
        plan = load_local_plan()
    if my_inventory is None:
        my_inventory = load_inventory()
    if print_priority is None:
        logger.info("\n\n\n\n\n\n\n\n\n\n\n\n")
        logger.warning("?????????????????????")

    logger.info("----------------------------------------------------------------------------------------")

    prior = 1
    ok_task_used = False
    ok_cost = None

    config = load_config()

    for priority in plan['plan']:
        if print_priority is not None and prior > print_priority:
            break
        priority_first_line = True
        if list(priority)[0] == 'stages':
            if print_priority == prior or print_priority is None:
                logger.info(
                    "??????  " + "??????".ljust(12) + "??????".ljust(5) + "??????".ljust(5) + "??????".ljust(5) + "??????".ljust(8) + "??????")
            stages_same_prior = priority['stages']
            ok_id = get_good_stage_id(stages_same_prior)
            for task_id, task in enumerate(stages_same_prior):
                remain = task['remain']
                fini_percent = int((remain / task[list(task)[0]]) * 100)
                if fini_percent == 0:
                    status_char = '???'
                elif list(task)[0] in get_stages_not_open():
                    status_char = '??'
                elif task_id == ok_id and ok_task_used is False:
                    status_char = '???'
                    ok_task_used = prior - 1
                else:
                    status_char = ' '
                if priority_first_line:
                    priority_first_line = False
                    priority_str = ' ' + str(prior).zfill(2).ljust(5)
                else:
                    priority_str = '      '
                if print_priority == prior or print_priority is None:
                    if fini_percent == 100 or task[list(task)[0]] >= 1000 or fini_percent == 0:
                        logger.info(priority_str + list(task)[0].ljust(
                            14 - int((len(list(task)[0].encode('utf-8')) - len(list(task)[0])) / 2)) + str(
                            task.get('sanity', '')).ljust(7) + str(task[list(task)[0]]).ljust(7) + str(remain).ljust(
                            7) + " --  " + status_char + "    " + task['//'])
                    else:
                        logger.info(priority_str + list(task)[0].ljust(
                            14 - int((len(list(task)[0].encode('utf-8')) - len(list(task)[0])) / 2)) + str(
                            task.get('sanity', '')).ljust(7) + str(task[list(task)[0]]).ljust(7) + str(remain).ljust(
                            7) + str(
                            fini_percent).rjust(3) + "% " + status_char + "    " + task['//'])
            if print_priority == prior or print_priority is None:
                logger.info("----------------------------------------------------------------------------------------")
        elif list(priority)[0] == 'blue_item':
            if print_priority == prior or print_priority is None:
                logger.info("??????  " + "??????".ljust(12))
            if ok_task_used is False:
                status_char = '???'
                ok_task_used = prior - 1
            else:
                status_char = ' '
            if print_priority == prior or print_priority is None:
                logger.info(' ' + str(prior).zfill(2).ljust(5) + '@BLUE_ITEM'.ljust(20) + status_char)
                logger.info("----------------------------------------------------------------------------------------")
        elif list(priority)[0] == 'planner':
            if print_priority == prior or print_priority is None:
                logger.info("??????  " + "??????".ljust(12) + "??????".ljust(5) + "??????".ljust(5) + "??????".ljust(5))
            item_list = []
            for item in priority[list(priority)[0]]:
                item_num_had = get_my_item_count(list(item)[0], my_inventory)
                item_num_need = item[list(item)[0]]
                item_name = list(item)[0]
                if item_num_need > 0:
                    item_list.append([item_name, item_num_need])
                # print('utf8', len(item_name.encode('utf-8')), len(item_name))
                if priority_first_line:
                    priority_first_line = False
                    priority_str = ' ' + str(prior).zfill(2).ljust(5)
                else:
                    priority_str = '      '
                if print_priority == prior or print_priority is None:
                    logger.info(
                        priority_str + item_name.ljust(
                            14 - int((len(item_name.encode('utf-8')) - len(item_name)) / 2)) +
                        str(item_num_had if item_num_had else '-').ljust(7) + str(item[list(item)[0]]).ljust(7) +
                        str(max(item_num_need - item_num_had, 0) if max(item_num_need - item_num_had, 0) else '-').ljust(8))
            arkplanner_plan_1, total_sanity_1 = create_plan_by_material(item_list, my_inventory)
            arkplanner_plan_2, total_sanity_2 = create_plan_by_non_material(item_list, my_inventory)
            arkplanner_plan = arkplanner_plan_2 + arkplanner_plan_1
            total_sanity = total_sanity_1 + total_sanity_2
            if len(arkplanner_plan) > 0:
                if print_priority == prior or print_priority is None:
                    logger.info(
                        "                                                   -  -  ???     arkplanner     ???  -  -   ")
                    logger.info("      " + "??????".ljust(12) + "??????".ljust(5) + "??????".ljust(5))
                ok_id = get_planner_good_stage_id(arkplanner_plan)
                for task_id, task in enumerate(arkplanner_plan):
                    if task['count'] == 0:
                        status_char = '???'
                    elif task['stage'] in get_stages_not_open() + config['stage_unavailable']:
                        status_char = '??'
                    elif task_id == ok_id and ok_task_used is False:
                        status_char = '???'
                        ok_task_used = prior - 1
                        ok_cost = total_sanity
                    else:
                        status_char = ' '
                    if print_priority == prior or print_priority is None:
                        logger.info(''.ljust(6) + task['stage'].ljust(
                            14 - int((len(task['stage'].encode('utf-8')) - len(task['stage'])) / 2)) + str(
                            task['cost']).ljust(7) + str(task['count']).ljust(7) + ''.ljust(7) + ''.rjust(
                            3) + "  " + status_char)
            if print_priority == prior or print_priority is None:
                logger.info("----------------------------------------------------------------------------------------")
        prior += 1

    ok_priority_data = plan['plan'][ok_task_used][list(plan['plan'][ok_task_used])[0]]
    ok_priority_category = list(plan['plan'][ok_task_used])[0]
    if ok_priority_category == 'stages':
        ok_cost = 0
        for stage in ok_priority_data:
            ok_cost += stage['sanity'] * stage['remain']

    if print_priority is None:  # ???????????????        # ok_task_used + 1 == print_priority or
        if ok_cost is not None:  # ??????????????????????????????
            print_sanity_usage(ok_cost)
        elif ok_priority_category == "blue_item":  # ??????????????????
            get_min_blue_item_stage(my_items=my_inventory, aog_data=get_aog_data())

        print_exp_lmb_info(my_inventory)

    return ok_cost


def run_plan():
    plan = load_local_plan()
    assert plan['plan'], "??????????????????????????????????????????????????????????????????"

    logger.warning('????????????')

    has_remain_sanity = True

    my_inventory = {}
    inventory_loaded = False

    need_sanity = 10

    priority_id = 1

    mp.update()

    while has_remain_sanity:
        for priority in plan['plan']:
            if list(priority)[0] != 'stages' and inventory_loaded is False:
                my_inventory: dict = load_inventory()
                back_to_main_menu()
                inventory_loaded = True
        if priority_id - 1 == len(plan['plan']):
            print("?????????????????????")
            break
        priority = plan['plan'][priority_id - 1]
        print_plan_with_plan(plan, my_inventory=my_inventory, print_priority=priority_id)
        if list(priority)[0] == 'stages':
            stages_same_prior = priority['stages']
            # ?????????????????????????????????????????????????????????
            stage_ok_id = get_good_stage_id(stages_same_prior)
            if stage_ok_id == -1:
                logger.warning('????????? ' + str(priority_id) + ' ??????????????????????????????')
                priority_id += 1
                continue  # ????????????????????????????????????????????????
            stage_data = stages_same_prior[stage_ok_id]
            stage_name = list(stage_data)[0]
            stage_count = stage_data[list(stage_data)[0]]
            stage_remain = stage_data['remain']
            logger.warning('?????????: %s, ?????? [%s], ?????????: %s, ????????????: %s, ??????: %s' % (
                priority_id, stage_name, stage_count, stage_remain, stage_data['//']))
            try:
                # ????????????????????????????????????
                goto_stage(stage_name, optimistic=False)
                suc = start_battle(stage_name)
                inventory_loaded = False
                if not suc:  # ???????????????????????????????????????
                    has_remain_sanity = False
                    need_sanity = get_stage_sanity_cost(stage_name)
                    # ????????????
                    break
                else:  # ????????????????????????
                    stage_data['remain'] -= 1
                    dump_plan_yaml(plan)
                    continue

            except RuntimeError as e:
                if "???????????????????????????" in e.args[0] or "ocr???????????????" in e.args[0]:
                    # ??????????????????????????????????????????
                    logger.info('?????? [%s] ?????????, ??????????????????' % stage_name)
                    push_stages_not_open(stage_name)
                    logger.info('??????????????????????????????' + str(get_stages_not_open()))
                    continue
                else:
                    # TODO: ????????????handle, ??????????????????
                    continue
            except TimeoutError as e:
                logger.warning('?????? [%s] ??????, ??????????????????' % stage_name)
                back_to_main_menu()
                continue
        elif list(priority)[0] == 'blue_item':
            logger.warning("?????????: " + str(priority_id) + ", ??????????????????????????????")
            min_blue_stage = get_min_blue_item_stage(my_items=my_inventory, aog_data=get_aog_data())
            logger.warning('?????????: %s, ?????? [%s]' % (
                priority_id, min_blue_stage))
            try:
                goto_stage(min_blue_stage, optimistic=False)
                suc = start_battle(min_blue_stage)
                inventory_loaded = False
                if not suc:  # ???????????????????????????????????????
                    has_remain_sanity = False
                    need_sanity = get_stage_sanity_cost(min_blue_stage)
                    # ????????????
                    break
                else:
                    continue
            except RuntimeError as e:
                if "???????????????????????????" in e.args[0] or "ocr???????????????" in e.args[0]:
                    # ??????????????????????????????????????????
                    logger.info('?????? [%s] ?????????, ??????????????????' % min_blue_stage)
                    push_stages_not_open(min_blue_stage)
                    logger.info('??????????????????????????????' + str(get_stages_not_open()))
                    continue
                else:
                    # TODO: ????????????handle, ??????????????????
                    continue
            except TimeoutError as e:
                logger.warning('?????? [%s] ??????, ??????????????????' % min_blue_stage)
                back_to_main_menu()
                continue
        elif list(priority)[0] == 'planner':
            item_list = []
            for item in priority[list(priority)[0]]:
                item_num_need = item[list(item)[0]]
                item_name = list(item)[0]
                if item_num_need > 0:
                    item_list.append([item_name, item_num_need])
            arkplanner_plan_1, total_sanity_1 = create_plan_by_material(item_list, my_inventory)
            arkplanner_plan_2, total_sanity_2 = create_plan_by_non_material(item_list, my_inventory)
            arkplanner_plan = arkplanner_plan_2 + arkplanner_plan_1
            total_sanity = total_sanity_1 + total_sanity_2
            ok_id = get_planner_good_stage_id(arkplanner_plan)
            if len(arkplanner_plan) > 0 and ok_id != -1:
                logger.warning('?????????: %s, ?????? [%s], ????????????: %s' % (
                    priority_id, arkplanner_plan[ok_id]['stage'], arkplanner_plan[ok_id]['count']))

                try:
                    # ????????????????????????????????????
                    goto_stage(arkplanner_plan[ok_id]['stage'], optimistic=False)
                    suc = start_battle(arkplanner_plan[ok_id]['stage'])
                    inventory_loaded = False
                    if not suc:  # ???????????????????????????????????????
                        has_remain_sanity = False
                        need_sanity = get_stage_sanity_cost(arkplanner_plan[ok_id]['stage'])
                        # ????????????
                        break
                    else:  # ????????????????????????
                        continue
                except RuntimeError as e:
                    if "???????????????????????????" in e.args[0] or "ocr???????????????" in e.args[0]:
                        # ??????????????????????????????????????????
                        logger.info('?????? [%s] ?????????, ??????????????????' % arkplanner_plan[ok_id]['stage'])
                        push_stages_not_open(arkplanner_plan[ok_id]['stage'])
                        logger.info('??????????????????????????????' + str(get_stages_not_open()))
                        continue
                    else:
                        # TODO: ????????????handle, ??????????????????
                        print(e)
                        continue
                except TimeoutError as e:
                    logger.warning('?????? [%s] ??????, ??????????????????' % (arkplanner_plan[ok_id]['stage']))
                    back_to_main_menu()
                    continue
            else:
                logger.warning('????????? ' + str(priority_id) + ' ??????????????????????????????')
                priority_id += 1
                continue  # ????????????????????????????????????????????????
    back_to_main_menu()
    time.sleep(1)

    if not has_remain_sanity:
        logger.info('???????????????')

    return need_sanity
