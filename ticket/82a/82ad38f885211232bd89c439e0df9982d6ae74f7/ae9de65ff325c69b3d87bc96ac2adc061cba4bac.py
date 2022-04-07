from twisted.internet import defer

class StoreFileStarter:

    # This class is an example, cut down from something that does more
    # logging.  It demonstrates how to get a result from a
    # successfully opened data connection for FTPClient.storeFile() in
    # Twisted 1.1.1, and an error in other cases.

    # This assumes that the desired result is an instance
    # SomeWrapper(consumer); something else could be used instead, and
    # the factoring could be different to make this more configuration
    # via constructor arguments or subclassing.

    def __init__(self, path):
        self.path = path
        self.deferred = defer.Deferred()
        self.responses = 0
        self.consumer = None

    def start(self, ftpClient):
        dConsumer, dlResponses = ftpClient.storeFile(self.path)
        dConsumer.addCallback(self.cbConsumer)
        dlResponses.addCallbacks(self.cbResponses, self.ebResponses)
        return self.deferred

    def cbConsumer(self, consumer):
        self.responses += 1
        if self.responses == 2:
            self.deferred.callback(SomeWrapper(consumer))
        else:
            self.consumer = consumer

    def cbResponses(self, value):
        self.responses += 1
        if self.responses == 2:
            assert self.consumer is not None
            self.deferred.callback(SomeWrapper(self.consumer))

    def ebResponses(self, error):
        # Unpack the error, since this was from a DeferredList with
        # fireOnOneErrback set:
        error = error.value[0]
        error.trap(ftp.CommandFailed)
        errcode, errmsg = error.value.args[0][0].split(None, 1)
        # more error codes could be handled here
        if errcode == "550":
            error = failure.Failure(
                OSError(errno.EACCES, errmsg, self.path))
        self.deferred.errback(error)


# A function that returns (a Deferred that returns) the desired value
# when storeFile() results in happiness.

# In a real application, the "starter" would be created up front, and
# the start method would be used as a callback for a Deferred that's
# fired when the FTPClient is available.

def createSomeWrapper(ftpClient, path):
    return StoreFileStarter(path).start(ftpClient)
