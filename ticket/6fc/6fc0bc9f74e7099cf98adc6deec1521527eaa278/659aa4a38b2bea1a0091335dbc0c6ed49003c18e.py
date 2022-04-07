
"""
This is a spike.  Don't check it in.  IT should be used as a reference for
what the API might look like, but it is _NOT_ to be used as a basis for the
implementation; it is wrong in a variety of colorful way, and it has no tests
whatsoever.
"""

from twisted.internet.defer import setDebugging
setDebugging(True)

from cStringIO import StringIO

from zope.interface import implements

from twisted.protocols.amp import AMP, Argument, Integer, String, Command

from twisted.protocols.basic import FileSender

from twisted.internet.interfaces import IPushProducer, IFinishableConsumer

from twisted.internet.defer import Deferred

from twisted.internet.protocol import ClientFactory, Factory

from twisted.internet import reactor

from tempfile import TemporaryFile


class Chunk(Command):
    """
    This command delivers a single chunk.
    """
    requiresAnswer = False
    arguments = [('producerID', Integer()),
                 ('data', String())]


class Pause(Command):
    """
    This command pauses a stream.
    """
    requiresAnswer = False
    arguments = [('producerID', Integer())]


class Resume(Command):
    """
    This command resumes a paused stream.
    """
    requiresAnswer = False
    arguments = [('producerID', Integer())]


class End(Command):
    """
    This command indicates the end of a stream.
    """
    requiresAnswer = False
    arguments = [('producerID', Integer())]


class Upload(Argument):
    """
    This command initiates a stream.
    """
    def fromStringProto(self, inString, proto):
        """
        Convert from a string to a Python value.
        """
        # inString should be an int, used for identifying the remote stream.
        return proto.createRemoteProducer(int(inString))


    def toStringProto(self, inObject, proto):
        """
        OK, we've got an object here that the user created.  What is it?  it's
        like, a producer ... with a hookup method?  What do I need to do here?
        I need to make sure that the producer here is connected to
        something... here...
        """
        outgoing = proto.createProducingStream(inObject)
        # a producing stream is on the producing side of the wire, but its role
        # is actually to provide a place for the provided IAMPProducer
        # implementor to deposit its data such that it will get delivered.
        return str(outgoing.producerID)



MAX_INIT_BUF_SZ = 64 * 1024 * 4


class FileConsumer:
    """
    an IFinishableConsumer that writes to a file.
    """
    implements(IFinishableConsumer)
    def __init__(self, fobj):
        """
        create an fpm with a file object
        """
        self.file = fobj
        self.deferred = Deferred()


    def write(self, data):
        """
        got some data from the stream.
        """
        self.file.write(data)


    def finish(self):
        """
        the stream is done.
        """
        self.file.seek(0) # convenient for some stuff, but is this actually good?
        self.transport = None
        self.deferred.callback(self.file)


    def registerProducer(self, producer, streaming):
        """
        I don't care!  I'm just gonna block!
        """


    def unregisterProducer(self):
        """
        Seems pretty unlikely, buddy.
        """




class RemoteProducer(object):
    """
    This is a representation on the receiving end of a remote producer.
    """
    implements(IPushProducer)

    def __init__(self, ampinst, producerID):
        """
        Create a producer with an AMP instance and a proto ID.
        """
        self.amp = ampinst
        self.producerID = producerID
        self.buf = ''
        self.consumer = None
        self.paused = False


    def connectConsumer(self, consumer):
        """
        hook an IFinishableConsumer up to this so it will receive data
        notifications et. al.

        this is the critical method that makes a thing an IAMPProducer rather
        than just a regular producer.
        """
        print 'CONNECTING RECEIVING CONSUMER!'
        self.consumer = consumer
        consumer.registerProducer(self, True)
        if self.buf:
            consumer.write(self.buf)
            self.buf = ''


    def pauseProducing(self):
        """
        Pause me.
        """
        if not self.paused:
            self.amp.callRemote(Pause, producerID=self.producerID)
            self.paused = True


    def resumeProducing(self):
        """
        Resume me (after pausing me).
        """
        if self.paused:
            self.amp.callRemote(Resume, producerID=self.producerID)
            self.paused = False


    def chunkReceived(self, data):
        """
        Called internally below to deliver data.
        """
        if self.consumer is not None:
            self.consumer.write(data)
        else:
            self.buf += data
            if len(self.buf) > MAX_INIT_BUF_SZ:
                self.pauseProducing()


    def endReceived(self):
        """
        A bloo bloo bloo bloo
        """
        if self.consumer is not None:
            self.consumer.finish()


    ######################## UTILITY CRAP

    def asFile(self, fileobj):
        """
        return a deferred which will fire with the given file when the file is
        written.
        """
        fpm = FileConsumer(fileobj)
        self.connectConsumer(fpm)
        return fpm.deferred


    def asTemporaryFile(self):
        """
        return a deferred which will fire with a temporary file object with the
        contents of the stream when the stream is done.
        """
        return self.asFile(TemporaryFile())


    def asString(self):
        """
        return a deferred which will fire with the string contents of stuff
        """
        return self.asFile(StringIO()).addCallback(lambda io: io.read())

    ######################## OK UTILITIES DONE


class RemoteConsumer:
    """
    A consumer which will take data from a local stream and
    """
    implements(IFinishableConsumer)
    producer = None

    def __init__(self, proto, producerID, ampproducer):
        """
        create a sending stream with something that implements IAMPProducer,
        meaning, connectConsumer.
        """
        self.amp = proto
        self.producerID = producerID
        ampproducer.connectConsumer(self)
        # This is kind of a gross dependency, but I am pretty sure this is the
        # way it's supposed to work all the time?
        self.amp.sendMap[self.producerID] = self
        if self.producer is not ampproducer:
            raise RuntimeError("producer doesn't match amp producer")


    def registerProducer(self, producer, streaming):
        """
        Hmm.  producer should be the same as self.producer?
        """
        print 'REGPROD'
        self.producer = producer
        self.streaming = streaming
        print 'RP'
        # Registering a producer is tricky, what's our state, whats its? - THIS
        # is the one that's really broken (other one doesn't need a calllater)
        reactor.callLater(0, producer.resumeProducing)
        print "RPD"


    def unregisterProducer(self):
        """
        who cares, I think
        """
        print 'UNREGd'
        self.producer = None
        self.streaming = None


    def pauseIt(self):
        """
        blah blah
        """
        self.producer.pauseProducing()


    def resumeIt(self):
        """
        etc
        """
        self.producer.resumeProducing()


    def write(self, data):
        """
        Okay time to put it on the wire.
        """
        self.amp.callRemote(Chunk, data=data, producerID=self.producerID)


    def finish(self):
        """
        self.amp.callRemote()
        """
        self.amp.producerDone(self.producerID)


import itertools
nexter = itertools.count().next

class StreamingAMP(AMP):
    """
    This is an AMP protocol expanded with streaming features.
    """

    producing = False

    def ampBoxReceived(self, box):
        """
        blah
        """
        print 'BOX', box

        return super(StreamingAMP, self).ampBoxReceived(box)

    def resumeProducing(self):
        """
        Resume producing all active producers.
        """
        # if you are here, and you try to resume producing right away, you're
        # still in the middle of serializing an argument to be sent out, so it
        # goes out before establishing the packet that makes the mapping to
        # where it should go.  hold off for a moment here (hackishly) and rip
        # the stack so that we can resume producing later.
        print 'hmm weird'
        reactor.callLater(0, self._reallyResumeProducing)

    def _reallyResumeProducing(self):
        """
        actually do it, once the stack is ripped
        """
        print 'REALLY RESUMING DUFUS'

        for producer in self.activeSendProducers:
            producer.resumeIt()


    def pauseProducing(self):
        """
        Pause producing all active producers.
        """
        for producer in self.activeSendProducers:
            producer.resumeIt()


    def createRemoteProducer(self, newID):
        """
        Create a stream which will receive data locally.
        """
        print 'CRS', newID
        prp = RemoteProducer(self, newID)
        self.receiveMap[newID] = prp
        return prp


    def createProducingStream(self, producer):
        """
        Create a stream which will mumble something
        """
        producerID = nexter()
        ss = RemoteConsumer(self, producerID, producer)
        print 'CREATING PRODUCING', ss, self.sendMap
        print 'SM', self.sendMap
        wlasp = len(self.activeSendProducers)
        self.activeSendProducers.append(ss) # ???
        if wlasp == 0:
            print 'REGISTERING MYSELF!!!'
            self.transport.registerProducer(self, False)
        return ss


    def producerDone(self, producerID):
        """
        a local producer finished, tell the other end and clean up
        """
        self.callRemote(End, producerID=producerID)
        it = self.sendMap.pop(producerID)
        self.activeSendProducers.remove(it) # ???
        if len(self.activeSendProducers) == 0:
            self.transport.unregisterProducer()


    def connectionMade(self):
        """
        The connection was made.  Set up stream tables.
        """
        super(StreamingAMP, self).connectionMade()
        self.receiveMap = {}
        self.sendMap = {}
        self.activeSendProducers = []


    def streamChunk(self, producerID, data):
        """
        A chunk of data was received for a particular stream.
        """
        print 'CHUNK', repr(producerID), repr(data)
        self.receiveMap[producerID].chunkReceived(data)
        return {}

    Chunk.responder(streamChunk)


    def streamEnd(self, producerID):
        """
        A stream has ended.
        """
        self.receiveMap.pop(producerID).endReceived()
        return {}

    End.responder(streamEnd)


    def streamPause(self, producerID):
        """
        The other end received too much data and now wants us to pause.
        """
        sendstream = self.sendMap[producerID]
        self.activeSendProducers.remove(sendstream)
        sendstream.pauseIt()
        return {}

    Pause.responder(streamPause)


    def streamResume(self, producerID):
        """
        The other end has some free space and now wants us to start sending that
        stream again.
        """
        sendstream = self.sendMap[producerID]
        sendstream.resumeIt()
        self.activeSendProducers.append(sendstream)
        return {}

    Resume.responder(streamResume)




class ActualFileSender(FileSender):
    """
    filesender plus a method to make it an IAMPProducer
    """
    CHUNK_SIZE = 100

    def __init__(self, fileToSend, amp):
        """
        create with a fileobj to send.
        """
        self.fileToSend = fileToSend
        self.amp = amp


    def connectConsumer(self, consumer):
        """
        connected consumer
        """
        print 'Starting over here...'
        def finishHim(result):
            print 'Done over here...'
            consumer.finish()
            print 'Really.'
            self.amp.die()
#             self.amp.transport.unregisterProducer()
        self.beginFileTransfer(
            self.fileToSend, consumer).addCallback(finishHim)




class Shove(Command):
    arguments = [('stuff', Upload()),
                 ('name', String()),
                 ('size', Integer())]

class Shover(StreamingAMP):
    """
    file sender
    """
    def connectionMade(self):
        """
        made a connection, start shoving.
        """
        print 'PUSHING'
        super(Shover, self).connectionMade()
        f = self.factory.file
        f.seek(0, 2)
        sz = f.tell()
        f.seek(0)
        def didit(result):
            self.die()
            print '************************* done calling shove', result
        self.callRemote(Shove,
                        stuff=ActualFileSender(f, self),
                        name=self.factory.filename,
                        size=sz).addCallback(didit)

    dead = 0
    def die(self):
        """
        die after the whole program is finished
        """
        print 'DIE*******', self.dead
        if self.dead:
            self.transport.loseConnection()
        else:
            self.dead += 1


    def connectionLost(self, reason):
        """
        lost the connection, time to die
        """
        print 'CL LOLOOL!'
        super(Shover, self).connectionLost(reason)
        reactor.stop()


class Pusher(StreamingAMP):
    """
    file receiver
    """
    def shove(self, stuff, name, size):
        """
        shove it
        """
        fn = name + ".GOTIT"
        print 'SHOVING', fn
        f = file(fn, 'wb')
        print 'SHOVED'
        def checksize(result):
            print 'CHECKIN DA SIZE'
            result.seek(0, 2)
            print 'expected', size, 'got', result.tell()
            print 'DONE'
        stuff.asFile(f).addCallback(checksize)
        return {}

    Shove.responder(shove)


import sys

def client():
    """
    client file host port: send the file to the host&port combo
    """
    cf = ClientFactory()
    cf.file = file(sys.argv[2])
    cf.protocol = Shover
    cf.filename = sys.argv[2]
    reactor.connectTCP(sys.argv[3], int(sys.argv[4]), cf)

def server():
    """
    make a server
    """
    pf = Factory()
    pf.protocol = Pusher
    reactor.listenTCP(int(sys.argv[2]), pf)


if sys.argv[1] == 'client':
    client()
elif sys.argv[1] == 'server':
    server()
else:
    print 'oops'
    sys.exit()

reactor.run()



