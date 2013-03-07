import puremvc.patterns.facade
from controller.StartUpCommand import StartUpCommand
from controller.ExitAppCommand import ExitAppCommand
from controller.DataUpdatedCommand import DataUpdatedCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'
    DATA_UPDATED = 'data_updated'
    DATA_CHANGED = 'data_changed'

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
        super(AppFacade, self).registerCommand(AppFacade.DATA_UPDATED, DataUpdatedCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)