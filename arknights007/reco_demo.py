from prts.resource import game_data_json

from prts import navigator
from prts.resource.image import get_img_path

from prts.resource.ship_skills import download_icons
from prts.ship_skill import reco_skills
from prts.imgreco.inventory import reco as inventory_reco

if __name__ == '__main__':
    inventory_reco.get_all_item_details_in_screen()