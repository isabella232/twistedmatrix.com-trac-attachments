# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example demonstrating how to send UDP broadcast messages for tracking a
cluster of hosts at Layer 2.

Each host broadcasts its ID on start up and upon receiving a broadcast, a host
will unicast it's ID to the broadcaster.
Additionally, each host periodically unicasts to each of its peers.

Run using twistd. Eg

* twistd -noy doc/core/examples/udpbroadcast.py
"""

from datetime import datetime, timedelta
from uuid import uuid1, UUID

from twisted.application import internet, service
from twisted.internet.protocol import DatagramProtocol
from twisted.python import log


BROADCAST_INTERVAL = timedelta(seconds=1)
STALE_INTERVAL = BROADCAST_INTERVAL * 2
MYID = uuid1()
PORT = 8555


class Peer(object):
    def __init__(self, id, address):
        self.id = id
        self.address = address


    def __repr__(self):
        return '<%s id=%r address=%r>' % (
            self.__class__.__name__, self.id, self.address)


class PeerTrackerProtocol(DatagramProtocol):
    noisy = False

    def __init__(self, controller, myid, port):
        self.controller = controller
        self.myid = myid
        self.port = port


    def startProtocol(self):
        self.transport.setBroadcastAllowed(True)
        self.broadcast()


    def datagramReceived(self, datagram, addr):
        uuid = UUID(bytes=datagram)
        if uuid != self.myid:
            peer = Peer(id=uuid, address=addr)
            self.controller.peerReceived(peer, self)


    def broadcast(self):
        self.transport.write(self.myid.bytes, ('<broadcast>', self.port))


    def ping(self, peer):
        self.transport.write(self.myid.bytes, (peer.address[0], self.port))



class Broadcaster(object):
    def __init__(self):
        self.peers = {}


    def peerReceived(self, peer, proto):
        if peer.id not in self.peers:
            log.msg(format='NEW_PEER %(peer)r', peer=peer)
            proto.broadcast()
        self.peers[peer.id] = (datetime.utcnow(), peer)


    def removeStalePeers(self, maxage):
        now = datetime.utcnow()
        for peerID, (lastSeen, peer) in self.peers.items():
            diff = now - lastSeen
            if diff > maxage:
                del self.peers[peerID]
                log.msg(
                    format='REMOVED_PEER: %(peer)r, %(lastSeen)s',
                    peer=peer, lastSeen=lastSeen)


    def pingPeers(self, proto):
        for lastSeen, peer in self.peers.values():
            log.msg(
                format='PING_PEER: %(address)r',
                address=peer.address[0])
            proto.ping(peer)


    def makeService(self, myid, port, staleInterval):
        application = service.Application('Broadcaster')

        root = service.MultiService()
        root.setServiceParent(application)

        proto = PeerTrackerProtocol(controller=self, myid=myid, port=port)
        root.addService(internet.UDPServer(port, proto))

        root.addService(
            internet.TimerService(
                staleInterval.total_seconds(),
                self.removeStalePeers, staleInterval))

        root.addService(
            internet.TimerService(
                staleInterval.total_seconds(),
                self.pingPeers, proto))

        return application


application = Broadcaster().makeService(
    myid=MYID, port=PORT, staleInterval=STALE_INTERVAL)
