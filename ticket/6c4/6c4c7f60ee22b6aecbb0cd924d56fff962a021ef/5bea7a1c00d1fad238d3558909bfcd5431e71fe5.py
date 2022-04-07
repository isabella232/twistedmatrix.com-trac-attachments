'''
@author: shylent
'''
from fifo import readFromFIFO, writeToFIFO
from tempfile import mkdtemp
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.task import deferLater
from twisted.python import log
from twisted.python.filepath import FilePath
from twisted.test.proto_helpers import AccumulatingProtocol
from twisted.trial import unittest
import errno
import os


class CatProtocol(ProcessProtocol):

    def __init__(self):
        self.receivedDeferred = None
        self.procEnded = None

    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        self.connMade.callback(self)

    def outReceived(self, data):
        if self.receivedDeferred is not None:
            d, self.receivedDeferred = self.receivedDeferred, None
            d.callback(data)

    def errReceived(self, data):
        log.msg("stderr data: %s" % data)

    def waitForData(self):
        self.receivedDeferred = Deferred()
        return self.receivedDeferred

    def processEnded(self, reason):
        if self.procEnded is not None:
            self.procEnded.callback(None)


class NotifyingAccumulator(AccumulatingProtocol):

    receivedDeferred = None

    def dataReceived(self, data):
        AccumulatingProtocol.dataReceived(self, data)
        if self.receivedDeferred is not None:
            d, self.receivedDeferred = self.receivedDeferred, None
            d.callback(data)

    def waitForData(self):
        self.receivedDeferred = Deferred()
        return self.receivedDeferred


class TestReader(unittest.TestCase):

    def setUp(self):
        self.tempdir = FilePath(mkdtemp())
        self.fifo_path = self.tempdir.child('test.pipe')
        os.mkfifo(self.fifo_path.path)
        cat_text = \
r"""import sys

f = open(sys.argv[1], 'w')
while True:
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    f.write(line)
    f.flush()

"""
        fd = self.tempdir.child('cat.py').open('w')
        fd.write(cat_text)
        fd.close()

    def test_start_reading_no_writer(self):
        """Starting a read with no writer present"""
        proto = AccumulatingProtocol()
        readFromFIFO(self.fifo_path, proto)
        fifo = proto.transport
        self.assert_(proto.made, "Opening the FIFO with O_NONBLOCK must always succeed")
        self.addCleanup(fifo.loseConnection)

    @inlineCallbacks
    def test_read(self):
        proto = NotifyingAccumulator()
        proto.closedDeferred = Deferred()

        readFromFIFO(self.fifo_path, proto)

        cat_proto = CatProtocol()
        cat_proto.connMade = Deferred()

        reactor.spawnProcess(cat_proto, 'python', ['python', self.tempdir.child('cat.py').path, self.fifo_path.path],
                             env=os.environ)
        yield cat_proto.connMade

        cat_proto.transport.write("Line1\n")
        yield proto.waitForData()

        self.assertEqual(proto.data, "Line1\n")

        proto.transport.startReading() # This should do nothing at all

        cat_proto.transport.write("Line2\n")
        yield proto.waitForData()

        self.assertEqual(proto.data, "Line1\nLine2\n")

        cat_proto.transport.loseConnection()

        yield proto.closedDeferred
        yield deferLater(reactor, 0, lambda: None)
        try:
            os.fstat(proto.transport._fd)
        except OSError, e:
            self.assertEqual(e.errno, errno.EBADF)
        else:
            self.fail("The descriptor must be closed by now")

    @inlineCallbacks
    def test_write(self):
        proto = NotifyingAccumulator()
        proto.closedDeferred = Deferred()

        readFromFIFO(self.fifo_path, proto)

        cat_proto = CatProtocol()
        cat_proto.connMade = Deferred()

        reactor.spawnProcess(cat_proto, 'python', ['python', self.tempdir.child('cat.py').path, self.fifo_path.path],
                             env=os.environ)
        yield cat_proto.connMade

        self.addCleanup(cat_proto.transport.loseConnection)

        self.assertRaises(NotImplementedError, proto.transport.startWriting)

        proto.receivedDeferred = Deferred()
        cat_proto.transport.write("Line1\n")
        yield proto.waitForData()

        self.assertEqual(proto.data, "Line1\n")

        proto.transport.loseConnection()

        yield proto.closedDeferred
        yield deferLater(reactor, 0, lambda: None)
        try:
            os.close(proto.transport._fd)
        except OSError, e:
            self.assertEqual(e.errno, errno.EBADF)
        else:
            self.fail("The descriptor must be closed by now")

    @inlineCallbacks
    def test_other_side_quit(self):
        proto = NotifyingAccumulator()
        proto.closedDeferred = Deferred()

        readFromFIFO(self.fifo_path, proto)

        cat_proto = CatProtocol()
        cat_proto.connMade = Deferred()

        reactor.spawnProcess(cat_proto, 'python', ['python', self.tempdir.child('cat.py').path, self.fifo_path.path],
                             env=os.environ)
        yield cat_proto.connMade

        proto.receivedDeferred = Deferred()
        cat_proto.transport.write("Line1\n")
        yield proto.waitForData()

        self.assertEqual(proto.data, "Line1\n")

        cat_proto.transport.signalProcess("KILL")

        yield proto.closedDeferred
        yield deferLater(reactor, 0, lambda: None)
        try:
            os.close(proto.transport._fd)
        except OSError, e:
            self.assertEqual(e.errno, errno.EBADF)
        else:
            self.fail("The descriptor must be closed by now")


    def tearDown(self):
        self.tempdir.remove()


class TestWriter(unittest.TestCase):

    def setUp(self):
        self.tempdir = FilePath(mkdtemp())
        self.fifo_path = self.tempdir.child('test.pipe')
        os.mkfifo(self.fifo_path.path)
        cat_text = \
r"""import sys
f = open(sys.argv[1], 'r', 1)
while True:
    line = f.readline()
    if not line:
        sys.exit(0)
    sys.stdout.write(line)
    sys.stdout.flush()
    

"""
        fd = self.tempdir.child('cat.py').open('w')
        fd.write(cat_text)
        fd.close()

    def test_start_writing_no_reader(self):
        """Starting a write with no reader present"""
        proto = AccumulatingProtocol()

        try:
            writeToFIFO(self.fifo_path, proto)
        except OSError, e:
            self.assertEqual(e.errno, errno.ENXIO)
        else:
            self.fail("Attempting to open for writing with O_NONBLOCK when no reader "
                      "is present must always result in ENXIO")

    @inlineCallbacks
    def test_write(self):
        cat_proto = CatProtocol()
        cat_proto.connMade = Deferred()
        cat_proto.procEnded = Deferred()

        reactor.spawnProcess(cat_proto, 'python', ['python', self.tempdir.child('cat.py').path, self.fifo_path.path],
                             env=os.environ)
        yield cat_proto.connMade
        yield deferLater(reactor, 0.2, lambda: None)
        proto = AccumulatingProtocol()

        writeToFIFO(self.fifo_path, proto)

        proto.transport.write("Nothing\n")
        data = yield cat_proto.waitForData()
        self.assertEqual(data, "Nothing\n")

        proto.transport.write("important\n")
        data = yield cat_proto.waitForData()
        self.assertEqual(data, "important\n")

        proto.transport.loseConnection()

        yield cat_proto.procEnded
        yield deferLater(reactor, 0, lambda: None)
        try:
            os.close(proto.transport._fd)
        except OSError, e:
            self.assertEqual(e.errno, errno.EBADF)
        else:
            self.fail("The descriptor must be closed by now")

    @inlineCallbacks
    def test_read(self):
        cat_proto = CatProtocol()
        cat_proto.connMade = Deferred()
        cat_proto.procEnded = Deferred()

        reactor.spawnProcess(cat_proto, 'python', ['python', self.tempdir.child('cat.py').path, self.fifo_path.path],
                             env=os.environ)
        yield cat_proto.connMade
        yield deferLater(reactor, 0.2, lambda: None)
        proto = AccumulatingProtocol()

        writeToFIFO(self.fifo_path, proto)

        proto.transport.write("Nothing\n")
        data = yield cat_proto.waitForData()
        self.assertEqual(data, "Nothing\n")

        self.assertRaises(NotImplementedError, proto.transport.startReading)

        proto.transport.write("important\n")
        data = yield cat_proto.waitForData()
        self.assertEqual(data, "important\n")

        proto.transport.loseConnection()

        yield cat_proto.procEnded
        yield deferLater(reactor, 0, lambda: None)
        try:
            os.close(proto.transport._fd)
        except OSError, e:
            self.assertEqual(e.errno, errno.EBADF)
        else:
            self.fail("The descriptor must be closed by now")

    def tearDown(self):
        self.tempdir.remove()
