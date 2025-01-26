import pytest

from fastaio import Component, get_root_component, initialize


def test_config_override():
    class Subcomponent0(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1
    
    class Subcomponent1(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.param0 = param0

    class Subcomponent2(Component):
        def __init__(self, name, param2="param2"):
            super().__init__(name)
            self.add_component(Subcomponent3, "subcomponent3", param3="param3*")
            self.param2 = param2

    class Subcomponent3(Component):
        def __init__(self, name, param3="param3"):
            super().__init__(name)
            self.add_component(Subcomponent4, "subcomponent4", param4="param4*")
            self.param3 = param3

    class Subcomponent4(Component):
        def __init__(self, name, param4="param4"):
            super().__init__(name)
            self.param4 = param4

    class Component0(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0", param0="param0*")
            self.add_component(Subcomponent1, "subcomponent1")
            self.add_component(Subcomponent2, "subcomponent2", param2="param2*")
            self.param0 = param0

    component0 = Component0("component0", param0="bar")
    initialize(component0)
    initialize(component0)
    assert component0.param0 == "bar"
    assert component0.components["subcomponent0"].param0 == "param0*"
    assert component0.components["subcomponent0"].param1 == "param1"
    assert component0.components["subcomponent1"].param0 == "param0"
    assert component0.components["subcomponent2"].param2 == "param2*"
    assert component0.components["subcomponent2"].components["subcomponent3"].param3 == "param3*"
    assert component0.components["subcomponent2"].components["subcomponent3"].components["subcomponent4"].param4 == "param4*"


def test_config_from_dict():
    class Subcomponent0(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1
    
    class Subcomponent1(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.param0 = param0

    class Subcomponent2(Component):
        def __init__(self, name, param2="param2"):
            super().__init__(name)
            self.add_component(Subcomponent3, "subcomponent3")
            self.param2 = param2

    class Subcomponent3(Component):
        def __init__(self, name, param3="param3"):
            super().__init__(name)
            self.add_component(Subcomponent4, "subcomponent4", param4="foo")
            self.param3 = param3

    class Subcomponent4(Component):
        def __init__(self, name, param4="param4"):
            super().__init__(name)
            self.param4 = param4

    class Component0(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0", param0="foo")
            self.add_component(Subcomponent1, "subcomponent1")
            self.add_component(Subcomponent2, "subcomponent2")
            self.param0 = param0

    config = {
        "component0": {
            "type": Component0,
            "config": {
                "param0": "bar",
            },
            "components": {
                "subcomponent0": {
                    "config": {
                        "param0": "foo2",
                    },
                },
                "subcomponent1": {
                    "config": {
                        "param0": "baz",
                    },
                },
                "subcomponent2": {
                    "config": {
                        "param2": "param2*",
                    },
                    "components": {
                        "subcomponent3": {
                            "config": {
                                "param3": "param3*",
                            },
                            "components": {
                                "subcomponent4": {
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

    component0 = get_root_component(config)
    initialize(component0)
    assert component0.param0 == "bar"
    assert component0.components["subcomponent0"].param0 == "foo2"
    assert component0.components["subcomponent0"].param1 == "param1"
    assert component0.components["subcomponent1"].param0 == "baz"
    assert component0.components["subcomponent2"].param2 == "param2*"
    assert component0.components["subcomponent2"].components["subcomponent3"].param3 == "param3*"
    assert component0.components["subcomponent2"].components["subcomponent3"].components["subcomponent4"].param4 == "param4*"


def test_wrong_config_from_dict_1():
    class Component0(Component):
        pass

    config = {
        "component0": {
            "type": Component0,
            "components": {
                "subcomponent0": {
                    "config": {
                        "param0": "foo",
                    },
                },
            },
        },
    }

    component0 = get_root_component(config)

    with pytest.raises(RuntimeError) as excinfo:
        initialize(component0)

    assert str(excinfo.value) == "Component not found: subcomponent0"


def test_wrong_config_from_dict_2():
    class Subcomponent0(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Component0(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0", param0="foo")

    config = {
        "component0": {
            "type": Component0,
            "components": {
                "subcomponent0": {
                    "config": {
                        "param0": "foo",
                    },
                    "components": {
                        "subcomponent1": {
                            "config": {
                                "param1": "bar",
                            },
                        },
                    },
                },
            },
        },
    }

    component0 = get_root_component(config)

    with pytest.raises(RuntimeError) as excinfo:
        initialize(component0)

    assert str(excinfo.value) == "Component not found: subcomponent1"


def test_config_from_dict_add_subcomponents():
    class Subcomponent0(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Subcomponent1(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Subcomponent10(Component):
        def __init__(self, name, param0="param0", param1="param1"):
            super().__init__(name)
            self.param0 = param0
            self.param1 = param1

    class Component0(Component):
        pass

    config = {
        "component0": {
            "type": Component0,
            "components": {
                "subcomponent0": {
                    "type": Subcomponent0,
                    "config": {
                        "param0": "foo",
                    },
                },
                "subcomponent1": {
                    "type": Subcomponent1,
                    "config": {
                        "param1": "bar",
                    },
                    "components": {
                        "subcomponent10": {
                            "type": Subcomponent10,
                            "config": {
                                "param0": "baz",
                             },
                        },
                    },
                },
            },
        },
    }

    component0 = get_root_component(config)
    initialize(component0)
    assert list(component0.components.keys()) == ["subcomponent0", "subcomponent1"]
    assert list(component0.components["subcomponent0"].components.keys()) == []
    assert list(component0.components["subcomponent1"].components.keys()) == ["subcomponent10"]
    assert list(component0.components["subcomponent1"].components["subcomponent10"].components.keys()) == []
    assert component0.components["subcomponent0"].param0 == "foo"
    assert component0.components["subcomponent0"].param1 == "param1"
    assert component0.components["subcomponent1"].param0 == "param0"
    assert component0.components["subcomponent1"].param1 == "bar"
    assert component0.components["subcomponent1"].components["subcomponent10"].param0 == "baz"
    assert component0.components["subcomponent1"].components["subcomponent10"].param1 == "param1"
