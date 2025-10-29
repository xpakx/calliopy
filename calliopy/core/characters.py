from calliopy.core.annotations import Component, Inject
from calliopy.core.frontend import DialogueManager
from calliopy.logger.logger import LoggerFactory
from calliopy.core.raylib import load_texture, unload_texture, Texture2D
from pathlib import Path
from dataclasses import dataclass


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
        self._mood = None

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

    def emote(self, mood: str):
        self._mood = mood


@dataclass
class ImageDef:
    name: str
    mood: str | None = None
    pos: tuple[int, int] = (500, 200)
    scale: float = 1.0
    opacity: float = 1.0
    hide: bool = False
    temporary: bool = False
    resolved_texture_name: str | None = None


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
        self.visible = {}
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
        img = ImageDef(
            name=image,
            mood=mood,
            pos=pos or (500, 200),
        )
        self._show(img)

    def hide(self, image: str) -> None:
        image = image.capitalize()
        if image in self.visible:
            del self.visible[image]

    def reset(self) -> None:
        self.visible.clear()

    def reset_temp(self) -> None:
        new_visible = {}
        for key, value in self.visible.items():
            if not value.temporary:
                new_visible[key] = value
        self.visible = new_visible

    def show_temp(
            self,
            image: str,
            mood: str | None = None,
            pos: tuple[int, int] | None = None
    ) -> None:
        img = ImageDef(
            name=image,
            mood=mood,
            pos=pos or (500, 200),
            temporary=True
        )
        self._show(img)

    def _show(
            self,
            image: ImageDef,
    ) -> None:
        if image.mood:
            mood = f"{image.name}_{image.mood}"
            mood_tex_info = self.textures.get(mood.capitalize())
            if not mood_tex_info:
                image.mood = None
                self.logger.warn(f"Tried to show missing mood: {mood}")
            else:
                image.resolved_texture_name = mood.capitalize()
                if not image.temporary:
                    char = self.characters.get(image.name.capitalize())
                    if char:
                        char._mood = image.mood

        if not image.mood:
            tex_info = self.textures.get(image.name.capitalize())

            if not tex_info:
                self.logger.warn(f"Tried to show missing image: {image}")
                return

            image.resolved_texture_name = image.name.capitalize()
        image.name = image.name.capitalize()
        self.visible[image.name] = image

    def get_texture(self, name: str) -> None | Texture2D:
        image = self.visible.get(name)
        if not image or not image.resolved_texture_name:
            return None
        name = image.resolved_texture_name
        img = self.textures.get(name)
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

    def get_character_color(self, name: str) -> int | None:
        char = self.characters.get(name)
        if not char:
            return None
        return char._color

    def update_moods_from_chars(self) -> None:
        for image in self.visible.values():
            if image.temporary and image.mood:
                continue
            char = self.characters.get(image.name)
            if not char or not char._mood or char._mood == image.mood:
                continue

            mood = f"{image.name}_{char._mood}"
            mood_tex_info = self.textures.get(mood.capitalize())
            if not mood_tex_info:
                continue
            image.resolved_texture_name = mood.capitalize()
