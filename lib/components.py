import wx
import main
import webbrowser

class WxApp(wx.App):

    appFrame = None

    def OnInit(self):
        self.appFrame = AppFrame()
        self.appFrame.Show()
        
        return True
        
class AppFrame(wx.Frame):

    tbIcon = None
    
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1, title='At last', size=(200,200))
        self.tbIcon = TrayIcon(self)    
    
class TrayIcon(wx.TaskBarIcon):
    TBMENU_RESTORE = wx.NewId()
    TBMENU_SITE = wx.NewId()
    TBMENU_EXIT = wx.NewId()
    
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        
        self.tbIcon = wx.Icon('images/favicon.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.tbIcon, 'Test')
        
        self.Bind(wx.EVT_MENU, self.onTaskbarRestore, id=self.TBMENU_RESTORE)
        self.Bind(wx.EVT_MENU, self.onTaskbarSite, id=self.TBMENU_SITE)
        self.Bind(wx.EVT_MENU, self.onTaskbarExit, id=self.TBMENU_EXIT)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.onTaskbarRightDown)
        self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.onTaskbarRightDown)
        
    def CreatePopupMenu(self, evt=None):
        menu = wx.Menu()
        menu.Append(self.TBMENU_RESTORE, 'Open Program')
        menu.Append(self.TBMENU_SITE, 'Go to site')
        menu.AppendSeparator()
        menu.Append(self.TBMENU_EXIT, 'Exit program')
        
        return menu
        
    def onTaskbarRestore(self, evt):
        pass
    
    def onTaskbarSite(self, evt):
        webbrowser.open(main.AppFacade.SITE)

    def onTaskbarExit(self, evt):
        self.RemoveIcon()
        self.Destroy()
        wx.GetApp().Exit()
        
    def onTaskbarRightDown(self, evt):
        menu = self.CreatePopupMenu()
        self.PopupMenu(menu)
        menu.Destroy()