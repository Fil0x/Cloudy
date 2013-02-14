import puremvc.patterns.command
import puremvc.patterns


class DataUpdatedCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        pass