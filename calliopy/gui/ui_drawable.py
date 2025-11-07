from calliopy.logger.logger import LoggerFactory
from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DrawableComponent
from calliopy.gui.ui import Element, Style
from calliopy.gui.parser.layout import UIParser


# TODO: make this usable like Character class
class UIComponent:
    def __init__(self, front_config) -> None:
        self.name = "component"
        self.x: int = 0
        self.y: int = 0
        self.width: int = front_config.width
        self.height: int = front_config.height
        self.root: Element | None = None
        self.initialized = False
        self.layout_file: str = ""
        self.style_file: str = ""

    def compute_layout(self) -> None:
        if not self.root:
            return
        self.root.compute_layout(self.x, self.y, self.width, self.height)
        self.initialized = True


@Component(tags=["ui", "gui"])
class UIDrawable(DrawableComponent):
    def __init__(self, gui_manager):
        self.logger = LoggerFactory.get_logger()
        self.layouts: dict[str, UIComponent] = {}
        self.component: UIComponent | None = None
        self._show = False
        self.dispatcher = gui_manager

    @Inject()
    def set_layouts(self, layouts: list[UIComponent]) -> None:
        for layout in layouts:
            self.register_layout(layout.name, layout)

    def draw(self):
        if self.component:
            self.component.root.draw()

    def init(self) -> None:
        pass

    def update(self) -> None:
        if self.component:
            self.component.root.update()

    def is_active(self) -> bool:
        return self.component is not None and self._show

    def destroy(self) -> None:
        # TODO: unload all images
        pass

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
