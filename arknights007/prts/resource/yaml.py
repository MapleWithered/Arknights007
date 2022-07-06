import functools
import os

from ruamel import yaml as ruamel_yaml

from . import get_resource_path


@functools.lru_cache()
def load_yaml(relative_path: str):
    real_path = get_resource_path(relative_path)
    assert os.path.exists(real_path), '未能检测到yaml文件.'
    with open(real_path, 'r', encoding='utf-8') as f:
        data = ruamel_yaml.load(f.read(), Loader=ruamel_yaml.RoundTripLoader)
    return data
