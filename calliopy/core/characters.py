from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DialogueManager
from calliopy.logger.logger import LoggerFactory
from pathlib import Path


class Character:
    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        if "name" in self.__dict__:
            return self.__dict__["name"]
        raise NotImplementedError(
            "Character must define either a `name` "
            "property, `self.name()` method "
            "or a `self.name` attribute."
        )

    @Inject()
    def set_dialogue(self, dial: DialogueManager) -> None:
        self.dial = dial

    def say(self, text: str) -> None:
        self.dial.say(self._name, text)

    @property
    def _name(self) -> str:
        if callable(self.name):
            return self.name()
        return self.name

    def __repr__(self):
        return f"<Character name={self._name!r}>"


@Component(tags=["char_manager", "chars"])
class CharacterManager:
    def __init__(self, characters: list[Character]) -> None:
        self.logger = LoggerFactory.get_logger()
        if characters is None:
            self.logger.warn("Character list is None")
        if len(characters) == 0:
            self.logger.debug("Character list is empty")
        self.logger.info("Registered characters", chars=characters)
        self.characters = {}
        for char in characters:
            self.characters[char._name] = char
        self.set_textures()
        self.visible = set()
        self.visible_temporary = set()
        self.auto_speaker_portraits = True

    def set_textures(self) -> None:
        self.bg_texture = "files/bg_forest.png"
        self.textures = {}
        for char in self.characters.keys():
            if type(char) is not str:
                continue
            p = f"files/{char.lower()}.png"
            path = Path(p)
            if not path.exists():
                continue
            self.textures[char] = {
                    "image": p,
                    "pos": (500, 200),
            }

        files_dir = Path("files")
        checked = set(c.lower() for c in self.characters if isinstance(c, str))
        for p in files_dir.glob("*.png"):
            name = p.stem.lower()
            if name.startswith("bg_") or name in checked:
                continue
            if name not in self.textures:
                self.textures[name.capitalize()] = {
                    "image": str(p),
                    "pos": (500, 200),
                }

    def show(self, image: str) -> None:
        self.visible.add(image)

    def hide(self, image: str) -> None:
        self.visible.remove(image)

    def reset(self) -> None:
        self.visible.clear()

    def reset_temp(self) -> None:
        self.visible_temporary.clear()

    def show_temp(self, image: str) -> None:
        self.visible_temporary.add(image)
