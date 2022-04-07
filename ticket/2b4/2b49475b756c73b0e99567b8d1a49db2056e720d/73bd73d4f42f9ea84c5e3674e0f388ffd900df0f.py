# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

"""Demo of wxPython integration with Twisted.

This shows creating a new FileDialog as a
local variable in a function.  This causes
reactor to stop processing permanently!!

"""

import sys
import wx

from twisted.python import log
from twisted.internet import wxreactor
wxreactor.install()

# import t.i.reactor only after installing wxreactor:
from twisted.internet import reactor, defer

class MyFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(300, 200))

        menu = wx.Menu()
        openId = wx.NewId()
        menu.Append(openId, 'Open', 'Open')
        menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")

        menuBar = wx.MenuBar()
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        wx.EVT_MENU(self, wx.ID_EXIT,  self.DoExit)
        wx.EVT_MENU(self, openId, self.DoOpen)
        
        # make sure reactor.stop() is used to stop event loop:
        wx.EVT_CLOSE(self, lambda evt: reactor.stop())

    def DoExit(self, event):
        reactor.stop()

    def DoOpen(self, event):
        dialog = wx.FileDialog(self, 'sdf', style = wx.OPEN)
        dialog.ShowModal()
        dialog.Destroy()

class MyApp(wx.App):
    def twoSecondsPassed(self):
        print "two seconds passed"
        reactor.callLater(2, self.twoSecondsPassed)

    def OnInit(self):
        frame = MyFrame(None, -1, "Hello, world")
        frame.Show(True)
        self.SetTopWindow(frame)
        # look, we can use twisted calls!
        reactor.callLater(2, self.twoSecondsPassed)
        return True


def demo():
    log.startLogging(sys.stdout)

    # register the wx.App instance with Twisted:
    app = MyApp(0)
    reactor.registerWxApp(app)

    # start the event loop:
    reactor.run()


if __name__ == '__main__':
    demo()
