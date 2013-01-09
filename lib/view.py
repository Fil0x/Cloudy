#import model
import main
import wx
import puremvc.patterns.mediator
import puremvc.interfaces

class TrayMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):
    NAME = 'TrayMediator'
    
    def __init__(self, viewComponent):
        super(TrayMediator, self).__init__(TrayMediator.NAME, viewComponent)
    
    def listNodificationInterests(self):
        return [ 
            main.AppFacade.SHOWCOMPACT,
            main.AppFacade.SHOWDETAILED
        ]
    
    def handleNotification(self, note):
        noteName = note.getName()
        if noteName == main.AppFacade.SHOWCOMPACT:
            #Show compact view
            pass
        elif noteName == main.AppFacade.SHOWDETAILED:
            #SHOWDETAILED
            pass