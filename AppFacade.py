import globals

import puremvc.patterns.facade
from controller.UploadCommand import UploadCommand
from controller.StartUpCommand import StartUpCommand
from controller.ExitAppCommand import ExitAppCommand
from controller.HistoryCommand import HistoryCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'

    SHOW_DETAILED = 'show_detailed'
    SHOW_COMPACT = 'show_compact'

    HISTORY_SHOW_COMPACT = 'compact_show_history'
    HISTORY_UPDATE_COMPACT = 'compact_update_history'
    HISTORY_UPDATE_DETAILED = 'detailed_update_history'

    UPLOAD_ADDED = 'upload_added'
    UPLOAD_UPDATED = 'upload_updated'
    UPLOAD_DONE = 'upload_done'

    globals = globals.Globals()

    def __init__(self):
        self.initializeFacade()

    @staticmethod
    def getInstance():
        return AppFacade()

    def initializeFacade(self):
        super(AppFacade, self).initializeFacade()

        self.initializeController()

    def initializeController(self):
        super(AppFacade, self).initializeController()

        super(AppFacade, self).registerCommand(AppFacade.STARTUP, StartUpCommand)
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_UPDATE_COMPACT, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_UPDATE_DETAILED, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_SHOW_COMPACT, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_ADDED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_UPDATED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_DONE, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)