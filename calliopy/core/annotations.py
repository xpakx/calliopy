from typing import Callable


def _ensure_meta_lists(cls) -> None:
    if not hasattr(cls, "__calliopy_decorators__"):
        cls.__calliopy_decorators__ = {}


def _decorate_component(cls, tag: str | list[str] | None):
    tags = [tag] if isinstance(tag, str) else tag or []
    cls.__calliopy_decorators__["Component"] = {
            "tag": tags
    }


# TODO: add necessary fields
def _decorate_scene(cls):
    cls.__calliopy_decorators__["Scene"] = {}


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
    repeatable: bool = False,                         # can run multiple times
    priority: int = 0,                                # scene selection priority
    probability: float = 1.0,                         # chance of appearing
    tags: list[str] | None = None                     # arbitrary labels
):
    def wrapper(cls):
        _ensure_meta_lists(cls)
        _decorate_component(cls, tags)
        _decorate_scene(cls)
        return cls
    return wrapper
