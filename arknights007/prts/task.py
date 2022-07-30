import time

from . import main_menu as main_menu
from . import navigator as navigator


def main_to_task():
    navigator.press_std_rect("/main_menu/task")
    time.sleep(1)


def press_weekly_button():
    navigator.press_std_rect("/task/weekly")
    time.sleep(1)


def check_and_get_all_reward():
    navigator.press_std_rect("/task/get_all")


def run_task():
    navigator.back_to_main_menu()
    if main_menu.main_check_task_remain():
        main_to_task()
        check_and_get_all_reward()
        navigator.handle_reward_scene()
        press_weekly_button()
        check_and_get_all_reward()
        navigator.handle_reward_scene()
        navigator.back_to_main_menu()


if __name__ == '__main__':
    run_task()
