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
        self.items = {} #The key is the service.

        mainLayout = QtGui.QVBoxLayout()
        for s in self.services:
            setattr(self, '{}Group'.format(s.lower()), QtGui.QGroupBox(s))
            getattr(self, '{}Group'.format(s.lower())).setLayout(self._createServiceContent(s, True))
            mainLayout.addWidget(getattr(self, '{}Group'.format(s.lower())))
        mainLayout.addSpacing(12)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

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

        if service in self.used_services:
            # s = QtGui.QCheckBox("Update system")
            # layout.addWidget(s)
            pass
        else:
            panel = NotAuthorizedPanel(service)
            self.items[service] = panel
            layout.addWidget(panel)

        return layout

        
class NotAuthorizedPanel(QtGui.QWidget):
    clickedSignal = QtCore.pyqtSignal(str)

    def __init__(self, service, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.service = service
        
        layout = QtGui.QHBoxLayout()
        
        self.code_edit = QtGui.QLineEdit()
        self.authorize_button = QtGui.QPushButton('Authorize')
        self.authorize_button.clicked.connect(self.onAuthorizeClicked)
        self.verify_button = QtGui.QPushButton('Verify')
        self.verify_button.setEnabled(False)
        self.verify_button.clicked.connect(self.onVerifyClicked)
        
        layout.addWidget(self.code_edit)
        layout.addWidget(self.authorize_button)
        layout.addWidget(self.verify_button)
        
        self.setLayout(layout)
       
    def onAuthorizeClicked(self, event): 
        self.verify_button.setEnabled(True)
        
    def onVerifyClicked(self, event):
        self.clickedSignal.emit(self.service)
   
class Settings(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)

        self.used_services = []

        self.contentsWidget = QtGui.QListWidget()
        self.contentsWidget.setViewMode(QtGui.QListView.IconMode)
        self.contentsWidget.setIconSize(QtCore.QSize(55, 55))
        self.contentsWidget.setMovement(QtGui.QListView.Static)
        self.contentsWidget.setMaximumWidth(90)
        self.contentsWidget.setSpacing(12)

        self.general_page = GeneralPage()
        self.accounts_page = AccountsPage(self.used_services)

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
