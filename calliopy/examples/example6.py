from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp
from calliopy.gui.annotations import UIAction
from calliopy.logger.logger import LoggerFactory
from calliopy.gui.ui_drawable import UIComponent
from dataclasses import dataclass


@UIAction(name="exit")
def exit_action(frontend):
    print("Exit action starts")
    frontend.close()


@UIAction(name="new_game")
def start_game_action(gui):
    gui.kill_lock()
    gui.hide()


@Component()
@dataclass
class Menu(UIComponent):
    name = "menu"
    x = 300
    y = 150
    width = 200
    height = 400
    layout_file = "files/layout.ui"
    style_file = "files/style.css"


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
