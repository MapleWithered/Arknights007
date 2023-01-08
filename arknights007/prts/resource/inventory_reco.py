import json
import os
import time
import typing

import cv2

from . import resource_path
from .online import download_from_multiple_servers
from ..prts_web_client import log, log_v


def _get_inv_reco_data_path(filename: typing.Optional[str] = None) -> str:
    if filename is None:
        return os.path.join(resource_path, 'inventory_reco')
    return os.path.join(resource_path, 'inventory_reco', filename)


def _download_inv_reco_data_from_all_server(filename: str) -> bytes:
    file_url = [
        "https://cdn.jsdelivr.net/gh/MapleWithered/arknights-ml@master/inventory/{}".format(filename),
        "https://raw.fastgit.org/MapleWithered/arknights-ml/master/inventory/{}".format(filename),
        "https://raw.githubusercontent.com/MapleWithered/arknights-ml/master/inventory/{}".format(filename),
    ]
    res = download_from_multiple_servers(file_url)
    return res


def _download_inv_reco_data(filename: str):
    path = _get_inv_reco_data_path(filename)
    res = _download_inv_reco_data_from_all_server(filename)
    with open(path, 'wb') as f:
        f.write(res)


def _update_inv_reco_data_if_necessary():
    index_path = _get_inv_reco_data_path('index_itemid_relation.json')
    net_path = _get_inv_reco_data_path('ark_material.onnx')

    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            local_index = json.load(f)
        if time.time() - local_index.get('down_time', 0) < 3600 * 2:
            return # not need to update
        os.remove(index_path + '.bak')
        os.rename(index_path, index_path + '.bak')
    else:
        local_index = {}

    try:
        _download_inv_reco_data('index_itemid_relation.json')
        with open(index_path, 'r', encoding='utf-8') as f:
            remote_index = json.load(f)
        assert remote_index['time']
        remote_index['down_time'] = time.time()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(remote_index, f, ensure_ascii=False, indent=4)
    except Exception:
        log("更新物品信息失败")
        if os.path.exists(index_path + '.bak'):
            os.rename(index_path + '.bak', index_path)
        return False

    if local_index.get('time', 0) != remote_index['time']:
        log("更新物品识别网络")
        _download_inv_reco_data('ark_material.onnx')
        return True


def _load_net_data():
    index_path = _get_inv_reco_data_path('index_itemid_relation.json')
    net_path = _get_inv_reco_data_path('ark_material.onnx')
    with open(net_path, 'rb') as f:
        data = f.read()
        net = cv2.dnn.readNetFromONNX(data)
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return net, data['idx2id'], data['id2idx'], data['idx2name'], data['idx2type']


def get_item_index():
    _update_inv_reco_data_if_necessary()
    index_path = _get_inv_reco_data_path('index_itemid_relation.json')
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_net_data():
    _update_inv_reco_data_if_necessary()
    return _load_net_data()
