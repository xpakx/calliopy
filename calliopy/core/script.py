from dataclasses import dataclass, field
from typing import Any, get_type_hints
import inspect


@dataclass
class DependencyData:
    name: str = "unknown"
    dep_type: str | None = None
    param: int = 0


@dataclass
class ComponentData:
    component_class: type
    dependencies: list[DependencyData] = field(default_factory=list)
    component: Any | None = None
    constructable: bool = True


class CalliopyScript:
    def __init__(self):
        self.scenes = []
        self.dial = None
        self.current = 0
        # TODO: these could be also returned from
        # methods, so we should have list by class
        self.components_by_class = {}
        self.components_by_tag = {}

    def run(self):
        print(self.components_by_class)
        print(self.components_by_tag)
        while self.current < len(self.scenes):
            scene = self.scenes[self.current]
            scene(self.dial)
            self.current += 1

    def register(self, component):
        constructable = True
        if "Scene" in self.get_decorators(component):
            constructable = False
            self.scenes.append(component)
        print(component.__name__)
        if "DialogueManager" == component.__name__:
            self.dial = component()

        if inspect.isfunction(component):
            dependencies = self.check_dependencies(component)
        elif inspect.isclass(component):
            dependencies = []  # TODO: use init function

        component_name = get_type_name(component)
        comp_data = ComponentData(
                component_class=component,
                dependencies=dependencies,
                constructable=constructable,
        )
        self.components_by_class[component_name] = comp_data
        comp_dec = self.get_decorators(component).get('Component', {})
        tags = comp_dec.get('tags', [])
        for tag in tags:
            self.components_by_tag[tag] = comp_data

    def check_dependencies(self, component) -> list[DependencyData]:
        dependencies = []
        signature = inspect.signature(component)
        type_hints = get_type_hints(component, globals(), locals())
        for i, (key, _) in enumerate(signature.parameters.items()):
            hint = type_hints.get(key)
            dep = DependencyData(
                    name=key,
                    dep_type=get_type_name(hint),
                    param=i,
            )
            dependencies.append(dep)
        return dependencies

    def get_decorators(self, cls) -> dict[str]:
        return getattr(cls,  "__calliopy_decorators__", {})


def get_type_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"
