import puremvc.patterns.facade
import controller


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'
    DATA_CHANGED = 'data_changed'
    DATA_UPDATED = 'data_updated'

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

        super(AppFacade, self).registerCommand(AppFacade.STARTUP, controller.StartUpCommand)
        super(AppFacade, self).registerCommand(AppFacade.DATA_UPDATED, controller.DataUpdatedCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, controller.ExitAppCommand)