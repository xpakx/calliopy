from calliopy.core.raylib import draw_rectangle
from calliopy.core.annotations import Component
from calliopy.core.drawable import DrawableComponent
from calliopy.logger.logger import LoggerFactory
from calliopy.core.animation import Animation, FieldForAnimation, Ease
from dataclasses import dataclass


@dataclass
class Transition:
    first_part: Animation
    second_part: Animation | None = None


class TransitionLib:
    @classmethod
    def fade(cls, overlay):
        return Transition(
            first_part=Animation(
                name="overlay",
                duration=1.5,
                start_value=0.0,
                end_value=1.0,
                soft_block=True,
                field=FieldForAnimation(overlay, "opacity"),
                ease_func=Ease.ease_out_cubic
            ),
            second_part=Animation(
                name="overlay",
                duration=1.5,
                start_value=1.0,
                end_value=0.0,
                field=FieldForAnimation(overlay, "opacity"),
                on_end=lambda: overlay.end_transiton(),
                ease_func=Ease.ease_in_cubic
            ),
        )


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
        self.after_switch = False

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
        if not self.active and self.after_switch:
            print(self.active)
        return self.active

    def after_scene_give_control(self) -> None:
        # TODO: add more two-part and one-part transitions
        if self.after_switch and not self.dial.transition_key:
            self.fade_in()
            self.after_switch = False
        if self.dial.transition_key:
            self.fade_out()
            self.after_switch = True

    def z_index(self) -> None:
        return 9000

    def end_transiton(self) -> None:
        self.active = False

    def fade_in(self) -> None:
        self.active = True
        self.time_passed = 0
        anim = TransitionLib.fade(self).second_part
        if anim:
            self.anim.animate(anim)

    def fade_out(self) -> None:
        self.active = True
        self.time_passed = 0
        anim = TransitionLib.fade(self).first_part
        self.anim.animate(anim)

    def on_new_scene(self) -> None:
        pass
