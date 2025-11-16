from calliopy.core.raylib import (
        set_trace_log_callback, set_target_fps, window_should_close,
        clear_background, draw_texture_pro, draw_texture, draw_rectangle,
        draw_rectangle_lines, draw_text, close_window, unload_texture,
        init_window, load_texture, begin_drawing, end_drawing,
        is_key_pressed, play_sound, get_frame_time,
        TRACELOGCALLBACK
)
from calliopy.core.raylib import WHITE, RAYWHITE, KEY_ENTER
from calliopy.core.raylib import Rectangle, Vector2
from calliopy.core.annotations import Component, Inject
from calliopy.core.script import ScriptManager
from calliopy.logger.logger import LoggerFactory
from calliopy.core.audio import AudioManager
from calliopy.core.animation import AnimationLib, Animation, FieldForAnimation
from calliopy.core.timer import TimeManager
from greenlet import greenlet
from dataclasses import dataclass
from abc import ABC, abstractmethod

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
    title: str = "Calliopy Visual Novel"


class DrawableComponent(ABC):
    @abstractmethod
    def init(self) -> None:
        """Initializes drawable component"""
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Deinitializes drawable component"""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Updates drawable component before drawing"""
        pass

    @abstractmethod
    def draw(self) -> None:
        """Draws drawable component"""
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """Return whether drawable should be updated and drawn"""
        pass

    def after_scene_give_control(self) -> None:
        pass

    def on_new_scene(self) -> None:
        pass

    def z_index(self) -> int:
        # 0 = background; 100 = portraits, 200 = dialogue
        # <=300 for user defined
        return 300


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
            gui,
            time_manager: TimeManager,
            anim_manager
    ):
        if not issubclass(front_config.__class__, FrontendConfig):
            raise Exception("Frontend config must extend FrontendConfig class")
        self.screen_width = front_config.width
        self.screen_height = front_config.height
        self.window_title = front_config.title
        self.font_size = front_config.font_size
        self.scheduler = scene_scheduler
        self.dial = dial
        self.chars = char_manager
        self.script = script
        self.audio = audio_manager
        self.gui = gui
        self.drawables = []
        self.timers = time_manager
        self.should_close = False
        self.anim = anim_manager

    @Inject()
    def set_drawables(self, drawables: list[DrawableComponent]) -> None:
        self.drawables = drawables
        self.drawables.sort(key=lambda s: s.z_index())

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

    def run(self):
        trace_callback = TRACELOGCALLBACK(get_raylib_logger())
        set_trace_log_callback(trace_callback)
        init_window(self.screen_width, self.screen_height, self.window_title)
        set_target_fps(60)

        self.audio.init_device()
        self.audio.preload("dialogue", "files/dialogue.mp3")

        bg = load_texture(self.chars.bg_texture)

        for drawable in self.drawables:
            drawable.init()

        while not window_should_close() and not self.should_close:
            dt = get_frame_time()
            for drawable in self.drawables:
                if drawable.is_active():
                    drawable.update(dt)
            begin_drawing()
            self.draw_background(bg)

            self.anim.tick(dt)
            for drawable in self.drawables:
                if drawable.is_active():
                    drawable.draw()

            proceed_scene = self.tick(dt)

            if proceed_scene:
                self.timers.reset_timers()
                has_scene = self.resume_scene()
                if not has_scene:
                    break
                for drawable in self.drawables:
                    drawable.after_scene_give_control()
                self.update_sounds()
                self.timers.update(self.dial)

            end_drawing()

        self.close()
        unload_texture(bg)
        for drawable in self.drawables:
            drawable.destroy()

        self.audio.destroy()

        close_window()

    def resume_scene(self) -> bool:
        if self.scheduler.current and not self.scheduler.current.dead:
            self.scheduler.resume()
        else:
            tag = self.scheduler.result
            new_scene, kwargs = self.script.get_next_scene(tag)
            if new_scene is None:
                return False
            for drawable in self.drawables:
                drawable.on_new_scene()
            self.scheduler.run_scene(new_scene, **kwargs)
        return True

    def update_sounds(self) -> None:
        to_play = self.audio.get_sound()
        if to_play:
            play_sound(to_play)

    def tick(self, dt: float) -> bool:
        proceed_scene = False
        if self.dial.current_text and is_key_pressed(KEY_ENTER):
            proceed_scene = True
        for i in range(len(self.dial.options)):
            if is_key_pressed(49+i):
                self.dial.choice_result = i
                proceed_scene = True
        if not self.scheduler.current:
            proceed_scene = True
        if self.dial.paused and is_key_pressed(KEY_ENTER):
            proceed_scene = True

        pause_ended, blocking = self.timers.process_timers(dt)
        if not proceed_scene:
            proceed_scene = pause_ended
        if blocking:
            proceed_scene = False
        return proceed_scene

    def close(self) -> None:
        self.dial.cancel()
        self.should_close = True


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
        self.paused = None
        self.pause_for = 0
        self.blocking_pause = False

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

    def pause(
            self, seconds: int | float | None = None,
            blocking: bool = False
    ):
        self.paused = True
        self.pause_for = 0
        self.blocking_pause = blocking
        if seconds is not None:
            self.pause_for = float(seconds)
        if self._abort:
            return
        self.speaker = None
        self.current_text = None
        self.scheduler.main.switch()
        self.paused = False
        self.pause_for = 0
        self.blocking_pause = False

    def cancel(self):
        self._abort = True


@Component(if_true="not custom_dialogue")
class DrawableDialogue(DrawableComponent):
    def __init__(self, dial: DialogueManager, chars, front_config) -> None:
        self.dial = dial
        self.chars = chars
        self.dial_color = 0x88000000
        self.font_size = front_config.font_size
        self.text_color = WHITE

    def init(self) -> None:
        pass

    def destroy(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        if self.dial.current_text:
            self.draw_dialogue()
        elif self.dial.options:
            self.draw_choice()

    def draw_dialogue(self) -> None:
        text = self.dial.current_text
        draw_rectangle(50, 450, 700, 120, self.dial_color)
        draw_rectangle_lines(50, 450, 700, 120, WHITE)
        draw_text(text, 60, 460, self.font_size, self.text_color)

    def draw_choice(self) -> None:
        for i, opt in enumerate(self.dial.options):
            draw_text(f"{i+1}. {opt}", 60, 500 + i*30, 24, WHITE)

    def is_active(self) -> bool:
        return self.dial.current_text or len(self.dial.options) > 0

    def get_current_dialogue_color(self) -> int:
        txt_col = WHITE
        if self.dial.speaker:
            col = self.chars.get_character_color(self.dial.speaker)
            if col is not None:
                txt_col = col
        return txt_col

    def after_scene_give_control(self) -> None:
        self.text_color = self.get_current_dialogue_color()

    def z_index(self) -> None:
        return 200


@Component(if_true="not custom_images")
class DrawableImages(DrawableComponent):
    def __init__(
            self,
            dial: DialogueManager,
            chars,
            front_config,
            anim_manager
    ) -> None:
        self.chars = chars
        self.dial = dial
        self.time_passed = 0
        self.anim = anim_manager
        self.logger = LoggerFactory.get_logger()

    def init(self) -> None:
        pass

    def destroy(self) -> None:
        self.chars.unload_all()

    def update(self, dt: float) -> None:
        self.time_passed += dt

    def draw(self) -> None:
        for key, value in self.chars.visible.items():
            c = self.chars.get_texture(key.capitalize())
            if c is None:
                continue
            tex = c['texture']
            pos = value.pos
            draw_texture(tex, pos[0], pos[1], value.color)

    def is_active(self) -> bool:
        return True

    def after_scene_give_control(self) -> None:
        self.change_portraits_for_scene()

    def z_index(self) -> None:
        return 100

    def change_portraits_for_scene(self) -> None:
        self.chars.reset_temp()
        if self.chars.auto_speaker_portraits:
            if self.dial.speaker:
                self.chars.show_temp(self.dial.speaker)
        self.chars.update_moods_from_chars()

        for key, value in self.chars.visible.items():
            self.register_animation(value)

    def register_animation(self, value):
        anim = value.animation
        if not anim:
            return
        if type(anim) is str and AnimationLib.has_animation(anim):
            anim_method = getattr(AnimationLib, anim)
            # TODO: only single-param animations should be
            # usable for str-based registering
            # or, optionally, we could add way to pass params
            anim = anim_method(value)
        if not isinstance(anim, Animation):
            self.logger.warn(f"Unknown animation {anim}")
            return
        self.anim.animate(anim)

    def on_new_scene(self) -> None:
        self.chars.reset()
        self.time_passed = 0


@Component(if_true="not custom_overlay")
class DrawableOverlay(DrawableComponent):
    def __init__(
            self,
            front_config,
            anim_manager,
    ) -> None:
        self.time_passed = 0
        self.anim = anim_manager
        self.logger = LoggerFactory.get_logger()
        self.active = False
        self.opacity = 0.0
        self.width = front_config.width
        self.height = front_config.height

    def init(self) -> None:
        pass

    def destroy(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.time_passed += dt

    def draw(self) -> None:
        opacity = 1 - abs(2*self.opacity - 1)
        a = int(0xFF * opacity)
        color = (a << 24) | 0x00000000
        draw_rectangle(0, 0, self.width, self.height, color)

    def is_active(self) -> bool:
        return self.active

    def after_scene_give_control(self) -> None:
        pass

    def z_index(self) -> None:
        return 9000

    def end_transiton(self) -> None:
        self.active = False

    def start_transition(self) -> None:
        self.active = True
        self.time_passed = 0
        anim = Animation(
            name="overlay",
            duration=1.5,
            start_value=0.0,
            end_value=1.0,
            field=FieldForAnimation(self, "opacity"),
            on_end=lambda: self.end_transiton()
        )
        self.anim.animate(anim)

    def on_new_scene(self) -> None:
        pass
