import json

import fps
from click.testing import CliRunner
from fps import Module, get_config, main


class UselessModule(Module):
    async def start(self):
        self.exit_app()


def test_wrong_cli_1():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "fps:Module",
            "--set",
            "param",
        ],
    )
    assert result.exit_code == 1


def test_wrong_cli_2():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "fps.Module",
        ],
    )
    assert result.exit_code == 1


def test_wrong_cli_3():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "fps:WrongModule",
        ],
    )
    assert result.exit_code == 1


def test_wrong_cli_4():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "wrong_module:Module",
        ],
    )
    assert result.exit_code == 1


def test_cli():
    runner = CliRunner()
    fps._cli.TEST = True
    result = runner.invoke(
        main,
        [
            "fps_module",
            "--set",
            "param=-1",
            "--set",
            "module0.param0=foo",
            "--set",
            "module1.param1=bar",
            "--set",
            "module2.param2=baz",
            "--set",
            "module2.module3.param3=123",
        ],
    )
    assert result.exit_code == 0
    config = get_config()
    fps._cli.TEST = False
    assert config == {
        "root_module": {
            "type": Module,
            "config": {"param": "-1"},
            "modules": {
                "module0": {"config": {"param0": "foo"}},
                "module1": {"config": {"param1": "bar"}},
                "module2": {
                    "config": {"param2": "baz"},
                    "modules": {"module3": {"config": {"param3": "123"}}},
                },
            },
        }
    }


def test_cli_with_config_file(tmp_path):
    config_dict = {
        "root_module": {
            "type": "fps_module",
            "config": {"param": 3},
            "modules": {
                "module0": {
                    "type": "fps_module",
                    "config": {
                        "param0": 0,
                        "param1": 1,
                    },
                },
            },
        },
    }
    with (tmp_path / "config.json").open("w") as f:
        json.dump(config_dict, f)

    runner = CliRunner()
    fps._cli.TEST = True
    result = runner.invoke(
        main,
        [
            "--config",
            str(tmp_path / "config.json"),
            "--set",
            "module0.param1=foo",
            "--set",
            "param=bar",
        ],
    )
    assert result.exit_code == 0
    config = get_config()
    fps._cli.TEST = False
    assert config == {
        "root_module": {
            "type": "fps_module",
            "config": {"param": "bar"},
            "modules": {
                "module0": {
                    "type": "fps_module",
                    "config": {
                        "param0": 0,
                        "param1": "foo",
                    },
                },
            },
        }
    }


def test_cli_with_config_file_and_module(tmp_path):
    config_dict = {
        "root_module": {
            "type": "fps_module",
            "config": {"param": 3},
            "modules": {
                "module0": {
                    "type": "fps_module",
                    "config": {
                        "param0": 0,
                        "param1": 1,
                    },
                },
            },
        },
    }
    with (tmp_path / "config.json").open("w") as f:
        json.dump(config_dict, f)

    runner = CliRunner()
    fps._cli.TEST = True
    result = runner.invoke(
        main,
        [
            "root_module",
            "--config",
            str(tmp_path / "config.json"),
            "--set",
            "module0.param1=foo",
            "--set",
            "param=bar",
        ],
    )
    assert result.exit_code == 0
    config = get_config()
    fps._cli.TEST = False
    assert config == {
        "root_module": {
            "type": "fps_module",
            "config": {"param": "bar"},
            "modules": {
                "module0": {
                    "type": "fps_module",
                    "config": {
                        "param0": 0,
                        "param1": "foo",
                    },
                },
            },
        }
    }


def test_cli_run_module():
    fps._cli.TEST = False
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "test_cli:UselessModule",
        ],
    )
    assert result.exit_code == 0
