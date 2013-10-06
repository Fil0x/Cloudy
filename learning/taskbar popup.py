import sys
from PyQt4 import QtGui, QtCore

class MyWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        
        self.setFixedSize(100, 100)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)

class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(lambda: QtGui.QApplication.instance().quit())
        self.setContextMenu(menu)
        self.activated.connect(self.onClick)
        self.w = MyWindow()
        self.w.setVisible(True)
        
    def onClick(self, event):
        p = self.popup_pos()
        if p:
            self.w.move(p)
        #The taskbar is hidden
        
    def popup_pos(self, width=100, height=100, m=20):
        d = QtGui.QApplication.desktop()
        av = d.availableGeometry()
        sc = d.screenGeometry()
        
        x = sc.x() - av.x()
        y = sc.y() - av.y()
        w = sc.width() - av.width()
        h = sc.height() - av.height()
        
        if h > 0: #bottom or top
            if y < 0: #top
                return QtCore.QPoint(sc.width()-width-m, h+m)
            else: #bottom
                return QtCore.QPoint(sc.width()-width-m, av.height()-height-m)
        elif w > 0: #left or right
            if x < 0: #left
                return QtCore.QPoint(w+m, sc.height()-height-m)
            else: #right
                return QtCore.QPoint(av.width()-width-m, sc.height()-height-m)
        
        #Taskbar is hidden
        return None
        
def main():
    app = QtGui.QApplication(sys.argv)

    w = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(r"images\popup-cancel.png"), w)

    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()