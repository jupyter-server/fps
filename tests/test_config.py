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

    class Component0(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0", param0="foo")
            self.add_component(Subcomponent1, "subcomponent1")
            self.param0 = param0

    component0 = Component0("component0", param0="bar")
    initialize(component0)
    initialize(component0)
    assert component0.components["subcomponent0"].param0 == "foo"
    assert component0.components["subcomponent0"].param1 == "param1"
    assert component0.components["subcomponent1"].param0 == "param0"
    assert component0.param0 == "bar"


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

    class Component0(Component):
        def __init__(self, name, param0="param0"):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0", param0="foo")
            self.add_component(Subcomponent1, "subcomponent1")
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
            },
        },
    }

    component0 = get_root_component(config)
    initialize(component0)
    assert component0.components["subcomponent0"].param0 == "foo2"
    assert component0.components["subcomponent0"].param1 == "param1"
    assert component0.components["subcomponent1"].param0 == "baz"
    assert component0.param0 == "bar"
