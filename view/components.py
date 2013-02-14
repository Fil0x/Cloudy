from AppFacade import AppFacade
import smtplib
from email.MIMEText import MIMEText
from PyQt4 import QtGui
from PyQt4 import QtCore


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        icon = QtGui.QIcon('images/favicon.ico')
        self.setIcon(icon)

        menu = QtGui.QMenu(parent)

        openAction = menu.addAction('Open')
        openAction.triggered.connect(self.onOpen)

        menu.addSeparator()

        feedbackAction = menu.addAction('Send feedback')
        feedbackAction.triggered.connect(self.onFeedback)

        settingsAction = menu.addAction('Preferences')
        settingsAction.triggered.connect(self.onSettings)

        menu.addSeparator()

        exitAction = menu.addAction('Quit')
        exitAction.triggered.connect(self.onExit)

        self.setContextMenu(menu)

    def onOpen(self, event):
        pass

    def onFeedback(self, event):
        feedback = FeedbackPage()
        feedback.show()

    def onSettings(self, event):
        pass

    def onExit(self, event):
        app = AppFacade()
        app.sendNotification(AppFacade.EXIT, None)


class SendMailWorker(QtCore.QThread):

    email = r'cloudyreports@gmail.com'
    password = r'tromerozepp190'

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
        msg['From'] = self.email
        msg['To'] = self.email

        mailServer = smtplib.SMTP('smtp.gmail.com', 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(self.email, self.password)
        mailServer.sendmail(self.email, self.email, msg.as_string())
        mailServer.close()

        self.emit(QtCore.SIGNAL('completed()'))


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

        #The worker thread has to be a class member because otherwise it gets
        #cleaned up as the function ends resulting in a blocked UI.
        self.worker = SendMailWorker(self.nameTxtBox.text(), self.emailTxtBox.text(),
                                     self.msgTxtBox.toPlainText())
        QtCore.QObject.connect(self.worker, QtCore.SIGNAL('completed()'), self.onMailComplete,
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