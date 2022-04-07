#!/usr/bin/env python
# Knoppix identification client. Will ask for on 224.0.0.1:9120
# a report from every client listening, and will print each response.
from twisted.internet.protocol import DatagramProtocol, ConnectedDatagramProtocol
from twisted.internet import reactor

class Request(ConnectedDatagramProtocol):
    def datagramReceived(self, data):
        print 'Response Recieved:', data

class Echo(DatagramProtocol):
    def datagramReceived(self, data, host):
        print 'Packet Recieved:', data.strip()
        print 'From Host:', host
        self.transport.write(data, host)

r = Request()
reactor.connectUDP('224.0.0.1', 9122, r)
reactor.listenUDP(9122, Echo())
r.transport.write('broadcast\n')
reactor.run()

