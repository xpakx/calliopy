from dataclasses import dataclass
from typing import Callable, Any


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
        if self.on_update:
            self.on_update(t)
        if self.field:
            value = self.get_value(t)
            setattr(self.field.obj, self.field.field_name, value)
        if self.elapsed >= self.duration:
            if self.on_end:
                self.on_end()
            return True
        return False

    def get_value(self, t: float):
        return self.start_value +\
                (self.end_value - self.start_value) * t


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
            "\r" + f"Progress: {t:.2f} | x = {dummy.x:.2f}",
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
    )

    while not anim.tick(1 / 60):
        time.sleep(1 / 60)
    print("")
