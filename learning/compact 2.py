from PyQt4 import QtCore, QtGui

class MyWindow(QtGui.QWidget):

    db_path = r'images/dropbox-{}.png'
    gd_path = r'images/googledrive-{}.png'
    pithos_path = r'images/pithos-{}.png'
    main_frame_background = r'QWidget {background-color:white}'

    def __init__(self, width=85, height=75):
        QtGui.QWidget.__init__(self)
        
        
        self.db_images = []
        self.pithos_images = []
        self.gd_images = []
        for i in range(2):
            for t in ['normal', 'scaled']:
                self.db_images.append(QtGui.QPixmap(self.db_path.format(t)))
                self.pithos_images.append(QtGui.QPixmap(self.pithos_path.format(t)))
                self.gd_images.append(QtGui.QPixmap(self.gd_path.format(t)))

        self.setFixedWidth(width)
        self.center()
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint |
                            QtCore.Qt.WindowCloseButtonHint)
                            
        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setGeometry(0, 0, width, height)
        self.main_frame.setStyleSheet(self.main_frame_background)

        #main layout
        self.label = QtGui.QLabel()
        self.label.setPixmap(self.db_images[0])
        self.label.setMouseTracking(True)
        self.label.installEventFilter(self)
        
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.label)

        self.main_frame.setLayout(self.layout)
        
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Enter:
            source.setPixmap(self.db_images[1])
            
            return True
        elif event.type() == QtCore.QEvent.Leave:
            source.setPixmap(self.db_images[0])
            
            return True
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            self.onClick()
            
            return True
            
        return QtGui.QWidget.eventFilter(self, source, event)
        
    def onClick(self):
        r = self.geometry()
        end = r.adjusted(0, 0, 0, 75)
        
        self.anim = QtCore.QPropertyAnimation(self, 'geometry')
        self.anim.setDuration(600)
        self.anim.setStartValue(r)
        self.anim.setEndValue(end)
        self.anim.start()
        
        s = self.main_frame.size()
        self.main_frame.resize(s.width(), s.height() + 75)
        self.label1 = QtGui.QLabel()
        self.label1.setPixmap(self.gd_images[0])
        self.label1.setMouseTracking(True)
        self.label1.installEventFilter(self)
        self.layout.addWidget(self.label1)
        
        
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
