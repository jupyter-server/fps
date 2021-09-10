from fps.config import PluginModel
from fps.hooks import register_config, register_plugin_name


class HelloConfig(PluginModel):
    random: bool = True


c = register_config(HelloConfig)
n = register_plugin_name("helloworld")
