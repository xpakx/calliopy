from calliopy.core.annotations import Scene
from calliopy.core.app import CalliopyApp
from calliopy.gui.annotations import UIAction
from calliopy.logger.logger import LoggerFactory


@UIAction(name="exit")
def exit_action(frontend):
    print("Exit action starts")
    frontend.close()


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
    load_gui = True

    factory = LoggerFactory.get_factory()
    factory.disable_all()
    if load_gui:
        from calliopy.gui.ui_manager import UIManager
        from calliopy.gui.ui_drawable import UIDrawable
        factory.enable_for(UIManager)
        factory.enable_for(UIDrawable)
    app = CalliopyApp()
    if load_gui:
        app.load_module("calliopy.gui")
        from calliopy.gui.parser.layout import UIParser
        from calliopy.gui.ui import Style

        def load_file(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        dispatcher = app.container.get_component(None, "gui_manager")
        ui = app.container.get_component(None, "gui")

        css = load_file("files/style.css")
        style = Style()
        style.parse(css)
        text = load_file("files/layout.ui")
        root = UIParser(text).body(style, dispatcher)
        ui.register_layout("menu", root)
    app.run()
