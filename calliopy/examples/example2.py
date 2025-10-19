from calliopy.core.annotations import Scene
from calliopy.core.app import CalliopyApp
from calliopy.core.frontend import DialogueManager


@Scene()
def scene(dial: DialogueManager):
    dial.say("Alice", "Hello Bob! Ready for an adventure?")
    c = dial.choice("Yes", "No")
    if c.index == 0:
        dial.say("Bob", "Great! Let's go!")
    else:
        dial.say("Bob", "Maybe later then...")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example2")
    app.run()
