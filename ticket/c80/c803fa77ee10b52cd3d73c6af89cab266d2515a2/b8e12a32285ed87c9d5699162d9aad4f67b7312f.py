import socket

from zope.interface import implements
from twisted.internet import base, interfaces, defer, address
from twisted.python import reflect, log

from twisted.python.runtime import platformType
if platformType == 'win32':
    from errno import WSAEWOULDBLOCK as EWOULDBLOCK
    from errno import WSAEINTR as EINTR
    from errno import WSAEMSGSIZE as EMSGSIZE
    from errno import WSAECONNREFUSED as ECONNREFUSED
    from errno import WSAECONNRESET
    EAGAIN=EWOULDBLOCK
else:
    from errno import EWOULDBLOCK, EINTR, EMSGSIZE, ECONNREFUSED, EAGAIN

class BufferFull(Exception): pass
    
def listenUDP(port, protocol, interface='', maxPacketSize=8192, reactor=None):
    """Connects a given L{DatagramProtocol} to the given numeric UDP port.

    @returns: object conforming to L{IListeningPort}.
    """
    if reactor is None:
        from twisted.internet import reactor
    p = Port(port, protocol, interface, maxPacketSize, reactor)
    p.startListening()
    return p

class Port(base.BasePort):
    """UDP port, listening for packets."""

    implements(interfaces.IUDPTransport, interfaces.ISystemHandle)

    addressFamily = socket.AF_INET
    socketType = socket.SOCK_DGRAM
    maxThroughput = 256 * 1024 # max bytes we read in one eventloop iteration

    # Actual port number being listened on, only set to a non-None
    # value when we are actually listening.
    _realPortNumber = None

    def __init__(self, port, proto, interface='', maxPacketSize=8192, reactor=None):
        """Initialize with a numeric port to listen on.
        """
        base.BasePort.__init__(self, reactor)
        self.port = port
        self.protocol = proto
        self.maxPacketSize = maxPacketSize
        self.interface = interface
        self.setLogStr()
        self._connectedAddr = None

    def __repr__(self):
        if self._realPortNumber is not None:
            return "<%s on %s>" % (self.protocol.__class__, self._realPortNumber)
        else:
            return "<%s not connected>" % (self.protocol.__class__,)

    def getHandle(self):
        """Return a socket object."""
        return self.socket

    def startListening(self):
        """Create and bind my socket, and begin listening on it.

        This is called on unserialization, and must be called after creating a
        server to begin listening on the specified port.
        """
        self._bindSocket()
        self._connectToProtocol()

    def _bindSocket(self):
        try:
            skt = self.createInternetSocket()
            skt.bind((self.interface, self.port))
            skt.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        except socket.error, le:
            raise error.CannotListenError, (self.interface, self.port, le)

        # Make sure that if we listened on port 0, we update that to
        # reflect what the OS actually assigned us.
        self._realPortNumber = skt.getsockname()[1]

        log.msg("%s starting on %s"%(self.protocol.__class__, self._realPortNumber))

        self.connected = 1
        self.socket = skt
        self.fileno = self.socket.fileno

    def _connectToProtocol(self):
        self.protocol.makeConnection(self)
        self.startReading()
        self.startWriting()

    # Inherit registerProducer/unregisterProducer/stopConsuming from
    # abstract.py (It doesn't do anything with its buffers)

    def doWrite(self):
        """Called when my socket is ready for writing."""
        self.stopWriting()
        if self.producer is not None:
            self.producer.resumeProducing()
            if self.streamingProducer:
                self.producer.pauseProducing()

    def doRead(self):
        """Called when my socket is ready for reading."""
        read = 0
        while read < self.maxThroughput:
            try:
                data, addr = self.socket.recvfrom(self.maxPacketSize)
            except socket.error, se:
                no = se.args[0]
                if no in (EAGAIN, EINTR, EWOULDBLOCK):
                    return
                if (no == ECONNREFUSED) or (platformType == "win32" and no == WSAECONNRESET):
                    if self._connectedAddr:
                        self.protocol.connectionRefused()
                else:
                    raise
            else:
                read += len(data)
                try:
                    self.protocol.datagramReceived(data, addr)
                except:
                    log.err()


    def _write(self, writer, *args):
        self.startWriting()
        try:
            return writer(*args)
        except socket.error, se:
            no = se.args[0]
            if no == EINTR:
                return self.write(datagram)
            elif no == EMSGSIZE:
                raise error.MessageLengthError, "message too long"
            elif no == ECONNREFUSED:
                self.protocol.connectionRefused()
            elif no == EAGAIN:
                raise BufferFull()
            else:
                raise
                    
    def write(self, datagram, addr=None):
        """Write a datagram.

        @param addr: should be a tuple (ip, port), can be None in connected mode.
        """
        if self._connectedAddr:
            assert addr in (None, self._connectedAddr)
            self._write(self.socket.send, datagram)
        else:
            assert addr != None
            if not addr[0].replace(".", "").isdigit():
                warnings.warn("Please only pass IPs to write(), not hostnames", DeprecationWarning, stacklevel=2)
            self._write(self.socket.sendto, datagram, addr)

    def writeSequence(self, seq, addr):
        self.write("".join(seq), addr)

    def connect(self, host, port):
        """'Connect' to remote server."""
        if self._connectedAddr:
            raise RuntimeError, "already connected, reconnecting is not currently supported (talk to itamar if you want this)"
        if not abstract.isIPAddress(host):
            raise ValueError, "please pass only IP addresses, not domain names"
        self._connectedAddr = (host, port)
        self.socket.connect((host, port))

    def _loseConnection(self):
        self.stopReading()
        if self.connected: # actually means if we are *listening*
            from twisted.internet import reactor
            reactor.callLater(0, self.connectionLost)

    def stopListening(self):
        if self.connected:
            result = self.d = defer.Deferred()
        else:
            result = None
        self._loseConnection()
        return result

    def loseConnection(self):
        warnings.warn("Please use stopListening() to disconnect port", DeprecationWarning, stacklevel=2)
        self.stopListening()

    def connectionLost(self, reason=None):
        """Cleans up my socket.
        """
        log.msg('(Port %s Closed)' % self._realPortNumber)
        self._realPortNumber = None
        base.BasePort.connectionLost(self, reason)
        if hasattr(self, "protocol"):
            # we won't have attribute in ConnectedPort, in cases
            # where there was an error in connection process
            self.protocol.doStop()
        self.connected = 0
        self.socket.close()
        del self.socket
        del self.fileno
        if hasattr(self, "d"):
            self.d.callback(None)
            del self.d

    def setLogStr(self):
        self.logstr = reflect.qual(self.protocol.__class__) + " (UDP)"

    def logPrefix(self):
        """Returns the name of my class, to prefix log entries with.
        """
        return self.logstr

    def getHost(self):
        """
        Returns an IPv4Address.

        This indicates the address from which I am connecting.
        """
        return address.IPv4Address('UDP', *(self.socket.getsockname() + ('INET_UDP',)))
