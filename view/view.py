import os
import sys
from operator import itemgetter
import datetime
if ".." not in sys.path:
    sys.path.append("..")

import AppFacade
import logger
import model.modelProxy
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtGui
from PyQt4 import QtCore
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
            self.facade.sendNotification(AppFacade.AppFacade.UPDATE_HISTORY)

    def onOpen(self):
        self.facade.sendNotification(AppFacade.AppFacade.SHOW_DETAILED)
        self.facade.sendNotification(AppFacade.AppFacade.DATA_CHANGED)

    def onSettings(self):
        print 'Opening settings'

    def onExit(self):
        self.facade.sendNotification(AppFacade.AppFacade.EXIT)

class CompactWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'CompactWindowMediator'

    def __init__(self, viewComponent):
        super(CompactWindowMediator, self).__init__(CompactWindowMediator.NAME, viewComponent)
        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)

        p = ApplicationManager()
        for s in p.get_services():
            self.viewComponent.items[s].droppedSignal.connect(self.onDrop)
        self.viewComponent.setVisible(True)

    def onDrop(self, data):
        self.proxy.add_file(data[0], str(data[1]))

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
                                   
        self.viewComponent.update_all_history(self._format_history())
        self.proxy.ht.signals.history_detailed.connect(self.onHistoryAdd)

    def onHistoryAdd(self, body):
        self.viewComponent.add_history_item([body[2]['path'], body[2]['link'], body[0], 
                                             body[2]['date'], body[1]])
        
    def _format_history(self):
        l = []
        r = self.proxy.get_history()
        for k, v in r.iteritems():
            for id, item in v.iteritems():
                l.append([item['path'], item['link'], k, item['date'], id])
        return sorted(l, key=itemgetter(3))
        
    def onAdd(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self.viewComponent,
                                     'Open file...', os.path.expanduser('~'))
        #TODO: choose service, directory
        #for i in filenames:
            #self.proxy.dropbox_add(str(i))

        #Ask the model proxy for the new data.
        #self.viewComponent.set_model_data(self.proxy.detailed_view_data())

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
        note_name = notification.getName()

        if note_name == AppFacade.AppFacade.SHOW_DETAILED and not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
        elif note_name == AppFacade.AppFacade.DATA_CHANGED and self.viewComponent.isVisible():
            #self.viewComponent.set_model_data(self.proxy.detailed_view_data())
            pass

class HistoryWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'HistoryWindowMediator'

    def __init__(self, viewComponent):
        super(HistoryWindowMediator, self).__init__(HistoryWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.logger = logger.logger_factory(self.__class__.__name__)
        #To avoid the constant reading from the disk.
        self.initialized = False

        self.proxy.ht.signals.history_compact.connect(self.onAdd)

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.UPDATE_HISTORY
        ]

    def _format_history(self):
        l = []
        r = self.proxy.get_history()
        for k, v in r.iteritems():
            for id, item in v.iteritems():
                l.append([k, item['path'], item['link'], item['date']])
        return sorted(l, key=itemgetter(3))

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.UPDATE_HISTORY:
            if not self.viewComponent.isVisible() and not body:
                #TODO: limit the items that are passed to max_count.
                self.viewComponent.update_all(self._format_history())
                self.viewComponent.setVisible(True)
                self.initialized = True

    def onAdd(self, body):
        if self.initialized:
            self.viewComponent.add_item(body[0], body[1]['path'],
                                        body[1]['link'], body[1]['date'])
        else:
            self.viewComponent.update_all(self._format_history())
            self.initialized = True
        if not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
