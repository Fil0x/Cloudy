import os
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

        actions = ['exitAction', 'openAction']
        methods = [self.onExit, self.onOpen]
        for item in zip(actions, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0]), QtCore.SIGNAL('triggered()'),
                               item[1], QtCore.Qt.QueuedConnection)
        viewComponent.activated.connect(self.onActivate)

    def onActivate(self, reason):
        if reason == QtGui.QSystemTrayIcon.Trigger:
            self.facade.sendNotification(AppFacade.AppFacade.SHOW_HISTORY)

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

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)

        buttons = ['add', 'remove', 'play', 'stop']
        methods = [self.onAdd, self.onRemove, self.onPlay, self.onStop]
        for item in zip(buttons, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0] + 'Btn'), QtCore.SIGNAL('clicked()'),
                                   item[1], QtCore.Qt.QueuedConnection)

    def onAdd(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self.viewComponent,
                                     'Open file...', os.path.expanduser('~'))
        #TODO: choose service, directory
        for i in filenames:
            self.proxy.dropbox_add(str(i))

        #Ask the model proxy for the new data.
        self.viewComponent.set_model_data(self.proxy.detailed_view_data())

    def onPlay(self):
        print 'OnPlay'

    def onRemove(self):
        print 'OnRemove'

    def onStop(self):
        print 'OnStop'

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
            self.viewComponent.set_model_data(self.proxy.detailed_view_data())

class HistoryWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'HistoryWindowMediator'

    def __init__(self, viewComponent):
        super(HistoryWindowMediator, self).__init__(HistoryWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.SHOW_HISTORY,
            AppFacade.AppFacade.UPDATE_HISTORY
        ]

    def handleNotification(self, notification):
        def _update_window(r, window):
            for k, v in r.iteritems():
                for id, item in v.iteritems():
                    window.add_item(k, item['path'], item['link'], item['date'])
        note_name = notification.getName()
        r = self.proxy.get_history()
        if note_name == AppFacade.AppFacade.SHOW_HISTORY and not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
            _update_window(r, self.viewComponent)
        elif note_name == AppFacade.AppFacade.UPDATE_HISTORY and self.viewComponent.isVisible():
            _update_window(r, self.viewComponent)
