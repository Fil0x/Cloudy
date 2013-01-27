import sys
from PyQt4 import QtGui
from view.components import SystemTrayIcon

from AppFacade import AppFacade

if __name__ == '__main__':
    qtApp = QtGui.QApplication(sys.argv)    
    trayIcon = SystemTrayIcon()


    app = AppFacade.getInstance()
    app.sendNotification(AppFacade.STARTUP, trayIcon)
        
    trayIcon.show() 
    
    sys.exit(qtApp.exec_())