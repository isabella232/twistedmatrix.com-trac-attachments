"""Create a bi-pane display with stdin, stdout and stderr shown in
different colours in the top pane and a composition buffer shown in
the bottom.
"""

from twisted.internet import protocol, process
from twisted.application import service, internet
from twisted.conch.insults import insults
from twisted.conch import telnet


class MyProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, terminal_protocol):
        self.tp = terminal_protocol

    def connectionMade(self):
        self.tp.terminal.write("Connection made.\n")
    def outReceived(self, data):
        self.tp.terminal.write("Out: %r\n"%data)
    def errReceived(self, data):
        self.tp.terminal.write("Err: %r\n"%data)
    def write(self, data):
        self.tp.terminal.write("In: %r %r\n" % (keyID, modifier))
        super(MyProcessProtocol, self).write(data)


class MyTerminalProtocol(insults.TerminalProtocol):
    width = 80
    height = 24
    
    def connectionMade(self):
        from twisted.internet import reactor
        #self.terminalSize(self.width, self.height)
        self.process = reactor.spawnProcess(MyProcessProtocol(self),
                                            "/bin/sh",
                                            ("/bin/sh",))
        
    def keystrokeReceived(self, keyID, modifier):
        self.process.write(keyID)


application = service.Application('insults_prototype')
factory = protocol.ServerFactory()
factory.protocol = lambda: telnet.TelnetTransport(
    telnet.TelnetBootstrapProtocol,
    insults.ServerProtocol,
    MyTerminalProtocol)
internet.TCPServer(1977, factory).setServiceParent(application)
