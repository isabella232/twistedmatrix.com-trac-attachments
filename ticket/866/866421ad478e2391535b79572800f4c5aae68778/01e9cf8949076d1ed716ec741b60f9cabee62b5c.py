# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An epoll() based implementation of the twisted main loop.

To install the event loop (and you should do this before any connections,
listeners or connectors are added)::

    from twisted.internet import epollreactor
    epollreactor.install()

API Stability: stable

Maintainer: U{Jp Calderone <mailto:exarkun@twistedmatrix.com>}
"""

# System imports
import select, sys

# Twisted imports
from twisted.python import epoll
from twisted.python import log, threadable
from twisted.internet import main, posixbase, error

# globals
reads = {}
writes = {}
selectables = {}
poller = epoll.create(1024)

class EPollReactor(posixbase.PosixReactorBase):
    """
    A reactor that uses epoll(4).
    """

    def _add(self, xer, primary, other, selectables, dir, antidir):
        """
        Private method for adding a descriptor from the event loop.
        
        It takes care of adding it if  new or modifying it if already added
        for another state (read -> read/write for example).
        """
        fd = xer.fileno()
        if fd not in primary:
            cmd = epoll.CTL_ADD
            flags = dir
            if fd in other:
                flags |= antidir
                cmd = epoll.CTL_MOD
            primary[fd] = 1
            selectables[fd] = xer
            epoll.control(poller, cmd, fd, flags)

    def addReader(self, reader, reads=reads, writes=writes, selectables=selectables):
        """
        Add a FileDescriptor for notification of data available to read.
        """
        self._add(reader, reads, writes, selectables, epoll.IN, epoll.OUT)

    def addWriter(self, writer, writes=writes, reads=reads, selectables=selectables):
        """
        Add a FileDescriptor for notification of data available to write.
        """
        self._add(writer, writes, reads, selectables, epoll.OUT, epoll.IN)

    def _remove(self, xer, primary, other, selectables, dir, antidir):
        """
        Private method for removing a descriptor from the event loop.
        
        It does the inverse job of _add, and also add a check in case of the fd
        has gone away.
        """
        fd = xer.fileno()
        if fd == -1:
            for fd, fdes in selectables.items():
                if xer is fdes:
                    break
            else:
                return
        if fd in primary:
            cmd = epoll.CTL_DEL
            flags = dir
            if fd in other:
                flags = antidir
                cmd = epoll.CTL_MOD
            else:
                del selectables[fd]
            del primary[fd]
            try:
                epoll.control(poller, cmd, fd, flags)
            except:
                pass

    def removeReader(self, reader, reads=reads, writes=writes, selectables=selectables):
        """
        Remove a Selectable for notification of data available to read.
        """
        self._remove(reader, reads, writes, selectables, epoll.IN, epoll.OUT)

    def removeWriter(self, writer, writes=writes, reads=reads, selectables=selectables):
        """
        Remove a Selectable for notification of data available to write.
        """
        self._remove(writer, writes, reads, selectables, epoll.OUT, epoll.IN)

    def removeAll(self, reads=reads, writes=writes, selectables=selectables):
        """
        Remove all selectables, and return a list of them.
        """
        if self.waker is not None:
            self.removeReader(self.waker)
        result = selectables.values()
        fds = selectables.keys()
        reads.clear()
        writes.clear()
        selectables.clear()
        for fd in fds:
            epoll.control(poller, epoll.CTL_DEL, fd, 0)
        if self.waker is not None:
            self.addReader(self.waker)
        return result

    def disconnectAll(self):
        """
        Remove all readers and writers, and then close the epoll fd.
        """
        try:
            return posixbase.PosixReactorBase.disconnectAll(self)
        finally:
            epoll.close(poller)

    def doPoll(self, timeout,
               reads=reads,
               writes=writes,
               selectables=selectables,
               select=select,
               log=log):
        """
        Poll the poller for new events.
        """
        if timeout is None:
            timeout = 1
        timeout = int(timeout * 1000) # convert seconds to milliseconds

        try:
            l = epoll.wait(poller, len(selectables), timeout)
        except:
            return
        _drdw = self._doReadOrWrite
        for fd, event in l:
            try:
                selectable = selectables[fd]
            except KeyError:
                pass
            else:
                log.callWithLogger(selectable, _drdw, selectable, fd, event)

    doIteration = doPoll

    def _doReadOrWrite(self, selectable, fd, event):
        """
        fd is available for read or write, make the work and raise errors
        if necessary.
        """
        why = None
        inRead = False
        if event in (epoll.HUP, epoll.ERR):
            why = main.CONNECTION_LOST
        else:
            try:
                if event & epoll.IN:
                    why = selectable.doRead()
                    inRead = True
                if not why and event & epoll.OUT:
                    why = selectable.doWrite()
                    inRead = False
                if selectable.fileno() != fd:
                    why = error.ConnectionFdescWentAway("Filedescriptor went away")
                    inRead = False
            except:
                log.err()
                why = sys.exc_info()[1]
        if why:
            self._disconnectSelectable(selectable, why, inRead)

def install():
    """
    Install the poll() reactor.
    """
    p = EPollReactor()
    main.installReactor(p)


__all__ = ["PollReactor", "install"]

