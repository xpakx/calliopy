import pytest
from utils import ScriptableDialogueManager

from calliopy.core.container import (
        CalliopyContainer, ComponentData, get_type_name
)
from calliopy.core.annotations import Scene, Component, Inject
from calliopy.core.script import ScriptManager


@Component()
class A:
    def __init__(self):
        pass


@Component()
class B:
    def __init__(self, a: A):
        self.a = a


@Component()
class C:
    def __init__(self, a: A, b: B):
        self.a = a
        self.b = b


@Component()
def func_component(a: A) -> B:
    return B(a)


@Scene()
def scene1():
    return "scene1"


@Scene()
def scene2():
    return "scene2"


class Tagged:
    pass


@pytest.fixture
def script():
    container = CalliopyContainer()
    container.register(ScriptManager)
    return container


def test_register_class_component(script):
    script.register(A)
    a_instance = script.get_component(get_type_name(A))
    assert isinstance(a_instance, A)


def test_register_class_with_dependency(script):
    script.register(A)
    script.register(B)
    b_instance = script.get_component(get_type_name(B))
    assert isinstance(b_instance, B)
    assert isinstance(b_instance.a, A)


def test_register_nested_dependencies(script):
    script.register(A)
    script.register(B)
    script.register(C)
    c_instance = script.get_component(get_type_name(C))
    assert isinstance(c_instance, C)
    assert isinstance(c_instance.a, A)
    assert isinstance(c_instance.b, B)
    assert isinstance(c_instance.b.a, A)


def test_function_component_registration(script):
    script.register(A)
    script.register(func_component)
    b_instance = script.get_component(get_type_name(B))
    assert isinstance(b_instance, B)
    assert isinstance(b_instance.a, A)


def test_component_with_tag(script):
    comp_data = ComponentData(component_class=Tagged, dependencies=[], constructable=True)
    script.add_component(comp_data, get_type_name(Tagged), Tagged, tags=["tag1"])
    tagged_instance = script.get_component(None, "tag1")
    assert isinstance(tagged_instance, Tagged)


def test_tag_wrong_type_returns_none(script):
    comp_data = ComponentData(component_class=Tagged, dependencies=[], constructable=True)
    script.add_component(comp_data, get_type_name(Tagged), Tagged, tags=["tag1"])
    result = script.get_component(get_type_name(A), "tag1")
    assert result is None


def test_scene_registration(script):
    script.register(scene1)
    script.register(scene2)
    scenes = script.get_component(None, "script_manager").scenes
    assert scene1 in scenes
    assert scene2 in scenes


def test_scene_execution_order(script):
    executed = []

    @Scene()
    def s1():
        executed.append(1)

    @Scene()
    def s2():
        executed.append(2)
    script.register(ScriptableDialogueManager)
    script.register(s1)
    script.register(s2)

    scenes = script.get_component(None, "script_manager")
    end = False
    tag = None
    while not end:
        scene, kwargs = scenes.get_next_scene(tag)
        if scene is None:
            end = True
        else:
            tag = scene(**kwargs)

    assert executed == [1, 2]


def test_multiple_components_same_type(script):
    class D:
        def __init__(self):
            pass
    script.register(D)
    script.register(D)
    instances = [script.get_component(get_type_name(D)) for _ in range(2)]
    assert all(isinstance(inst, D) for inst in instances)


def test_dependency_param_indices(script):
    script.register(A)
    script.register(B)
    b_data_list = script.components_by_class[get_type_name(B)]
    b_data = b_data_list[0]
    dep = b_data.dependencies[0]
    assert dep.name == "a"
    assert dep.param == 0


def test_setter_with_dep_and_default(script):
    class X:
        def __init__(self):
            self.val = None

        @Inject()
        def configure(self, missing: int = 99):
            self.val = missing

    script.register(X)
    x = script.get_component(get_type_name(X))
    assert x.val == 99


def test_list_dependency(script):
    @Component()
    class X:
        def __init__(self):
            pass

    @Component()
    class Y(X):
        def __init__(self):
            pass

    @Component()
    class C:
        def __init__(self, a_list: list[X]):
            self.a_list = a_list

    script.register(X)
    script.register(Y)
    script.register(C)

    c = script.get_component(get_type_name(C))
    assert isinstance(c.a_list, list)
    assert len(c.a_list) == 2


def test_dependency_default_used(script):
    @Component()
    class B:
        def __init__(self, missing: int = 123):
            self.missing = missing

    script.register(B)
    b = script.get_component(get_type_name(B))
    assert b.missing == 123
