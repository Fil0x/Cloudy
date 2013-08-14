import sys
if ".." not in sys.path:
    sys.path.append("..")

import version
from view.view import SysTrayMediator
from view.view import DetailedWindowMediator
from view.components import DetailedWindow
import model.modelProxy
import puremvc.patterns.command
import puremvc.patterns


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        self.facade.registerProxy(model.modelProxy.ModelProxy())
        
        self.facade.registerMediator(SysTrayMediator(notification.getBody()))
        self.facade.registerMediator(DetailedWindowMediator(DetailedWindow(version.__version__)))