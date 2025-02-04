import pytest

from fastaio import Module, get_root_module, initialize, merge_config


def test_config_override():
    class Submodule0(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1
    
    class Submodule1(Module):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.param0 = param0

    class Submodule2(Module):
        def __init__(self, name, param2="param2"):
            super().__init__(name)
            self.add_module(Submodule3, "submodule3", param3="param3*")
            self.param2 = param2

    class Submodule3(Module):
        def __init__(self, name, param3="param3"):
            super().__init__(name)
            self.add_module(Submodule4, "submodule4", param4="param4*")
            self.param3 = param3

    class Submodule4(Module):
        def __init__(self, name, param4="param4"):
            super().__init__(name)
            self.param4 = param4

    class Module0(Module):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0", param0="param0*")
            self.add_module(Submodule1, "submodule1")
            self.add_module(Submodule2, "submodule2", param2="param2*")
            self.param0 = param0

    module0 = Module0("module0", param0="bar")
    initialize(module0)
    initialize(module0)
    assert module0.param0 == "bar"
    assert module0.modules["submodule0"].param0 == "param0*"
    assert module0.modules["submodule0"].param1 == "param1"
    assert module0.modules["submodule1"].param0 == "param0"
    assert module0.modules["submodule2"].param2 == "param2*"
    assert module0.modules["submodule2"].modules["submodule3"].param3 == "param3*"
    assert module0.modules["submodule2"].modules["submodule3"].modules["submodule4"].param4 == "param4*"


def test_config_from_dict():
    class Submodule0(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1
    
    class Submodule1(Module):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.param0 = param0

    class Submodule2(Module):
        def __init__(self, name, param2="param2"):
            super().__init__(name)
            self.add_module(Submodule3, "submodule3")
            self.param2 = param2

    class Submodule3(Module):
        def __init__(self, name, param3="param3"):
            super().__init__(name)
            self.add_module(Submodule4, "submodule4", param4="foo")
            self.param3 = param3

    class Submodule4(Module):
        def __init__(self, name, param4="param4"):
            super().__init__(name)
            self.param4 = param4

    class Module0(Module):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0", param0="foo")
            self.add_module(Submodule1, "submodule1")
            self.add_module(Submodule2, "submodule2")
            self.param0 = param0

    config = {
        "module0": {
            "type": Module0,
            "config": {
                "param0": "bar",
            },
            "modules": {
                "submodule0": {
                    "config": {
                        "param0": "foo2",
                    },
                },
                "submodule1": {
                    "config": {
                        "param0": "baz",
                    },
                },
                "submodule2": {
                    "config": {
                        "param2": "param2*",
                    },
                    "modules": {
                        "submodule3": {
                            "config": {
                                "param3": "param3*",
                            },
                            "modules": {
                                "submodule4": {
                                    "config": {
                                        "param4": "param4*",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }

    module0 = get_root_module(config)
    initialize(module0)
    assert module0.param0 == "bar"
    assert module0.modules["submodule0"].param0 == "foo2"
    assert module0.modules["submodule0"].param1 == "param1"
    assert module0.modules["submodule1"].param0 == "baz"
    assert module0.modules["submodule2"].param2 == "param2*"
    assert module0.modules["submodule2"].modules["submodule3"].param3 == "param3*"
    assert module0.modules["submodule2"].modules["submodule3"].modules["submodule4"].param4 == "param4*"


def test_config_from_dict_with_type_as_str():
    config = {
        "module0": {
            "type": "fastaio:Module",
            "modules": {
                "module0": {
                    "type": "fastaio:Module",
                    "modules": {
                        "module00": {
                            "type": "fastaio:Module",
                        },
                    },
                },
            },
        },
    }

    module0 = get_root_module(config)
    initialize(module0)
    assert module0.modules["module0"].modules["module00"]


def test_wrong_config_from_dict_1():
    class Module0(Module):
        pass

    config = {
        "module0": {
            "type": Module0,
            "modules": {
                "submodule0": {
                    "config": {
                        "param0": "foo",
                    },
                },
            },
        },
    }

    module0 = get_root_module(config)

    with pytest.raises(RuntimeError) as excinfo:
        initialize(module0)

    assert str(excinfo.value) == "Module not found: submodule0"


def test_wrong_config_from_dict_2():
    class Submodule0(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Module0(Module):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0", param0="foo")

    config = {
        "module0": {
            "type": Module0,
            "modules": {
                "submodule0": {
                    "config": {
                        "param0": "foo",
                    },
                    "modules": {
                        "submodule1": {
                            "config": {
                                "param1": "bar",
                            },
                        },
                    },
                },
            },
        },
    }

    module0 = get_root_module(config)

    with pytest.raises(RuntimeError) as excinfo:
        initialize(module0)

    assert str(excinfo.value) == "Module not found: submodule1"


def test_config_from_dict_add_submodules():
    class Submodule0(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Submodule1(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Submodule10(Module):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Module0(Module):
        pass

    config = {
        "module0": {
            "type": Module0,
            "modules": {
                "submodule0": {
                    "type": Submodule0,
                    "config": {
                        "param0": "foo",
                    },
                },
                "submodule1": {
                    "type": Submodule1,
                    "config": {
                        "param1": "bar",
                    },
                    "modules": {
                        "submodule10": {
                            "type": Submodule10,
                            "config": {
                                "param0": "baz",
                             },
                        },
                    },
                },
            },
        },
    }

    module0 = get_root_module(config)
    initialize(module0)
    assert list(module0.modules.keys()) == ["submodule0", "submodule1"]
    assert list(module0.modules["submodule0"].modules.keys()) == []
    assert list(module0.modules["submodule1"].modules.keys()) == ["submodule10"]
    assert list(module0.modules["submodule1"].modules["submodule10"].modules.keys()) == []
    assert module0.modules["submodule0"].param0 == "foo"
    assert module0.modules["submodule0"].param1 == "param1"
    assert module0.modules["submodule1"].param0 == "param0"
    assert module0.modules["submodule1"].param1 == "bar"
    assert module0.modules["submodule1"].modules["submodule10"].param0 == "baz"
    assert module0.modules["submodule1"].modules["submodule10"].param1 == "param1"


def test_merge_config():
    d0 = {
        "module0": {
            "type": "Module0",
            "config": {
                "param0": 0,
                "param1": 1,
            },
            "modules": {
                "module1": {
                    "type": "Module1",
                    "modules": {
                        "module2": {
                            "type": "Module2",
                            "config": {
                                "param2": 2,
                                "param3": 3,
                            }
                        }
                    }
                }
            }
        }
    }

    d1 = {
        "module0": {
            "config": {
                "param1": 11,
            },
            "modules": {
                "module1": {
                    "modules": {
                        "module2": {
                            "config": {
                                "param2": 22,
                            },
                        },
                        "module3": {
                            "type": "Module3",
                            "config": {
                                "param4": 4,
                            }
                        }
                    }
                }
            }
        }
    }

    d = merge_config(d0, d1)
    assert d == {
        "module0": {
            "type": "Module0",
            "config": {
                "param0": 0,
                "param1": 11,
            },
            "modules": {
                "module1": {
                    "type": "Module1",
                    "modules": {
                        "module2": {
                            "type": "Module2",
                            "config": {
                                "param2": 22,
                                "param3": 3,
                            }
                        },
                        "module3": {
                            "type": "Module3",
                            "config": {
                                "param4": 4,
                            }
                        }
                    }
                }
            }
        }
    }
