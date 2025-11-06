from calliopy.core.annotations import Scene
from calliopy.core.app import CalliopyApp
from calliopy.gui.annotations import UIAction
from calliopy.logger.logger import LoggerFactory


@UIAction(name="exit")
def exit_action(dial):
    print("Exit action starts")
    dial.cancel()


@Scene()
def test_scene(dial, gui):
    dial.narrate("UI actions")
    if gui:
        gui.dispatch_action("exit")
    else:
        print("No GUI manager")
    dial.narrate("Unreachable")


if __name__ == "__main__":
    load_gui = True

    factory = LoggerFactory.get_factory()
    factory.disable_all()
    if load_gui:
        from calliopy.gui.ui_manager import UIManager
        factory.enable_for(UIManager)
    app = CalliopyApp()
    if load_gui:
        app.load_module("calliopy.gui")
    app.run()
