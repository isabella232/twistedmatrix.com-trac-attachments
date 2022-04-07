#!/usr/bin/env python
import OpenSSL
import socket
import struct

junk='a'*1100
def buildContext():
    return OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)

def connect(context):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    conn = OpenSSL.SSL.Connection(context,s)
    conn.connect(("localhost",8000))

    # Put the socket in blocking mode
    conn.setblocking(1)

    # Set the timeout using the setsockopt
    #tv = struct.pack('ii', int(6), int(0))
    #conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, tv)
    try:
        conn.do_handshake()
    except OpenSSL.SSL.WantReadError:
        print "Timeout"

    print "State " , conn.state_string()

    # Send question
    conn.send(junk)

    try:
        recvstr = conn.recv(len(junk))
        print "Got data: %d"%(len(recvstr))
    except OpenSSL.SSL.WantReadError:
        print "Timeout"

if __name__=='__main__':
    context = buildContext()
    while(1):
        connect(context)
