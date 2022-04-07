from twisted.internet.serialport import SerialPort
from twisted.internet.protocol import BaseProtocol

def go(port, reac):
    _ = SerialPort(BaseProtocol(), port, reac)
    
if __name__ == "__main__":

    import sys
    port = sys.argv[1]
    
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    from twisted.internet import reactor
    
    reactor.callWhenRunning(go, port, reactor)
    reactor.run()
