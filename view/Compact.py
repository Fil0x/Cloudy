import os

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
        self.droppedSignal.emit((self.service, m))

class MyFrame(QtGui.QFrame):
    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        painter.setRenderHint(QtGui.QPainter.Antialiasing);
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(40,43,49, 190))

        painter.drawRoundedRect(0, 0, self.width(), self.height(), 5., 5.)
        
class CompactWindow(QtGui.QWidget):

    dropbox = r'images/dropbox-{}.png'
    googledrive = r'images/googledrive-{}.png'
    pithos = r'images/pithos-{}.png'

    def __init__(self, services, orientation, pos, screen_id):
        QtGui.QWidget.__init__(self)

        #Data
        self.items = {} #Key is a service.
        self.move_pos = None
        self.services = services
        self.orientation = orientation #Widget Expansion

        self.dropbox_images = []
        self.pithos_images = []
        self.googledrive_images = []
        for i in range(2):
            for t in ['normal', 'scaled']:
                self.dropbox_images.append(QtGui.QPixmap(self.dropbox.format(t)))
                self.pithos_images.append(QtGui.QPixmap(self.pithos.format(t)))
                self.googledrive_images.append(QtGui.QPixmap(self.googledrive.format(t)))
        #End data

        self.setAutoFillBackground(False)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        d = QtGui.QApplication.desktop()
        pos_rect = d.availableGeometry(screen_id).adjusted(pos[0], pos[1], 0, 0)
        self.move(pos_rect.topLeft())

        self.main_frame = MyFrame(self)

        size = self.size()
        self.main_frame.resize(size.width(), size.height())

        #main layout
        self.layout = getattr(QtGui, 'Q{}BoxLayout'.format(orientation))()
        for s in services:
            self.layout.addWidget(self.create_item(s), QtCore.Qt.AlignCenter)

        self.main_frame.setLayout(self.layout)
        if orientation == 'H':
            self.main_frame.resize(len(services)*88, 85)
            self.layout.setAlignment(QtCore.Qt.AlignVCenter)
        else:
            self.main_frame.resize(87, len(services)*80)
            self.layout.setAlignment(QtCore.Qt.AlignHCenter)

    def get_window_info(self):
        d = QtGui.QApplication.desktop()
        pos = [self.pos().x(), self.pos().y()]
        screen_id = d.screenNumber(self)
        
        return [pos, screen_id, self.orientation]
            
    def add_item(self, service):
        start = self.main_frame.geometry()
        self.layout.addWidget(self.create_item(service))
            
        if self.orientation == 'H':
            end = start.adjusted(0, 0, 88, 0)
            self.resize(self.width() + 88, self.height())
        else:
            end = start.adjusted(0, 0, 0, 80)
            self.resize(self.width(), self.height() + 80)

        self.animate(start, end)
        
    def remove_item(self, service):
        start = self.main_frame.geometry()
        self.layout.removeWidget(self.items[service])
        self.items[service].close()
        del self.items[service]
            
        if self.orientation == 'H':
            end = start.adjusted(0, 0, -88, 0)
            self.resize(self.width() - 88, self.height())
        else:
            end = start.adjusted(0, 0, 0, -80)
            self.resize(self.width(), self.height() - 80)
            
        self.animate(start, end)

    def create_item(self, service):
        e = getattr(self, '{}_images'.format(service.lower()))
        label = MyLabel(e[0], e[1], service)

        self.items[service] = label
        return label
        
    def animate(self, start, end, dur=600):
        self.anim = QtCore.QPropertyAnimation(self.main_frame, 'geometry')
        self.anim.setDuration(dur)
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def mousePressEvent(self, event):
        self.move_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            diff = event.pos() - self.move_pos
            new_pos = self.pos() + diff

            self.move(new_pos)
