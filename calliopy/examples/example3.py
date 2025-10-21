from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp


@Component()
class Test:
    def __init__(self):
        self.is_day = False

    def get_time(self):
        if self.is_day:
            return "It's a day"
        return "It's a night"


@Component(tags="day")
class DayCycle:
    def __init__(self, test: Test) -> None:
        self.test = test

    def advance(self):
        self.test.is_day = not self.test.is_day


@Scene()
def scene(dial):
    dial.say("Alice", "Hello Bob! Ready for an adventure?")
    c = dial.choice("Yes", "No")
    if c.index == 0:
        dial.say("Bob", "Great! Let's go!")
    else:
        dial.say("Bob", "Maybe later then...")
        return "scene3"


@Scene()
def scene2(dial, day):
    dial.narrate(day.test.get_time())
    dial.say("Alice", "What a wonderful forest")
    return "end"


@Scene()
def scene3(dial):
    dial.narrate("Alice leaves alone")


@Scene()
def end(dial):
    dial.narrate("THE END")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example3")
    app.run()
