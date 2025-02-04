from click.testing import CliRunner
from fastaio import Module, get_config, main


def test_wrong_cli_1():
    runner = CliRunner()
    result = runner.invoke(main, [
        "fastaio:Module",
        "--set", "param",
    ])
    assert result.exit_code == 1

def test_wrong_cli_2():
    runner = CliRunner()
    result = runner.invoke(main, [
        "fastaio.Module",
    ])
    assert result.exit_code == 1

def test_wrong_cli_3():
    runner = CliRunner()
    result = runner.invoke(main, [
        "fastaio:WrongModule",
    ])
    assert result.exit_code == 1

def test_wrong_cli_4():
    runner = CliRunner()
    result = runner.invoke(main, [
        "wrong_module:Module",
    ])
    assert result.exit_code == 1

def test_cli():
    runner = CliRunner()
    runner.invoke(main, [
        "fastaio_module",
        "--set", "param=-1",
        "--set", "module0.param0=foo",
        "--set", "module1.param1=bar",
        "--set", "module2.param2=baz",
        "--set", "module2.module3.param3=123",
        ]
    )
    assert get_config() == {
        "root_module": {
            "type": Module,
            "config": {
                "param": "-1"
            },
            "modules": {
                "module0": {
                    "config": {
                        "param0": "foo"
                    }
                },
                "module1": {
                    "config": {
                        "param1": "bar"
                    }
                },
                "module2": {
                    "config": {
                        "param2": "baz"
                    },
                    "modules": {
                        "module3": {
                            "config": {
                                "param3": "123"
                            }
                        }
                    }
                }
            }
        }
    }
