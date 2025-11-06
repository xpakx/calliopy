from calliopy.core.raylib import (
        Rectangle,
        draw_rectangle_rec,
        draw_text,
        get_mouse_position, check_collision_point_rec,
        is_mouse_button_pressed,
        MOUSE_BUTTON_LEFT,
)
from calliopy.gui.parser.css import CSSParser


class Style:
    def __init__(self):
        self.rules = {}

    def clear(self):
        self.rules = {}

    def parse(self, text: str):
        parser = CSSParser(text)
        blocks = parser.style()
        for selector, body in blocks:
            self.rules[selector] = body

    def get(self, selector, key, default=None):
        return self.rules.get(selector, {}).get(key, default)

    def get_int(self, selector, key, default=0):
        val = self.get(selector, key)
        return int(val) if val and val.isdigit() else default

    def resolve(self, element, state=None):
        state = state or "normal"
        out = {}
        base_sel = element.selector

        candidates = [base_sel]
        candidates += [f"{base_sel}.{cls}" for cls in element.classes]
        if state == "hover":
            candidates += [f"{s}:hover" for s in candidates]

        for sel in candidates:
            if sel in self.rules:
                out.update(self.rules[sel])

        return out


class Element:
    def __init__(self, selector, style: Style, classes=None, children=None):
        self.selector = selector
        self.classes = classes or []
        self.style = style
        self.children = children or []
        self.rect = Rectangle(0, 0, 0, 0)
        self.text = None
        self.hover = False
        self.bg = None
        self.fg = 0xFFFFFFFF
        self.padding = 0
        self.default_bg = None
        self.default_fg = "#fff"

    def compute_layout(self, x, y, available_w, available_h):
        props = self.style.resolve(self)
        w = int(props.get("width", "100"))
        h = int(props.get("height", "30"))
        self.rect = Rectangle(x, y, w, h)
        self.update_style()

    def draw(self):
        if (self.bg):
            draw_rectangle_rec(self.rect, self.bg)
        if (self.text):
            draw_text(self.text,
                      int(self.rect.x + self.padding),
                      int(self.rect.y + self.padding),
                      20,
                      self.fg)

    def update_style(self):
        state = "hover" if self.hover else "normal"
        props = self.style.resolve(self, state)
        bg = props.get("bg", self.default_bg)
        fg = props.get("fg", self.default_fg)
        self.bg = _parse_color(bg) if bg else None
        self.fg = _parse_color(fg) if fg else None
        self.padding = int(props.get("padding", "4"))

    def update(self):
        mouse = get_mouse_position()
        old_hover = self.hover
        self.hover = check_collision_point_rec(mouse, self.rect)
        if self.hover != old_hover:
            self.update_style()

    def print(self, indent=0):
        pad = "  " * indent
        print(f"{pad}{self.__class__.__name__} {self.selector}"
              f" {self.classes} {self.text or ''}")
        if self.children:
            print(f"{pad}children:")
            for e in self.children:
                e.print(indent + 1)


# -------- LAYOUTS -------- #
class VBox(Element):
    def __init__(self, style, children=None):
        super().__init__("vbox", style, children=children)

    def compute_layout(self, x, y, available_w, available_h):
        spacing = int(self.style.resolve(self).get("spacing", "4"))
        current_y = y
        for child in self.children:
            child.compute_layout(x, current_y, available_w, available_h)
            current_y += child.rect.height + spacing
        total_height = current_y - y
        self.rect = Rectangle(x, y, available_w, total_height)
        self.update_style()

    def draw(self):
        super().draw()
        for child in self.children:
            child.draw()

    def update(self):
        for child in self.children:
            if hasattr(child, "update"):
                child.update()


# -------- ELEMS -------- #
class Button(Element):
    def __init__(
            self, text, style, classes=None, dispatcher=None, callback=None
    ):
        super().__init__("button", style, classes)
        self.text = text
        self.callback = callback
        self.dispatcher = dispatcher
        self.default_bg = "#555"

    def update(self):
        super().update()
        if self.hover and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.dispatcher:
                self.dispatcher.dispatch_event(
                        self.callback, self
                )


def _parse_color(hexstr: str) -> int:
    hexstr = hexstr.lstrip("#")

    if len(hexstr) == 3:
        hexstr = "".join(c * 2 for c in hexstr)

    if len(hexstr) == 6:
        hexstr += "ff"

    r = int(hexstr[0:2], 16)
    g = int(hexstr[2:4], 16)
    b = int(hexstr[4:6], 16)
    a = int(hexstr[6:8], 16)

    return (a << 24) | (b << 16) | (g << 8) | r


def _create_element(
        tag, style, classes, src=None, dispatcher=None, action=None
):
    if tag == "vbox":
        return VBox(style)
    elif tag == "button":
        return Button("", style, classes, dispatcher, action)
    return Element(tag, style, classes)


if __name__ == "__main__":
    from calliopy.core.raylib import (
        init_window, close_window, begin_drawing, end_drawing,
        clear_background, set_target_fps, window_should_close,
        BLACK
    )
    from calliopy.gui.parser.layout import UIParser

    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    class EventDispatcher:
        def __init__(self):
            pass

        def dispatch_event(self, name, owner, event=None):
            print(f"Clicked {owner.text}, event {name}")
            if event:
                print(event)

    dispatcher = EventDispatcher()

    init_window(800, 600, "UI Menu Demo")
    set_target_fps(60)

    css = load_file("files/style.css")
    style = Style()
    style.parse(css)
    text = load_file("files/layout.ui")
    root = UIParser(text).body(style, dispatcher)
    root.compute_layout(300, 200, 200, 400)

    while not window_should_close():
        root.update()
        begin_drawing()
        clear_background(BLACK)
        root.draw()
        end_drawing()
    close_window()
