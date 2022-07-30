import time
import datetime

from .main_menu import main_menu_reco_sanity
from .navigator import back_to_main_menu
from .planner import run_plan, print_plan_with_plan
from .ship import run_ship
from .friend import run_friend
from .public_recruit import run_public_recruit
from .shopping_center import run_credit_store
from .task import run_task
from .logger import log


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
