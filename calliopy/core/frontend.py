from calliopy.core.raylib import Raylib, KEY_ENTER
from calliopy.core.raylib import WHITE, RAYWHITE
from calliopy.core.raylib import Rectangle, Vector2
from calliopy.core.annotations import Component
from calliopy.logger.logger import LoggerFactory
from greenlet import greenlet

# TODO: remove
bg_texture = "files/bg_forest.png"
characters = [
    {"image": "files/alice.png", "pos": (0, 200)},
    {"image": "files/bob.png", "pos": (500, 200)},
]

log_level = {
        1: "TRACE", 2: "DEBUG", 3: "INFO",
        4: "WARNING", 5: "ERROR", 6: "FATAL",
}


def get_raylib_logger():
    logger = LoggerFactory.get_logger(for_cls="raylib")

    def trace_callback(level, message):
        lvl = log_level[level]
        logger.debug(f"[raylib:{lvl}] {message.decode('utf-8')}")
    return trace_callback


class CalliopyFrontend:
    def __init__(self, width=800, height=600, font_size=24):
        self.screen_width = width
        self.screen_height = height
        self.font_size = font_size
        self.raylib = Raylib()
        self.scheduler = None
        self.dial = None

    def set_dialogue_manager(self, dial):
        self.dial = dial

    def set_scheduler(self, scheduler):
        self.scheduler = scheduler

    def set_script(self, script):
        self.script = script

    def run(self):
        raylib = self.raylib
        trace_callback = get_raylib_logger()
        raylib.set_trace_log_callback(trace_callback)
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

            bg_w, bg_h = bg.width, bg.height
            scale = max(self.screen_width / bg_w, self.screen_height / bg_h)

            raylib.draw_texture_pro(
                bg,
                Rectangle(0, 0, bg_w, bg_h),
                Rectangle(0, 0, bg_w * scale, bg_h * scale),
                Vector2(0, 0),
                0,
                WHITE
            )

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

            proceed_scene = False
            if self.dial.current_text and raylib.is_key_pressed(KEY_ENTER):
                proceed_scene = True
            for i in range(len(self.dial.options)):
                if raylib.is_key_pressed(49+i):
                    self.dial.choice_result = i
                    proceed_scene = True
            if not self.scheduler.current:
                proceed_scene = True

            if proceed_scene:
                if self.scheduler.current and not self.scheduler.current.dead:
                    self.scheduler.resume()
                else:
                    tag = self.scheduler.result
                    new_scene, kwargs = self.script.get_next_scene(tag)
                    if new_scene is None:
                        break
                    self.scheduler.run_scene(new_scene, **kwargs)

            raylib.end_drawing()

        self.dial.cancel()  # TODO: do for all components

        for tex in char_textures:
            raylib.unload_texture(tex)
        raylib.unload_texture(bg)

        raylib.close_window()


class ChoiceResult:
    def __init__(self, index):
        self.index = index


@Component(tags="scene_scheduler")
class SceneScheduler:
    def __init__(self):
        self.current = None
        self.main = greenlet.getcurrent()
        self.result = None

    def run_scene(self, scene_func, *args, **kwargs):
        g = greenlet(lambda: scene_func(*args, **kwargs))
        self.current = g
        g.switch()

    def resume(self):
        if self.current and not self.current.dead:
            self.result = self.current.switch()


@Component(tags=["dialogue", "dial"])
class DialogueManager:
    def __init__(self, scene_scheduler):
        self.scheduler = scene_scheduler
        self._abort = False
        self.current_text = ""
        self.speaker = None
        self.mood = None
        self.choice_result = None
        self.options = []

    def say(self, speaker, text):
        if self._abort:
            return
        self.speaker = speaker
        self.current_text = text
        self.scheduler.main.switch()
        self.current_text = ""

    def choice(self, *options):
        if self._abort:
            return ChoiceResult(0)
        self.options = list(options)
        self.choice_result = None
        self.scheduler.main.switch()
        result = self.choice_result
        self.options = []
        return ChoiceResult(result)

    def narrate(self, text):
        if self._abort:
            return
        self.speaker = None
        self.current_text = text
        self.scheduler.main.switch()
        self.current_text = ""

    def cancel(self):
        self._abort = True
