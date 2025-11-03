from calliopy.core.raylib import (
        set_trace_log_callback, set_target_fps, window_should_close,
        clear_background, draw_texture_pro, draw_texture, draw_rectangle,
        draw_rectangle_lines, draw_text, close_window, unload_texture,
        init_window, load_texture, begin_drawing, end_drawing,
        is_key_pressed, play_sound,
        TRACELOGCALLBACK
)
from calliopy.core.raylib import WHITE, RAYWHITE, KEY_ENTER
from calliopy.core.raylib import Rectangle, Vector2
from calliopy.core.annotations import Component
from calliopy.core.script import ScriptManager
from calliopy.logger.logger import LoggerFactory
from calliopy.core.audio import AudioManager
from greenlet import greenlet
from dataclasses import dataclass

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


@Component(tags="front_config")
@dataclass
class FrontendConfig:
    width: int = 800
    height: int = 600
    font_size = 24


@Component(tags="frontend")
class CalliopyFrontend:

    def __init__(
            self,
            front_config: FrontendConfig,
            dial,
            scene_scheduler,
            char_manager,
            script: ScriptManager,
            audio_manager: AudioManager,
    ):
        if not issubclass(front_config.__class__, FrontendConfig):
            raise Exception("Frontend config must extend FrontendConfig class")
        self.screen_width = front_config.width
        self.screen_height = front_config.height
        self.font_size = front_config.font_size
        self.scheduler = scene_scheduler
        self.dial = dial
        self.chars = char_manager
        self.script = script
        self.audio = audio_manager

    def draw_background(self, bg):
        clear_background(RAYWHITE)

        bg_w, bg_h = bg.width, bg.height
        scale = max(self.screen_width / bg_w, self.screen_height / bg_h)

        draw_texture_pro(
            bg,
            Rectangle(0, 0, bg_w, bg_h),
            Rectangle(0, 0, bg_w * scale, bg_h * scale),
            Vector2(0, 0),
            0,
            WHITE
        )

    def draw_speaker(self):
        for key, value in self.chars.visible.items():
            c = self.chars.get_texture(key.capitalize())
            if c is None:
                continue
            tex = c['texture']
            pos = value.pos
            draw_texture(tex, pos[0], pos[1], WHITE)

    def draw_dialogue(self, text: str, bg_col, txt_col):
        draw_rectangle(50, 450, 700, 120, bg_col)
        draw_rectangle_lines(50, 450, 700, 120, WHITE)
        draw_text(text, 60, 460, self.font_size, txt_col)

    def run(self):
        trace_callback = TRACELOGCALLBACK(get_raylib_logger())
        set_trace_log_callback(trace_callback)
        init_window(self.screen_width, self.screen_height, "Mini VN")
        set_target_fps(60)

        self.audio.init_device()
        self.audio.preload("dialogue", "files/dialogue.mp3")

        bg = load_texture(self.chars.bg_texture)

        DIAL_COLOR = 0x88000000
        txt_col = WHITE

        while not window_should_close():
            begin_drawing()
            self.draw_background(bg)
            self.draw_speaker()

            if self.dial.current_text:
                self.draw_dialogue(self.dial.current_text, DIAL_COLOR, txt_col)

            for i, opt in enumerate(self.dial.options):
                draw_text(f"{i+1}. {opt}", 60, 500 + i*30, 24, WHITE)

            proceed_scene = False
            if self.dial.current_text and is_key_pressed(KEY_ENTER):
                proceed_scene = True
            for i in range(len(self.dial.options)):
                if is_key_pressed(49+i):
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
                    self.chars.reset()
                    self.scheduler.run_scene(new_scene, **kwargs)
                self.chars.reset_temp()
                if self.chars.auto_speaker_portraits:
                    if self.dial.speaker:
                        self.chars.show_temp(self.dial.speaker)
                txt_col = WHITE
                if self.dial.speaker:
                    col = self.chars.get_character_color(self.dial.speaker)
                    if col is not None:
                        txt_col = col
                self.chars.update_moods_from_chars()
                to_play = self.audio.get_sound()
                if to_play:
                    play_sound(to_play)

            end_drawing()

        self.dial.cancel()  # TODO: do for all components
        self.chars.unload_all()
        unload_texture(bg)

        self.audio.destroy()

        close_window()


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
