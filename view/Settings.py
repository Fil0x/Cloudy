import sys

import local

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

class GeneralPage(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        configGroup = QtGui.QGroupBox("Server configuration")

        serverLabel = QtGui.QLabel("Server:")
        serverCombo = QtGui.QComboBox()
        serverCombo.addItem("Trolltech (Australia)")
        serverCombo.addItem("Trolltech (Germany)")
        serverCombo.addItem("Trolltech (Norway)")
        serverCombo.addItem("Trolltech (People's Republic of China)")
        serverCombo.addItem("Trolltech (USA)")

        serverLayout = QtGui.QHBoxLayout()
        serverLayout.addWidget(serverLabel)
        serverLayout.addWidget(serverCombo)

        configLayout = QtGui.QVBoxLayout()
        configLayout.addLayout(serverLayout)
        configGroup.setLayout(configLayout)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(configGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

class AccountsPage(QtGui.QWidget):
    def __init__(self, used_services, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.services = local.services
        self.used_services = used_services
        self.notauth_panels = {} #The key is the service.
        self.auth_panels = {} #The key is the service.

        mainLayout = QtGui.QVBoxLayout()
        for s in self.services:
            self.notauth_panels[s] = NotAuthorizedPanel(s)
            self.auth_panels[s] = getattr(sys.modules[__name__], '{}AuthorizedPanel'.format(s))()
            setattr(self, '{}Group'.format(s.lower()), QtGui.QGroupBox(s))
            getattr(self, '{}Group'.format(s.lower())).setLayout(self._createServiceContent(s, True))
            mainLayout.addWidget(getattr(self, '{}Group'.format(s.lower())))
        mainLayout.addSpacing(12)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def showEvent(self, event):
        for v in self.notauth_panels.itervalues():
            v.code_edit.setEnabled(False)
            v.verify_button.setEnabled(False)
        
    def add_service(self, service):
        self.used_services.append(service)
        self._clearLayout(service)
        self._createServiceContent(service)
        
    def remove_service(self, service):
        self.used_services.remove(service)
        self._clearLayout(service)
        self._createServiceContent(service)
        
    #http://tinyurl.com/mcj4zpk
    def _clearLayout(self, service):
        layout = getattr(self, '{}Group'.format(service.lower())).layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)

            if isinstance(item, QtGui.QWidgetItem):
                item.widget().setVisible(False)
            else:
                self.clearLayout(item.layout())

            layout.removeItem(item)

    def _createServiceContent(self, service, new=False):
        if new:
            layout = QtGui.QVBoxLayout()
        else:
            layout = getattr(self, '{}Group'.format(service.lower())).layout()
        layout.addWidget(self.notauth_panels[service])
        layout.addWidget(self.auth_panels[service])
            
        # if service in self.used_services:
            # layout.addWidget(self.auth_panels[service])
        # else:
            # layout.addWidget(self.notauth_panels[service])
        if service in self.used_services:
            self.notauth_panels[service].setVisible(False)
            self.auth_panels[service].setVisible(True)
        else:
            self.auth_panels[service].setVisible(False)
            self.notauth_panels[service].setVisible(True)

        return layout

class NotAuthorizedPanel(QtGui.QWidget):
    verifySignal = QtCore.pyqtSignal(str, str)
    authorizeSignal = QtCore.pyqtSignal(str)

    def __init__(self, service, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.service = service

        layout = QtGui.QHBoxLayout()

        self.code_edit = QtGui.QLineEdit()
        self.code_edit.setEnabled(False)
        self.code_edit.textChanged.connect(self.onTextChanged)

        self.authorize_button = QtGui.QPushButton('Authorize')
        self.authorize_button.clicked.connect(self.onAuthorizeClicked)

        self.verify_button = QtGui.QPushButton('Verify')
        self.verify_button.setEnabled(False)
        self.verify_button.clicked.connect(self.onVerifyClicked)

        layout.addWidget(self.code_edit)
        layout.addWidget(self.authorize_button)
        layout.addWidget(self.verify_button)

        self.setLayout(layout)

    def onTextChanged(self, text):
        if len(text):
            self.verify_button.setEnabled(True)
        else:
            self.verify_button.setEnabled(False)

    def onAuthorizeClicked(self, event):
        self.code_edit.setEnabled(True)
        self.authorizeSignal.emit(self.service)

    def onVerifyClicked(self, event):
        self.verify_button.setEnabled(False)
        self.verifySignal.emit(self.service, self.code_edit.text())

class DropboxAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str) 

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        layout = QtGui.QGridLayout()
        
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.clicked.connect(self.onRemoveClick)
        
        layout.addWidget(QtGui.QLabel('Lol authenticated.'), 0, 0)
        layout.addWidget(self.remove_button, 0, 2)
        
        self.setLayout(layout)
        
    def onRemoveClick(self, event):
        self.removeSignal.emit('Dropbox')
        
class PithosAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str) 

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        layout = QtGui.QGridLayout()
        
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.clicked.connect(self.onRemoveClick)
        
        layout.addWidget(QtGui.QLabel('Lol authenticated.'), 0, 0)
        layout.addWidget(self.remove_button, 0, 2)
        
        self.setLayout(layout)
        
    def onRemoveClick(self, event):
        self.removeSignal.emit('Pithos')
        
class GoogleDriveAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str) 

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        layout = QtGui.QGridLayout()
        
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.clicked.connect(self.onRemoveClick)
        
        layout.addWidget(QtGui.QLabel('Lol authenticated.'), 0, 0)
        layout.addWidget(self.remove_button, 0, 2)
        
        self.setLayout(layout)
        
    def onRemoveClick(self, event):
        self.removeSignal.emit('GoogleDrive')
        
class Settings(QtGui.QWidget):
    def __init__(self, used_services, parent=None):
        super(Settings, self).__init__(parent)

        self.contentsWidget = QtGui.QListWidget()
        self.contentsWidget.setViewMode(QtGui.QListView.IconMode)
        self.contentsWidget.setIconSize(QtCore.QSize(55, 55))
        self.contentsWidget.setMovement(QtGui.QListView.Static)
        self.contentsWidget.setMaximumWidth(90)
        self.contentsWidget.setSpacing(12)

        self.general_page = GeneralPage()
        self.accounts_page = AccountsPage(used_services)

        self.pagesWidget = QtGui.QStackedWidget()
        self.pagesWidget.addWidget(self.general_page)
        self.pagesWidget.addWidget(self.accounts_page)

        self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)

        self.setLayout(mainLayout)
    
    def show_settings(self):
        self.contentsWidget.setCurrentRow(0)
        
    def show_accounts(self):
        self.contentsWidget.setCurrentRow(1)
        
    def add_service(self, service):
        self.accounts_page.add_service(service)
      
    def remove_service(self, service):
        self.accounts_page.remove_service(service)
        
    def changePage(self, current, previous):
        if not current:
            current = previous

        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def createIcons(self):
        configButton = QtGui.QListWidgetItem(self.contentsWidget)
        configButton.setIcon(QtGui.QIcon(r'images/settings-general.png'))
        configButton.setText("General")
        configButton.setTextAlignment(QtCore.Qt.AlignHCenter)
        configButton.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        updateButton = QtGui.QListWidgetItem(self.contentsWidget)
        updateButton.setIcon(QtGui.QIcon(r'images/settings-account.png'))
        updateButton.setText("Accounts")
        updateButton.setTextAlignment(QtCore.Qt.AlignHCenter)
        updateButton.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        self.contentsWidget.currentItemChanged.connect(self.changePage)
