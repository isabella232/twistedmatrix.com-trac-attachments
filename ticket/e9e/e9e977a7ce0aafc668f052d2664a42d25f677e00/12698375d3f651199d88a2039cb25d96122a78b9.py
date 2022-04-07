# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
This module provides CoreFoundation event loop support for Twisted.

In order to use this support, simply do the following::

    |  from twisted.internet import cfreactor2
    |  cfreactor2.install()

Then use twisted.internet APIs as usual. Stop the event loop using
reactor.stop(), not AppHelper.stopEventLoop().

IMPORTANT: tests will fail when run under this reactor. This is
expected and probably does not reflect on the reactor's ability to run
real applications.

Maintainer: U{Phil Christensen<mailto:phil@bubblehouse.org>}
"""

from twisted.internet import _threadedselect
from PyObjCTools import AppHelper

class CFReactor(_threadedselect.ThreadedSelectReactor):
    """
    CoreFoundation reactor.

    Cocoa drives the event loop, select() runs in a thread.
    """
    _stopping = False

    def stop(self):
        """
        Stop the reactor.
        """
        if self._stopping:
            return
        self._stopping = True
        _threadedselect.ThreadedSelectReactor.stop(self)

    def run(self, installSignalHandlers=True):
        self.interleave(AppHelper.callAfter, installSignalHandlers=installSignalHandlers)
        self.mainLoop()

    def mainLoop(self):
        """
        Start the reactor.
        """
        self.addSystemEventTrigger("after", "shutdown", AppHelper.stopEventLoop)
        AppHelper.runEventLoop()

def install():
    """
    Configure the twisted mainloop to be run inside the wxPython mainloop.
    """
    reactor = CFReactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor


__all__ = ['install']
