from fps.config import PluginModel
from fps.hooks import register_config


class HelloConfig(PluginModel):
    random: bool = True


c = register_config(HelloConfig)
