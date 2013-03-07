import sys
if ".." not in sys.path:
    sys.path.append("..")

import AppFacade
from PyQt4 import QtCore
import puremvc.interfaces
import puremvc.patterns.mediator


class SysTrayMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'SysTrayMediator'

    def __init__(self, viewComponent):
        super(SysTrayMediator, self).__init__(SysTrayMediator.NAME, viewComponent)

        QtCore.QObject.connect(viewComponent.exitAction, QtCore.SIGNAL('triggered()'),
                               self.onExit, QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(viewComponent.openAction, QtCore.SIGNAL('triggered()'),
                               self.onOpen, QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(viewComponent.settingsAction, QtCore.SIGNAL('triggered()'),
                               self.onSettings, QtCore.Qt.QueuedConnection)                               

    def onOpen(self):
        print 'Opening App'
        
    def onSettings(self):
        print 'Opening settings'

    def onExit(self):
        self.facade.sendNotification(AppFacade.AppFacade.EXIT)