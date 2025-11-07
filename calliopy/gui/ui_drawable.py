from calliopy.logger.logger import LoggerFactory
from calliopy.core.annotations import Component
from calliopy.core.frontend import DrawableComponent
from calliopy.gui.ui import Element


@Component(tags=["ui", "gui"])
class UIDrawable(DrawableComponent):
    def __init__(self):
        self.logger = LoggerFactory.get_logger()
        self.layouts: dict[str, Element] = {}
        self.root: Element | None = None
        self._show = False

    def draw(self):
        if self.root:
            self.root.draw()

    def init(self) -> None:
        for key, layout in self.layouts.items():
            self.logger.debug(f"Initializing layout {key}")
            layout.compute_layout(300, 150, 200, 400)

    def update(self) -> None:
        if self.root:
            self.root.update()

    def is_active(self) -> bool:
        return self.root is not None and self._show

    def destroy(self) -> None:
        # TODO: unload all images
        pass

    def show(self, view: str | None) -> None:
        if view is None:
            self.hide()
            return
        root = self.layouts.get(view)
        if not root:
            self.logger.warn(f"Tried to open non-existing layout {view}")
            self.hide()
            return
        self._show = True
        self.root = root

    def hide(self) -> None:
        self._show = False
        self.root = None

    # TODO: make a UIComponent class that will define x, y, w, h,
    # and layout/style files
    def register_layout(self, view: str, root: Element) -> None:
        if view in self.layouts:
            self.logger.warn(f"Overwriting view {view}")
        self.layouts[view] = root
