import inspect
import importlib
import os
import sys
import pkgutil
from typing import Any, List, Type, Tuple
from types import ModuleType
from calliopy.core.frontend import CalliopyFrontend
from calliopy.core.script import CalliopyScript
from calliopy.logger.logger import LoggerFactory


class CalliopyApp:
    def __init__(
            self,
            module_name: str | None = None,
            ) -> None:
        self.logger = LoggerFactory.get_logger()
        if module_name is None:
            module_name = '__main__'
        self.container = CalliopyScript()
        self.load_module("calliopy.core")
        self.load_module(module_name)

    def inspect_module_class(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isclass)

    def inspect_module_func(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isfunction)

    def run(self) -> None:
        self.frontend = CalliopyFrontend()
        dialogue = self.container.get_dial()
        scheduler = self.container.get_scheduler()
        self.container.init_scenes()
        self.frontend.set_dialogue_manager(dialogue)
        self.frontend.set_scheduler(scheduler)
        self.frontend.set_script(self.container)
        self.frontend.run()

    def load_module(self, module_name: str) -> None:
        all_classes, all_funcs = self.get_module_classes(module_name)
        components = self.get_components(all_classes)
        self.logger.debug(components)
        components_func = self.get_components(all_funcs)
        self.logger.debug(components_func)
        for cls in components_func:
            self.container.register(cls)
        for cls in components:
            self.container.register(cls)

    def import_module(self, name: str) -> Tuple[bool, ModuleType]:
        if "__main__" in sys.modules:
            main_module = sys.modules["__main__"]
            if getattr(main_module, "__package__", None):
                package_name = main_module.__package__
                # TODO: test this
                file_stem = os.path.splitext(os.path.basename(main_module.__file__))[0]
                module_name = f"{package_name}.{file_stem}"
                self.logger.debug("MAIN:", module_name, name)
                if module_name == name:
                    self.logger.debug(f"Skipping __main__ module: {name}")
                    return True, main_module
        if name in sys.modules:
            package = sys.modules[name]
            loaded = True
            self.logger.debug(f"Skipping already loaded module: {name}")
        else:
            package = importlib.import_module(name)
            loaded = False
        return loaded, package

    def get_module_classes(self, package_name: str) -> List[Any]:
        _, package = self.import_module(package_name)

        if not package or not package.__file__:
            self.logger.debug(package_name)
            self.logger.debug(package is None)
            self.logger.debug(package.__file__ is None)
            raise Exception("Error")

        all_classes = set()
        all_funcs = set()
        is_init = package.__file__.endswith("__init__.py")
        is_dir = os.path.isdir(package.__file__)

        if not is_init and not is_dir:
            # single file module
            all_classes.update(self.inspect_module_class(package))
            all_funcs.update(self.inspect_module_func(package))
        else:
            # package
            package_dir = os.path.dirname(package.__file__)
            if not package_dir:
                raise Exception("Error")

            for _, module_name, is_pkg in pkgutil.\
                    walk_packages([package_dir], prefix=package_name + "."):
                try:
                    _, module = self.import_module(module_name)
                    all_classes.update(self.inspect_module_class(module))
                    all_funcs.update(self.inspect_module_func(module))
                except ImportError as e:
                    self.logger.error(f"Failed to import module {module_name}: {e}")

        return all_classes, all_funcs

    def get_components(self, all_classes: List[Any]) -> List[Any]:
        return [obj for name, obj in all_classes if
                'Component' in get_decorators(obj)]


def get_decorators(cls: Type) -> List[str]:
    return getattr(cls,  "__calliopy_decorators__", [])
