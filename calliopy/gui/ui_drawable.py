from calliopy.logger.logger import LoggerFactory
from calliopy.core.annotations import Component
from calliopy.core.frontend import DrawableComponent


@Component(tags=["ui", "gui"])
class UIDrawable(DrawableComponent):
    def __init__(self):
        self.logger = LoggerFactory.get_logger()
        self.root = None
        self.show = False

    def draw(self):
        if self.root:
            self.root.draw()

    def init(self) -> None:
        if self.root:
            self.root.compute_layout(300, 150, 200, 400)

    def update(self) -> None:
        if self.root:
            self.root.update()

    def is_active(self) -> bool:
        return self.root is not None and self.show

    def destroy(self) -> None:
        # TODO: unload all images
        pass
