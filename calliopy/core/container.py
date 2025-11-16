from dataclasses import dataclass, field
from typing import Any, get_type_hints, Callable, List
from typing import get_args, get_origin
import inspect
from calliopy.logger.logger import LoggerFactory


@dataclass
class DependencyData:
    name: str = "unknown"
    dep_type: str | None = None
    list_of: bool = False
    param: int = 0
    default: Any = None


@dataclass
class SetterData:
    method: Callable | None = None
    dependencies: list[DependencyData] = field(default_factory=list)


@dataclass
class ComponentData:
    component_class: type
    dependencies: list[DependencyData] = field(default_factory=list)
    component: Any | None = None
    constructable: bool = True
    setters: list[SetterData] = field(default_factory=list)


@dataclass
class ConstructionContext:
    scope: str = ""  # MAYBE: not sure we will need that
    constructed: list[ComponentData] = field(default_factory=list)

    def reset(self) -> None:
        self.constructed = []


class CalliopyContainer:
    def __init__(self):
        self.components_by_class = {}
        self.names = set()
        self.components_by_tag = {}
        self.logger = LoggerFactory.get_logger()
        # TODO: load flags
        self.flags = {}
        # TODO: not sure if having this as field is a good idea
        # we don't allow any multithreading anyway, so it can
        # stay for now
        self.context = ConstructionContext()

    def register(self, component):
        comp_orig_name = get_type_name(component)
        if comp_orig_name in self.names:
            return
        comp_dec = self.get_decorators(component).get('Component', {})

        if not self.evaluate_conditional_creation(comp_dec):
            return

        constructable = comp_dec.get('constructable', True)
        self.logger.debug(component.__name__)

        component_name: str | None = None
        component_resolved_type: type | None = None
        if inspect.isfunction(component):
            dependencies = self.check_dependencies(component)

            type_hints = get_type_hints(component, globals(), locals())
            return_type = type_hints.get('return')
            self.logger.debug(type_hints)
            self.logger.debug("Returns", return_type)
            if return_type is not None and constructable:
                component_name = get_type_name(return_type)
                component_resolved_type = return_type
        elif inspect.isclass(component):
            init = getattr(component, "__init__", lambda self: None)
            dependencies = self.check_dependencies(init, True)
            component_name = get_type_name(component)
            component_resolved_type = component

        if component_name is None and constructable:
            self.logger.warn("Constructable Component type is unknown")
            return

        if component_name is None:
            component_name = get_type_name(component)

        comp_data = ComponentData(
                component_class=component,
                dependencies=dependencies,
                constructable=constructable,
        )

        if component_resolved_type is not None:
            comp_data.setters = self.get_setters(component_resolved_type)

        tags = comp_dec.get('tags', [])
        self.add_component(comp_data, component_name, component_resolved_type, tags)
        self.names.add(comp_orig_name)

    def add_component(
            self,
            comp_data: ComponentData,
            component_name: str,
            component_resolved_type: type,
            tags: list[str] | None
    ) -> None:
        self.add_component_by_type(comp_data, component_name)
        for tag in tags:
            self.components_by_tag[tag] = comp_data
        if component_resolved_type is not None:
            for tp in component_resolved_type.__mro__:
                if tp == object:
                    continue
                if tp == component_resolved_type:
                    continue
                name = get_type_name(tp)
                self.add_component_by_type(comp_data, name)

    def add_component_by_type(
            self,
            comp_data: ComponentData,
            component_name: str
    ) -> None:
        if self.components_by_class.get(component_name) is None:
            self.components_by_class[component_name] = []
        self.components_by_class[component_name].append(comp_data)

    def check_dependencies(self, component, is_constructor=False) -> list[DependencyData]:
        dependencies = []
        signature = inspect.signature(component)
        type_hints = get_type_hints(component, globals(), locals())
        for i, (key, param) in enumerate(signature.parameters.items()):
            if is_constructor and i == 0:
                continue  # skip 'self'
            param_num = i-1 if is_constructor else i
            hint = type_hints.get(key)
            type_name = get_type_name(hint) if hint is not None else None
            default = None
            if param.default is not inspect.Parameter.empty:
                default = param.default
            dep = DependencyData(
                    name=key,
                    dep_type=type_name,
                    param=param_num,
                    default=default,
            )
            if hint is not None:
                origin = get_origin(hint)
                if origin is not None and origin in [list, List]:
                    args = get_args(hint)
                    if args:
                        wrapped_type = args[0]
                        if wrapped_type:
                            dep.dep_type = get_type_name(wrapped_type)
                            dep.list_of = True
            dependencies.append(dep)
        return dependencies

    def get_decorators(self, cls) -> dict[str]:
        return getattr(cls,  "__calliopy_decorators__", {})

    def get_component(
            self,
            type_name: str | None,
            tag: str | None = None
    ) -> ComponentData | None:
        self.context.reset()
        component = self.do_get_component(type_name, tag)
        self.post_construction()
        return component

    def do_get_component(
            self,
            type_name: str | None,
            tag: str | None = None
    ) -> ComponentData | None:
        self.logger.debug("getting component", type_name, tag)
        if tag:
            self.logger.debug(self.components_by_tag.get(tag))
            comp_data: ComponentData = self.components_by_tag.get(tag)
            if comp_data:
                self.logger.debug("Tag found")
                class_name = get_type_name(comp_data.component_class)
                if type_name is not None and type_name != class_name:
                    if not self.is_type_subclass(comp_data, type_name):
                        self.logger.warn("Tagged component of wrong type")
                        return None
                if comp_data.component is None and comp_data.constructable:
                    comp_data.component = self.construct_component(comp_data)
                return comp_data.component
        self.logger.debug("Tag not found, searching by type")

        comps = self.components_by_class.get(type_name)
        if not comps or len(comps) == 0:
            self.logger.warn("No component with type")
            return None

        if len(comps) > 1:
            self.logger.warn("multiple component with type")

        for comp_data in comps:
            if not comp_data.constructable:
                continue
            if comp_data.component is None:
                comp_data.component = self.construct_component(comp_data)
            return comp_data.component

        return None

    def construct_component(self, comp_data: ComponentData) -> Any:
        self.logger.debug("constructing", comp_data)
        kwargs = {}
        for dep in comp_data.dependencies:
            dep_instance = self.construct_dependency(dep)
            if dep_instance is None:
                self.logger.warn(f"Cannot resolve dependency {dep.name} of type {dep.dep_type}")
                if dep.name in ["args", "kwargs"]:
                    continue
            kwargs[dep.name] = dep_instance

        if inspect.isclass(comp_data.component_class):
            component = comp_data.component_class(**kwargs)
        else:
            component = comp_data.component_class(**kwargs)

        self.context.constructed.append(comp_data)

        return component

    def run_setters(self, comp_data: ComponentData, component: Any) -> Any:
        for setter in comp_data.setters:
            kwargs = {}
            for dep in setter.dependencies:
                dep_instance = self.construct_dependency(dep)
                if dep_instance is None:
                    self.logger.warn(f"Cannot resolve setter dependency {dep.name} of type {dep.dep_type}")
                kwargs[dep.name] = dep_instance
            setter.method(component, **kwargs)

    def construct_dependency(self, dep: DependencyData) -> Any:
        if dep.dep_type == get_type_name(type(self)):
            return self
        if dep.list_of:
            dep_list = self.components_by_class.get(dep.dep_type, [])
            dep_instance = []
            for subdep in dep_list:
                if subdep.component is None and subdep.constructable:
                    subdep.component = self.construct_component(subdep)
                elem = subdep.component
                if elem is None:
                    continue
                dep_instance.append(elem)
        else:
            dep_instance = self.do_get_component(dep.dep_type, dep.name)
        if dep_instance is None and dep.default is not None:
            return dep.default
        return dep_instance

    def run_function(self, func: Any) -> Any:
        self.context.reset()
        comp = self.components_by_class.get(get_type_name(func))
        if not comp:
            self.logger.warn(f"No function {get_type_name(func)}")
            return None
        component = comp[0]
        kwargs = {}
        for dep in component.dependencies:
            dep_instance = self.do_get_component(dep.dep_type, dep.name)
            if dep_instance is None:
                self.logger.warn(f"Cannot resolve dependency {dep.name} of type {dep.dep_type}")
            kwargs[dep.name] = dep_instance
        self.post_construction()

        return func(**kwargs)

    def get_function(self, func: Any) -> Any:
        self.context.reset()
        comp = self.components_by_class.get(get_type_name(func))
        if not comp:
            self.logger.warn(f"No function {get_type_name(func)}")
            return None
        component = comp[0]
        kwargs = {}
        for dep in component.dependencies:
            dep_instance = self.do_get_component(dep.dep_type, dep.name)
            if dep_instance is None:
                self.logger.warn(f"Cannot resolve dependency {dep.name} of type {dep.dep_type}")
            kwargs[dep.name] = dep_instance
        self.post_construction()

        return func, kwargs

    def post_construction(self) -> None:
        for comp in self.context.constructed:
            self.run_setters(comp, comp.component)

    def get_setters(self, cls) -> list[SetterData]:
        all_methods = inspect.getmembers(cls, predicate=lambda x: callable(x))
        setters = []
        for name, method in all_methods:
            if name != "__init__" and name.startswith('__'):
                continue
            if "Setter" not in self.get_decorators(method):
                continue
            data = SetterData(
                method=method,
                dependencies=self.check_dependencies(method, True),
            )
            setters.append(data)
        return setters

    # TODO: not ideal, we should probably just pass type to get_component
    def is_type_subclass(self, component: ComponentData, type_name: str) -> bool:
        for tp in component.component_class.__mro__:
            if tp == object:
                continue
            sub_name = get_type_name(tp)
            if sub_name == type_name:
                return True
        return False

    def get_components_by_predicate(
            self,
            predicate: Callable[[type], bool],
            constructable: bool | None = None
    ) -> list[Callable]:
        results = []
        for comp_list in self.components_by_class.values():
            for comp_data in comp_list:
                if constructable is not None and comp_data.constructable != constructable:
                    continue
                if predicate(comp_data):
                    results.append(comp_data.component_class)
        return results

    def get_functions_with_decorator(self, decorator: str) -> list[Callable]:
        return self.get_components_by_predicate(
            lambda comp: decorator in self.get_decorators(comp.component_class),
            constructable=False
        )

    # TODO: improve and add very simple DSL
    def evaluate_conditional_creation(self, comp_dec: dict):
        var = comp_dec.get('if_true')
        if var is None:
            return True
        if var.startswith('not '):
            var = var.split()[1]
            return var not in self.flags
        return var in self.flags


def get_type_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"
