from Feedback import FeedbackPage

from PyQt4 import QtGui

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        icon = QtGui.QIcon(r'images/favicon.ico')
        self.setIcon(icon)

        menu = QtGui.QMenu(parent)

        #@Mediator
        self.openAction = menu.addAction('Open')
        #@Mediator
        self.settingsAction = menu.addAction('Settings')
        
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
