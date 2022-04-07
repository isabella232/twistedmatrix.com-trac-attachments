# This module was originally written as part of...
#
# sAsync:
# An enhancement to the SQLAlchemy package that provides persistent
# dictionaries, text indexing and searching, and an access broker for
# conveniently managing database access, table setup, and
# transactions. Everything can be run in an asynchronous fashion using the
# Twisted framework and its deferred processing capabilities.
#
# Copyright (C) 2006 by Edwin A. Suominen, http://www.eepatents.com
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Unit tests for syncbridge
"""

import sre, time, copy
from twisted.python.failure import Failure
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.internet.defer import succeed, DeferredList
from twisted.trial.unittest import TestCase

import sasync.syncbridge as syncbridge

DELAY = 0.1
VERBOSE = False


class TestTask(TestCase):
    def fakeSyncTask(self, x):
        time.sleep(DELAY)
        return 10*x

    def testRun(self):
        def gotResult(result):
            self.failUnlessEqual(result, 50)

        task = syncbridge.Task(self.fakeSyncTask, (5,), {}, 0)
        d = task.d
        reactor.callInThread(task.run)
        return d

    def testSerial(self):
        def taskFactory(niceness):
            return syncbridge.Task(self.fakeSyncTask, (5,), {}, niceness)
        taskA = taskFactory(0)
        taskB = taskFactory(0)
        self.failUnless(taskA < taskB)

    def testNiceness(self):
        taskA = syncbridge.Task(self.fakeSyncTask, (5,), {}, 1)
        taskB = syncbridge.Task(self.fakeSyncTask, (5,), {}, 0)
        self.failUnless(taskA > taskB)

    def testTerminator(self):
        taskA = syncbridge.Task(self.fakeSyncTask, (5,), {}, 0, terminator=True)
        taskB = syncbridge.Task(self.fakeSyncTask, (5,), {}, 10)
        self.failUnless(taskA > taskB)
        

class MockTask(object):
    def __init__(self, string, priority, terminator=False):
        self.string = str(string)
        self.terminator = terminator
        self.priority = 1000 * priority + self.serial()

    def __cmp__(self, other):
        if self.terminator:
            return -1
        else:
            return cmp(self.priority, other.priority)

    def __str__(self):
        return self.string

    @classmethod
    def serial(cls):
        if not hasattr(cls, 'number'):
            cls.number = 0
        else:
            cls.number += 1
        return cls.number


class TestPriorityQueue(TestCase):
    def setUp(self):
        self.queue = syncbridge.PriorityQueue()

    def initial(self):
        for char in 'abcd':
            item = MockTask(char, 0)
            self.queue.put(item)

    def contents(self, known):
        def doInThread():
            if VERBOSE:
                print "\n\n"
            items = ""
            while not self.queue.empty():
                item = self.queue.get()
                if VERBOSE:
                    print str(item), item.priority
                items += str(item)
            return items
        return deferToThread(doInThread).addCallback(
            self.failUnlessEqual, known)

    def testSamePriorityFIFO(self):
        self.initial()
        return self.contents('abcd')

    def testShutdownFull(self):
        self.initial()
        self.queue.put(MockTask('-', 0, terminator=True))
        return self.contents('abcd-')
    
    def testHigherPriorityFirst(self):
        self.initial()
        self.queue.put(MockTask('e', -1))
        return self.contents('eabcd')
        
    def testLowerPriorityLast(self):
        self.queue.put(MockTask('e', 1))
        self.initial()
        self.queue.put(MockTask('f', 1))
        return self.contents('abcdef')
        
    def testMixedPriorities(self):
        self.queue.put(MockTask('e', 2))
        self.queue.put(MockTask('f', 1))
        self.initial()
        self.queue.put(MockTask('g', 0))
        self.queue.put(MockTask('h', -1))
        self.queue.put(MockTask('i', -2))
        self.queue.put(MockTask('j', -2))
        self.queue.put(MockTask('k', 0))
        return self.contents('ijhabcdgkfe')


class TSQ_Mixin:
    def setUp(self):
        self.s = syncbridge.SynchronousQueue()
        return self.s.startup()

    def tearDown(self):
        return self.s.shutdown()

    def fakeSyncTask(self, x):
        time.sleep(DELAY)
        return 100*x


class TestSyncQueueShutdown(TSQ_Mixin, TestCase):
    def testShutdownWhileRunning(self):
        mutable = []
        
        def fakeSyncTask(x):
            time.sleep(DELAY)
            mutable.append(10*x)

        def checkTotal(null):
            self.failUnlessEqual(mutable[0], 50)

        d1 = self.s.deferToQueue(fakeSyncTask, 5)
        d2 = self.s.shutdown()
        return DeferredList([d1, d2]).addCallback(checkTotal)

    def testShutdownWhileEmpty(self):
        return self.s.shutdown()

    def testShutdownMultiple(self):
        d1 = self.s.shutdown()
        d2 = self.s.shutdown()
        d3 = deferToThread(time.sleep, 10*DELAY)
        d3.addCallback(lambda _:self.s.shutdown())
        return DeferredList([d1, d2, d3])

    def testDeleteWithoutShutdown(self):
        # This makes trial sit around forever
        # del self.s
        pass


class TestSyncQueue(TSQ_Mixin, TestCase):
    def testInsideVsOutside(self):
        def checkInside():
            self.failUnlessEqual(self.s._TLS.where, 'inside')
            
        self.failUnlessEqual(self.s._TLS.where, 'outside')
        return self.s.deferToQueue(checkInside)

    def testRunOneTask(self):
        def gotResult(result):
            self.failUnlessEqual(result, 500)
            
        return self.s.deferToQueue(self.fakeSyncTask, 5).addCallback(gotResult)

    def testRunSeveralNormalTasks(self):
        results = []
        
        def gotResult(result):
            results.append(result)

        def checkResults(null):
            self.failUnlessEqual(results, [0,100,200,300,400])

        dL = []
        for x in xrange(5):
            dL.append(self.s.deferToQueue(
                self.fakeSyncTask, x).addCallback(gotResult))
        return DeferredList(dL).addCallback(checkResults)

    def testRunSeveralOddTasks(self):
        results = []

        def fakeSyncTask(x):
            time.sleep(DELAY)
            return 100*x

        def waitBeforeHighPriorityTask():
            # Wait time is 2.5 times how long each fakeSyncTask takes
            time.sleep(2.5*DELAY)

        def doneWaiting(null):
            d = self.s.deferToQueue(fakeSyncTask, 20, niceness=-2)
            d.addCallback(gotResult)
            return d
        
        def gotResult(result):
            results.append(result)

        def checkResults(null):
            # Tasks 100 and 1000 should run first, in order that depends on
            # race condition
            firstTwo = results[0:2]
            firstTwo.sort()
            self.failUnlessEqual(firstTwo, [100, 1000])
            # Time before next task is 2*DELAY, but highest priority task isn't
            # dispatched until 2.5*DELAY. So task 200 should run next.
            self.failUnlessEqual(results[2], 200)
            # Highest priority task is dispatched while task 200 is running and
            # should run after it.
            self.failUnlessEqual(results[3], 2000)
            # Remaining tasks are normal priority and run in order dispatched.
            self.failUnlessEqual(results[4:], [300, 400, 500])

        dL = []
        # Immediately dispatch tasks resulting in 100, 200, 300, 400, 500,
        # with normal priority
        for x in xrange(5):
            d = self.s.deferToQueue(fakeSyncTask, x+1)
            d.addCallback(gotResult)
            dL.append(d)
        # Then dispatch task resulting in 1000, with higher priority
        d = self.s.deferToQueue(fakeSyncTask, 10, niceness=-1)
        d.addCallback(gotResult)
        dL.append(d)
        # Then, after a significant wait, dispatch task resulting in 2000, with
        # highest priority
        d = deferToThread(waitBeforeHighPriorityTask)
        d.addCallback(doneWaiting)
        dL.append(d)
        # Return a deferred to all these tasks getting done
        return DeferredList(dL).addCallback(checkResults)

    def testRunTaskWithInternalAsyncCall(self):
        def deferToSlow():
            def later(null):
                return self.y + 3.14
            return deferToThread(time.sleep, DELAY).addCallback(later)
        
        def syncTask():
            time.sleep(DELAY)
            self.y = 10
            time.sleep(DELAY)
            return self.s.blockDeferred(deferToSlow)

        def gotResult(result):
            self.failUnlessEqual(result, 13.14)

        return self.s.deferToQueue(syncTask).addCallback(gotResult)

