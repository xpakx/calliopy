from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DialogueManager
from calliopy.logger.logger import LoggerFactory


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
        self.logger.info("Registered characters", characters)
        self.characters = {}
        for char in characters:
            self.characters[char._name] = char
