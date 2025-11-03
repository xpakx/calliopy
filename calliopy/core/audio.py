from calliopy.core.annotations import Component
from calliopy.logger.logger import LoggerFactory
from calliopy.core.raylib import (
        close_audio_device, unload_sound,
        load_sound, init_audio_device,
        set_master_volume,
)


@Component(tags=["audio", "audio_manager"])
class AudioManager:
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()
        self.sound_lib = {}
        self.to_play = None

    def init_device(self) -> None:
        init_audio_device()
        set_master_volume(0.5)

    def destroy(self) -> None:
        self.unload_all()
        close_audio_device()

    def play(
            self,
            key: str
    ) -> None:
        self.to_play = key

    def preload(self, key: str, path: str) -> None:
        self.sound_lib[key] = load_sound(path)

    def unload(self, key: str) -> None:
        sound = self.sound_lib.get(key)
        if not sound:
            return
        unload_sound(sound)

    def unload_all(self) -> None:
        for sound in self.sound_lib.values():
            unload_sound(sound)

    def get_sound(self):
        if not self.to_play:
            return None
        ret = self.sound_lib.get(self.to_play)
        self.to_play = None
        return ret
