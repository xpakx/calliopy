from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DialogueManager
from calliopy.logger.logger import LoggerFactory
from calliopy.core.raylib import load_texture, unload_texture, Texture2D
from pathlib import Path
from typing import Any


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

    @name.setter
    def name(self, value: str) -> None:
        self.__dict__["name"] = value

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

    @property
    def color(self) -> str | None:
        if "color" in self.__dict__:
            return self.__dict__["color"]
        return None

    @color.setter
    def color(self, value: str) -> None:
        self.__dict__["color"] = value

    @property
    def _color(self) -> str:
        if callable(self.color):
            return self.color()
        return self.color

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

    def show(
            self,
            image: str,
            mood: str | None = None,
            pos: tuple[int, int] | None = None
    ) -> None:
        self._show(self.visible, image, mood, pos)

    def hide(self, image: str) -> None:
        print(self.visible)
        self.visible.remove(image)

    def reset(self) -> None:
        self.visible.clear()

    def reset_temp(self) -> None:
        self.visible_temporary.clear()

    def show_temp(
            self,
            image: str,
            mood: str | None = None,
            pos: tuple[int, int] | None = None
    ) -> None:
        self._show(self.visible_temporary, image, mood, pos)

    def _show(
            self,
            images: set[str],
            image: str,
            mood: str | None,
            pos: tuple[int, int] | None
    ) -> None:
        mood_tex_info = None
        if mood:
            mood_tex_info = self.textures.get(f"{image}_{mood}".capitalize())

        tex_info = self.textures.get(image.capitalize())

        if not tex_info:
            self.logger.warn(f"Tried to show missing image: {image}")
            return

        if pos is not None:
            tex_info["pos"] = pos

        if mood_tex_info:
            mood_tex_info["pos"] = pos
            images.add(f"{image}_{mood}")
            return

        images.add(image)

    def get_texture(self, image: str) -> None | Texture2D:
        img = self.textures.get(image)
        if not img:
            return None
        if not img.get('texture'):
            img['texture'] = load_texture(img["image"])
        if not img.get('texture'):
            return None
        return img

    def preload(self, image: str) -> None:
        img = self.textures.get(image)
        if not img or img.get('texture'):
            return
        img['texture'] = load_texture(img["image"])

    def unload(self, image: str) -> None:
        img = self.textures.get(image)
        if not img or img.get('texture'):
            return
        if img.get('texture'):
            unload_texture(img['texture'])

    def unload_all(self) -> None:
        for c in self.textures.values():
            if c.get('texture'):
                unload_texture(c['texture'])

    def get_character_color(self, name: str) -> Any:
        char = self.characters.get(name)
        if not char:
            return None
        return char._color
