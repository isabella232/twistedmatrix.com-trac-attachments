import os
import socket
import struct
import sys

from twisted.python import sendmsg


if __name__ == '__main__':

    # This code segfaults when running with twisted/trunk commit
    # 98a3df200968b78bd3b985dfd4fb10a5b415d6fc on Linux Python 2
    # due to a bug in src/twisted/python/_sendmsg.c and glibc's
    # CMSG_NXTHDR implementation.

    # get connected sockets
    s1, s2 = socket.socketpair(socket.AF_UNIX)

    # two CMSGs in ancillary data (no segfault with just one)
    ancillary = [
        (socket.SOL_SOCKET, sendmsg.SCM_RIGHTS, struct.pack('i', s1.fileno())),
        (socket.SOL_SOCKET, sendmsg.SCM_RIGHTS, struct.pack('i', s2.fileno())),
    ]

    expected = {
        2: 'Expecting to segfault.',
        3: 'Should not segfault.',
    }
    print expected.get(sys.version_info.major, 'Unpexpected Python version.')
    retval = sendmsg.sendmsg(s1, data=b'some data', ancillary=ancillary)
    print 'Did not segfault.'
