
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet import iocpreactor
iocpreactor.install()

from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
from time import time
from array import array


time_then = time()

data = None
perspective = None
transfer_count = 0

def connection_success(message):
    global time_then
    time_then = time()
    print "Connected:",message
    send_data(perspective)
    send_data(perspective)
    send_data(perspective)
    send_data(perspective)
    print 'All data sent'
 
def failure(error):
    print "error received:", error
    reactor.stop()

def transfer_success(message):
    global time_then, transfer_count
    diff = time() - time_then
    time_then = time()
    print "Transfer Done:",message
    print "Time Diff:",diff
    transfer_count += 1
    if transfer_count >= 4:
        shutdown()

def transfer_failure(error):
    print "Transfer error received:", error
    reactor.stop()

def shutdown():
    print 'Shutting down in 10 seconds...'
    reactor.callLater(10, reactor.stop)

    
def connected(p):
    global perspective
    perspective = p
    perspective.callRemote('echo', "Connection started").addCallbacks(connection_success, failure)
    print "Connection Initiated."

def setup_data():
    global data
    data = {
        'values': [],
        'description': 'Some data'
    }
    for i in range(64000) :
        data['values'].append({
            'timestamp': i,
            'value': i + 0.001,
            'sample_id': i
        })
    print "Data setup"
    return data

def send_data(perspective):
    perspective.callRemote('transfer', data, "Dict of values").addCallbacks(transfer_success, transfer_failure)
    print "Data transmitted"

    
setup_data()
factory = pb.PBClientFactory()
reactor.connectTCP("localhost", pb.portno, factory)
factory.login(
    UsernamePassword("guest", "guest")).addCallbacks(connected, failure)

reactor.run()
