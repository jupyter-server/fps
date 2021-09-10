from fps.config import PluginModel
from fps.config import get_config as fps_get_config
from fps.hooks import register_config, register_plugin_name


class HelloConfig(PluginModel):
    random: bool = False
    greeting: str = "hello"
    count: int = 0


def get_config():
    return fps_get_config(HelloConfig)


c = register_config(HelloConfig)
n = register_plugin_name("helloworld")
