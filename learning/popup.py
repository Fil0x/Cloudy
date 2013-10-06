import sys
from PyQt4 import QtGui, QtCore

'''
ISSUE: if the list gets updated while the mouse is over an element, 
it will be moved down but the click will still copy the share of that element.
'''
class ListViewModel(QtCore.QAbstractListModel):

    def __init__(self, data, max_count=5, parent=None, *args):
        QtCore.QAbstractListModel.__init__(self, parent, *args)
        self.data = data
        self.max_count = max_count

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.data)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.data[index.row()])
        else:
            return QtCore.QVariant()
            
    def addNewElements(self, items):
        ''' [[img, filename, sharelink]...] '''
        if len(items) >= self.max_count:
            self.beginRemoveRows(QtCore.QModelIndex(), 0, self.max_count - 1)
            del self.data[:]
            self.endRemoveRows()
        elif (len(self.data) + len(items)) > self.max_count:
            begin_row = self.max_count - len(items)
            end_row = len(self.data) - 1
            self.beginRemoveRows(QtCore.QModelIndex(), begin_row, end_row)
            self.data = self.data[:begin_row]
            self.endRemoveRows()
        
        self.beginInsertRows(QtCore.QModelIndex(), 0, len(items) - 1)
        for i in items:
            self.data.insert(0, i)
            
        self.endInsertRows()
        
class ListItemDelegate(QtGui.QStyledItemDelegate):
    
    sharelink_path = r'images/popup-sharelink.png'
    sharelink_pos = QtCore.QPoint(220, 2)
    
    def __init__(self, device, font):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.brush = QtGui.QBrush(QtGui.QColor('#E5FFFF'))
        self.sharelink_img = QtGui.QImage(self.sharelink_path)
        self.date_color = QtGui.QColor(QtCore.Qt.black)
        self.date_color.setAlpha(80)

    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[index.row()]

        if option.state & QtGui.QStyle.State_MouseOver:
            painter.fillRect(option.rect, self.brush)

        painter.translate(option.rect.topLeft())
        painter.setClipRect(option.rect.translated(-option.rect.topLeft()))
        painter.setFont(self.font)
        painter.drawImage(QtCore.QPoint(5, 5), d[0])
        painter.drawText(QtCore.QPoint(40, 15), d[1])
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), 'awesome date')
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)
        
        painter.restore()

    
    def editorEvent(self, event, model, option, index):
        sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(), 
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                print 'Shared!'
            
        return False
        
    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(35, 35)

class MyWindow(QtGui.QWidget):

    db_path = r'images/dropbox-small.png'
    pithos_path = r'images/pithos-small.png'
    gd_path = r'images/googledrive-small.png'
    main_frame_background = r'QWidget {background-color:white}'
    static_title_style = r'QLabel {font-weight:bold}'
    close_button_img = r'images/popup-cancel.png'
    font = QtGui.QFont('Tahoma', 10)


    def __init__(self, width=320, height=240):
        QtGui.QWidget.__init__(self)

        self.data = [] #[[self.gd_icon, 'foo.pdf', 'html']]*2
        self.db_icon = QtGui.QImage(self.db_path)
        self.pithos_icon = QtGui.QImage(self.pithos_path)
        self.gd_icon = QtGui.QImage(self.gd_path)
        
        self.setFixedSize(width, height)
        self.center()

        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)

        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setGeometry(0, 0, width, height)
        self.main_frame.setStyleSheet(self.main_frame_background)

        #Upper layout
        static_title = QtGui.QLabel('Recently uploaded')
        static_title.setStyleSheet(self.static_title_style)
        static_title.setFont(self.font)

        close_button = QtGui.QPushButton(self.main_frame)
        close_button.setFlat(True)
        close_button.setIcon(QtGui.QIcon(self.close_button_img))
        close_button.clicked.connect(lambda: self.deleteLater())

        upper_layout = QtGui.QHBoxLayout()
        upper_layout.addWidget(static_title, 1)
        upper_layout.addWidget(close_button, 0)

        #Main layout
        line = QtGui.QFrame(self)
        line.setGeometry(QtCore.QRect(0, 30, width, 2))
        line.setFrameShape(QtGui.QFrame.HLine)

        self.model = ListViewModel(self.data, parent=self)
        
        self.list = QtGui.QListView()
        self.list.setModel(self.model)
        self.list.setItemDelegate(ListItemDelegate(self, self.font))
        self.list.setMouseTracking(True)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(upper_layout)
        main_layout.addWidget(line)
        main_layout.addWidget(self.list)

        self.main_frame.setLayout(main_layout)
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1500)
        #self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.onTimeout)
        self.timer.start()
        
    def onTimeout(self):
        print 'adding'
        l = [[self.db_icon, 'moo.pdf', 'html']]*1
        self.model.addNewElements(l)
        #l = [self.db_icon, 'moo.pdf', 'html']
        #self.model.addNewElement(l)
        
    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())

if __name__ == '__main__':
    qtApp = QtGui.QApplication(sys.argv)
    frame = MyWindow()
    frame.show()
    sys.exit(qtApp.exec_())