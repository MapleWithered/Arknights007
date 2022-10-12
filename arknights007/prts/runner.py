import time
import datetime

import ruamel.yaml as yaml

from .config import get_config_path
from .main_menu import main_menu_reco_sanity
from .navigator import back_to_main_menu
from .planner import run_plan, print_plan_with_plan
from .ship import run_ship
from .friend import run_friend
from .public_recruit import run_public_recruit
from .shopping_center import run_credit_store
from .task import run_task
from .prts_web_client import PRTSSocketClient, PRTSHTTPClient, log

def run_all():
    PRTSSocketClient.connect()
    next_round_sanity = 0
    back_to_main_menu()
    time_target = 0
    while True:
        while time.time() < time_target:
            time.sleep(5)
        log("<br>"*20)
        log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%m/%d %H:%M:%S')} - 开始执行任务计划")
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['plan']:
            config_path = get_config_path('runner.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f.read(), Loader=yaml.RoundTripLoader)
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始刷图")
            reserve_sanity = eval(str(config.get('reserve_sanity', 0)), {'next_round_sanity': next_round_sanity})
            next_round_sanity = run_plan(reserve_sanity)
            single_run_sanity = eval(str(config.get('single_run_sanity', 0)), {'next_round_sanity': next_round_sanity})
            next_run_sanity = reserve_sanity
            while next_run_sanity < reserve_sanity + single_run_sanity:
                next_run_sanity += next_round_sanity
            time_target = time.time() + (next_run_sanity - main_menu_reco_sanity(force=True)) * 360
            # print time.time()+time_sleep as HH:MM
            # log("\n" * 20)
            print_plan_with_plan()
        else:
            time_target = time.time() + 10800
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['ship']:
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始收基建")
            run_ship()
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['friend']:
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始访问好友")
            run_friend()
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['credit_store']:
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始收信用")
            run_credit_store()
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['public_recruit']:
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始公招")
            run_public_recruit()
        runner_task = PRTSHTTPClient.get("/api/v1/runner_task").json()
        if runner_task['task']:
            log(f"{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')} 开始收任务")
            run_task()
        log(f"将在{datetime.datetime.fromtimestamp(time_target).strftime('%H:%M')}继续下一次执行")