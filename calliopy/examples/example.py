from calliopy.core.annotations import Scene
from calliopy.core.app import CalliopyApp
from calliopy.core.frontend import DialogueManager


@Scene()
def scene(dial: DialogueManager):
    dial.say("Alice", "Hello, Bob! Nice day, isn't it?")
    dial.say("Bob", "Indeed, Alice. The forest is beautiful today.")
    dial.say("Alice", "Let's go explore a bit further!")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example")
    app.run()
