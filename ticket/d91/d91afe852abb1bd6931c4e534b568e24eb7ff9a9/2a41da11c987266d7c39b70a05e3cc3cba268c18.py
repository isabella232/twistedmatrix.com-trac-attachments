from twisted.internet import reactor, defer

def terminate():
    print "terminating..."
    d = defer.Deferred()
    # do things that long last (eg. database, network, etc.)
    reactor.callLater(1, d.callback, None)
    return d

def stop_reactor_twice():
    reactor.stop()
    reactor.stop()

reactor.addSystemEventTrigger("before", "shutdown", terminate)
reactor.callWhenRunning(stop_reactor_twice)
reactor.run()


# Output without patch:
# 1. 'terminate' method is called twice
# 2. exception is not meaningful
"""
terminating...
terminating...
Unhandled error in Deferred:
Traceback (most recent call last):
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/defer.py", line 317, in _runCallbacks
    self.result = callback(self.result, *args, **kw)
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/defer.py", line 507, in _cbDeferred
    self.callback(self.resultList)
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/defer.py", line 239, in callback
    self._startRunCallbacks(result)
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/defer.py", line 304, in _startRunCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/defer.py", line 317, in _runCallbacks
    self.result = callback(self.result, *args, **kw)
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/base.py", line 406, in _cbContinueSystemEvent
    self._continueSystemEvent(eventType)
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/base.py", line 411, in _continueSystemEvent
    for callList in sysEvtTriggers[1], sysEvtTriggers[2]:
exceptions.TypeError: 'NoneType' object is unsubscriptable
"""

# Output with patch:
# 1. 'terminate' method is called once, as expected
# 2. exception states what's actually wrong
"""
Traceback (most recent call last):
  File "test2.py", line 16, in <module>
    reactor.run()
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/posixbase.py", line 221, in run
    self.mainLoop()
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/posixbase.py", line 229, in mainLoop
    self.runUntilCurrent()
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/base.py", line 573, in runUntilCurrent
    call.func(*call.args, **call.kw)
--- <exception caught here> ---
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/base.py", line 423, in _continueSystemEvent
    callable(*args, **kw)
  File "test2.py", line 12, in stop_reactor_twice
    reactor.stop()
  File "/home/yoann/tmp/twisted-before-shutdown/trunk/twisted/internet/base.py", line 339, in stop
    raise error.ReactorAlreadyStopped, "don't stop reactor twice"
twisted.internet.error.ReactorAlreadyStopped: don't stop reactor twice
"""

