from prts.resource import game_data_json

from prts import navigator
from prts.resource.image import get_img_path

from prts.resource.ship_skills import download_icons
from prts.ship_skill import reco_skills

if __name__ == '__main__':
    download_icons()
    reco_skills(True)