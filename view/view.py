import sys
if ".." not in sys.path:
    sys.path.append("..")

import AppFacade
import model.modelProxy
from PyQt4 import QtCore, QtGui
import puremvc.interfaces
import puremvc.patterns.mediator


class SysTrayMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'SysTrayMediator'

    def __init__(self, viewComponent):
        super(SysTrayMediator, self).__init__(SysTrayMediator.NAME, viewComponent)

        actions = ['exitAction', 'openAction', 'settingsAction']
        methods = [self.onExit, self.onOpen, self.onSettings]
        for item in zip(actions, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0]), QtCore.SIGNAL('triggered()'),
                               item[1], QtCore.Qt.QueuedConnection)

    def onOpen(self):
        self.facade.sendNotification(AppFacade.AppFacade.SHOW_DETAILED)
        self.facade.sendNotification(AppFacade.AppFacade.DATA_CHANGED)
        
    def onSettings(self):
        print 'Opening settings'

    def onExit(self):
        self.facade.sendNotification(AppFacade.AppFacade.EXIT)
        
class DetailedWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):
    
    NAME = 'DetailedWindowMediator'
    
    def __init__(self, viewComponent):
        super(DetailedWindowMediator, self).__init__(DetailedWindowMediator.NAME, viewComponent)
        
        self.dataProxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        
        buttons = ['add', 'remove', 'play', 'stop', 'settings']
        methods = [self.onAdd, self.onRemove, self.onPlay, self.onStop, self.onSettings]
        for item in zip(buttons, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0] + 'Btn'), QtCore.SIGNAL('clicked()'),
                                   item[1], QtCore.Qt.QueuedConnection)

    def onAdd(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self.viewComponent,
                                     'Open file...', r'C:\Users\Fadi\Desktop')
        #TODO: choose service, directory
        for i in filenames:
            self.dataProxy.dropbox_add(str(i))
            
        #Ask the model proxy for the new data.
        self.viewComponent.set_model_data(self.dataProxy.detailed_view_data())
        
    def onRemove(self):
        print 'OnRemove'
        
    def onPlay(self):
        print 'OnPlay'
       
    def onStop(self):
        print 'OnStop'
        
    def onSettings(self):
        print 'OnSettings'
        
    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.SHOW_DETAILED,
            AppFacade.AppFacade.DATA_CHANGED
        ]
        
    def handleNotification(self, notification):
        noteName = notification.getName()
        
        if noteName == AppFacade.AppFacade.SHOW_DETAILED and not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
        elif noteName == AppFacade.AppFacade.DATA_CHANGED and self.viewComponent.isVisible():
            self.viewComponent.set_model_data(self.dataProxy.detailed_view_data())