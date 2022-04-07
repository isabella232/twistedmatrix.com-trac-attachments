from twisted.internet import protocol 
from twisted.protocols.basic import _PauseableMixin
 
class Int8StringReceiver(protocol.Protocol, _PauseableMixin):
    """A receiver for int8-prefixed strings.

    An int8 string is a string prefixed by 1 bytes, the 8-bit length of
    the string encoded in network byte order.

    This class publishes the same interface as NetstringReceiver.
    """

    recvd = ""

    def stringReceived(self, msg):
        """Override this.
        """
        raise NotImplementedError

    def dataReceived(self, recd):
        """Convert int8 prefixed strings into calls to stringReceived.
        """
        self.recvd = self.recvd + recd
        while len(self.recvd) > 0 and not self.paused:
            length = ord(self.recvd[0]) 
            if len(self.recvd) < length+1:
                break
            packet = self.recvd[1:length+1]
            self.recvd = self.recvd[length+1:]
            self.stringReceived(packet)

    def sendString(self, data):
        """Send an int8-prefixed string to the other end of the connection.
        """
        assert len(data) < 256, "message too long"
        self.transport.write(struct.pack("!h",len(data)) + data)

