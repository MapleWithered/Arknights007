import time

from prts import battle, navigator, ship, task

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
        res = run_stage("PR-C-2")
        if not res:
            ship.run_ship()
            task.run_task()
            time.sleep(3600)
        else:
            counter += 1
            print(counter, "Succeeded.")
