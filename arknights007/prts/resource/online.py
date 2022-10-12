import typing

import requests

import queue
from threading import Thread


# noinspection PyBroadException
from ..prts_web_client import log_v


def download_url_to_bytes(url: str) -> typing.Optional[bytes]:
    try:
        resp = requests.get(url)
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    return resp.content


def download_from_multiple_servers(urls: typing.List[str]) -> typing.Optional[bytes]:
    que = queue.Queue(maxsize=len(urls))
    threads_list = []

    for url in urls:
        t = Thread(target=lambda q, arg1: q.put(download_url_to_bytes(arg1)), args=(que, url))
        t.start()
        threads_list.append(t)

    res = None
    while res is None:
        res = que.get()
    return res
