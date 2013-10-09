import os

from lib.util import raw

from PyQt4 import QtGui
from PyQt4 import QtCore

class MyLabel(QtGui.QLabel):
    droppedSignal = QtCore.pyqtSignal(tuple)

    def __init__(self, normal, scaled, service):
        QtGui.QLabel.__init__(self)

        self.normal = normal
        self.scaled = scaled
        self.setPixmap(self.normal)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.service = service

    def dragEnterEvent(self, event):
        event.accept()

        self.setPixmap(self.scaled)

    def dragLeaveEvent(self, event):
        event.accept()

        self.setPixmap(self.normal)

    def dropEvent(self, e):
        e.accept()
        self.setPixmap(self.normal)
        
        m = e.mimeData()
        if m.hasUrls() and len(m.urls()) < 4:
            for url in m.urls():
                p = raw(url.path()[1:])
                if os.path.isfile(p):
                    self.droppedSignal.emit((self.service, p))
                #else:
                    #Dont accept the folders for now

class CompactWindow(QtGui.QWidget):

    dropbox = r'images/dropbox-{}.png'
    googledrive = r'images/googledrive-{}.png'
    pithos = r'images/pithos-{}.png'
    main_frame_background = r'QWidget {background-color:white}'

    def __init__(self, services, orientation, pos, screen_id):
        QtGui.QWidget.__init__(self)

        #Data
        self.items = {} #Key is a service.
        self.move_pos = None
        self.services = services
        self.orientation = orientation #Expansion

        self.dropbox_images = []
        self.pithos_images = []
        self.googledrive_images = []
        for i in range(2):
            for t in ['normal', 'scaled']:
                self.dropbox_images.append(QtGui.QPixmap(self.dropbox.format(t)))
                self.pithos_images.append(QtGui.QPixmap(self.pithos.format(t)))
                self.googledrive_images.append(QtGui.QPixmap(self.googledrive.format(t)))
        #End data

        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint |
                            QtCore.Qt.WindowCloseButtonHint)
        d = QtGui.QApplication.desktop()
        pos_rect = d.availableGeometry(screen_id).adjusted(pos[0], pos[1], 0, 0)
        self.move(pos_rect.topLeft())

        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setStyleSheet(self.main_frame_background)

        size = self.size()
        self.main_frame.resize(size.width(), size.height())

        #main layout
        self.layout = getattr(QtGui, 'Q{}BoxLayout'.format(orientation))()
        for s in services:
            self.layout.addWidget(self.add_item(s), QtCore.Qt.AlignCenter)

        self.main_frame.setLayout(self.layout)
        if orientation == 'H':
            self.main_frame.resize(len(services)*88, 85)
            self.layout.setAlignment(QtCore.Qt.AlignVCenter)
        else:
            self.main_frame.resize(87, len(services)*80)
            self.layout.setAlignment(QtCore.Qt.AlignHCenter)

    def mousePressEvent(self, event):
        self.move_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            diff = event.pos() - self.move_pos
            new_pos = self.pos() + diff

            self.move(new_pos)

    def add_item(self, service):
        e = getattr(self, '{}_images'.format(service.lower()))
        label = MyLabel(e[0], e[1], service)

        self.items[service] = label
        return label

    def onClick(self):
        r = self.geometry()
        end = r.adjusted(0, 0, 0, 70)

        self.anim = QtCore.QPropertyAnimation(self, 'geometry')
        self.anim.setDuration(600)
        self.anim.setStartValue(r)
        self.anim.setEndValue(end)
        self.anim.start()
#/CompactWindow
        