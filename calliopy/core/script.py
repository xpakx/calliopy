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
            if self.dial._abort:
                return
            scene = self.scenes[self.current]
            self.run_function(scene)
            self.current += 1

    def get_dial(self):
        self.dial = self.get_component(None, "dial")
        return self.dial

    def register(self, component):
        comp_orig_name = get_type_name(component)
        if comp_orig_name in self.names:
            return
        constructable = True
        if "Scene" in self.get_decorators(component):
            print(comp_orig_name, self.get_decorators(component)["Scene"])
            constructable = False
            print(comp_orig_name)
            self.scenes.append(component)
        print(component.__name__)

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
            init = getattr(component, "__init__", lambda self: None)
            dependencies = self.check_dependencies(init, True)
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

    def check_dependencies(self, component, is_constructor=False) -> list[DependencyData]:
        dependencies = []
        signature = inspect.signature(component)
        type_hints = get_type_hints(component, globals(), locals())
        for i, (key, _) in enumerate(signature.parameters.items()):
            if is_constructor and i == 0:
                continue  # skip 'self'
            param_num = i-1 if is_constructor else i
            hint = type_hints.get(key)
            type_name = get_type_name(hint) if hint is not None else None
            dep = DependencyData(
                    name=key,
                    dep_type=type_name,
                    param=param_num,
            )
            dependencies.append(dep)
        return dependencies

    def get_decorators(self, cls) -> dict[str]:
        return getattr(cls,  "__calliopy_decorators__", {})

    def get_component(self, type_name: str | None, tag: str | None = None) -> ComponentData | None:
        print("getting component", type_name, tag)
        if tag:
            print(self.components_by_tag.get(tag))
            comp_data: ComponentData = self.components_by_tag.get(tag)
            if comp_data:
                print("Tag found")
                class_name = get_type_name(comp_data.component_class)
                if type_name is not None and type_name != class_name:
                    print("Tagged component of wrong type")
                    return None
                if comp_data.component is None and comp_data.constructable:
                    comp_data.component = self.construct_component(comp_data)
                return comp_data.component
        print("Tag not found, searching by type")

        comps = self.components_by_class.get(type_name)
        if not comps or len(comps) == 0:
            print("No component with type")
            return None

        if len(comps) > 1:
            print("Warn: multiple component with type")

        for comp_data in comps:
            if not comp_data.constructable:
                continue
            if comp_data.component is None:
                comp_data.component = self.construct_component(comp_data)
            return comp_data.component

        return None

    def construct_component(self, comp_data: ComponentData) -> Any:
        print("constructing", comp_data)
        kwargs = {}
        for dep in comp_data.dependencies:
            dep_instance = self.get_component(dep.dep_type, dep.name)
            if dep_instance is None:
                print(f"Cannot resolve dependency {dep.name} of type {dep.dep_type}")
            kwargs[dep.name] = dep_instance

        if inspect.isclass(comp_data.component_class):
            return comp_data.component_class(**kwargs)
        else:
            return comp_data.component_class(**kwargs)

    def run_function(self, func: Any) -> Any:
        comp = self.components_by_class.get(get_type_name(func))
        component = comp[0]
        kwargs = {}
        for dep in component.dependencies:
            dep_instance = self.get_component(dep.dep_type, dep.name)
            if dep_instance is None:
                print(f"Cannot resolve dependency {dep.name} of type {dep.dep_type}")
            kwargs[dep.name] = dep_instance

        return func(**kwargs)


def get_type_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"
