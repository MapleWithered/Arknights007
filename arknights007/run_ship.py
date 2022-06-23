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


if __name__ == '__main__':
    while True:
        try:
            ship.run_ship(True)
        except Exception as e:
            navigator.back_to_main_menu()
            ship.run_ship(True)
        time.sleep(900)
    # TODO: Feat. 当有更高优先级时把低优先级的换下来
