from zope.interface import Interface, implements
from twisted.python import log
from twisted.internet import defer

import memcache


class IResolver(Interface):
    def resolve(key):
        """Return the memcache backend address for the given key.
        """


class Resolver(object):
    """An IResolver implementation that resolve the memcache backend
    using a list of regular expressions.
    """
    
    implements(IResolver)
    noisy = True

    def __init__(self, config):
        import re

        self.config = [(re.compile(r), d) for r, d in config]

        
    def resolve(self, key):
        for r, d in self.config:
            if r.search(key):
                if self.noisy:
                    log.msg("memcache resolver: key '%s', backend '%s'" % (key, d))
                return d

        raise Exception("unable to resolve the key '%s'" % key)

        
class MemCacheClient(object):
    """An high level memcache backend.
    """
    
    def __init__(self, resolver, protocolFactory=memcache.MemCacheProtocol):
        self.resolver = resolver
        self.protocolFactory = protocolFactory
        # Keep persistent connections, mapped by backend address
        self.connections = {}


    def connect(self, key):
        def cb(proto):
            self.connections[(host, port)] = proto
            return proto

        host, port = self.resolver.resolve(key)
        
        try:
            proto = self.connections[(host, port)]
            return defer.succeed(self.protocol)
        except KeyError:
            from twisted.internet import protocol, reactor

            d = protocol.ClientCreator(reactor, self.protocolFactory
                                       ).connectTCP(host, port) 
            return d.addCallback(cb)

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
        return self.connect(key).addCallbacks(cbConnect)

    def invalidate(self, key):
        """Invalidate the cache value associated with the given key.
        """

        def cbConnect(proto):
            return proto.delete(key)

        # Make sure to be connected
        return self.connect(key).addCallback(cbConnect)



if __name__ == '__main__':
    import sys
    from twisted.internet import reactor


    log.startLogging(sys.stdout)


    def fun(a, b):
        raise ValueError('value error')

        print 'callable', a, b
        return a + b

    def callback(result):
        print 'callback:', result

    def errback(reason):
        reason.printTraceback()


    config = [
        (r'[a-z]+', ('127.0.0.1', 11211)),
        (r'\d+', ('127.0.0.1', 11212))
         ]
    resolver = Resolver(config)
    client = MemCacheClient(resolver)

    client.cache('x', fun, '2', '3'
                 ).addCallbacks(callback, errback
                                ).addBoth(lambda _: reactor.stop())

    reactor.run()
