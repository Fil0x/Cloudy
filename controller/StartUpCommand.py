import sys
if ".." not in sys.path:
    sys.path.append("..")

import version
import model.modelProxy
from view.view import SysTrayMediator
from view.History import HistoryWindow
from view.Compact import CompactWindow
from view.Detailed import DetailedWindow
from view.view import CompactWindowMediator
from view.view import HistoryWindowMediator
from view.view import DetailedWindowMediator
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns
import puremvc.patterns.command


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        self.facade.registerProxy(model.modelProxy.ModelProxy())
        
        self.facade.registerMediator(SysTrayMediator(notification.getBody()))
        self.facade.registerMediator(HistoryWindowMediator(HistoryWindow()))
        
        p = ApplicationManager()
        #Compact Window
        w = CompactWindow(p.get_services(), p.get_orientation(), 
                          p.get_pos('Compact'), 0)
        self.facade.registerMediator(CompactWindowMediator(w))
        #Detailed Window
        d = DetailedWindow(version.__version__, p.get_pos('Detailed'),
                           p.get_size(), p.get_maximized(), 0)
        self.facade.registerMediator(DetailedWindowMediator(d))
        
        