import adb
import navigator


def run_stage(stage: str):
    navigator.goto_stage()
    navigator.run_once()


if __name__ == '__main__':
    ...
