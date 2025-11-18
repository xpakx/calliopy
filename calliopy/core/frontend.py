from calliopy.core.raylib import (
        set_trace_log_callback, set_target_fps, window_should_close,
        clear_background, draw_texture_pro,
        close_window, unload_texture,
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
from calliopy.core.dialogue import DialogueManager, SceneScheduler
from calliopy.core.drawable import DrawableComponent
from calliopy.core.timer import TimeManager
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
    title: str = "Calliopy Visual Novel"


@Component(tags="frontend")
class CalliopyFrontend:

    def __init__(
            self,
            front_config: FrontendConfig,
            dial: DialogueManager,
            scene_scheduler: SceneScheduler,
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
                self.anim.on_script_control()
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
        if is_key_pressed(KEY_ENTER):
            self.anim.soft_blocking = False

        pause_ended, blocking = self.timers.process_timers(dt)
        if not proceed_scene:
            proceed_scene = pause_ended
        if blocking:
            proceed_scene = False
        if self.anim.blocking or self.anim.soft_blocking:
            proceed_scene = False
        return proceed_scene

    def close(self) -> None:
        self.dial.cancel()
        self.should_close = True
