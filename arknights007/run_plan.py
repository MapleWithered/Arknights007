import time

from prts.planner import load_inventory, run_plan, print_plan_with_plan

from prts.resource.navigator import get_stage_info_and_map, get_stage_sanity_cost
from prts.navigator import back_to_main_menu, is_main_menu
from prts.ship import run_ship, handle_drone
from prts.task import run_task

from prts.main_menu import main_menu_reco_sanity
import datetime

if __name__ == '__main__':
    next_round_sanity = 0
    back_to_main_menu()
    time_target = 0
    while True:
        while time.time() < time_target:
            time.sleep(5)
        next_round_sanity = run_plan()
        time_target = time.time() + (next_round_sanity - main_menu_reco_sanity(force=True)) * 360
        # print time.time()+time_sleep as HH:MM
        print("\n"*20)
        print_plan_with_plan()
        print(f"将在{datetime.datetime.fromtimestamp(time_target).strftime('%H:%M')}继续刷图")
        run_ship()
        run_task()