from PyQt4 import QtCore, QtGui

class MyLabel(QtGui.QLabel):
    def __init__(self, img1, img2):
        QtGui.QLabel.__init__(self)
    
        self.img1 = img1
        self.img2 = img2
        self.setPixmap(self.img1)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        print 'omg'
        self.setPixmap(self.img2)
        
        event.accept()
        
    def dragLeaveEvent(self, event):
        print 'omg1'
        self.setPixmap(self.img1)
        
        event.accept()
        
    def dropEvent(self, event):
        print 'omg2'
        self.setPixmap(self.img1)
        
        event.accept()

class MyWindow(QtGui.QWidget):

    dropbox = r'images/dropbox-{}.png'
    googledrive = r'images/googledrive-{}.png'
    pithos = r'images/pithos-{}.png'
    main_frame_background = r'QWidget {background-color:white}'

    services = ['Dropbox', 'GoogleDrive', 'Pithos']

    def __init__(self, width=85, height=75):
        QtGui.QWidget.__init__(self)

        self.items = {} #Key is the hashed label.
        self.move_pos = None

        self.dropbox_images = []
        self.pithos_images = []
        self.googledrive_images = []
        for i in range(2):
            for t in ['normal', 'scaled']:
                self.dropbox_images.append(QtGui.QPixmap(self.dropbox.format(t)))
                self.pithos_images.append(QtGui.QPixmap(self.pithos.format(t)))
                self.googledrive_images.append(QtGui.QPixmap(self.googledrive.format(t)))

        self.setFixedWidth(width)
        self.center()
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint |
                            QtCore.Qt.WindowCloseButtonHint)

        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setStyleSheet(self.main_frame_background)

        #main layout
        self.layout = QtGui.QVBoxLayout()
        for s in self.services:
            size = self.main_frame.size()
            self.main_frame.resize(size.width(), size.height() + 70)
            self.layout.addWidget(self.add_item(s))

        self.main_frame.setLayout(self.layout)

    def mousePressEvent(self, event):
        self.move_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            diff = event.pos() - self.move_pos
            new_pos = self.pos() + diff

            self.move(new_pos)

    def add_item(self, service):
        e = getattr(self, '{}_images'.format(service.lower()))

        label = MyLabel(e[0], e[1])

        self.items[id(label)] = service
         
        return label
    
    def onClick(self):
        r = self.geometry()
        end = r.adjusted(0, 0, 0, 75)

        self.anim = QtCore.QPropertyAnimation(self, 'geometry')
        self.anim.setDuration(600)
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
