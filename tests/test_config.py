from fastaio import Component, get_root_component


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
            self.subcomponent0 = self.add_component(Subcomponent0, "subcomponent0", param0="foo")
            self.subcomponent1 = self.add_component(Subcomponent1, "subcomponent1")
            self.param0 = param0

    component0 = Component0("component0", param0="bar")
    assert component0.subcomponent0.param0 == "foo"
    assert component0.subcomponent0.param1 == "param1"
    assert component0.subcomponent1.param0 == "param0"
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
            self.param0 = param0

    config = {
        "component0": {
            "type": Component0,
            "config": {
                "param0": "bar",
            },
            "components": {
                "subcomponent0": {
                    "type": Subcomponent0,
                    "config": {
                        "param0": "foo",
                    },
                },
                "subcomponent1": {
                    "type": Subcomponent1,
                },
            },
        },
    }

    root_component = get_root_component(config)
    assert root_component.components["subcomponent0"].param0 == "foo"
    assert root_component.components["subcomponent0"].param1 == "param1"
    assert root_component.components["subcomponent1"].param0 == "param0"
    assert root_component.param0 == "bar"
