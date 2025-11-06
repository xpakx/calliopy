from calliopy.logger.logger import LoggerFactory
from calliopy.core.container import CalliopyContainer
from calliopy.core.annotations import Component


@Component(tags=["ui_manager", "gui"])
class UIManager:
    def __init__(self, container: CalliopyContainer):
        self.container = container
        self.logger = LoggerFactory.get_logger()
        self.actions = {}
        self.init_actions()
        self.logger.log("Registered actions", actions=self.actions)

    def init_actions(self):
        action_list = self.container.get_functions_with_decorator("UIAction")

        for action in action_list:
            dec = self.container.get_decorators(action)['UIAction']
            self.actions[dec['name']] = action

    def dispatch_action(self, name):
        action = self.actions.get(name)
        if not action:
            return
        func, kwargs = self.container.get_function(action)
        func(**kwargs)
