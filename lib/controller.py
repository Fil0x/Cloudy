#import model
import view
import main
import puremvc.patterns.command
import puremvc.interfaces

class StartupCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, note):
        mainpanel = note.getBody()
        self.facade.registerMediator(view.TrayMediator(mainpanel.tbIcon))