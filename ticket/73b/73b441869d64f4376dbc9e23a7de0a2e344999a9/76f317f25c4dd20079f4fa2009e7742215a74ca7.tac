
# commands to produce error
#
#   $ touch foo.txt
#   $ twistd -ny twisted-inotify-bug.tac
#   $ emacs foo.txt
#      edit some text, save the file (C-x C-s)
#   $ echo "a" >> foo.txt
#   $ emacs foo.txt
#      edit some text, save the file (C-x C-s)
#
# error produced
#
#   2010-10-09 22:43:17-0400 [-] Unhandled Error
#           Traceback (most recent call last):
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/python/log.py", line 84, in callWithLogger
#               return callWithContext({"system": lp}, func, *args, **kw)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/python/log.py", line 69, in callWithContext
#               return context.call({ILogContext: newCtx}, func, *args, **kw)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/python/context.py", line 59, in callWithContext
#               return self.currentContext().callWithContext(ctx, func, *args, **kw)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/python/context.py", line 37, in callWithContext
#               return func(*args,**kw)
#           --- <exception caught here> ---
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/selectreactor.py", line 146, in _doReadOrWrite
#               why = getattr(selectable, method)()
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/inotify.py", line 230, in doRead
#               fdesc.readFromFD(self._fd, self._doRead)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/fdesc.py", line 94, in readFromFD
#               callback(output)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/inotify.py", line 257, in _doRead
#               iwp._notify(path, mask)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/inotify.py", line 132, in _notify
#               callback(self, filepath, events)
#             File "twisted-inotify-bug.tac", line 27, in event
#               ignore( fpobj.path )
#             File "twisted-inotify-bug.tac", line 37, in ignore
#               notifier.ignore( filepath.FilePath( pathname ) )
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/inotify.py", line 371, in ignore
#               self._rmWatch(wd)
#             File "/usr/lib/python2.4/site-packages/Twisted-10.1.0-py2.4-linux-i686.egg/twisted/internet/inotify.py", line 202, in _rmWatch
#               iwp = self._watchpoints.pop(wd)
#           exceptions.KeyError: True
   


import os
import time

import twisted
from twisted.python import filepath
from twisted.internet import inotify

from twisted.application import service, internet
from twisted.web import static, server, resource


FILEPATH = './foo.txt'


def event ( notifier, fpobj, mask ) :
    print
    print( 'mask: ' + str(mask) )
    print( 'human readable mask: ' + str(inotify.humanReadableMask(mask)) )
    print( 'filepath: ' + fpobj.path )
    print

    # re-watch this file
    if mask == 2048 : # move-self
        ignore( fpobj.path )
        time.sleep(0.3) # sleep to make sure the file exists again by the time we re-watch it
        watch( fpobj.path )

def watch ( pathname ) :
    global notifier
    notifier.watch( filepath.FilePath( pathname ), callbacks=[event] )

def ignore ( pathname ) :
    global notifier
    notifier.ignore( filepath.FilePath( pathname ) )
             

application = service.Application("twisted inotify bug example")
service = internet.TCPServer(8080, twisted.web.server.Site( server.Site(static.File(os.getcwd())) ) )
service.setServiceParent(application)


notifier = inotify.INotify()
notifier.startReading()

watch( FILEPATH )
