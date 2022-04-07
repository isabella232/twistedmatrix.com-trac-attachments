"""
Memcache client protocol for Twisted. See
L{http://cvs.danga.com/browse.cgi/wcmtools/memcached/doc/protocol.txt} for
any information.
"""

from twisted.protocols import basic
from twisted.internet import defer, protocol
from twisted.python import log

import types, marshal

try:
    from collections import deque
except ImportError:
    class deque(list):
        def popleft(self):
            return self.pop(0)

try:
    import cPickle as pickle
except ImportError:
    import pickle


class MemCacheProtocol(basic.LineReceiver):
    """
    MemCache protocol: connect to a memcached server to store/retrieve values.
    """
    _FLAG_PICKLE = 1
    _FLAG_INTEGER = 2
    _FLAG_LONG = 4
    _FLAG_FLOAT = 8
    _FLAG_MARSHAL = 16
    _FLAG_STR = 32
    factory = None
    pickle_version = 2
    marshal_version = 2

    def __init__(self):
        """
        Create the protocol.
        """
        self._current = deque()
        self._lenExpected = 0
        self._getBuffer = ""

    def connectionMade(self):
        """
        Called when connection is made.
        """
        if self.factory:
            self.factory.clientConnectionMade(self)

    def rawDataReceived(self, data):
        """
        Collect data for a get.
        """
        self._getBuffer += data
        if len(self._getBuffer) >= self._lenExpected:
            buf = self._getBuffer[:self._lenExpected]
            rem = self._getBuffer[self._lenExpected+2:]
            d, key, flags, length = self._current[0]
            val = buf
            if flags & self._FLAG_INTEGER:
                val = int(val)
            elif flags & self._FLAG_LONG:
                val = long(val)
            elif flags & self._FLAG_FLOAT:
                val = float(val)
            elif flags & self._FLAG_MARSHAL:
                val = marshal.loads(val)
            elif flags & self._FLAG_PICKLE:
                val = pickle.loads(val)
            self._lenExpected = 0
            self._getBuffer = ""
            self._current[0].append(val)
            self.setLineMode(rem)

    def lineReceived(self, line):
        """
        Receive line commands from the server.
        """
        if line == "STORED":
            # Set response
            d = self._current.popleft()[0]
            d.callback(True)
        elif line == "NOT STORED":
            # Set response
            d = self._current.popleft()[0]
            d.callback(False)
        elif line == "END":
            data = self._current.popleft()
            if len(data) == 5:
                # Get
                data[0].callback(data[4])
            elif len(data) == 1:
                # Empty get
                data[0].callback(None)
            else:
                # Stats
                data[0].callback(data[1])
        elif line == "NOT FOUND":
            # Incr/Decr/Delete
            d = self._current.popleft()[0]
            d.callback(False)
        elif line.startswith("VALUE"):
            # Prepare Get
            ign, key, flags, length = line.split()
            self._lenExpected = int(length)
            self._getBuffer = ""
            self._current[0].extend([key, int(flags), int(length)])
            self.setRawMode()
        elif line.startswith("STAT"):
            # Stat response
            data = self._current[0]
            ign, key, val = line.split(" ", 2)
            data[1][key] = val
        elif line.startswith("VERSION"):
            # Version response
            d = self._current.popleft()[0]
            d.callback(line.split(" ", 1)[1])
        elif line == "ERROR":
            log.err("Non-existent command sent.")
        elif line.startswith("CLIENT_ERROR"):
            log.err("Invalid input: %s" % line.split(" ", 1)[1])
        elif line.startswith("SERVER_ERROR"):
            log.err("Server error: %s" % line.split(" ", 1)[1])
        elif line == "DELETED":
            # Delete response
            d = self._current.popleft()[0]
            d.callback(True)
        elif line == "OK":
            # Flush_all response
            d = self._current.popleft()[0]
            d.callback(True)
        else:
            # Increment/Decrement response
            d, key, oldval = self._current.popleft()
            val = int(line)
            d.callback(val)

    def incr(self, key, val=1):
        """
        Increment the value of C{key} by given value (default to 1).
        C{key} must be consistent with an int. Return the new value.

        Warning: if it's not an int, it will coerce the value in cache to an
        int but will not fail.
        """
        return self._incrdecr("incr", key, val)

    def decr(self, key, val=1):
        """
        Decrement the value of C{key} by given value (default to 1).
        C{key} must be consistent with an int. Return the new value, coerced to
        0 if negative.

        Warning: if it's not an int, it will coerce the value in cache to an
        int but will not fail.
        """
        return self._incrdecr("decr", key, val)

    def _incrdecr(self, cmd, key, val):
        """
        Internal wrapper for incr/decr.
        """
        fullcmd = "%s %s %d" % (cmd, key, int(val))
        self.sendLine(fullcmd)
        d = defer.Deferred()
        self._current.append([d, key, val])
        return d

    def replace(self, key, val, expireTime=0):
        """
        Replace the given C{key}. It must already exists in the server.
        """
        return self._set("replace", key, val, expireTime)

    def add(self, key, val, expireTime=0):
        """
        Add the given C{key}. It must not exists in the server.
        """
        return self._set("add", key, val, expireTime)

    def set(self, key, val, expireTime=0):
        """
        Set the given C{key}.
        """
        return self._set("set", key, val, expireTime)

    def _marshal_dumps(self, val):
        """
        Override marshal dumps for 2.3 compatibility.
        """
        if self.marshal_version:
            return marshal.dumps(val, self.marshal_version)
        return marshal.dumps(val)

    def _pickle_dumps(self, val):
        """
        Wrapper pickle dumps.
        """
        return pickle.dumps(val, self.pickle_version)

    def _set(self, cmd, key, val, expireTime):
        """
        Internal wrapper for setting values.
        """
        flags = 0
        if isinstance(val, types.StringTypes):
            pass
        elif isinstance(val, int):
            flags |= self._FLAG_INTEGER
            val = "%d" % val
        elif isinstance(val, long):
            flags |= self._FLAG_LONG
            val = "%d" % val
        elif isinstance(val, float):
            flags |= self._FLAG_FLOAT
            val = "%f" % val
        elif isinstance(val, str):
            flags |= self._FLAG_STR
        else:
            try:
                val = self._marshal_dumps(val)
            except ValueError:
                flags |= self._FLAG_PICKLE
                val = self._pickle_dumps(val)
            else:
                flags |= self._FLAG_MARSHAL
        length = len(val)
        fullcmd = "%s %s %d %d %d" % (cmd, key, flags, expireTime, length)
        self.sendLine(fullcmd)
        self.sendLine(val)
        d = defer.Deferred()
        self._current.append([d, key, flags, length])
        return d

    def get(self, key):
        """
        Get the given C{key}.
        """
        fullcmd = "get %s" % key
        self.sendLine(fullcmd)
        d = defer.Deferred()
        self._current.append([d])
        return d

    def stats(self):
        """
        Get some stats from the server. It will be available as a dict.
        """
        self.sendLine("stats")
        d = defer.Deferred()
        # Add with a dict that will hold stat values
        self._current.append([d, {}])
        return d

    def version(self):
        """
        Get the version of the server.
        """
        self.sendLine("version")
        d = defer.Deferred()
        self._current.append([d])
        return d

    def delete(self, key):
        """
        Delete an existing C{key}.
        """
        self.sendLine("delete %s" % key)
        d = defer.Deferred()
        self._current.append([d])
        return d

    def flushAll(self):
        """
        Flush all cached values.
        """
        self.sendLine("flush_all")
        d = defer.Deferred()
        self._current.append([d])
        return d

import sys

if 0x2040000 <= sys.hexversion < 0x2050000:
    # Marshal version of 1
    MemCacheProtocol.marshal_version = 1
elif sys.hexversion < 0x2040000:
    # Marshal version of 0
    MemCacheProtocol.marshal_version = 0

class MemCacheClient(protocol.ClientFactory):
    """Client to memcache."""
    protocol = MemCacheProtocol

