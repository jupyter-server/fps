import logging
import os
from collections import OrderedDict
from types import ModuleType
from typing import Any, Dict, List, Tuple, Type

import toml
from pydantic import BaseModel, create_model, validator

import fps
from fps.errors import ConfigError
from fps.utils import get_pkg_name, get_plugin_name

logger = logging.getLogger("fps")


class PluginModel(BaseModel):
    enabled: bool = True

    class Config:
        extra = "forbid"


def create_default_plugin_model(plugin_name: str):
    return create_model(f"{plugin_name}Model", __base__=PluginModel)


class MiddlewareModel(BaseModel):
    class_path: str
    kwargs: Dict[str, Any] = {}


class FPSConfig(BaseModel):
    # fastapi
    title: str = "FPS"
    version: str = fps.__version__
    description: str = "A fast plugins server"

    # plugins
    enabled_plugins: List[str] = []
    disabled_plugins: List[str] = []

    # plugin middlewares
    middlewares: List[MiddlewareModel] = []

    @validator("enabled_plugins", "disabled_plugins")
    def plugins_format(cls, plugins):
        warnings = [p for p in plugins if p.startswith("[") or p.endswith("]")]
        if warnings:
            logger.warning(
                f"Enabled or disabled plugins {warnings} include list delimiter(s), "
                "it could be due to bad configuration"
            )
        return plugins

    class Config:
        extra = "forbid"


class Config:

    _models: Dict[Type[PluginModel], Tuple[str, PluginModel]] = {}
    _based_on: Dict[Type[PluginModel], List[str]] = {}
    _files: Dict[str, dict] = {}
    _plugin2name: Dict[ModuleType, str] = {}
    _pkg2name: Dict[str, str] = {}

    def __new__(cls, plugin_model: Type[PluginModel]) -> PluginModel:
        try:
            return cls._models[plugin_model][1]
        except KeyError:
            logger.error(f"Config model '{plugin_model}' is not yet registered")
            exit(1)

    @classmethod
    def register(
        cls,
        config_name: str,
        config_model: Type[PluginModel],
        force_update: bool = False,
    ):
        config_objs: List[dict] = []
        files = cls.find_files(config_name)

        # parse files if not yet done
        for f in files:
            if f not in cls._files:
                cls._files[f] = cls.read_file(f)

        # all possible objects containing config for plugin
        config_objs = [cls._files[f] for f in files]

        # check the relevant files for plugin and compute the merged values
        if config_objs:
            relevant_files = [
                f
                for f in files
                if config_name in cls._files[f] and cls._files[f][config_name]
            ]
            config_obj = {
                k: v
                for f in relevant_files
                for k, v in cls._files[f][config_name].items()
            }
        else:
            relevant_files = []
            config_obj = {}

        # update the config if new files are detected
        update = cls._based_on.get(config_model, []) != relevant_files

        # compute/update config if necessary
        if config_model not in cls._models or update or force_update:
            if config_obj:
                config = config_model.parse_obj(config_obj)
            else:
                config = config_model()

            cls._models[config_model] = (config_name, config)
            cls._based_on[config_model] = relevant_files

    @classmethod
    def check_not_used_sections(cls):
        all_config_sections = {k for f in cls._files.values() for k in f}
        all_plugins_names = {n for n in cls._plugin2name.values()}
        all_plugins_names.add("fps")

        not_used = {n for n in all_config_sections if n not in all_plugins_names}
        if not_used:
            logger.warning(
                f"Configuration section(s) are not used by any plugin {not_used}"
            )

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
    def find_files(config_name: str):
        ext = ".toml"
        config_files = [f + ext for f in ("fps", config_name)]

        # file define by user in env variable 'FPS_CONFIG_FILE'
        if "FPS_CONFIG_FILE" in os.environ:
            config_files.append(os.environ["FPS_CONFIG_FILE"])

        # file passed by user as a CLI argument '--config'
        if "FPS_EXTRA_CONFIG_FILE" in os.environ:
            config_files.append(os.environ["FPS_EXTRA_CONFIG_FILE"])

        # file generated by the CLI from extra args
        if "FPS_CLI_CONFIG_FILE" in os.environ:
            config_files.append(os.environ["FPS_CLI_CONFIG_FILE"])

        config_files = list(OrderedDict.fromkeys(config_files))

        return [os.path.abspath(f) for f in config_files if f and os.path.isfile(f)]

    @classmethod
    def register_plugin_name(
        cls,
        plugin: ModuleType,
        name: str = None,
    ):
        plugin_name = get_plugin_name(plugin)
        pkg = get_pkg_name(plugin, strip_fps=False)

        if not name:
            if pkg in cls._pkg2name:
                name = cls._pkg2name[pkg]
                logger.debug(f"Re-using plugins package name '{name}'")
            else:
                name = get_pkg_name(plugin, strip_fps=True)
                logger.debug(f"Using default name '{name}' for plugins package '{pkg}'")
        else:
            if pkg not in cls._pkg2name:
                logger.info(f"Registering name '{name}' for plugins package '{pkg}'")
                cls._pkg2name[pkg] = name
            else:
                raise ConfigError

        logger.debug(f"Registering name '{name}' for plugin '{plugin_name}'")
        cls._plugin2name[plugin] = name

        return name

    @classmethod
    def plugin_name(cls, plugin: ModuleType) -> str:
        try:
            return cls._plugin2name[plugin]
        except KeyError:
            return cls.register_plugin_name(plugin)

    @classmethod
    def from_name(cls, plugin_name):
        configs = [c for n, c in cls._models.values() if n == plugin_name]

        if len(configs) == 0:
            return None
        elif len(configs) == 1:
            return configs[0]
        else:
            raise ValueError("Conflict: same name declared in multiple plugins")

    @classmethod
    def clear_names(cls):
        cls._plugin2name.clear()
        cls._pkg2name.clear()

    @classmethod
    def clear_models(cls):
        cls._models.clear()
        cls._based_on.clear()
        cls._files.clear()


def get_config(model: Type[PluginModel]) -> PluginModel:
    return Config(model)
