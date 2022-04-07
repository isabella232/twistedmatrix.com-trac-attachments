import logging
from twisted.python import log


class Logger(logging.Logger, log.LogPublisher):

    def __init__(self, name):
        logging.Logger.__init__(self, name)
        log.LogPublisher.__init__(self)

        self.observer = log.PythonLoggingObserver(loggerName="")
        self.addObserver(self.observer.emit)
        self.observer.logger = self

def foo(result):
    raise RuntimeError("This is not the way.")


logging.setLoggerClass(Logger)

logger = logging.getLogger("my-module")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.info("foobar")

logger.msg(logger)

from twisted.internet.defer import Deferred

d = Deferred()
d.addCallback(foo)
d.addErrback(logger.err)

d.callback("foobaz")
