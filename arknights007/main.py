import time

import matplotlib.pyplot as plt

from adb import ADB
import arknights007.imgreco.template as template
import arknights007.imgreco.imgops as imgops
import arknights007.resource as res
import navigator
import arknights007.imgreco.ocr as ocr
import arknights007.battle as battle


def run_stage(stage: str):
    navigator.goto_stage()
    navigator.run_once()


if __name__ == '__main__':
    ADB.connect()
    # print(res.get_stage_map_local("OF-F4"))
    # # stage_info = res.get_stage_info_full("1-1")
    # # stage_map: list = stage_info.stage_map
    # # ocr.ocr_all_stage(stage_map)
    # stages = ['0-1', '0-2', '0-3', '0-4', '0-5', '0-6', '0-7', '0-8',
    #           '0-9', '0-10', '0-11',
    #           '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8',  '1-9', '1-10', '1-11',
    #           '1-12',
    #            '2-1', 'S2-1', '2-2', 'S2-2', 'S2-3', 'S2-4', '2-3',  '2-4', 'S2-5', 'S2-6', 'S2-7',
    #            '2-5', '2-6',  '2-7', 'S2-8', 'S2-9', '2-8', '2-9', 'S2-10', 'S2-11', 'S2-12', '2-10',
    #           '3-1', '3-2', '3-3',  'S3-1', 'S3-2', '3-4', '3-5', '3-6', '3-7', 'S3-3', '3-8', 'S3-4', 'S3-5',
    #           'S3-6', 'S3-7',
    #           '4-1', '4-2', '4-3', 'S4-1', 'S4-2', 'S4-3', '4-4', '4-5', '4-6', 'S4-4', 'S4-5', 'S4-6', '4-7', '4-8',
    #           '4-9', 'S4-7', 'S4-8', 'S4-9', 'S4-10', '4-10',
    #           '5-1', '5-2', 'S5-1', '5-3', '5-4', '5-5', '5-6', 'S5-3', 'S5-4', '5-7', '5-8', '5-9', 'S5-5', 'S5-6',
    #           'S5-7', 'S5-8', '5-10', 'S5-9',
    #           '6-1', '6-2', '6-3', '6-4', '6-5', '6-6', '6-7', '6-8',  '6-9', '6-10', 'S6-1', 'S6-2', '6-11',
    #           '6-12', '6-13', '6-14', '6-15', 'S6-3', 'S6-4', '6-16', '6-17', '6-18', 'H6-1', 'H6-4',
    #           '7-1', '7-2', '7-3', '7-4', '7-5',  '7-6', '7-7', '7-8', '7-9', '7-10', '7-11', '7-12', '7-13',
    #           '7-14', '7-15', '7-16', 'S7-1', 'S7-2', '7-17', '7-18', '7-19', '7-20',
    #           'R8-1', 'M8-1',  'R8-2', 'M8-2', 'R8-3', 'M8-3', 'R8-4', 'M8-4', 'R8-5', 'M8-5', 'R8-6', 'R8-7',
    #           'R8-8',  'M8-6', 'R8-9', 'M8-7', 'R8-10', 'R8-11', 'M8-8',  'JT8-1', 'JT8-2',
    #           'JT8-3',
    #           'LS-1', 'LS-2', 'LS-3', 'LS-4', 'LS-5',
    #           'CA-1', 'CA-2', 'CA-3', 'CA-4', 'CA-5',
    #           'SK-1', 'SK-2', 'SK-3', 'SK-4', 'SK-5',
    #           'PR-A-1', 'PR-A-2',
    #           'PR-B-1', 'PR-B-2']
    # for stage in stages:
    #     print("Goto " + stage)
    #     navigator.goto_stage(stage)
    # navigator.goto_stage("S4-10")
    # navigator.goto_stage("PR-A-2")
    # navigator.goto_stage("SK-5")
    # navigator.goto_stage("9-15")
    counter = 0
    while True:
        res = battle.start_battle("IW-8")
        if not res:
            time.sleep(180)
        else:
            counter += 1
            print(counter, "Succeeded.")
