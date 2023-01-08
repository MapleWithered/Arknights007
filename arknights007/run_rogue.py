
from prts.rogue.mizuki.run import *
from prts.rogue.general import *

import time

if __name__ == '__main__':
    count = 0
    first_time = time.time()
    last_time = time.time()
    while True:
        run('mizuki')
        count += 1
        print(f"Ran {count} times. last run {time.time() - last_time} s. avg {(time.time() - first_time) / count} s.")
        last_time = time.time()

