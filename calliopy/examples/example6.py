from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp
from calliopy.gui.annotations import UIAction
from calliopy.logger.logger import LoggerFactory
from calliopy.gui.ui_drawable import UIComponent


@UIAction(name="exit")
def exit_action(frontend):
    print("Exit action starts")
    frontend.close()


@Component()
class Menu(UIComponent):
    def __init__(self) -> None:
        self.name = "menu"
        self.x = 300
        self.y = 150
        self.width = 200
        self.height = 400
        self.root = None
        self.initialized = False
        self.layout_file = "files/layout.ui"
        self.style_file = "files/style.css"


@Scene()
def test_scene(dial, gui_manager, gui):
    dial.narrate("UI actions")
    gui.show("menu")
    dial.narrate("menu")
    gui.hide()
    dial.narrate("no menu")
    if gui_manager:
        gui_manager.dispatch_event("exit")
    else:
        print("No GUI manager")
    dial.narrate("Unreachable")


if __name__ == "__main__":
    from calliopy.gui.ui_manager import UIManager
    from calliopy.gui.ui_drawable import UIDrawable

    factory = LoggerFactory.get_factory()
    factory.disable_all()
    factory.enable_for(UIManager)
    factory.enable_for(UIDrawable)

    app = CalliopyApp()
    app.load_module("calliopy.gui")
    app.run()
