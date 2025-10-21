from calliopy.core.annotations import Scene, Component
from calliopy.core.app import CalliopyApp


@Component()
class TimeOfDay:
    def __init__(self):
        self.is_day = True

    def toggle(self):
        self.is_day = not self.is_day

    def description(self):
        return "bright and sunny" if self.is_day else "dark and moonlit"


@Component()
class Inventory:
    def __init__(self):
        self.items = []

    def add(self, item: str):
        self.items.append(item)

    def has(self, item: str):
        return item in self.items


@Component()
class Characters:
    def __init__(self):
        self.mood = {"Alice": "cheerful", "Bob": "grumpy"}


@Component(tags="charsd")
class CharData:
    def __init__(self, characters: Characters, inv: Inventory):
        self.characters = characters
        self.inventory = inv


@Scene()
def intro(dial, time: TimeOfDay):
    dial.narrate(f"The world is {time.description()}.")
    dial.say("Alice", "Bob! Are you ready for today's adventure?")
    c = dial.choice("Absolutely!", "Not really...")
    if c.index == 1:
        return "alice_leaves"


@Scene()
def forest_path(dial, time: TimeOfDay, charsd):
    dial.narrate(f"The forest path is quiet. {time.description()} surrounds you.")
    dial.say("Bob", "I hope we don't run into trouble...")
    dial.say("Alice", "Oh, come on! It'll be fun!")
    c = dial.choice("Investigate the strange noise", "Keep walking")
    if c.index == 1:
        charsd.inventory.add("Mushroom")
        dial.say("Alice", "Look, I found a mushroom!")
        return "forest_cabin"


@Scene()
def mysterious_clearing(dial, charsd):
    dial.narrate("You enter a clearing and see a glowing orb hovering in the air.")
    c = dial.choice("Touch the orb", "Step back carefully")
    if c.index == 0:
        dial.say("Bob", "Wait, that looks dangerous!")
        dial.say("Alice", "Too late, I touched it...")
        charsd.inventory.add("Orb")
        charsd.characters.mood["Alice"] = "excited"
    else:
        dial.say("Alice", "Better safe than sorry.")
        charsd.characters.mood["Bob"] = "relieved"


@Scene()
def forest_cabin(dial, charsd):
    dial.narrate("You arrive at a small cabin in the woods.")
    if charsd.inventory.has("Orb"):
        dial.say("Alice", "Look! The orb is glowing strangely inside the cabin...")
    if charsd.inventory.has("Mushroom"):
        dial.say("Bob", "Hmm, maybe this mushroom could be useful...")
    dial.say("Alice", f"My mood is {charsd.characters.mood['Alice']}, yours is {charsd.characters.mood['Bob']}")
    c = dial.choice("Enter the cabin", "Camp outside")
    if c.index == 1:
        return "camp_outside"


@Scene()
def inside_cabin(dial, time: TimeOfDay):
    dial.narrate("The cabin is dusty but cozy. You light a fire and rest.")
    time.toggle()
    dial.narrate(f"After a while, it becomes {time.description()}.")
    return "end"


@Scene()
def camp_outside(dial, time: TimeOfDay):
    dial.narrate("You decide to camp under the stars. The night is calm.")
    time.toggle()
    dial.say("Alice", "I love nights like this, don't you?")
    return "end"


@Scene()
def alice_leaves(dial):
    dial.narrate("Alice leaves alone into the world, leaving Bob behind.")
    return "end"


@Scene()
def end(dial):
    dial.narrate("Your adventure concludes. THE END.")


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example4")
    app.run()
