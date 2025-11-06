from calliopy.core.annotations import _decorate_component, _ensure_meta_lists


def _decorate_ui_action(cls, name):
    cls.__calliopy_decorators__["UIAction"] = {
            "name": name,
    }


def UIAction(name: str | None = None):
    def wrapper(cls):
        action = name if name else cls.__name__
        _ensure_meta_lists(cls)
        _decorate_component(cls, [], False)
        _decorate_ui_action(cls, action)
        return cls
    return wrapper
