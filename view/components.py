import os
import smtplib
import operator

import local
from lib.util import raw

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore
from email.MIMEText import MIMEText

#@Mediator = Action will be handled by its mediator.

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        icon = QtGui.QIcon(r'images/favicon.ico')
        self.setIcon(icon)

        menu = QtGui.QMenu(parent)

        #@Mediator
        self.openAction = menu.addAction('Open')

        menu.addSeparator()

        feedbackAction = menu.addAction('Send feedback')
        feedbackAction.triggered.connect(self.onFeedback)

        menu.addSeparator()

        #@Mediator
        self.exitAction = menu.addAction('Quit')
        #@Mediator
        #Handler for the left click.

        self.setContextMenu(menu)

    def onFeedback(self, event):
        feedback = FeedbackPage()
        feedback.show()


class SendMailWorker(QtCore.QThread):

    def __init__(self, name, usermail, message):
        QtCore.QThread.__init__(self)
        self.name = name
        self.usermail = usermail
        self.message = message

    def __del__(self):
        self.wait()

    def run(self):
        self.message = 'Name: {}\nUsermail: {}\n{}'.format(self.name, self.usermail, self.message)

        msg = MIMEText(self.message)

        msg['Subject'] = 'Report'
        msg['From'] = local.email
        msg['To'] = local.email

        mailServer = smtplib.SMTP('smtp.gmail.com', 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(local.email, local.password)
        mailServer.sendmail(local.email, local.email, msg.as_string())
        mailServer.close()

        self.emit(QtCore.SIGNAL('sent()'))

class FeedbackPage(QtGui.QWidget):

    bgImagePath = r'images/feedback-bg.png'
    leNameBox = r'Your name'
    leEmailBox = r'Your email'
    leMsgBox = r'Please type your message here..'
    emailTextLabel = r''
    closeBtnPath = r'images/feedback-close.png'
    closeBtnStyle = r'background-color: rgba(255, 255, 255, 0%)'
    sendBtnStyle = r'background-color: rgba(96, 92, 196, 100%)'
    textboxStyle = r'border-radius: 40px;'
    infoMessage = r'<b><font size="6">Send us your feedback</font></b><br/> '
    font = 'Helvetica'


    def __init__(self):
        QtGui.QWidget.__init__(self)

        bgImage = QtGui.QPixmap(self.bgImagePath)
        self.setMinimumSize(bgImage.size())
        self.setMaximumSize(bgImage.size())
        self.center()

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setBackgroundImage(bgImage)

        closeBtn = QtGui.QToolButton(self)
        closeBtn.setGeometry(553, 31, 31, 31)
        closeBtn.setAutoFillBackground(True)
        closeBtn.setStyleSheet(self.closeBtnStyle)
        closeBtn.setIcon(QtGui.QIcon(self.closeBtnPath))
        closeBtn.setIconSize(QtCore.QSize(31, 31))
        closeBtn.setCursor(QtCore.Qt.PointingHandCursor)
        closeBtn.clicked.connect(lambda: self.deleteLater())

        self.mainFrame = QtGui.QFrame(self)
        self.mainFrame.setGeometry(80, 80, 458, 250)

        self.nameTxtBox = QtGui.QLineEdit(self.leNameBox)
        self.nameTxtBox.setFont(QtGui.QFont(self.font))

        self.emailTxtBox = QtGui.QLineEdit(self.leEmailBox)
        self.emailTxtBox.setFont(QtGui.QFont(self.font))

        self.msgTxtBox = QtGui.QTextEdit(self.leMsgBox)
        self.msgTxtBox.setFont(QtGui.QFont(self.font))

        self.sendBtn = QtGui.QPushButton('Send')
        self.sendBtn.clicked.connect(self.onSend)
        self.sendBtn.setStyleSheet(self.sendBtnStyle)

        upperLayout = QtGui.QHBoxLayout()
        upperLayout.setSpacing(10)
        upperLayout.addWidget(self.nameTxtBox)
        upperLayout.addWidget(self.emailTxtBox)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(QtGui.QLabel(self.infoMessage))
        mainLayout.addLayout(upperLayout)
        mainLayout.addWidget(self.msgTxtBox)
        mainLayout.addWidget(self.sendBtn)

        self.mainFrame.setLayout(mainLayout)

    def onSend(self, event):
        self.sendBtn.setText('Sending..')
        for i in self.mainFrame.children():
            i.setEnabled(False)

        self.worker = SendMailWorker(self.nameTxtBox.text(), self.emailTxtBox.text(),
                                     self.msgTxtBox.toPlainText())
        QtCore.QObject.connect(self.worker, QtCore.SIGNAL('sent()'), self.onMailComplete,
                               QtCore.Qt.QueuedConnection)

        self.worker.start()

    def onMailComplete(self):
        self.sendBtn.setText('Thank you for your feedback!')

    def setBackgroundImage(self, img):
        pic = QtGui.QLabel(self)
        pic.setGeometry(0, 0, self.size().width(), self.size().height())
        pic.setPixmap(img)

    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())


class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header, data=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)

        #Hax
        self.data = [['']*(len(header)+1)] if not data else data
        self.header = header
        self.hidden_col = len(header)

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data[0]) if len(self.data) else 0

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.data[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if col != self.hidden_col and orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.data = sorted(self.data, key=operator.itemgetter(Ncol))
        if order == Qt.Qt.DescendingOrder:
            self.data.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))
        
    def add_item(self, item):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
        self.data.append(item)
        self.endInsertRows()
        
    def remove(self, id, index=None):
        i = 0
        if index:
            i = index
        else:
            i = zip(*self.data)[-1].index(id)
        self.beginRemoveRows(QtCore.QModelIndex(), i, i)
        self.data = self.data[0:i] + self.data[i+1:]
        self.endRemoveRows()
        
    def remove_all(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.data) - 1)
        del self.data[:]
        self.endRemoveRows()
        
class BaseDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, device, font, images=None):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.images = images
        
    def createEditor(self, parent, option, index):
        return None
        
class UploadTableDelegate(BaseDelegate):
        
    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[index.row()][index.column()]
        
        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)
        #painter.drawImage(QtCore.QPoint(5, 5), self.images[0])
        if len(d) >= 20:
            d = d[:20] + '...'
        painter.drawText(QtCore.QPoint(40, 20), d)
        '''
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), str(d[3]))
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)
        '''
        painter.restore()

    def editorEvent(self, event, model, option, index):
        '''sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                import webbrowser
                webbrowser.open(link)'''

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class HistoryTableDelegate(BaseDelegate):
        
    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[index.row()][index.column()]
        
        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)
        #painter.drawImage(QtCore.QPoint(5, 5), self.images[0])
        if len(d) >= 20:
            d = d[:20] + '...'
        painter.drawText(QtCore.QPoint(40, 20), d)
        '''
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), str(d[3]))
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)
        '''
        painter.restore()

    def editorEvent(self, event, model, option, index):
        '''sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                import webbrowser
                webbrowser.open(link)'''

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class DetailedWindow(QtGui.QMainWindow):
    #http://www.jankoatwarpspeed.com/ultimate-guide-to-table-ui-patterns/
    
    font = QtGui.QFont('Tahoma', 10)
    addBtnPath = r'images/detailed-add.png'
    playBtnPath = r'images/detailed-play.png'
    stopBtnPath = r'images/detailed-stop.png'
    file_icon_path = r'images/detailed-doc.png'
    removeBtnPath = r'images/detailed-remove.png'
    settingsBtnPath = r'images/detailed-configure.png'
    tableBackgroundPath = r'images/detailed-background.jpg'
    windowStyle = r'QMainWindow {background-color: rgba(108, 149, 218, 100%)}'
    table_style = r'alternate-background-color: #E5FFFF;background-color: white;'

    def __init__(self, title):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle(title)
        self.setVisible(False)
        self.setStyleSheet(self.windowStyle)
        
        file_image = QtGui.QImage(self.file_icon_path)
        
        self.history_header = ['Name', 'Destination', 'Service', 'Date']
        self.uploads_header = ['Name', 'Progress', 'Status', 'Destination', 
                               'Service', 'Conflict']
        self.data = [map(str, range(1, 8)), map(str, range(2, 9))]*2
        self.data2 = [map(str, range(2, 7)), map(str, range(1, 6))]*2
        
        self.upload_table = self._create_table(self.uploads_header)
        self.upload_table.setItemDelegate(UploadTableDelegate(self, self.font))
        
        self.history_table = self._create_table(self.history_header)
        self.history_table.setItemDelegate(HistoryTableDelegate(self, self.font))

        self._createRibbon()
        self._createSideSpaces()

        tab = QtGui.QTabWidget()
        tab.setTabShape(QtGui.QTabWidget.Triangular)
        tab.insertTab(0, self.upload_table, 'Active')
        tab.insertTab(1, self.history_table, 'History')
        tab.insertTab(2, QtGui.QLabel('SETTINGS'), 'Settings')

        self.setCentralWidget(tab)

    def add_history_item(self, item):
        #[name, dest, service, date, id]
        self.history_table.model().add_item(item)
        
    def update_all_history(self, items):
        self.history_table.model().remove_all()
        for i in items:
            self.add_history_item(i)
            
    def delete_history_item(self, id, row=None):
        self.history_table.model().remove(id, row)
        
    def closeEvent(self, event):
        self.setVisible(False)
        event.ignore()

    def selection_changed(self, new, old):
        for i in new.indexes():
            self.upload_table.selectRow(i.row())

    def _createSideSpaces(self):
        '''
        Add some space on the left and right of the table.
        '''
        leftDockWidget = QtGui.QDockWidget()
        leftDockWidget.setTitleBarWidget(QtGui.QWidget())
        leftDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.LeftDockWidgetArea, leftDockWidget)

        rightDockWidget = QtGui.QDockWidget()
        rightDockWidget.setTitleBarWidget(QtGui.QWidget())
        rightDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, rightDockWidget)

    def _createRibbon(self):
        def _createDockWidget(elem):
            dockWidget = QtGui.QDockWidget()
            #Hide the dock title bar
            dockWidget.setTitleBarWidget(QtGui.QWidget())

            setattr(self, elem, QtGui.QPushButton())
            getattr(self, elem).setIcon(QtGui.QIcon(getattr(self, elem + 'Path')))
            getattr(self, elem).setFlat(True)
            dockWidget.setWidget(getattr(self, elem))
            self.addDockWidget(Qt.Qt.TopDockWidgetArea, dockWidget)

        #@Mediator
        _createDockWidget('addBtn')
        _createDockWidget('removeBtn')
        _createDockWidget('playBtn')
        _createDockWidget('stopBtn')

    def _create_table(self, header):
        tbl = QtGui.QTableView()

        tm = MyTableModel(header, parent=self)
        tbl.setModel(tm)
        QtCore.QObject.connect(tbl.selectionModel(),
                               QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                               self.selection_changed)

        tbl.setMinimumSize(704, 300)
        tbl.setShowGrid(False)
        tbl.setFont(self.font)
        tbl.hideColumn(len(header))

        vh = tbl.verticalHeader()
        vh.setVisible(False)

        hh = tbl.horizontalHeader()
        for i in range(len(header)):
            hh.setResizeMode(i, QtGui.QHeaderView.Stretch)

        # set column width to fit contents
        tbl.setAlternatingRowColors(True);
        tbl.setStyleSheet(self.table_style);
        tbl.resizeColumnsToContents()
        tbl.setSortingEnabled(True)

        return tbl

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

    def removeAll(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.max_count - 1)
        del self.data[:]
        self.endRemoveRows()

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
        painter.drawText(QtCore.QPoint(40, 30), d[3])
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)

        painter.restore()


    def editorEvent(self, event, model, option, index):
        sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                import webbrowser
                webbrowser.open(link)

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(35, 35)

class HistoryWindow(QtGui.QWidget):

    db_path = r'images/dropbox-small.png'
    pithos_path = r'images/pithos-small.png'
    gd_path = r'images/googledrive-small.png'
    main_frame_background = r'QWidget {background-color:white}'
    static_title_style = r'QLabel {font-weight:bold}'
    close_button_img = r'images/popup-cancel.png'
    font = QtGui.QFont('Tahoma', 10)


    def __init__(self, width=320, height=240):
        QtGui.QWidget.__init__(self)

        self.data = [] #[[self.gd_icon, 'foo.pdf', 'html', 'date']]
        self.dropbox_icon = QtGui.QImage(self.db_path)
        self.pithos_icon = QtGui.QImage(self.pithos_path)
        self.googledrive_icon = QtGui.QImage(self.gd_path)

        self.setVisible(False)
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
        close_button.clicked.connect(self.onClose)

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

    def onClose(self):
        #Need to think of a better way
        self.setVisible(False)

    def add_item(self, service, file_name, link, date):
        e = getattr(self, '{}_icon'.format(service.lower()))
        l = [[e, file_name, link, date]]
        self.model.addNewElements(l)

    def update_all(self, items):
        self.model.removeAll()
        for i in items:
            self.add_item(*i[:])

    #find tray icon and place it on top
    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())

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
