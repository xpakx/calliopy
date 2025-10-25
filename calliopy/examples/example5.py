from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp
from calliopy.core.characters import Character
from dataclasses import dataclass


@Component()
class Alice(Character):
    @property
    def name(self):
        return "Alice"


# TODO: container overwrites defaults,
# still not sure what should it do
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
    return SimpleChar(name='Diana')


@Scene()
def end(dial, alice: Alice, bob: Bob, celeste: Celeste, diana):
    alice.say("Huh?")
    celeste.say("'tis but a test.")
    diana.say("A test?")
    bob.say("Indeed it is.")


@Scene()
def charlist(dial, chars):
    print(chars.characters)
    ls = [k for k in chars.characters.keys() if k is not None]
    chars.show("alice")
    dial.narrate("Characters list:\n" +
                 ", ".join(ls))


@Scene()
def images(dial, chars):
    chars.reset()
    chars.show("bob")
    dial.narrate("Bob")
    chars.hide("bob")
    chars.show("alice")
    dial.narrate("Alice")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example5")
    app.run()
