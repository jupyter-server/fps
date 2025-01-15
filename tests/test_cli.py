from click.testing import CliRunner
from fastaio import Component, get_config, main


def test_wrong_cli():
    runner = CliRunner()
    runner.invoke(main, [
        "fastaio.Component",
        "--set", "param",
        ])

def test_cli():
    runner = CliRunner()
    runner.invoke(main, [
        "fastaio.Component",
        "--set", "param=-1",
        "--set", "component0.param0=foo",
        "--set", "component1.param1=bar",
        "--set", "component2.param2=baz",
        "--set", "component2.component3.param3=123",
        ]
    )
    assert get_config() == {
        "root_component": {
            "type": Component,
            "config": {
                "param": "-1"
            },
            "components": {
                "component0": {
                    "config": {
                        "param0": "foo"
                    }
                },
                "component1": {
                    "config": {
                        "param1": "bar"
                    }
                },
                "component2": {
                    "config": {
                        "param2": "baz"
                    },
                    "components": {
                        "component3": {
                            "config": {
                                "param3": "123"
                            }
                        }
                    }
                }
            }
        }
    }
