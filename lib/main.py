import wx
import controller
import components
import puremvc.patterns.facade

class AppFacade(puremvc.patterns.facade.Facade):
    
    SITE = 'http://cslab.ece.ntua.gr/~fsami/test/'
    
    STARTUP = 'startup'
    APPEXIT = 'appExit'
    
    SHOWCOMPACT = 'showCompact'
    SHOWDETAILED = 'showDetailed'
    
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
        
        super(AppFacade, self).registerCommand(AppFacade.STARTUP, controller.StartupCommand)
    
if __name__ == '__main__':
    app = AppFacade.getInstance()
    wxApp = components.WxApp(0)
    app.sendNotification(AppFacade.STARTUP, wxApp.appFrame)
    wxApp.MainLoop()