import model

import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class ErrorCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()
        if note_name == AppFacade.AppFacade.NETWORK_ERROR:
            print note_name
        elif note_name == AppFacade.AppFacade.OUT_OF_STORAGE:
            print note_name
        elif note_name == AppFacade.AppFacade.SERVICE_OFFLINE:
            print note_name
        elif note_name == AppFacade.AppFacade.INVALID_CREDENTIALS:
            print note_name
        elif note_name == AppFacade.AppFacade.FILE_NOT_FOUND:
            note_body[0].signals.file_not_found.emit(note_body[1])
