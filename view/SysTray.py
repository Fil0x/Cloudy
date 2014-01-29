from Feedback import FeedbackPage

from PyQt4 import QtGui

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        icon = QtGui.QIcon(r'images/appicon.png')
        self.setIcon(icon)

        menu = QtGui.QMenu(parent)

        #@Mediator
        self.openAction = menu.addAction('Hide/Show Main window')
        #@Mediator
        self.recentAction = menu.addAction('Hide/Show Recent uploads')
        
        menu.addSeparator()
        
        #@Mediator
        self.settingsAction = menu.addAction('General settings')
        #@Mediator
        self.accountsAction = menu.addAction('Account settings')

        menu.addSeparator()

        feedbackAction = menu.addAction('Send feedback')
        feedbackAction.triggered.connect(self.onFeedback)

        menu.addSeparator()

        #@Mediator
        self.exitAction = menu.addAction('Quit')

        #@Mediator
        #Handler for the left click.

        self.setContextMenu(menu)
        self.setVisible(True)

    def show_message(self, title, msg, type='Information', duration=10000):
        #type = Information, NoIcon, Warning, Critical
        msg_type = getattr(QtGui.QSystemTrayIcon, type)
        self.showMessage(title, msg, msg_type, duration)

    def onFeedback(self, event):
        feedback = FeedbackPage()
        feedback.show()

    def closeEvent(self, event):
        print 'LULZ'
