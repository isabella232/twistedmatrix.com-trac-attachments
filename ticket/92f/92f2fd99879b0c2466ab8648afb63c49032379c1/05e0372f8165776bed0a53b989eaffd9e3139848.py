from twisted.internet import defer, reactor
from twisted.trial import unittest

def sleep(seconds):
    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, seconds)
    return d

class ExampleTest(unittest.TestCase):
    timeout = 5

    @defer.inlineCallbacks    
    def test_hypothetically_big_and_complicated(self):
        yield sleep(1) 
        yield sleep(1)
        yield sleep(1)
        yield sleep(100)
        yield sleep(1)
        
    
output = """
tfitz@ubuntu:~/example$ trial example.py
example
  ExampleTest
    test_hypothetically_big_and_complicated ...                         [ERROR]
                        [ERROR]

===============================================================================
[ERROR]: example.ExampleTest.test_hypothetically_big_and_complicated

Traceback (most recent call last):
Failure: twisted.internet.defer.TimeoutError: <example.ExampleTest testMethod=test_hypothetically_big_and_complicated> (test_hypothetically_big_and_complicated) still running at 5.0 secs
===============================================================================
[ERROR]: example.ExampleTest.test_hypothetically_big_and_complicated

Traceback (most recent call last):
Failure: twisted.trial.util.DirtyReactorAggregateError: Reactor was unclean.
DelayedCalls: (set twisted.internet.base.DelayedCall.debug = True to debug)
<DelayedCall 0xb740f92c [98.001240015s] called=0 cancelled=0 Deferred.callback(100)>
-------------------------------------------------------------------------------
Ran 1 tests in 5.007s

FAILED (errors=2)
"""

desired_output = """
example
  ExampleTest
    test_hypothetically_big_and_complicated ...                         [ERROR]

===============================================================================
[ERROR]: example.ExampleTest.test_hypothetically_big_and_complicated

Traceback (most recent call last):
  File "/usr/lib/python2.6/dist-packages/twisted/internet/defer.py", line 823, in _inlineCallbacks
    result = g.send(result)
  File "/home/tfitz/example/example.py", line 18, in test_hypothetically_big_and_complicated
    yield sleep(100)
exceptions.Exception: Timeout
-------------------------------------------------------------------------------
Ran 1 tests in 3.013s

FAILED (errors=1)

"""