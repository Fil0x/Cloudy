import local

import smtplib
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore
from email.MIMEText import MIMEText

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
