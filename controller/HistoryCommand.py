import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class HistoryCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()
        if note_name == AppFacade.AppFacade.HISTORY_UPDATE_COMPACT:
            note_body[0].signals.history_compact.emit(note_body[1:])
        elif note_name == AppFacade.AppFacade.HISTORY_UPDATE_DETAILED:
            note_body[0].signals.history_detailed.emit(note_body[1:])