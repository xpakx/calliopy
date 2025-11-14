from calliopy.logger.logger import LoggerFactory
from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DrawableComponent
from calliopy.core.timer import TimeManager, Timer
from calliopy.gui.ui import Element, Style, Image
from calliopy.gui.parser.layout import UIParser
from dataclasses import is_dataclass, fields


# TODO: make this usable like Character class
class UIComponent:
    def __init__(self, front_config) -> None:
        self.width: int = front_config.width
        self.height: int = front_config.height
        self.root: Element | None = None
        self.initialized = False

    # for dataclasses
    def __post_init__(self) -> None:
        self.root: Element | None = None
        self.initialized = False

        instance_fields = self.__dict__
        cls_fields = set() if isinstance(self, type) else self.__class__.__dict__
        cls_fields = {
            name: val for name, val in cls_fields.items()
            if not name.startswith("_")
        }
        datacls_fields = set() if not is_dataclass(self) else fields(self)
        datacls_fields = {
            f.name: f.default for f in datacls_fields
            if not f.name.startswith("_")
        }

        all_fields = cls_fields
        all_fields.update(datacls_fields)
        all_fields.update(instance_fields)

        if "name" not in all_fields:
            raise Exception("Name for layout not defined")
        if "layout_file" not in all_fields:
            raise Exception("Layout file not defined")
        if "style_file" not in all_fields:
            raise Exception("Style file not defined")

    def compute_layout(self) -> None:
        if not self.root:
            return
        self.root.compute_layout(self.x, self.y, self.width, self.height)
        self.initialized = True

    @property
    def x(self) -> str | None:
        if "_x" in self.__dict__:
            return self.__dict__["_x"]
        return 0

    @x.setter
    def x(self, value: str) -> None:
        self.__dict__["_x"] = value

    @property
    def y(self) -> str | None:
        if "_y" in self.__dict__:
            return self.__dict__["_y"]
        return 0

    @y.setter
    def y(self, value: str) -> None:
        self.__dict__["_y"] = value

    @property
    def width(self) -> str | None:
        if "_width" in self.__dict__:
            return self.__dict__["_width"]
        return 0

    @width.setter
    def width(self, value: str) -> None:
        self.__dict__["_width"] = value

    @property
    def height(self) -> str | None:
        if "_height" in self.__dict__:
            return self.__dict__["_height"]
        return 0

    @height.setter
    def height(self, value: str) -> None:
        self.__dict__["_height"] = value

    def destroy(self):
        if self.root:
            self.unload_images(self.root)

    def unload_images(self, elem: Element):
        if isinstance(elem, Image):
            elem.unload()
        for child in getattr(elem, "children", []):
            self.unload_images(child)


@Component(tags=["ui", "gui"])
class UIDrawable(DrawableComponent):
    def __init__(
            self,
            gui_manager,
            time_manager: TimeManager,
    ):
        self.logger = LoggerFactory.get_logger()
        self.layouts: dict[str, UIComponent] = {}
        self.component: UIComponent | None = None
        self._show = False
        self.dispatcher = gui_manager
        self.timers = time_manager
        self.lock: Timer | None = None

    @Inject()
    def set_layouts(self, layouts: list[UIComponent]) -> None:
        for layout in layouts:
            self.register_layout(layout.name, layout)

    def draw(self):
        if self.component:
            self.component.root.draw()

    def init(self) -> None:
        menu = self.layouts.get('menu')
        if menu:
            self.lock = self.timers.simple_lock("menu_lock")
            self.show('menu')

    def kill_lock(self) -> None:
        if self.lock:
            self.lock.kill = True

    def update(self, dt: float) -> None:
        if self.component:
            self.component.root.update()

    def is_active(self) -> bool:
        return self.component is not None and self._show

    def destroy(self) -> None:
        self.logger.debug("Unloading images from layouts")
        for layout in self.layouts.values():
            layout.destroy()

    def show(self, view: str | None) -> None:
        if view is None:
            self.hide()
            return
        component = self.layouts.get(view)
        if not component:
            self.logger.warn(f"Tried to open non-existing layout {view}")
            self.hide()
            return
        if not component.initialized:
            self.init_layout(component)
        if not component.initialized or not component.root:
            self.logger.warn(f"Layout {view} couldn't be initialized")
            self.hide()
            return

        self._show = True
        self.component = component

    def hide(self) -> None:
        self._show = False
        self.component = None

    def register_layout(self, view: str, layout: UIComponent) -> None:
        if view in self.layouts:
            self.logger.warn(f"Overwriting view {view}")
        self.layouts[view] = layout

    def init_layout(self, layout: UIComponent) -> None:
        css = self.load_file(layout.style_file)
        if css is None:
            return
        style = Style()
        style.parse(css)
        text = self.load_file(layout.layout_file)
        if text is None:
            return
        layout.root = UIParser(text).body(style, self.dispatcher)
        layout.compute_layout()

    def load_file(self, path: str) -> str | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Couldn't load file {path}", error=e)
            return None
