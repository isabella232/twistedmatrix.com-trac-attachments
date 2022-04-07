#!/usr/bin/env python
"""Demonstrate exceptions being swallowed on Mac OS X

The bug only shows up when using Twisted (UseTwisted true).
(Though oddly enough Cmd-Q quits -- after raising the exception -- when not using Twisted.)
"""
import Tkinter
root = Tkinter.Tk()

UseTwisted = True
if UseTwisted:
    import twisted.internet.tksupport
    twisted.internet.tksupport.install(root)
    reactor = twisted.internet.reactor

def doQuit():
    """Raise an exception instead of calling reactor.stop() to demonstrate the bug"""
    print "About to raise an exception"
    raise RuntimeError("Example exception")

Tkinter.Label(root, text="Cmd-Q (Python>Quit Python) hides the exception").pack()
Tkinter.Button(root, text="This button command does not hide exception", command=doQuit).pack()
if UseTwisted:
    Tkinter.Button(root, text="Quit", command=reactor.stop).pack()
else:
    Tkinter.Button(root, text="Quit", command=root.quit).pack()

root.createcommand("::tk::mac::Quit", doQuit)

if UseTwisted:
    reactor.run()
else:
    root.mainloop()
