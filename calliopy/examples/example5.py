from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp
from calliopy.core.characters import Character
from dataclasses import dataclass


@Component()
class Alice(Character):
    @property
    def name(self):
        return "Alice"


@Component()
@dataclass
class Bob(Character):
    name: str = "Bob"


@Component()
class Celeste(Character):
    def name(self):
        return "Celeste"


@dataclass
class SimpleChar(Character):
    name: str = ""


@Component(tags='diana')
def diana(dial) -> SimpleChar:
    diana = SimpleChar(name='Diana')
    diana.dial = dial
    return diana


@Scene()
def end(dial, alice: Alice, celeste: Celeste, diana):
    alice.say("Huh?")
    celeste.say("'tis but a test.")
    diana.say("A test?")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example5")
    app.run()
