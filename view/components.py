import local
import smtplib
import operator
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore
from email.MIMEText import MIMEText


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        icon = QtGui.QIcon('images/favicon.ico')
        self.setIcon(icon)

        menu = QtGui.QMenu(parent)

        #Open action clicked event will be handled by its mediator
        self.openAction = menu.addAction('Open')

        menu.addSeparator()

        feedbackAction = menu.addAction('Send feedback')
        feedbackAction.triggered.connect(self.onFeedback)

        #Settings action clicked event will be handled by its mediator
        self.settingsAction = menu.addAction('Preferences')

        menu.addSeparator()

        #Exit action clicked event will be handled by its mediator
        self.exitAction = menu.addAction('Quit')

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
        closeBtn.clicked.connect(lambda: self.hide())

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

        #The worker thread has to be a class member otherwise it gets
        #cleaned up as the function ends, resulting in a blocked UI.
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


class DetailedWindow(QtGui.QMainWindow):
    
    addBtnPath = r'images/detailed-add.png'
    removeBtnPath = r'images/detailed-remove.png'
    playBtnPath = r'images/detailed-play.png'
    stopBtnPath = r'images/detailed-stop.png'
    settingsBtnPath = r'images/detailed-configure.png'
    tableBackgroundPath = r'images/detailed-background.jpg'
    
    windowStyle = r'QMainWindow {background-color: rgba(108, 149, 218, 100%)}'
    
    def __init__(self, title):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle(title)
        self.setVisible(False)
        self.setStyleSheet(self.windowStyle)

        self.header = ['Name', 'Service', 'Destination', 'Status',
                       'Progress', 'Conflict', 'Completed']
        self.table = self._createTable()
        
        self._createRibbon()
        self._createSideSpaces()

        tab = QtGui.QTabWidget()
        tab.setTabShape(QtGui.QTabWidget.Triangular)
        tab.insertTab(0, self.table, 'Active')
        tab.insertTab(1, QtGui.QLabel('HISTORY'), 'History')
        tab.insertTab(2, QtGui.QLabel('LOGS'), 'Logs')

        self.setCentralWidget(tab)

        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        sb.setStatusTip('Ready')
        self.setStatusBar(sb)
    
    def set_model_data(self, data):
        self.table.setModel(MyTableModel(data, self.header, self))
        QtCore.QObject.connect(self.table.selectionModel(),
                               QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                               self.selection_changed)
        if data:
            self.table.setColumnHidden(7, True)
    
    def closeEvent(self, event):
        ''' 
        Override this event so the app won't close 
        when we press 'X'.
        '''
        self.setVisible(False)
        event.ignore()
     
    def selection_changed(self, new, old):
        for i in new.indexes():
            self.table.selectRow(i.row())

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
        
        #Handlers will be assigned in DetailedWindowMediator.
        _createDockWidget('addBtn')
        _createDockWidget('removeBtn')
        _createDockWidget('playBtn')
        _createDockWidget('stopBtn')
        _createDockWidget('settingsBtn')
            
    def _createTable(self):
        tbl = QtGui.QTableView()
        #tbl.setStyleSheet('background-image: url({})'.format(self.tableBackgroundPath))
        
        tm = MyTableModel([], self.header, self)
        tbl.setModel(tm)
        QtCore.QObject.connect(tbl.selectionModel(),
                               QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                               self.selection_changed)
        
        tbl.setMinimumSize(704, 300)
        tbl.setShowGrid(False)
        
        font = QtGui.QFont('Arial', 8)
        tbl.setFont(font)
        
        vh = tbl.verticalHeader()
        vh.setVisible(False)
        
        hh = tbl.horizontalHeader()
        for i in range(len(self.header)):
            hh.setResizeMode(i, QtGui.QHeaderView.Stretch)

        # set column width to fit contents
        tbl.resizeColumnsToContents()

        tbl.setSortingEnabled(True)

        return tbl
      
class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        
        self.arraydata = data
        self.header = header
        
    def rowCount(self, parent):
        return len(self.arraydata)
        
    def columnCount(self, parent):
        return len(self.arraydata[0]) if len(self.arraydata) else 0
        
    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.arraydata[index.row()][index.column()])
        
    def headerData(self, col, orientation, role):
        #The 8th column is the key and we don't want to show it.
        if col != 7 and orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()
        
    def sort(self, Ncol, order):
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))        
        if order == Qt.Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))