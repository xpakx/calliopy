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
        self.components_by_class = {}
        self.names = set()
        self.components_by_tag = {}

    def run(self):
        print(self.components_by_class)
        print(self.components_by_tag)
        print(self.scenes)
        while self.current < len(self.scenes):
            scene = self.scenes[self.current]
            scene(self.dial)
            self.current += 1

    def register(self, component):
        comp_orig_name = get_type_name(component)
        if comp_orig_name in self.names:
            return
        constructable = True
        if "Scene" in self.get_decorators(component):
            constructable = False
            print(comp_orig_name)
            self.scenes.append(component)
        print(component.__name__)
        if "DialogueManager" == component.__name__:
            self.dial = component()

        component_name: str | None = None
        if inspect.isfunction(component):
            dependencies = self.check_dependencies(component)

            type_hints = get_type_hints(component, globals(), locals())
            return_type = type_hints.get('return')
            print(type_hints)
            print("Returns", return_type)
            if return_type is not None and constructable:
                component_name = get_type_name(return_type)
        elif inspect.isclass(component):
            dependencies = []  # TODO: use init function
            component_name = get_type_name(component)

        if component_name is None and constructable:
            print("Constructable Component type is unknown")
            return

        if component_name is None:
            component_name = get_type_name(component)

        comp_data = ComponentData(
                component_class=component,
                dependencies=dependencies,
                constructable=constructable,
        )
        comp_dec = self.get_decorators(component).get('Component', {})
        tags = comp_dec.get('tags', [])
        self.add_component(comp_data, component_name, tags)
        self.names.add(comp_orig_name)  # TODO: use orig_name as tag

    def add_component(
            self,
            comp_data: ComponentData,
            component_name: str,
            tags: list[str] | None
    ) -> None:
        if self.components_by_class.get(component_name) is None:
            self.components_by_class[component_name] = []
        self.components_by_class[component_name].append(comp_data)
        for tag in tags:
            self.components_by_tag[tag] = comp_data

    def check_dependencies(self, component) -> list[DependencyData]:
        dependencies = []
        signature = inspect.signature(component)
        type_hints = get_type_hints(component, globals(), locals())
        for i, (key, _) in enumerate(signature.parameters.items()):
            hint = type_hints.get(key)
            type_name = get_type_name(hint) if hint is not None else None
            dep = DependencyData(
                    name=key,
                    dep_type=type_name,
                    param=i,
            )
            dependencies.append(dep)
        return dependencies

    def get_decorators(self, cls) -> dict[str]:
        return getattr(cls,  "__calliopy_decorators__", {})


def get_type_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"
