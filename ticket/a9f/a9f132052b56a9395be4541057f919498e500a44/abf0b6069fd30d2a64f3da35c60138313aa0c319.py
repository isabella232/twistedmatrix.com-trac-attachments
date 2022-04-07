from twisted.names import dns, client, root, cache, resolve, hosts

from twisted.internet.error import CannotListenError
from exceptions import KeyboardInterrupt, ImportError
import logging
logging.basicConfig(level=logging.DEBUG)
DNSLogger = logging.getLogger('rootResolver')

running = False

def printAnswer((answers, auth, add)):
    if not len(answers):
        DNSLogger.debug('No answers')
    else:
        DNSLogger.debug('ANSWER: %s ' ','.join([str(x.payload) for x in answers]))

def printFailure(failure):
    error=failure.trap(CannotListenError, ImportError)
    message=failure.getErrorMessage()
    DNSLogger.critical("FAILURE: %s(%s)" % (error.__name__,message))
    running = False

theResolver=None
if __name__ == "__main__":
    resolvers=[]
    hostResolver = hosts.Resolver(file='named.root.txt')
    rootResolver = root.bootstrap(hostResolver)
    resolvers.append(rootResolver)
    theResolver = resolve.ResolverChain(resolvers)

    running = True
    
    while running:
        try:
            throwaway=theResolver._lookup('www.google.com',dns.A,dns.IN,60)
            throwaway.addCallbacks(callback=printAnswer,errback=printFailure)
        except KeyboardInterrupt:
            running = False
