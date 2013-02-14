import puremvc.patterns.command
import puremvc.patterns
from PyQt4 import QtCore


class ExitAppCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        QtCore.QCoreApplication.instance().quit()