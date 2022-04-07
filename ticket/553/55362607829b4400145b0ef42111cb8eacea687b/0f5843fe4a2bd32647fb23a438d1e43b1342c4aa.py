from zope.interface import providedBy

from twisted.test.proto_helpers import MemoryReactor
from twisted.internet.task import Clock

class Composite(object):
    """
    A helper to compose other objects based on their declared (zope.interface)
    interfaces.

    This is used here to create a reactor from separate implementations of
    different reactor interfaces - for example, from L{Clock} and
    L{ReactorFDSet} to create a reactor which provides L{IReactorTime} and
    L{IReactorFDSet}.
    """
    def __init__(self, parts):
        """
        @param parts: An iterable of the objects to compose.  The methods of
            these objects which are part of any interface the objects declare
            they provide will be made methods of C{self}.  (Non-method
            attributes are not supported.)

        @raise ValueError: If an interface is provided by more than one of the
            objects in C{parts}.
        """
        seen = set()
        for p in parts:
            for i in providedBy(p):
                if i in seen:
                    raise ValueError("More than one part provides %r" % (i,))
                seen.add(i)
                for m in i.names():
                    setattr(self, m, getattr(p, m))



reactor = Composite([Clock(), MemoryReactor()])
