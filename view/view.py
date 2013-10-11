import os
import sys
import datetime
from operator import itemgetter
if ".." not in sys.path:
    sys.path.append("..")

import logger
import globals
import AppFacade
import model.modelProxy
from lib.util import raw
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtGui
from PyQt4 import QtCore
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
        viewComponent.activated.connect(self.onActivate)

    def onActivate(self, reason):
        if reason == QtGui.QSystemTrayIcon.Trigger:
            self.facade.sendNotification(AppFacade.AppFacade.HISTORY_SHOW_COMPACT,
                                         [globals.get_globals()])

    def onOpen(self):
        self.facade.sendNotification(AppFacade.AppFacade.SHOW_DETAILED)

    def onSettings(self):
        self.facade.sendNotification(AppFacade.AppFacade.SHOW_SETTINGS)

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
        m = data[1]
        if m.hasUrls() and len(m.urls()) < 4:
            for url in m.urls():
                p = raw(url.path()[1:])
                if os.path.isfile(p):
                    self.proxy.add_file(data[0], str(p))

class DetailedWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'DetailedWindowMediator'

    def __init__(self, viewComponent):
        super(DetailedWindowMediator, self).__init__(DetailedWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.g = globals.get_globals()

        buttons = ['add', 'remove', 'play', 'stop']
        methods = [self.onAdd, self.onRemove, self.onPlay, self.onStop]
        for item in zip(buttons, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0] + 'Btn'), QtCore.SIGNAL('clicked()'),
                                   item[1], QtCore.Qt.QueuedConnection)

        self.viewComponent.update_all_history(self._format_history())

        self.g.signals.history_detailed.connect(self.onHistoryAdd)
        self.g.signals.upload_detailed_start.connect(self.onUploadStart)
        self.g.signals.upload_detailed_update.connect(self.onUploadUpdate)
        self.g.signals.upload_detailed_finish.connect(self.onUploadComplete)

    def onUploadStart(self, body):
        self.viewComponent.add_upload_item(body)

    def onUploadUpdate(self, body):
        self.viewComponent.update_upload_item(body)

    def onUploadComplete(self, id):
        self.viewComponent.delete_upload_item(id)

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
        index = self.viewComponent.get_current_tab()
        delete = self.viewComponent.get_selected_ids(index)

        if not delete:
            return
            
        if index == 0:
            pass
        elif index == 1:
            self.facade.sendNotification(AppFacade.AppFacade.HISTORY_DELETE_ITEM,
                                         delete)

    def onStop(self):
        print 'OnStop'

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.SHOW_DETAILED,
            AppFacade.AppFacade.SHOW_SETTINGS,
            AppFacade.AppFacade.DELETE_HISTORY_DETAILED
        ]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.SHOW_DETAILED and not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
        elif note_name == AppFacade.AppFacade.SHOW_SETTINGS:
            self.viewComponent.show_settings()
            if not self.viewComponent.isVisible():
                self.viewComponent.setVisible(True)
        elif note_name == AppFacade.AppFacade.DELETE_HISTORY_DETAILED:
            for i in body:
                self.viewComponent.delete_history_item(i)

class HistoryWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'HistoryWindowMediator'

    def __init__(self, viewComponent):
        super(HistoryWindowMediator, self).__init__(HistoryWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.g = globals.get_globals()

        self.logger = logger.logger_factory(self.__class__.__name__)
        #To avoid the constant reading from the disk.
        self.initialized = False

        self.g.signals.history_compact_show.connect(self.onShow)
        self.g.signals.history_compact_update.connect(self.onAdd)

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.DELETE_HISTORY_COMPACT
        ]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.DELETE_HISTORY_COMPACT:
            if self.viewComponent.isVisible():
                self.viewComponent.update_all(self._format_history())

    def _format_history(self):
        l = []
        r = self.proxy.get_history()
        for k, v in r.iteritems():
            for id, item in v.iteritems():
                l.append([k, item['path'], item['link'], item['date']])
        return sorted(l, key=itemgetter(3))

    def onShow(self):
        if not self.viewComponent.isVisible():
            #TODO: limit the items that are passed to max_count.
            self.viewComponent.update_all(self._format_history())
            self.viewComponent.setVisible(True)
            self.initialized = True
        else:
            self.viewComponent.setVisible(False)

    def onAdd(self, body):
        if self.initialized:
            self.viewComponent.add_item(body[0], body[1]['path'],
                                        body[1]['link'], body[1]['date'])
        else:
            self.viewComponent.update_all(self._format_history())
            self.initialized = True
        if not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)
