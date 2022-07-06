import os
import typing

config_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), '../../config')

__all__ = ['config_path', 'get_config_path', 'yaml']


def get_config_path(path: typing.Optional[str] = None) -> str:
    if path is not None:
        return os.path.join(config_path, path)
    else:
        return config_path
