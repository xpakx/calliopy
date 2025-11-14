from calliopy.core.annotations import Component
from typing import Callable
from dataclasses import dataclass


@dataclass
class Timer:
    name: str
    timer: float
    blocking: bool = False
    permanent: bool = False
    kill: bool = False
    after: Callable[[str], None] | None = None
    ontick: Callable[[str, float], None] | None = None


@Component(tags=["time_manager", "timers"])
class TimeManager:
    def __init__(self) -> None:
        self.timers: list[Timer] = []

    def reset_timers(self) -> None:
        self.timers = []

    def process_timers(
            self, dt: float) -> tuple[bool, bool]:
        timers = self.timers
        blocking = False
        pause_end = False
        i = 0
        while i < len(timers):
            timer = timers[i]
            if not timer.permanent:
                timer.timer -= dt
            if timer.kill:
                timers[i] = timers[-1]
                timers.pop()
                continue
            if timer.timer <= 0 and not timer.permanent:
                timers[i] = timers[-1]
                timers.pop()
                if timer.name == "pause":
                    pause_end = True
                if timer.after:
                    timer.after(timer.name)
            else:
                if timer.blocking:
                    blocking = True
                i += 1
                if timer.ontick:
                    timer.ontick(timer.name, dt)
        return pause_end, blocking

    def register_timer(self, timer: Timer) -> None:
        self.timers.append(timer)

    def update(self, dial) -> None:
        if dial.pause_for > 0:
            self.timers.append(
                    Timer(
                        timer=dial.pause_for,
                        name="pause",
                        blocking=dial.blocking_pause,
                    )
            )

    def simple_lock(self, name: str) -> Timer:
        lock = Timer(
                name=name,
                timer=0.0,
                blocking=True,
                permanent=True
        )
        self.register_timer(lock)
        return lock
