import sys

from twisted.python import log
from twisted.internet import defer

import memcache



class MemCacheClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.protocol = None


    def connect(self):
        if self.protocol is None:
            from twisted.internet import protocol, reactor
            return protocol.ClientCreator(reactor, memcache.MemCacheProtocol
                                          ).connectTCP(self.host, self.port)
        else:
            defer.succeed(self.protocol)


    def cache(self, key, callable, *args, **kwargs):
        """If an entry with the given key if found in the cache, it is
        returned.
        Else the callable function is called with the given arguments
        and the returned value is stored in cache.

        Returns the result of the the callable function.

        XXX TODO: handle connection errors
        """

        def cbConnect(proto):
            def cbGet(value):
                if value is None:
                    return call()
                else:
                    # Return the cached value
                    return value

            def ebGet(reason):
                # Ignore the error
                # XXX return callable(*args, **kwargs)
                return call()
            
            def call():
                # Compute the value from the function and store it in
                # the cache
                return defer.maybeDeferred(callable, *args,
                                           **kwargs).addCallback(set)
            
            def set(value):
                # Set the value in the cache, ignoring errors
                return proto.set(key, value).addBoth(lambda _: value)

            # Check for the value in the cache
            return proto.get(key).addCallbacks(cbGet, ebGet)
                
        # Make sure to be connected
        return self.connect().addCallbacks(cbConnect)

    def invalidate(self, key):
        """Invalidate the cache value associated with the given key.
        """

        def cbConnect(proto):
            return proto.delete(key)

        # Make sure to be connected
        return self.connect().addCallback(cbConnect)



if __name__ == '__main__':
    from twisted.internet import reactor
    
    def fun(a, b):
        #raise ValueError('value error')

        print 'callable', a, b
        return a + b

    def callback(result):
        print 'callback:', result

    def errback(reason):
        print 'errback:', reason


    client = MemCacheClient('127.0.0.1', 11211)
    client.cache('x', fun, '2', '3'
                 ).addCallbacks(callback, errback
                                ).addBoth(lambda _: reactor.stop())

    #log.startLogging(sys.stdout)
    reactor.run()
