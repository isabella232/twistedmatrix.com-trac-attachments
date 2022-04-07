try:
    from twisted.internet import threadedselectreactor
except ImportError:   # Use my local copy if threadedselectreactor's still not released 
    import threadedselectreactor

reactor = threadedselectreactor.install()

from twisted.web import client
import wx

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Minimal")
        self.text = wx.TextCtrl(self,wx.ID_ANY,'',(0,0),self.GetClientSizeTuple(),style=wx.TE_MULTILINE)
        self.Show()

        reactor.callLater(2,self.getGoogle)
    def getGoogle(self):    
        def gotGoogle(page):
            self.text.SetValue(page)
        self.text.SetValue("Now it'll be broken :(\n\tfetching ...")
        return client.getPage("http://www.google.com/").addCallback(gotGoogle)

class Application(wx.App):
    def OnInit(self):
        self.mainFrame = MainFrame()
        self.SetTopWindow(self.mainFrame)
        reactor.interleave(wx.CallAfter)
        reactor.addSystemEventTrigger('after', 'shutdown', self.Destroy, True)
        return True

if __name__=="__main__":
    Application().MainLoop()
