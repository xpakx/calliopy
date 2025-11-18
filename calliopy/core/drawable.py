from abc import ABC, abstractmethod
from calliopy.core.raylib import (
        draw_texture, draw_rectangle,
        draw_rectangle_lines, draw_text,
        WHITE
)
from calliopy.core.annotations import Component
from calliopy.logger.logger import LoggerFactory
from calliopy.core.animation import AnimationLib, Animation, FieldForAnimation, Ease
from calliopy.core.dialogue import DialogueManager


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

    def on_progress_scene_ready(self) -> False:
        return False  # isBlocking

    def on_new_scene(self) -> None:
        pass

    def z_index(self) -> int:
        # 0 = background; 100 = portraits, 200 = dialogue
        # <=300 for user defined
        return 300


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
            dial,
    ) -> None:
        self.time_passed = 0
        self.anim = anim_manager
        self.logger = LoggerFactory.get_logger()
        self.active = False
        self.opacity = 0.0
        self.width = front_config.width
        self.height = front_config.height
        self.dial = dial

    def init(self) -> None:
        pass

    def destroy(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.time_passed += dt

    def draw(self) -> None:
        a = int(0xFF * self.opacity)
        color = (a << 24) | 0x00000000
        draw_rectangle(0, 0, self.width, self.height, color)

    def is_active(self) -> bool:
        return self.active

    def after_scene_give_control(self) -> None:
        if self.dial.transition_key:
            self.dial.transition_key = None
            # TODO
            self.start_transition()

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
            start_value=1.0,
            end_value=0.0,
            soft_block=True,
            field=FieldForAnimation(self, "opacity"),
            on_end=lambda: self.end_transiton(),
            ease_func=Ease.ease_in_cubic
        )
        self.anim.animate(anim)

    def on_new_scene(self) -> None:
        pass


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
