from calliopy.core.dialogue import DialogueManager, ChoiceResult
from calliopy.core.annotations import Component


@Component(tags="dial")
class ScriptableDialogueManager(DialogueManager):
    def __init__(self):
        super().__init__(None)
        self._script = []
        self._call_count = 0
        self.say_log = []
        self._abort = False

    def script(self, script: list[int] | None = None):
        self._script = script or []

    def say(self, who, text):
        self.say_log.append((who, text))

    def choice(self, *options):
        if self._call_count < len(self._script):
            idx = self._script[self._call_count]
            self._call_count += 1
        else:
            idx = 0

        return ChoiceResult(idx)
