import pluggy
import pytest
from pydantic import ValidationError

from fps.app import create_app
from fps.config import Config, FPSConfig, PluginModel
from fps.errors import ConfigError
from fps.hooks import HookType


def hookimpl_pluginname(func):
    return pluggy.HookimplMarker(HookType.CONFIG.value)(specname="plugin_name")(func)


def hookimpl_config(func):
    return pluggy.HookimplMarker(HookType.CONFIG.value)(specname="config")(func)


def test_forbid_extras(config_file, plugin_manager):

    with open(config_file, "w") as f:
        f.write("[fps]\nsome_extra = 'extra'")

    with pytest.raises(ValidationError) as exc_info:
        create_app()

    expected = [
        {
            "loc": ("some_extra",),
            "msg": "extra fields not permitted",
            "type": "value_error.extra",
        }
    ]
    assert exc_info.value.errors() == expected


class Plugin1:
    @staticmethod
    @hookimpl_pluginname
    def plugin_name():
        return "some-plugin"


class Plugin2:
    @staticmethod
    @hookimpl_pluginname
    def plugin_name():
        return "my-plugin"


@pytest.mark.parametrize(
    "plugins",
    (
        [
            Plugin1(),
        ],
    ),
)
def test_plugin_names(app, plugins):

    assert len(Config._plugin2name) == len(plugins)
    assert Config._plugin2name == {plugins[0]: "some-plugin"}

    assert len(Config._pkg2name) == 1
    assert Config._pkg2name == {"tests": "some-plugin"}

    assert Config.plugin_name(plugins[0]) == "some-plugin"


@pytest.mark.parametrize("plugins", ([Plugin1(), Plugin2()],))
def test_plugin_package_name_redefinition(plugin_manager):
    with pytest.raises(ConfigError):
        create_app()


class MultipleNamesPlugin:
    @staticmethod
    @hookimpl_pluginname
    def plugin_name():
        return "some-plugin"

    @staticmethod
    @hookimpl_pluginname
    def plugin_name2():
        return "other-plugin"


@pytest.mark.parametrize(
    "plugins",
    (
        [
            MultipleNamesPlugin(),
        ],
    ),
)
def test_plugin_name_redefinition(plugin_manager):
    with pytest.raises(ConfigError):
        create_app()


class TestConfigFiles:
    class Plugin3:
        class Plugin3Config(PluginModel):
            count: int = 0

        @classmethod
        @hookimpl_config
        def plugin_config(cls):

            return cls.Plugin3Config

    @staticmethod
    @pytest.fixture
    def fps_only_config():
        yield "[fps]\ndescription = 'foo'"

    @staticmethod
    @pytest.fixture
    def plugin_config():
        yield "[tests]\ncount = '10'"

    @pytest.mark.parametrize(
        "plugins",
        (
            [
                Plugin3(),
            ],
        ),
    )
    def test_no_file(self, app, config_file, plugins):

        assert self.Plugin3.Plugin3Config in Config._models
        assert Config._models[self.Plugin3.Plugin3Config] == (
            "tests",
            self.Plugin3.Plugin3Config(),
        )

        assert len(Config._models) == 2
        assert FPSConfig in Config._models

        assert len(Config._based_on[self.Plugin3.Plugin3Config]) == 0
        assert len(Config._based_on[FPSConfig]) == 0

    @pytest.mark.parametrize(
        "plugins",
        (
            [
                Plugin3(),
            ],
        ),
    )
    @pytest.mark.parametrize(
        "config_content", (pytest.lazy_fixture(("fps_only_config",)))
    )
    def test_fps_config(self, app, plugins, config_file, config_content):

        assert self.Plugin3.Plugin3Config in Config._models
        assert Config._models[self.Plugin3.Plugin3Config] == (
            "tests",
            self.Plugin3.Plugin3Config(),
        )

        assert len(Config._models) == 2
        assert FPSConfig in Config._models

        assert len(Config._based_on[self.Plugin3.Plugin3Config]) == 0

        assert len(Config._based_on[FPSConfig]) == 1
        assert Config._based_on[FPSConfig][0] == str(config_file)
        assert Config(FPSConfig).description == "foo"

    @pytest.mark.parametrize(
        "plugins",
        (
            [
                Plugin3(),
            ],
        ),
    )
    @pytest.mark.parametrize(
        "config_content", (pytest.lazy_fixture(("plugin_config",)))
    )
    def test_plugin_config(self, app, plugins, config_file, config_content):

        assert self.Plugin3.Plugin3Config in Config._models
        assert Config._models[self.Plugin3.Plugin3Config] == (
            "tests",
            self.Plugin3.Plugin3Config(count=10),
        )

        assert len(Config._models) == 2
        assert FPSConfig in Config._models

        assert len(Config._based_on[self.Plugin3.Plugin3Config]) == 1
        assert Config._based_on[self.Plugin3.Plugin3Config][0] == str(config_file)
        assert Config(self.Plugin3.Plugin3Config).count == 10

        assert len(Config._based_on[FPSConfig]) == 0
