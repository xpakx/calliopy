from calliopy.core.frontend import DialogueManager, ChoiceResult


class ScriptableDialogueManager(DialogueManager):
    def __init__(self, script: list[int] | None = None):
        super().__init__()
        self._script = script or []
        self._call_count = 0
        self.say_log = []

    def say(self, who, text):
        self.say_log.append((who, text))

    def choice(self, *options):
        if self._call_count < len(self._script):
            idx = self._script[self._call_count]
            self._call_count += 1
        else:
            idx = 0

        return ChoiceResult(idx)
