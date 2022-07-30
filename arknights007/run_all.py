import os
import sys
import time

from prts.resource.image import get_img_path
from prts import navigator
from prts.planner import load_inventory, run_plan, print_plan_with_plan

from prts.resource.navigator import get_stage_info_and_map, get_stage_sanity_cost
from prts.navigator import back_to_main_menu, is_main_menu, record_play
from prts.ship import run_ship, handle_drone
from prts.task import run_task
from prts.friend import run_friend
from prts.public_recruit import run_public_recruit
from prts.shopping_center import run_credit_store
from prts.main_menu import main_menu_reco_sanity
from prts.logger import log
import datetime


def run_all():
    next_round_sanity = 0
    back_to_main_menu()
    time_target = 0
    while True:
        while time.time() < time_target:
            time.sleep(5)
        next_round_sanity = run_plan()
        time_target = time.time() + (next_round_sanity - main_menu_reco_sanity(force=True)) * 360
        # print time.time()+time_sleep as HH:MM
        log("\n" * 20)
        print_plan_with_plan()
        log(f"将在{datetime.datetime.fromtimestamp(time_target).strftime('%H:%M')}继续刷图")
        run_ship()
        run_friend()
        run_credit_store()
        run_public_recruit()
        run_task()


if __name__ == '__main__':
    try:
        run_all()
    except KeyboardInterrupt:
        print('Exiting')
        record_play(get_img_path('/common_record/release.yaml'), no_delay=True)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
