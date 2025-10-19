from calliopy.core.raylib import Raylib, KEY_ENTER
from calliopy.core.raylib import WHITE, RAYWHITE
from calliopy.core.annotations import Component
import threading

# TODO: remove
bg_texture = "files/bg_forest.png"
characters = [
    {"image": "files/alice.png", "pos": (0, 200)},
    {"image": "files/bob.png", "pos": (500, 200)},
]


class CalliopyFrontend:
    def __init__(self, width=800, height=600, font_size=24):
        self.screen_width = width
        self.screen_height = height
        self.font_size = font_size
        self.raylib = Raylib()
        self.scene_thread = None
        self.dial = None

    def set_dialogue_manager(self, dial):
        self.dial = dial

    def set_scene_thread(self, scene_thread):
        self.scene_thread = scene_thread

    def run(self):
        raylib = self.raylib
        raylib.init_window(self.screen_width, self.screen_height, "Mini VN")
        raylib.set_target_fps(60)

        bg = raylib.load_texture(bg_texture)
        char_textures = [raylib.load_texture(c["image"]) for c in characters]
        char_positions = [c["pos"] for c in characters]
        char_data = list(zip(char_textures, char_positions))

        C = 0x88000000

        while not raylib.window_should_close():
            raylib.begin_drawing()
            raylib.clear_background(RAYWHITE)
            raylib.draw_texture(bg, 0, 0, WHITE)

            if self.dial.speaker == "Bob":
                tex = char_data[1][0]
                pos = char_data[1][1]
                raylib.draw_texture(tex, pos[0], pos[1], WHITE)
            elif self.dial.speaker == "Alice":
                tex = char_data[0][0]
                pos = char_data[0][1]
                raylib.draw_texture(tex, pos[0], pos[1], WHITE)

            if self.dial.current_text:
                raylib.draw_rectangle(50, 450, 700, 120, C)
                raylib.draw_rectangle_lines(50, 450, 700, 120, WHITE)
                raylib.draw_text(self.dial.current_text, 60, 460, self.font_size, WHITE)

            for i, opt in enumerate(self.dial.options):
                raylib.draw_text(f"{i+1}. {opt}", 60, 500 + i*30, 24, WHITE)

            if self.dial.current_text and raylib.is_key_pressed(KEY_ENTER):
                self.dial.waiting_for_input.set()

            for i in range(len(self.dial.options)):
                if raylib.is_key_pressed(49+i):
                    self.dial.choice_result = i
                    self.dial.waiting_for_input.set()

            raylib.end_drawing()
            if not self.scene_thread.is_alive():
                break

        self.dial.cancel()  # TODO: do for all components

        for tex in char_textures:
            raylib.unload_texture(tex)
        raylib.unload_texture(bg)

        self.scene_thread.join()
        raylib.close_window()


class ChoiceResult:
    def __init__(self, index):
        self.index = index


@Component(tags=["dialogue", "dial"])
class DialogueManager:
    def __init__(self):
        self._abort = False
        self.current_text = ""
        self.speaker = None
        self.mood = None
        self.waiting_for_input = threading.Event()
        self.choice_result = None
        self.options = []

    def say(self, speaker, text):
        if self._abort:
            return
        self.speaker = speaker
        self.current_text = text
        self.waiting_for_input.clear()
        self.waiting_for_input.wait()
        self.current_text = ""

    def choice(self, *options):
        if self._abort:
            return
        self.options = list(options)
        self.choice_result = None
        self.waiting_for_input.clear()
        self.waiting_for_input.wait()
        result = self.choice_result
        self.options = []
        return ChoiceResult(result)

    def cancel(self):
        self._abort = True
        self.waiting_for_input.set()
