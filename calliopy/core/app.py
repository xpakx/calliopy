import inspect
import importlib
import os
import pkgutil
import threading
from typing import Any, List, Type
from types import ModuleType
from calliopy.core.frontend import CalliopyFrontend, DialogueManager


def scene(dial: DialogueManager):
    dial.say("Alice", "Hello, Bob! Nice day, isn't it?")
    dial.say("Bob", "Indeed, Alice. The forest is beautiful today.")
    dial.say("Alice", "Let's go explore a bit further!")


class CalliopyApp:
    def __init__(
            self,
            module_name: str,
            ) -> None:
        self.load_module("calliopy.core")
        self.load_module(module_name)

    def inspect_module_class(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isclass)

    def inspect_module_func(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isfunction)

    def run(self) -> None:
        self.frontend = CalliopyFrontend()
        dial = DialogueManager()
        self.frontend.set_dialogue_manager(dial)
        scene_thread = threading.Thread(target=scene, args=(dial,))
        scene_thread.start()
        self.frontend.set_scene_thread(scene_thread)
        self.frontend.run()

    def load_module(self, module_name: str) -> None:
        all_classes, all_funcs = self.get_module_classes(module_name)
        components = self.get_components(all_classes)
        print(components)
        components_func = self.get_components(all_funcs)
        print(components_func)

    def get_module_classes(self, package_name: str) -> List[Any]:
        package = importlib.import_module(package_name)
        if not package or not package.__file__:
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
                    module = importlib.import_module(module_name)
                    all_classes.update(self.inspect_module_class(module))
                    all_funcs.update(self.inspect_module_func(module))
                except ImportError as e:
                    print(f"Failed to import module {module_name}: {e}")

        return all_classes, all_funcs

    def get_components(self, all_classes: List[Any]) -> List[Any]:
        return [obj for name, obj in all_classes if
                'Component' in get_decorators(obj)]


def get_decorators(cls: Type) -> List[str]:
    return getattr(cls,  "__calliopy_decorators__", [])
