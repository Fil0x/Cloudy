from PyQt4 import QtCore
import puremvc.patterns.command
import puremvc.patterns


class ExitAppCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        QtCore.QCoreApplication.instance().quit()