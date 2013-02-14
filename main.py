import sys
from PyQt4 import QtGui

from AppFacade import AppFacade
from view.components import SystemTrayIcon

if __name__ == '__main__':
    qtApp = QtGui.QApplication(sys.argv)
    sysTrayIcon = SystemTrayIcon()

    app = AppFacade.getInstance()
    app.sendNotification(AppFacade.STARTUP, sysTrayIcon)

    sysTrayIcon.show()

    sys.exit(qtApp.exec_())