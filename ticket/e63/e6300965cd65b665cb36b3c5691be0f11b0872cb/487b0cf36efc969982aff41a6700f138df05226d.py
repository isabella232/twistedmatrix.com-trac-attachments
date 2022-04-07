# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""A win32event based implementation of the Twisted main loop.

This requires win32all or ActivePython to be installed.

API Stability: semi-stable

Maintainer: U{Itamar Shtull-Trauring<mailto:twisted@itamarst.org>}


LIMITATIONS:
 1. WaitForMultipleObjects and thus the event loop can only handle 64 objects.
 2. Process running has some problems (see Process docstring).


TODO:
 1. Event loop handling of writes is *very* problematic (this is causing failed tests).
    Switch to doing it the correct way, whatever that means (see below).
 2. Switch everyone to using Free Software so we don't have to deal with proprietary APIs.


ALTERNATIVE SOLUTIONS:
 - IIRC, sockets can only be registered once. So we switch to a structure
   like the poll() reactor, thus allowing us to deal with write events in
   a decent fashion. This should allow us to pass tests, but we're still
   limited to 64 events.

Or:

 - Instead of doing a reactor, we make this an addon to the select reactor.
   The WFMO event loop runs in a separate thread. This means no need to maintain
   separate code for networking, 64 event limit doesn't apply to sockets,
   we can run processes and other win32 stuff in default event loop. The
   only problem is that we're stuck with the icky socket based waker.
   Another benefit is that this could be extended to support >64 events
   in a simpler manner than the previous solution.

The 2nd solution is probably what will get implemented.
"""

# Win32 imports
from win32file import WSAEventSelect, FD_READ, FD_WRITE, FD_CLOSE, \
                      FD_ACCEPT, FD_CONNECT
from win32event import CreateEvent, SetEvent, MsgWaitForMultipleObjects, \
                       WAIT_OBJECT_0, WAIT_TIMEOUT, INFINITE, QS_ALLINPUT, QS_ALLEVENTS
import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32process
try:
    import win32security
except ImportError:
    win32security = None
import pywintypes
import msvcrt
import win32gui

# Twisted imports
from threading import Thread
from Queue import Queue, Empty
from twisted.internet import abstract, posixbase, main, error
from twisted.python import log, threadable, failure, components
from twisted.internet.interfaces import IReactorFDSet, IReactorProcess
from twisted.persisted import styles

# System imports
import os
import threading
import string
import time
import sys
from zope.interface import implements


# globals
reads = {}
writes = {}
events = {}

def dictRemove(dct, value):
    try:
        del dct[value]
    except KeyError:
        pass

def dictRemoveReader(events, reads, reader):
    try:
        del events[reads[reader]]
        del reads[reader]
    except KeyError:
        pass

def raiseException(e):
    raise e

class Win32Reactor(posixbase.PosixReactorBase):
    """Reactor that uses Win32 event APIs."""

    implements(IReactorFDSet, IReactorProcess)

    dummyEvent = CreateEvent(None, 0, 0, None)

    def __init__(self):
        threadable.init(1)
        self.toThreadQueue = Queue()
        self.toMainThread = Queue(1)
        self.workerThread = None
        self.mainWaker = None
        posixbase.PosixReactorBase.__init__(self)
        self.addSystemEventTrigger('after', 'shutdown', self._mainLoopShutdown)
        self._max_event_set_size = 0
    
    def wakeUp(self):
        # we want to wake up from any thread
        self.waker.wakeUp()
    
    def installWaker(self):
        if not self.waker:
            self.waker = w = _Waker()
            self.addEvent(w.event, w, '_pass')

    def callLater(self, *args, **kw):
        tple = posixbase.PosixReactorBase.callLater(self, *args, **kw)
        self.wakeUp()
        return tple
    
    def _sendToMain(self, msg, *args):
        #print >>sys.stderr, 'sendToMain', msg, args
        self.toMainThread.put((msg, args))
        if self.mainWaker is not None:
            self.mainWaker()

    def _sendToThread(self, fn, *args):
        #print >>sys.stderr, 'sendToThread', fn, args
        self.toThreadQueue.put((fn, args))

    def _makeSocketEvent(self, fd, action, why):
        """Make a win32 event object for a socket."""
        attr = '_threadedwin32eventreactor_cached_%d' % why
        try:
            event = getattr(fd,attr)
        except AttributeError:
            event = CreateEvent(None, 0, 0, None)
            WSAEventSelect(fd, event, why)
            setattr(fd,attr,event)
        self.addEvent(event,fd,action)
        return event

    def addEvent(self, event, fd, action, events=events):
        """Add a new win32 event to the event loop."""
        #print >> sys.stderr,'add event',event
        self._sendToThread(events.__setitem__, event, (fd,action))
        self.wakeUp()
    
    def removeEvent(self, event):
        """Remove an event."""
        #print >> sys.stderr,'remove event',event
        self._sendToThread(dictRemove,events,event)

    def addReader(self, reader, reads=reads):
        """Add a socket FileDescriptor for notification of data available to read.
        """
        #print >> sys.stderr,'add reader',reader
        event = self._makeSocketEvent(reader, 'doRead', FD_READ|FD_ACCEPT|FD_CONNECT|FD_CLOSE)
        self._sendToThread(reads.__setitem__, reader, event)
        self.wakeUp()

    def addWriter(self, writer, writes=writes):
        """Add a socket FileDescriptor for notification of data available to write.
        """
        #print >> sys.stderr,'add writer',writer
        self._sendToThread(writes.__setitem__, writer, 1)
        self.wakeUp()

    def removeReader(self, reader):
        """Remove a Selectable for notification of data available to read.
        """
        #print >> sys.stderr,'remove reader',reader
        self._sendToThread(dictRemoveReader,events,reads,reader)

    def removeWriter(self, writer, writes=writes):
        """Remove a Selectable for notification of data available to write.
        """
        #print >> sys.stderr,'remove writer',writer
        self._sendToThread(dictRemove,writes,writer)

    def removeAll(self):
        """Remove all selectables, and return a list of them."""
        return self._removeAll(reads, writes)

    def _workerInThread(self):
        try:
            while 1:
                fn, args = self.toThreadQueue.get()
                #print >>sys.stderr, "worker got", fn, args
                fn(*args)
        except SystemExit:
            pass
        except:
            f = failure.Failure()
            self._sendToMain('Failure', f)

    def doIteration(self,timeout):
        self._init_wait(timeout)
        msg, args = self.toMainThread.get()
        #print >>sys.stderr, 'got', msg, args
        getattr(self, '_process_' + msg)(*args)

    def _init_wait(self,timeout):
        canDoMoreWrites = 0
        #print >> sys.stderr, 'checking writes',writes
        for fd in writes.keys():
            if log.callWithLogger(fd, self._runWrite, fd):
                canDoMoreWrites = 1
        if canDoMoreWrites:
            timeout = 0
        self._sendToThread(self.doWaitForMultipleEventsInThread, timeout)
                
    def doWaitForMultipleEventsInThread(self, timeout,
                                reads=reads,
                                writes=writes):
        log.msg(channel='system', event='iteration', reactor=self)

        if timeout is None:
            #timeout = INFINITE
            timeout = 100
        else:
            timeout = int(timeout * 1000)

        if not (events or writes):
            # sleep so we don't suck up CPU time. do we we need this branch?
            # surely having a waker always means we have at least one event
            time.sleep(timeout / 1000.0)
        else:
            handles = events.keys() or [self.dummyEvent]
            self._max_event_set_size = max(self._max_event_set_size,len(handles))
            #print >>sys.stderr, 'waiting for',handles,timeout
            try:
                val = MsgWaitForMultipleObjects(handles, 0, timeout, QS_ALLINPUT | QS_ALLEVENTS)
            except:
                #print >>sys.stderr, 'was waiting for',len(handles),timeout
                raise
            #print >>sys.stderr, "waited and got", val
            if val == WAIT_TIMEOUT:
                pass
            elif val == WAIT_OBJECT_0 + len(handles):
                exit = win32gui.PumpWaitingMessages()
                if exit:
                    self._sendToMain('Quit') # this code path not tested
                    return
            elif val >= WAIT_OBJECT_0 and val < WAIT_OBJECT_0 + len(handles):
                fd, action = events[handles[val - WAIT_OBJECT_0]]
                self._sendToMain('Notify', fd, action)
                return 

        # drop-through if nothing to report. nested returns above have also called _sendToMain
        self._sendToMain('Nothing',)

    def _process_Quit(self):
        self.callLater(0, self.stop) 

    def _process_Nothing(self):
        pass

    def _process_Notify(self, fd, action):
        log.callWithLogger(fd, self._runAction, action, fd)

    def _process_Failure(self, f):
        f.raiseException() # not sure this is handled right....
            
    def _runWrite(self, fd):
        closed = 0
        try:
            closed = fd.doWrite()
        except:
            closed = sys.exc_info()[1]
            log.deferr()

        if closed:
            self.removeReader(fd)
            self.removeWriter(fd)
            try:
                fd.connectionLost(failure.Failure(closed))
            except:
                log.deferr()
        elif closed is None:
            return 1

    def _runAction(self, action, fd):
        try:
            closed = getattr(fd, action)()
        except:
            closed = sys.exc_info()[1]
            log.deferr()

        if closed:
            self._disconnectSelectable(fd, closed, action == 'doRead')

    def spawnProcess(self, processProtocol, executable, args=(), env={}, path=None, usePTY=0):
        """Spawn a process."""
        Process(self, processProtocol, executable, args, env, path)

    def ensureWorkerThread(self):
        if self.workerThread is None or not self.workerThread.isAlive():
            self.workerThread = Thread(target=self._workerInThread)
            self.workerThread.setDaemon(True)
            self.workerThread.start()
    
    def mainLoopBegin(self):
        if self.running:
            self.runUntilCurrent()

    def _interleave(self):
        while self.running:
            #print >>sys.stderr, "runUntilCurrent"
            self.runUntilCurrent()
            t2 = self.timeout()
            t = self.running and t2
            self._init_wait(t)
            #print >>sys.stderr, "yielding"
            yield None
            #print >>sys.stderr, "fetching"
            msg, args = self.toMainThread.get()
            #print >>sys.stderr, 'got',msg,args
            getattr(self, '_process_' + msg)(*args)

    def interleave(self, waker, *args, **kw):
        """
        waker(func) is a callable that will be called from
        some random thread.  Its job is to call func from
        the same thread that called this method.

        You should use this like a ninja master to integrate
        with foreign event loops.
        """
        self.startRunning(*args, **kw)
        loop = self._interleave()
        def mainWaker(waker=waker, loop=loop):
            #print >>sys.stderr, "mainWaker()"
            waker(loop.next)
        self.mainWaker = mainWaker
        loop.next()
        self.ensureWorkerThread()
    
    def _mainLoopShutdown(self):
        self.mainWaker = None
        if self.workerThread is not None:
            #print >>sys.stderr, 'getting...'
            self._sendToThread(raiseException, SystemExit)
            self.wakeUp()
            try:
                while 1:
                    msg, args = self.toMainThread.get_nowait()
                    #print >>sys.stderr, "ignored:", (msg, args)
            except Empty:
                pass
            self.workerThread.join()
            self.workerThread = None
        try:
            while 1:
                fn, args = self.toThreadQueue.get_nowait()
                if fn is self.doWaitForMultipleEventsInThread:
                    log.msg('Iteration is still in the thread queue!')
                elif fn is raiseException and args[0] is SystemExit:
                    pass
                else:
                    fn(*args)
        except Empty:
            pass



components.backwardsCompatImplements(Win32Reactor)


def install():
    threadable.init(1)
    r = Win32Reactor()
    from twisted.internet import main
    main.installReactor(r)
    return r


class _Waker(log.Logger, styles.Ephemeral):
    def __init__(self):
        self.event = CreateEvent(None,0,0,None)
    def wakeUp(self):
        SetEvent(self.event)
    def _pass(self):
        pass  # Have just been woken up. nothing to do

    

class Process(abstract.FileDescriptor):
    """A process that integrates with the Twisted event loop.

    Issues:

     - stdin close is actually signalled by process shutdown, which is wrong.
       Solution is to register stdin pipe with event loop and check for the
       correct event type - this needs to be implemented.

    If your subprocess is a python program, you need to:

     - Run python.exe with the '-u' command line option - this turns on
       unbuffered I/O. Buffering stdout/err/in can cause problems, see e.g.
       http://support.microsoft.com/default.aspx?scid=kb;EN-US;q1903

     - If you don't want Windows messing with data passed over
       stdin/out/err, set the pipes to be in binary mode::

        import os, sys, mscvrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

    """

    buffer = ''

    def __init__(self, reactor, protocol, command, args, environment, path):
        self.reactor = reactor
        self.protocol = protocol

        # security attributes for pipes
        if win32security is not None:
            sAttrs = win32security.SECURITY_ATTRIBUTES()
            sAttrs.bInheritHandle = 1
        else:
            sAttrs = None

        # create the pipes which will connect to the secondary process
        self.hStdoutR, hStdoutW = win32pipe.CreatePipe(sAttrs, 0)
        self.hStderrR, hStderrW = win32pipe.CreatePipe(sAttrs, 0)
        hStdinR,  self.hStdinW  = win32pipe.CreatePipe(sAttrs, 0)

        # set the info structure for the new process.
        StartupInfo = win32process.STARTUPINFO()
        StartupInfo.hStdOutput = hStdoutW
        StartupInfo.hStdError  = hStderrW
        StartupInfo.hStdInput  = hStdinR
        StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES

        # Create new handles whose inheritance property is false
        pid = win32api.GetCurrentProcess()

        tmp = win32api.DuplicateHandle(pid, self.hStdoutR, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
        win32file.CloseHandle(self.hStdoutR)
        self.hStdoutR = tmp

        tmp = win32api.DuplicateHandle(pid, self.hStderrR, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
        win32file.CloseHandle(self.hStderrR)
        self.hStderrR = tmp

        tmp = win32api.DuplicateHandle(pid, self.hStdinW, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
        win32file.CloseHandle(self.hStdinW)
        self.hStdinW = tmp

        # Add the specified environment to the current environment - this is
        # necessary because certain operations are only supported on Windows
        # if certain environment variables are present.
        env = os.environ.copy()
        env.update(environment or {})

        # create the process
        cmdline = "%s %s" % (command, string.join(args[1:], ' '))
        self.hProcess, hThread, dwPid, dwTid = win32process.CreateProcess(None, cmdline, None, None, 1, 0, env, path, StartupInfo)

        # close handles which only the child will use
        win32file.CloseHandle(hStderrW)
        win32file.CloseHandle(hStdoutW)
        win32file.CloseHandle(hStdinR)

        self.outQueue = Queue()
        self.closed = 0
        self.closedNotifies = 0

        # notify protocol
        self.protocol.makeConnection(self)

        self.reactor.addEvent(self.hProcess, self, 'inConnectionLost')
        threading.Thread(target=self.doWrite).start()
        threading.Thread(target=self.doReadOut).start()
        threading.Thread(target=self.doReadErr).start()

    def signalProcess(self, signalID):
        if signalID in ("INT", "TERM", "KILL"):
            win32process.TerminateProcess(self.hProcess, 1)

    def write(self, data):
        """Write data to the process' stdin."""
        self.outQueue.put(data)

    def closeStdin(self):
        """Close the process' stdin."""
        self.outQueue.put(None)

    def closeStderr(self):
        if hasattr(self, "hStderrR"):
            win32file.CloseHandle(self.hStderrR)
            del self.hStderrR

    def closeStdout(self):
        if hasattr(self, "hStdoutR"):
            win32file.CloseHandle(self.hStdoutR)
            del self.hStdoutR

    def loseConnection(self):
        """Close the process' stdout, in and err."""
        self.closeStdin()
        self.closeStdout()
        self.closeStderr()

    def outConnectionLost(self):
        self.closeStdout() # in case process closed it, not us
        self.protocol.outConnectionLost()
        self.connectionLostNotify()

    def errConnectionLost(self):
        self.closeStderr() # in case processed closed it
        self.protocol.errConnectionLost()
        self.connectionLostNotify()

    def _closeStdin(self):
        if hasattr(self, "hStdinW"):
            win32file.CloseHandle(self.hStdinW)
            del self.hStdinW
            self.outQueue.put(None)

    def inConnectionLost(self):
        self._closeStdin()
        self.protocol.inConnectionLost()
        self.connectionLostNotify()

    def connectionLostNotify(self):
        """Will be called 3 times, by stdout/err threads and process handle."""
        self.closedNotifies = self.closedNotifies + 1
        if self.closedNotifies == 3:
            self.closed = 1
            self.connectionLost()

    def connectionLost(self, reason=None):
        """Shut down resources."""
        exitCode = win32process.GetExitCodeProcess(self.hProcess)
        self.reactor.removeEvent(self.hProcess)
        abstract.FileDescriptor.connectionLost(self, reason)
        if exitCode == 0:
            err = error.ProcessDone(exitCode)
        else:
            err = error.ProcessTerminated(exitCode)
        self.protocol.processEnded(failure.Failure(err))

    def doWrite(self):
        """Runs in thread."""
        while 1:
            data = self.outQueue.get()
            if data == None:
                break
            try:
                win32file.WriteFile(self.hStdinW, data, None)
            except win32api.error:
                break

        self._closeStdin()

    def doReadOut(self):
        """Runs in thread."""
        while 1:
            try:
                finished = 0
                buffer, bytesToRead, result = win32pipe.PeekNamedPipe(self.hStdoutR, 1)
                finished = (result == -1) and not bytesToRead
                if bytesToRead == 0 and result != -1:
                    bytesToRead = 1
                hr, data = win32file.ReadFile(self.hStdoutR, bytesToRead, None)
            except win32api.error:
                finished = 1
            else:
                self.reactor.callFromThread(self.protocol.outReceived, data)

            if finished:
                self.reactor.callFromThread(self.outConnectionLost)
                return

    def doReadErr(self):
        """Runs in thread."""
        while 1:
            try:
                finished = 0
                buffer, bytesToRead, result = win32pipe.PeekNamedPipe(self.hStderrR, 1)
                finished = (result == -1) and not bytesToRead
                if bytesToRead == 0 and result != -1:
                    bytesToRead = 1
                hr, data = win32file.ReadFile(self.hStderrR, bytesToRead, None)
            except win32api.error:
                finished = 1
            else:
                self.reactor.callFromThread(self.protocol.errReceived, data)

            if finished:
                self.reactor.callFromThread(self.errConnectionLost)
                return



__all__ = ["Win32Reactor", "install"]
