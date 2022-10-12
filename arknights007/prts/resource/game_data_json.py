import json
import os
import typing

from . import resource_path
from .online import download_from_multiple_servers
from ..prts_web_client import log, log_v


def _download_game_data_from_all_server(filename: str) -> bytes:
    file_url = [
        "https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel/FILENAME",
        "https://raw.fastgit.org/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/FILENAME",
        "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/FILENAME"
    ]

    for i in range(len(file_url)):
        file_url[i] = file_url[i].replace("FILENAME", filename)

    res = download_from_multiple_servers(file_url)
    return res


def _get_game_data_path(filename: typing.Optional[str] = None) -> str:
    if filename is None:
        return os.path.join(resource_path, 'game_data')
    return os.path.join(resource_path, 'game_data', filename)


def _download_game_data(filename: str):
    path = _get_game_data_path(filename)
    res = _download_game_data_from_all_server(filename)
    with open(path, 'wb') as f:
        f.write(res)


def _get_game_data_latest_version():
    res = _download_game_data_from_all_server("data_version.txt").decode("utf-8")
    date_str = res[res.find("on ") + 3: res.find("\nVersionControl")].replace("/", '')
    version_str = res[res.find("VersionControl:") + 15:].replace("\n", '').strip()
    return {'version': version_str, 'date': date_str}


def _get_game_data_local_version():
    filepath = _get_game_data_path("data_version.txt")
    if not os.path.exists(filepath):
        return {'version': None, 'date': None}
    with open(filepath, 'r', encoding='utf-8') as f:
        res = f.read().strip()
        date_str = res[res.find("on ") + 3: res.find("\nVersionControl")].replace("/", '')
        version_str = res[res.find("VersionControl:") + 15:].replace("\n", '').strip()
        return {'version': version_str, 'date': date_str}


def update_all_game_data():
    log("更新游戏数据JSON中...")
    for filename in os.listdir(_get_game_data_path()):
        if filename.endswith(".json") or filename.endswith("data_version.txt"):
            log_v(filename, end=" ")
            _download_game_data(filename)
            log_v("✅")
    _download_game_data("data_version.txt")
    log("更新完成")


def get_game_data_dict(filename: str, force_update=False):
    filepath = _get_game_data_path(filename)
    if not os.path.exists(filepath):
        log(f"游戏数据JSON文件{filename}不存在, 尝试下载...")
        _download_game_data(filename)
    if force_update:
        update_all_game_data()
    if _get_game_data_local_version() != _get_game_data_latest_version():
        log("游戏数据JSON已过时")
        update_all_game_data()
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
