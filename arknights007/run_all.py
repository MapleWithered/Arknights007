import time

import matplotlib.pyplot as plt

import arknights007.task as task
from arknights007.adb import ADB
import arknights007.imgreco.template as template
import arknights007.imgreco.imgops as imgops
import arknights007.resource as res
import arknights007.navigator as navigator
import arknights007.imgreco.ocr as ocr
import arknights007.battle as battle
import arknights007.ship as ship


def run_stage(stage: str):
    while True:
        try:
            navigator.goto_stage(stage)
            res = battle.start_battle(stage)
            break
        except RuntimeError:
            return False
    return res


def battle_forever(stage):
    counter = 0
    while True:
        res = run_stage(stage)
        if not res:
            time.sleep(180)
        else:
            counter += 1
            print(counter, "Succeeded.")


if __name__ == '__main__':
    counter = 0
    while True:
        res = run_stage("LE-6")
        if not res:
            ship.run_ship()
            task.run_task()
            time.sleep(3600)
        else:
            counter += 1
            print(counter, "Succeeded.")
