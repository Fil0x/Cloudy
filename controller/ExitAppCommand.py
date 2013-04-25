import sys
if ".." not in sys.path:
    sys.path.append("..")

import model.modelProxy
from PyQt4 import QtCore
import puremvc.patterns.command
import puremvc.patterns


class ExitAppCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        #The application is closing, we have to store the uploads
        #that are not completed.
        self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME).dump()
        QtCore.QCoreApplication.instance().quit()