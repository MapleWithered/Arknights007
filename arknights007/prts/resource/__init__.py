import os
import typing

__all__ = ['resource_path', 'get_resource_path', 'game_data_json', 'image', 'yaml', 'navigator', 'online']

resource_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), '../../resources')


def get_resource_path(path: typing.Optional[str] = None) -> str:
    if path is not None:
        return os.path.join(resource_path, path)
    else:
        return resource_path
