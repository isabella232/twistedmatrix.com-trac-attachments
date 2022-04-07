import zope.interface
import twisted.plugin
import cPickle as pickle
from twisted.spread import pb
from twisted.internet import defer, protocol, reactor
from twisted.python import log

class PP(protocol.ProcessProtocol):
    def __init__(self, processdone):
        self.output = ""
        self.d_connected = defer.Deferred()
        self.d_connected.addCallback(log.msg)
        self.d_connected.addErrback(log.err)
        self.processdone = processdone
        
    def connectionMade(self):
       self.transport.closeStdin()
       self.d_connected.callback("Connected")
           
    def outReceived(self, data):
       pass
        
    def errReceived(self, data):
       log.err(data)

    def processEnded(self, status):
        self.transport.loseConnection()
        self.processdone.callback("all done")
        
    def die(self):
        log.msg("Kill %s:%d" % (self.name, self.transport.pid))
        os.kill(self.transport.pid, signal.SIGKILL)
        
        
class TimingOutCommand:
    def __init__(self, timeout, command, args):
        self.done = defer.Deferred()
        self.done.addCallback(self._canceltimeout_cmd)
        self.done.addErrback(log.err)
        self.timeout =  timeout
        self.command = command
        self.args = args
        self.connector = PP(self.done)
        env = os.environ
        args = [command, self.args]
        reactor.spawnProcess(self.connector, command, args, env=env)
        self.canceltimeout = False
        reactor.callLater(timeout, self._timeout_cmd)
        
    def _timeout_cmd(self):
        if self.canceltimeout:
            log.msg("Trying to timeout command, but timeout was cancelled")
            return
        log.msg("Timed out before it could finish")
        self.timeout_cmd()
        
    def _canceltimeout_cmd(self, result):
        self.canceltimeout = True
        self.canceltimeout_cmd()
        
    def conceltimeout_cmd(self):
        raise NotImplementedError
        
    def timeout_cmd(self):
        raise NotImplementedError
        
class CmdTimeout(TimingOutCommand):
    def __init__(self, timeout, command, args):
        TimingOutCommand.__init__(self, timeout, command, args)
        
    def canceltimeout_cmd(self):
        pass
        
    def timeout_cmd(self):
        log.msg("cancelling!!!")
        
if __name__ == "__main__":
    log.FileLogObserver.timeFormat = '[%d/%b/%Y:%H:%M:%S]'
    log.startLogging(sys.stdout)
    a = CmdTimeout(3, "/bin/sleep", "10")
    reactor.run()
