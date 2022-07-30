from typing import Optional
from enum import Enum
from multiprocessing import Process

from .runner import *


class Status(Enum):
    IDLE = 1
    RUN_PLAN = 2
    RUN_SHIP = 3
    RUN_FRIEND = 4
    RUN_CREDIT_STORE = 5
    RUN_PUB_RECRUIT = 6
    RUN_TASK = 7
    RUN_ALL = 888


status_code: int = 0


class PRTSDaemon:
    _prts_process: Optional[Process] = None
    _status_code: Status = Status.IDLE

    @classmethod
    def get_status(cls):
        if cls._prts_process is None:
            cls._status_code = Status.IDLE
            return Status.IDLE
        if not cls._prts_process.is_alive():
            cls._status_code = Status.IDLE
            return Status.IDLE
        return cls._status_code

    @classmethod
    def kill_process(cls) -> int:
        if cls._prts_process is None:
            return 1
        if not cls._prts_process.is_alive():
            return 1

        cls._prts_process.kill()
        cls._prts_process.join()
        cls._prts_process = None
        cls._status_code = Status.IDLE

        return 0

    @classmethod
    def run_plan(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_PLAN
        cls._prts_process = Process(target=run_plan)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_ship(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_SHIP
        cls._prts_process = Process(target=run_ship)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_friend(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_FRIEND
        cls._prts_process = Process(target=run_friend)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_credit_store(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_CREDIT_STORE
        cls._prts_process = Process(target=run_credit_store)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_public_recruit(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_PUB_RECRUIT
        cls._prts_process = Process(target=run_public_recruit)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_task(cls) -> int:
        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_TASK
        cls._prts_process = Process(target=run_task)
        cls._prts_process.start()

        return 0

    @classmethod
    def run_all(cls) -> int:        # Temp

        if cls.get_status() != Status.IDLE:
            return -1

        cls._status_code = Status.RUN_ALL
        cls._prts_process = Process(target=run_all)
        cls._prts_process.start()

        return 0
