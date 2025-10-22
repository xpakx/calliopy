from typing import Callable
from inspect import isclass


def _ensure_meta_lists(cls) -> None:
    if not hasattr(cls, "__calliopy_decorators__"):
        cls.__calliopy_decorators__ = {}


def _decorate_component(cls, tag: str | list[str] | None):
    tags = [tag] if isinstance(tag, str) else tag or []
    cls.__calliopy_decorators__["Component"] = {
            "tags": tags
    }


# TODO: add necessary fields
def _decorate_scene(
        cls,
        after: str | None = None,
        default: bool = False,
        if_true: Callable[[], bool] | str | None = None,
        branch: str | None = None,
        repeatable: bool = True,
        priority: int = 0,
        probability: float = 1.0
):
    num = SceneCounter.next()
    cls.__calliopy_decorators__["Scene"] = {
            "name": cls.__name__,
            "num": num,
            "after": after,
            "default": default,
            "if_true": if_true,
            "branch": branch,
            "repeatable": repeatable,
            "priority": priority,
            "probability": probability,
    }
    print("Scene:", cls.__name__, num)


def Component(tags: str | list[str] | None = None):
    def wrapper(cls):
        _ensure_meta_lists(cls)
        _decorate_component(cls, tags)
        return cls
    return wrapper


def Scene(
    after: str | None = None,                         # run after another scene
    default: bool = False,                            # run first
    if_true: Callable[[], bool] | str | None = None,  # condition for scene
    branch: str | None = None,                        # branch label
    repeatable: bool = True,                          # can run multiple times
    priority: int = 0,                                # scene selection priority
    probability: float = 1.0,                         # chance of appearing
    tags: list[str] | None = None                     # arbitrary labels
):
    def wrapper(cls):
        _ensure_meta_lists(cls)
        _decorate_component(cls, tags)
        _decorate_scene(
                cls,
                after,
                default,
                if_true,
                branch,
                repeatable,
                priority,
                probability
        )
        return cls
    return wrapper


class SceneCounter:
    _num = 0

    @classmethod
    def next(cls) -> int:
        r = cls._num
        cls._num += 1
        return r


def _decorate_inject(method):
    method.__calliopy_decorators__["Setter"] = {}


def Inject():
    def wrapper(method):
        if isclass(method):
            raise Exception("Only methods can be decorated with Inject")
        _ensure_meta_lists(method)
        _decorate_inject(method)
        return method
    return wrapper
