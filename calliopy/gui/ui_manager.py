from calliopy.logger.logger import LoggerFactory
from calliopy.core.container import CalliopyContainer
from calliopy.core.annotations import Component


@Component(tags=["ui_manager", "gui_manager"])
class UIManager:
    def __init__(self, container: CalliopyContainer):
        self.container = container
        self.logger = LoggerFactory.get_logger()
        self.actions = {}
        self.init_actions()
        self.logger.debug("Registered actions", actions=self.actions)

    def init_actions(self):
        action_list = self.container.get_functions_with_decorator("UIAction")

        for action in action_list:
            dec = self.container.get_decorators(action)['UIAction']
            self.actions[dec['name']] = action

    def dispatch_event(self, name: str, caller=None, event=None):
        self.logger.debug(f"Dispatching event {name}")
        action = self.actions.get(name)
        if not action:
            self.logger.warn(
                    f"Tried to dispatch nonexisting {name} event.",
                    event=event, caller=caller
            )
            return
        func, kwargs = self.container.get_function(action)
        self.logger.debug(
                f"Got function for event {name}",
                function=func, arguments=kwargs
        )
        func(**kwargs)
