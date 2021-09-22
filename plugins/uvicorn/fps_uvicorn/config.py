from fps.config import PluginModel
from fps.hooks import register_config, register_plugin_name


class UvicornConfig(PluginModel):
    # uvicorn server
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 0

    # custom CLI options
    open_browser: bool = False


c = register_config(UvicornConfig)
n = register_plugin_name("uvicorn")
