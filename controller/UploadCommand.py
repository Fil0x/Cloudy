import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class UploadCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()
        if note_name == AppFacade.AppFacade.UPLOAD_ADDED:
            note_body[0].signals.upload_detailed_start.emit(note_body[1:])
        elif note_name == AppFacade.AppFacade.UPLOAD_UPDATED:
            note_body[0].signals.upload_detailed_update.emit(note_body[1:])
        elif note_name == AppFacade.AppFacade.UPLOAD_DONE:
            note_body[0].signals.upload_detailed_finish.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.UPLOAD_PAUSING:
            note_body[0].signals.upload_detailed_pausing.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.UPLOAD_PAUSED:
            note_body[0].signals.upload_detailed_paused.emit(note_body[1])