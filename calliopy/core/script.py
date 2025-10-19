class CalliopyScript:
    def __init__(self):
        self.scenes = []
        self.dial = None
        self.current = 0

    def run(self):
        while self.current < len(self.scenes):
            scene = self.scenes[self.current]
            scene(self.dial)
            self.current += 1

    def register(self, component):
        if "Scene" in self.get_decorators(component):
            self.scenes.append(component)
        print(component.__name__)
        if "DialogueManager" == component.__name__:
            self.dial = component()

    def get_decorators(self, cls) -> dict[str]:
        return getattr(cls,  "__calliopy_decorators__", {})
