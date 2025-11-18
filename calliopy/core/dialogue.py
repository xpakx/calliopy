from calliopy.core.annotations import Component
from greenlet import greenlet


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
        self.transition_key: str | None = None

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

    def transition(self, key: str) -> None:
        self.transition_key = key
        self.scheduler.main.switch()
        self.transition_key = None
