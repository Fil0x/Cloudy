from PyQt4 import QtCore, QtGui

class MyWindow(QtGui.QWidget):

    def __init__(self, width=100, height=100):
        QtGui.QWidget.__init__(self)

        self.resize(width, height)
        self.center()
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint |
                            QtCore.Qt.WindowCloseButtonHint)
                            
        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setGeometry(0, 0, width, height)

        #main layout
        button = QtGui.QPushButton('ok')
        button.clicked.connect(self.onClick)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(button)

        self.main_frame.setLayout(layout)

    def onClick(self, event):
        r = self.geometry()
        end = r.adjusted(0, 0, 75, 0)
        
        self.anim = QtCore.QPropertyAnimation(self, 'geometry')
        self.anim.setDuration(800)
        self.anim.setStartValue(r)
        self.anim.setEndValue(end)
        self.anim.start()
        
    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())

if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    window.show()

    sys.exit(app.exec_())
