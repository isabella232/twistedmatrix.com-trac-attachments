from zope.interface import implementer

from twisted.test.proto_helpers import MemoryReactor
from twisted.internet.task import Clock
from twisted.internet.base import _ThreePhaseEvent
from twisted.internet.interfaces import IReactorCore

@implementer(IReactorCore)
class MemoryCoreReactor(MemoryReactor, Clock):
    """
    Fake reactor with listenTCP, IReactorTime and just enough of an
    implementation of IReactorCore.
    """
    def __init__(self):
        MemoryReactor.__init__(self)
        Clock.__init__(self)
        self._triggers = {}

    def addSystemEventTrigger(self, phase, eventType, f, *args, **kw):
        event = self._triggers.setdefault(eventType, _ThreePhaseEvent())
        return eventType, event.addTrigger(phase, f, *args, **kw)

    def removeSystemEventTrigger(self, triggerID):
        eventType, handle = triggerID
        event = self._triggers.setdefault(eventType, _ThreePhaseEvent())
        event.removeTrigger(handle)

    def fireSystemEvent(self, eventType):
        event = self._triggers.get(eventType)
        if event is not None:
            event.fireEvent()

