# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from __future__ import division

from twisted.internet import protocol
from twisted.application import internet, service

from twisted.conch.insults import insults
from twisted.conch.telnet import TelnetTransport, TelnetBootstrapProtocol

from twisted.conch.insults.text import attributes as A, assembleFormattedText



class AssembleTextDemo(insults.TerminalProtocol):
    width = 80
    height = 24


    def connectionMade(self):
        self.terminal.eraseDisplay()
        self.terminal.resetPrivateModes([insults.privateModes.CURSOR_MODE])


    def keystrokeReceived(self, keyID, modifier):
        self.terminal.reset()
        if keyID == b"q":
            self.terminal.loseConnection()
        elif keyID == b"s":
            formatted = A.fg.red["test"]
            self.terminal.write(assembleFormattedText(formatted))
        elif keyID == b"b":
            formatted = A.fg.red[b"test"]
            self.terminal.write(assembleFormattedText(formatted))



def makeService():
    f = protocol.ServerFactory()
    f.protocol = lambda: TelnetTransport(TelnetBootstrapProtocol,
                                         insults.ServerProtocol,
                                         AssembleTextDemo)
    return internet.TCPServer(6023, f)



application = service.Application("Assemble Text Demo")
makeService().setServiceParent(application)
