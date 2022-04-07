
# System imports
import select, sys

import libevent

from zope.interface import implements

from twisted.internet import posixbase, main, error
from twisted.python import log
from twisted.internet.interfaces import IReactorFDSet

# globals
reads = {}
writes = {}
selectables = {}

class LibEventReactor(posixbase.PosixReactorBase):
    """A reactor that uses libevent."""
    implements(IReactorFDSet)

    def _add(self, xer, flags, mdict):
        """Create the event for reader/writer.
        """
        fd = xer.fileno()
        if fd not in mdict:
            event = libevent.createEvent(fd, flags, self._doReadOrWrite)
            mdict[fd] = event
            event.addToLoop()
            selectables[fd] = xer

    def addReader(self, reader):
        """Add a FileDescriptor for notification of data available to read.
        """
        self._add(reader, libevent.EV_READ|libevent.EV_PERSIST, reads)

    def addWriter(self, writer, writes=writes, selectables=selectables):
        """Add a FileDescriptor for notification of data available to write.
        """
        self._add(writer, libevent.EV_WRITE|libevent.EV_PERSIST, writes)

    def _remove(self, selectable, mdict, other):
        """Remove an event if found.
        """
        fd = selectable.fileno()
        if fd == -1:
            for fd, fdes in selectables.items():
                if selectable is fdes:
                    break
            else:
                return
        if fd in mdict:
            event = mdict.pop(fd)
            try:
                event.removeFromLoop()
            except:
                pass
            if fd not in other:
                del selectables[fd]
    
    def removeReader(self, reader, reads=reads, writes=writes):
        """Remove a Selectable for notification of data available to read.
        """
        return self._remove(reader, reads, writes)

    def removeWriter(self, writer, writes=writes, reads=reads):
        """Remove a Selectable for notification of data available to write.
        """
        return self._remove(writer, writes, reads)

    def removeAll(self, reads=reads, writes=writes, selectables=selectables):
        """Remove all selectables, and return a list of them."""
        if self.waker is not None:
            self.removeReader(self.waker)
        result = selectables.values()
        events = reads.copy()
        events.update(writes)

        reads.clear()
        writes.clear()
        selectables.clear()

        for event in events.values():
            event.removeFromLoop()
        if self.waker is not None:
            self.addReader(self.waker)
        return result

    def _doReadOrWrite(self, fd, events, eventObj, selectables=selectables):
        try:
            selectable = selectables[fd]
        except KeyError:
            return
        why = None
        inRead = False
        try:
            if events & libevent.EV_READ:
                why = selectable.doRead()
                inRead = True
            if not why and events & libevent.EV_WRITE:
                why = selectable.doWrite()
                inRead = False
            if selectable.fileno() != fd:
                why = error.ConnectionFdescWentAway('Filedescriptor went away')
                inRead = False
        except:
            log.err()
            why = sys.exc_info()[1]
        if why:
            self._disconnectSelectable(selectable, why, inRead)

    def doIteration(self, timeout):
        libevent.loop(libevent.EVLOOP_NONBLOCK | libevent.EVLOOP_ONCE)

def install():
    """Install the libevent reactor."""
    p = LibEventReactor()
    main.installReactor(p)

__all__ = ["LibEventReactor", "install"]

