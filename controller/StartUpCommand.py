import sys
if ".." not in sys.path:
    sys.path.append("..")

import version
import model.modelProxy
from view.view import SysTrayMediator
from view.components import DetailedWindow
from view.components import HistoryWindow
from view.view import DetailedWindowMediator
from view.view import HistoryWindowMediator

import puremvc.patterns
import puremvc.patterns.command


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        self.facade.registerProxy(model.modelProxy.ModelProxy())
        
        self.facade.registerMediator(SysTrayMediator(notification.getBody()))
        self.facade.registerMediator(DetailedWindowMediator(DetailedWindow(version.__version__)))
        self.facade.registerMediator(HistoryWindowMediator(HistoryWindow()))