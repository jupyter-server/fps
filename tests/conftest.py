import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pluggy import PluginManager

from fps import hooks
from fps.app import create_app


@pytest.fixture
def config_content():

    yield ""


@pytest.fixture
def config_file(tmp_path, config_content):
    tmp_conf = Path(tmp_path) / "fps.toml"
    os.chdir(tmp_path)

    with open(tmp_conf, "w") as f:
        f.write(config_content)

    yield tmp_conf

    os.remove(tmp_conf)


@pytest.fixture(scope="session")
def plugins():
    yield []


@pytest.fixture
def plugin_manager(plugins, mocker):
    def get_plugin_manager_mock(hook_type: hooks.HookType) -> PluginManager:
        pm = PluginManager(hook_type.value)
        pm.add_hookspecs(hooks)
        for p in plugins:
            pm.register(p)

        return pm

    mocker.patch("fps.app._get_pluggin_manager", side_effect=get_plugin_manager_mock)

    yield


@pytest.fixture
def app(plugin_manager, config_file):
    yield create_app()


@pytest.fixture
def client(app):
    yield TestClient(app)
