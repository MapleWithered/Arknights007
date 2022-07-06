import time

import prts.navigator as navigator
import prts.ship as ship

if __name__ == '__main__':
    while True:
        try:
            ship.run_ship(True)
        except Exception as e:
            navigator.back_to_main_menu()
            ship.run_ship(True)
        time.sleep(900)
    # TODO: Feat. 当有更高优先级时把低优先级的换下来
