from fps.config import PluginModel
from fps.hooks import register_config, register_plugin_name


class DashboardConfig(PluginModel):
    foo: bool = False


c = register_config(DashboardConfig)
n = register_plugin_name("dashboard")
