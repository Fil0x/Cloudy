import sys
if ".." not in sys.path:
    sys.path.append("..")

import version
from view.view import SysTrayMediator
from view.view import DetailedWindowMediator
from view.components import DetailedWindow
from model.modelProxy import ModelProxy
import puremvc.patterns.command
import puremvc.patterns


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        self.facade.registerProxy(ModelProxy())
        
        self.facade.registerMediator(SysTrayMediator(notification.getBody()))
        self.facade.registerMediator(DetailedWindowMediator(DetailedWindow(version.VERSION)))