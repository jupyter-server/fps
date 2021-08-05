import logging
import os
from collections import OrderedDict
from types import ModuleType
from typing import Dict, List, Tuple, Type

import toml
from pydantic import BaseModel

import fps
from fps.errors import ConfigError
from fps.utils import get_plugin_name


class PluginModel(BaseModel):
    enabled: bool = True


class FPSConfig(BaseModel):
    # fastapi
    title: str = "FPS"
    version: str = fps.__version__
    description: str = "A fast plugins server"

    # uvicorn server
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 0

    # custom options
    open_browser: bool = False


logger = logging.getLogger("fps")


class Config:

    _models: Dict[Type[PluginModel], Tuple[ModuleType, PluginModel]] = {}
    _based_on: Dict[Type[PluginModel], List[str]] = {}
    _obj: dict = None
    _files: Dict[str, dict] = {}
    _names: dict = {}

    def __new__(cls, plugin_model: Type[PluginModel], file: str = None) -> PluginModel:
        try:
            return cls._models[plugin_model][1]
        except KeyError:
            logger.error(f"Plugin config model {plugin_model} is not yet registered")
            exit(1)

    @classmethod
    def register(
        cls,
        plugin: ModuleType,
        plugin_model: Type[PluginModel],
        force_update: bool = False,
    ):
        config_objs: List[dict] = []
        plugin_name = cls.plugin_name(plugin)
        files = cls.find_files(plugin_name)

        # parse files is not yet done
        for f in files:
            if f not in cls._files:
                cls._files[f] = cls.read_file(f)

        # all possible objects containing config for plugin
        config_objs = [cls._files[f] for f in files]

        # check the relevant file for plugin and compute the merged values
        if config_objs:
            relevant_files = [
                f
                for i, f in enumerate(files)
                if plugin_name in cls._files[f] and cls._files[f][plugin_name]
            ]
            config_obj = {
                k: v
                for f in relevant_files
                for k, v in cls._files[f][plugin_name].items()
            }
        else:
            relevant_files = []
            config_obj = {}

        # update the config if new files are detected
        update = cls._based_on.get(plugin_model, []) != relevant_files

        # compute/update config if necessary
        if plugin_model not in cls._models or update or force_update:
            if config_obj:
                config = plugin_model.parse_obj(config_obj)
            else:
                config = plugin_model()

            cls._models[plugin_model] = (plugin, config)
            cls._based_on[plugin_model] = relevant_files

    @classmethod
    def update(cls, force: bool = False):
        for model, (plugin, _) in cls._models.items():
            cls.register(plugin, model, force_update=force)

    @staticmethod
    def read_file(config_file: str = None):
        path = os.path.abspath(config_file)

        with open(path) as f:
            try:
                return dict(toml.load(f))
            except toml.TomlDecodeError as e:
                raise ConfigError(f"Failed to load config file '{path}': {e}.")

    @staticmethod
    def find_files(plugin_name: str):
        ext = ".toml"
        config_files = [f + ext for f in ("fps", plugin_name)]

        if "FPS_CONFIG_FILE" in os.environ:
            config_files.append(os.environ["FPS_CONFIG_FILE"])

        config_files = list(OrderedDict.fromkeys(config_files))

        return [f for f in config_files if f and os.path.isfile(f)]

    @classmethod
    def register_plugin_name(cls, plugin, name: str):
        cls._names[plugin] = name

    @classmethod
    def plugin_name(cls, plugin: ModuleType) -> str:
        if plugin in cls._names:
            return cls._names[plugin]
        else:
            return get_plugin_name(plugin)

    @classmethod
    @property
    def plugins_names(cls) -> List[str]:
        return list(cls._names.values())
