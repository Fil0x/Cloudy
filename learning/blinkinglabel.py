import sys
from PyQt4 import QtGui, QtCore


class Example(QtGui.QWidget):

    s = r'BLINKING TEXT'
    
    def __init__(self, parent=None):
        super(Example, self).__init__(parent, QtCore.Qt.Window)
        self.initUI()

    def initUI(self):
        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
    
        self.setAcceptDrops(True)
        
        layout = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton('Button')
        self.button.clicked.connect(self.onClick)
        
        self.l = QtGui.QLabel('')
        
        layout.addWidget(self.button)
        layout.addWidget(self.l)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimeout)
        self.timer.setInterval(2000)
        self.timer.setSingleShot(True)
        
        self.setLayout(layout)
        self.setWindowTitle('Blinking text')
        self.setGeometry(300, 300, 280, 150)
        self.center()
        
    def onClick(self):
        self.l.setText(self.s)
        self.timer.start()
        
    def onTimeout(self):
        self.l.clear()

    def center(self):
        myFrame = self.geometry()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        myFrame.moveCenter(screenCenter)
        self.move(myFrame.topLeft())

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    p = QtGui.QWidget()
    ex = Example(p)
    ex.show()
    app.exec_()