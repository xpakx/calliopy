from calliopy.logger.logger import LoggerFactory
from calliopy.core.container import CalliopyContainer
from calliopy.core.annotations import Component


@Component(tags=["script_manager"])
class ScriptManager:
    def __init__(self, container: CalliopyContainer, dial):
        self.container = container
        self.dial = dial
        self.current = 0
        self.logger = LoggerFactory.get_logger()
        self.init_scenes()

    def init_scenes(self):
        self.set_scenes()
        self.logger.debug(self.scenes)
        self.logger.debug(self.container.components_by_class)
        self.logger.debug(self.container.components_by_tag)
        self.scenes.sort(key=lambda s: s.__calliopy_decorators__["Scene"]["num"])
        self.tag = None

    def set_scenes(self):
        self.scenes = self.container.get_functions_with_decorator("Scene")

    def get_next_scene(self, tag):
        if self.dial._abort:
            return None, None
        if self.current >= len(self.scenes):
            return None, None
        scene = self.next_scene(tag)
        return self.container.get_function(scene)

    def next_scene(self, tag: str | None):
        if tag is not None:
            for i, scene in enumerate(self.scenes):
                if scene.__name__ == tag:
                    self.current = i + 1
                    return scene
        scene = self.scenes[self.current]
        self.current += 1
        return scene
