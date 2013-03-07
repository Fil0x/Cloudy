import sys
if ".." not in sys.path:
    sys.path.append("..")


from view.view import SysTrayMediator
import puremvc.patterns.command
import puremvc.patterns


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):

        systray = notification.getBody()
        self.facade.registerMediator(SysTrayMediator(systray))