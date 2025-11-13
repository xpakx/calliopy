from dataclasses import dataclass
from typing import Callable, Any
from calliopy.core.annotations import Component


@dataclass
class FieldForAnimation:
    obj: Any
    field_name: str


@dataclass
class Animation:
    name: str
    duration: float
    start_value: float
    end_value: float
    elapsed: float = 0.0
    on_update: Callable[[float], None] | None = None
    on_end: Callable[[], None] | None = None
    field: FieldForAnimation | None = None
    ease_func: Callable[[float], float] = lambda t: t

    def tick(self, dt: float) -> bool:
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        t = self.ease_func(t)
        value = self.get_value(t)
        if self.on_update:
            self.on_update(value)
        if self.field:
            setattr(self.field.obj, self.field.field_name, value)
        if self.elapsed >= self.duration:
            if self.on_end:
                self.on_end()
            return True
        return False

    def get_value(self, t: float):
        return self.start_value +\
                (self.end_value - self.start_value) * t


class Ease:
    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t ** 3

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return (t - 1) ** 3 + 1

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t ** 3 if t < 0.5 else (t - 1) * (2 * t - 2) ** 2 + 1


class AnimationLib:
    @staticmethod
    def fade_in_color(value, t: float):
        new_a = int(0xFF * t)
        value.color = (new_a << 24) | (0x00FFFFFF & value.color)

    @classmethod
    def fadein(
            cls, image, total_time: int = 0.2,
            ease: Callable[[float], float] = Ease.linear
    ):
        return Animation(
            name=f"fadein_{image.name}",
            duration=total_time,
            start_value=0.0,
            end_value=1.0,
            on_update=lambda t: cls.fade_in_color(image, t),
            ease_func=ease
        )

    @classmethod
    def fadeout(
            cls, image, total_time: int = 0.2,
            ease: Callable[[float], float] = Ease.linear
    ):
        return Animation(
            name=f"fadeout_{image.name}",
            duration=total_time,
            start_value=1.0,
            end_value=0.0,
            on_update=lambda t: cls.fade_in_color(image, t),
            ease_func=ease
        )

    @classmethod
    def has_animation(cls, name: str) -> bool:
        attr = cls.__dict__.get(name)
        return isinstance(attr, classmethod)


@Component(tags=["anim", "anim_manager"])
class AnimationManager:
    def __init__(self):
        self.animations: list[Animation] = []

    def animate(self, animation: Animation):
        self.animations.append(animation)

    def tick(self, dt: float):
        i = 0
        while i < len(self.animations):
            anim = self.animations[i]
            if anim.tick(dt):
                self.animations[i] = self.animations[-1]
                self.animations.pop()
            else:
                i += 1

    def clear(self):
        for anim in self.animations:
            anim.tick(anim.duration)
        self.animations.clear()


if __name__ == "__main__":
    import time

    class Dummy:
        def __init__(self):
            self.x = 0.0

    dummy = Dummy()

    anim = Animation(
        name="move_x",
        duration=2.0,
        start_value=0.0,
        end_value=100.0,
        field=FieldForAnimation(dummy, "x"),
        on_update=lambda t: print(
            "\r" + f"Progress: {t/100.0:.2f} | x = {dummy.x:.2f}",
            end="",
            flush=True
        ),
        on_end=lambda: print("\nAnimation done!")
    )

    while not anim.tick(1 / 60):
        time.sleep(1 / 60)

    text = "Printable text"
    total_len = len(text)

    def update(t: float):
        n = int(total_len * t)
        print("\r" + text[:n], end="", flush=True)

    anim = Animation(
        name="typewriter",
        duration=0.1 * len(text),
        start_value=0.0,
        end_value=1.0,
        on_update=update,
        ease_func=Ease.ease_in_quad
    )

    while not anim.tick(1 / 60):
        time.sleep(1 / 60)
    print("")
