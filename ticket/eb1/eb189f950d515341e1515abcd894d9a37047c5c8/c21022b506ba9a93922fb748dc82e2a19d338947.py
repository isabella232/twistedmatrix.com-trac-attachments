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
Unit tests for taskqueue
"""

import copy, time, random, threading
import zope.interface
from twisted.internet import defer, reactor
from twisted.trial.unittest import TestCase

import sasync.taskqueue as taskqueue
from mock import MockTask, MockWorker

DELAY = 0.01
VERBOSE = False


class TestTask(TestCase):
    def taskFactory(self, priority, series=0):
        return taskqueue._Task(lambda _: None, (None,), {}, priority, series)

    def testConstructorWithValidArgs(self):
        func = lambda : None
        task = taskqueue._Task(func, (1,), {2:3}, 100, None)
        self.failUnlessEqual(task.callTuple, (func, (1,), {2:3}))
        self.failUnlessEqual(task.priority, 100)
        self.failUnlessEqual(task.series, None)
        self.failUnless(isinstance(task.d, defer.Deferred))

    def testConstructorWithBogusArgs(self):
        self.failUnlessRaises(
            TypeError, taskqueue._Task, lambda : None, 1, {2:3}, 100, None)
        self.failUnlessRaises(
            TypeError, taskqueue._Task, lambda : None, (1,), 2, 100, None)

    def testPriorityOtherTask(self):
        taskA = self.taskFactory(0)
        taskB = self.taskFactory(1)
        taskC = self.taskFactory(1.1)
        self.failUnless(taskA < taskB)
        self.failUnless(taskB < taskC)
        self.failUnless(taskA < taskC)
    
    def testPriorityOtherNone(self):
        taskA = self.taskFactory(10000)
        self.failUnless(taskA < None)


class TestTaskFactory(TestCase):
    def setUp(self):
        self.tf = taskqueue._TaskFactory(MockTask)

    def listInOrder(self, theList):
        if VERBOSE:
            strList = [str(x) for x in theList]
            print "\nSerial Numbers:\n%s\n" % ", ".join(strList)
        unsorted = copy.copy(theList)
        theList.sort()
        self.failUnlessEqual(theList, unsorted)

    def testSerialOneSeries(self):
        serialNumbers = []
        for null in xrange(5):
            this = self.tf._serial(None)
            self.failUnless(isinstance(this, float))
            self.failIf(this in serialNumbers)
            serialNumbers.append(this)
        self.listInOrder(serialNumbers)

    def testSerialMultipleSeriesConcurrently(self):
        serialNumbers = []
        for null in xrange(5):
            x = self.tf._serial(1)
            y = self.tf._serial(2)
            serialNumbers.extend([x,y])
        self.failUnlessEqual(
            serialNumbers,
            [1, 2, 2, 3, 3, 4, 4, 5, 5, 6 ])
        #    x0 y0 x1 y1 x2 y2 x3 y3 x4 y4
        
    def testSerialAnotherSeriesComingLate(self):
        serialNumbers = []
        for null in xrange(5):
            x = self.tf._serial(1)
            serialNumbers.append(x)
        for null in xrange(5):
            y = self.tf._serial(2)
            serialNumbers.append(y)
        self.listInOrder(serialNumbers)


class TestIWorker(TestCase):
    def testInvariantCheckClassAttribute(self):
        class NoAttr(object):
            zope.interface.implements(taskqueue.IWorker)
            cQualified = []

        class AttrOK(object):
            zope.interface.implements(taskqueue.IWorker)
            cQualified = []

        class AttrBogus(object):
            zope.interface.implements(taskqueue.IWorker)
            cQualified = 'foo'

        for WorkerClass in (NoAttr, AttrOK):
            worker = WorkerClass()
            try:
                taskqueue.IWorker.validateInvariants(worker)
            except:
                self.fail(
                    "Acceptable class attribute shouldn't raise an exception")
        self.failUnlessRaises(
            taskqueue.InvariantError,
            taskqueue.IWorker.validateInvariants, AttrBogus())

    def testInvariantCheckInstanceAttribute(self):
        class Worker(object):
            zope.interface.implements(taskqueue.IWorker)

        worker = Worker()
        for attr in (None, []):
            if attr is not None:
                worker.iQualified = attr
            try:
                taskqueue.IWorker.validateInvariants(worker)
            except:
                self.fail(
                    "Acceptable instance attribute shouldn't raise exception")
        worker.iQualified = 'foo'
        self.failUnlessRaises(
            taskqueue.InvariantError,
            taskqueue.IWorker.validateInvariants, worker)


class TestPriorityBasic(TestCase):
    def setUp(self):
        self.heap = taskqueue.Priority()
        self.tf = taskqueue._TaskFactory(MockTask)

    def _standard(self):
        for char in 'abcd':
            item = self.tf.new(char, (), {}, 0)
            self.heap.put(item)

    def _contents(self, known):
        def loop():
            items = ""
            while len(self.heap.heap):
                wfd = defer.waitForDeferred(self.heap.get())
                yield wfd
                item = wfd.getResult()
                if VERBOSE and isinstance(item, MockTask):
                    print str(item), item.priority
                items += str(item)
            yield items

        d = defer.deferredGenerator(loop)()
        d.addCallback(self.failUnlessEqual, known)
        return d

    def testPukesOnInvalidNiceness(self):
        for invalidNiceness in (1000, -1000, 21, -21, 1.5, 'foo'):
            self.failUnlessRaises(
                ValueError, self.tf.new, 'a', (), {}, invalidNiceness)

    def testSamePriorityFIFO(self):
        self._standard()
        return self._contents('abcd')

    def testShutdownFull(self):
        self._standard()
        self.heap.put(None)
        return self._contents('abcdNone')
    
    def testHigherPriorityAdvanced(self):
        self._standard()
        self.heap.put(self.tf.new('e', (), {}, -18))
        self._standard()
        self.heap.put(self.tf.new('e', (), {}, -18))
        return self._contents('aebecdabcd')
        
    def testLowerPriorityDelayed(self):
        self._standard()        
        self.heap.put(self.tf.new('e', (), {}, 18))
        self._standard()
        self.heap.put(self.tf.new('f', (), {}, 18))
        return self._contents('abcdabcdef')
        
    def testMixedPriorities(self):
        self._standard()
        self.heap.put(self.tf.new('e', (), {}, 18))
        self.heap.put(self.tf.new('f', (), {}, 9))
        self._standard()
        self.heap.put(self.tf.new('g', (), {}, 0))
        self.heap.put(self.tf.new('h', (), {}, -9))
        self.heap.put(self.tf.new('i', (), {}, -18))
        self.heap.put(self.tf.new('j', (), {}, -18))
        self.heap.put(self.tf.new('k', (), {}, 0))
        return self._contents('abijcdhabcdgfke')


class TestPriorityPipelining(TestCase):
    def setUp(self):
        self.heap = taskqueue.Priority()
        self.tf = taskqueue._TaskFactory(MockTask)

    def _queueTwoSeries(self, N, nicenessA, nicenessB):
        def putter(info):
            series, niceness = info
            item = self.tf.new("%s" % series, (), {}, niceness, series)
            self.heap.put(item)

        def put(series, niceness):
            d = defer.Deferred()
            d.addCallback(putter)
            # For desired 2:1 prioritizing ratio, pipeline prioritizing
            # behavior emerges with input vs. output rate ratio of 2:1 and
            # stabilizes by the time the ratio has reached 3:1
            reactor.callLater(0.001, d.callback, (series, niceness))
            return d

        mutable = []
        def putLoop():
            # Put stuff in quickly
            while not mutable:
                wfd = defer.waitForDeferred(put('A', nicenessA))
                yield wfd
                wfd = defer.waitForDeferred(put('B', nicenessB))
                yield wfd
        putLoop = defer.deferredGenerator(putLoop)

        items = {}
        def getLoop():
            # Get stuff slowly and stop the put loop when done getting
            N_sub = int(round(0.3*N))
            for k in xrange(N_sub):
                # Do gets at about the same rate as puts
                d = defer.Deferred()
                reactor.callLater(0.01, d.callback, None)
                yield defer.waitForDeferred(d)
                # Wait for a new item to get
                wfd = defer.waitForDeferred(self.heap.get())
                yield wfd
                item = wfd.getResult()
                if VERBOSE:
                    print k, str(item), item.priority
                items[item.series] = items.get(item.series, 0) + 1
            mutable.append(None)
        getLoop = defer.deferredGenerator(getLoop)

        d1 = putLoop()
        d2 = getLoop()
        return defer.DeferredList([d1,d2]).addCallback(lambda _: items)

    def _checkRatio(self, items, minRatio, maxRatio):
        ratio = float(items['B']) / float(items['A'])
        minMsg = "Ratio %f must be >= %f" % (ratio, minRatio)
        self.failUnless(ratio >= minRatio, minMsg)
        maxMsg = "Ratio %f must be <= %f" % (ratio, maxRatio)
        self.failUnless(ratio <= maxRatio, maxMsg)

    def testNicenessHalfRate(self):
        d = self._queueTwoSeries(300, 0, 10)
        d.addCallback(self._checkRatio, 0.45, 0.55)
        return d
    
    def testNicenessDoubleRate(self):
        d = self._queueTwoSeries(300, 0, -10)
        d.addCallback(self._checkRatio, 1.6, 2.5)
        return d

    def testNicenessQuarterRate(self):
        d = self._queueTwoSeries(300, 0, 20)
        d.addCallback(self._checkRatio, 0.23, 0.27)
        return d
    
    def testNicenessQuadrupleRate(self):
        d = self._queueTwoSeries(300, 0, -20)
        # I would expect 4.0 instead of 5.0, but nothing's perfect
        d.addCallback(self._checkRatio, 3.5, 5.0)
        return d


class TestAssignmentFactory(TestCase):
    def setUp(self):
        self.af = taskqueue._AssignmentFactory()
    
    def testGetQueue(self):
        q1a = self.af.getQueue(1)
        q1b = self.af.getQueue(1)
        self.failUnlessEqual(q1a, q1b)
        q2 = self.af.getQueue(2)
        self.failIfEqual(q1a, q2)
        for q in (q1a, q2):
            self.failUnless(isinstance(q, defer.DeferredQueue))

    def testQueuePutOnNew(self):
        def checkWhatGot(got):
            self.failUnless(isinstance(got, taskqueue._Assignment))
        
        task = MockTask(lambda x: 10*x, (2,), {}, 100, None)
        self.af.new(task)
        queue = self.af.getQueue(None)
        d = queue.get()
        d.addCallback(checkWhatGot)
        return d

    def testRequestBasic(self):
        OriginalAssignment = taskqueue._Assignment
        
        class ModifiedAssignment(taskqueue._Assignment):
            mutable = []
            def accept(self, worker):
                self.mutable.append(worker)
                self.d.callback(None)

        def finishUp(null, worker):
            self.failUnlessEqual(ModifiedAssignment.mutable, [worker])
            taskqueue._Assignment = OriginalAssignment

        taskqueue._Assignment = ModifiedAssignment
        task = MockTask(lambda x: 10*x, (2,), {}, 100, None)
        worker = MockWorker()
        worker.hired = False
        self.af.request(worker, None)
        for dList in worker.assignments.itervalues():
            self.failUnlessEqual(
                [isinstance(x, defer.Deferred) for x in dList], [True])
        d = self.af.new(task)
        d.addCallback(finishUp, worker)
        return d

    def testRequestAndAccept(self):
        task = MockTask(lambda x: 10*x, (2,), {}, 100, None)
        worker = MockWorker()
        worker.hired = False
        self.af.request(worker, None)
        d = defer.DeferredList([self.af.new(task), task.d])
        d.addCallback(lambda _: self.failUnlessEqual(worker.ran, [task]))
        return d


class TestWorkerManagerHiring(TestCase):
    def setUp(self):
        self.mgr = taskqueue.WorkerManager()

    def testHireRejectBogus(self):
        class AttrBogus(object):
            zope.interface.implements(taskqueue.IWorker)
            cQualified = 'foo'

        self.failUnlessRaises(
            taskqueue.ImplementationError, self.mgr.hire, None)
        self.failUnlessRaises(
            taskqueue.InvariantError, self.mgr.hire, AttrBogus())

    def _checkAssignments(self, workerID):
        worker = self.mgr.workers[workerID]
        assignments = getattr(worker, 'assignments', {})
        for key in assignments.iterkeys():
            self.failUnlessEqual(assignments.keys().count(key), 1)
        self.failUnless(isinstance(assignments, dict))
        for assignment in assignments.itervalues():
            self.failUnlessEqual(
                [True for x in assignment
                 if isinstance(x, defer.Deferred)], [True])

    def testHireClassQualifications(self):
        class CQWorker(MockWorker):
            cQualified = ['foo']

        worker = CQWorker()
        workerID = self.mgr.hire(worker)
        self._checkAssignments(workerID)
        
    def testHireInstanceQualifications(self):
        worker = MockWorker()
        worker.iQualified = ['bar']
        workerID = self.mgr.hire(worker)
        self._checkAssignments(workerID)

    def testHireMultipleWorkersThenShutdown(self):
        ID_1 = self.mgr.hire(MockWorker())
        ID_2 = self.mgr.hire(MockWorker())
        self.failIfEqual(ID_1, ID_2)
        self.failUnlessEqual(len(self.mgr.workers), 2)
        d = self.mgr.shutdown()
        d.addCallback(lambda _: self.failUnlessEqual(self.mgr.workers, {}))
        return d

    def testTerminate(self):
        worker = MockWorker()
        workerID = self.mgr.hire(worker)
        return self.mgr.terminate(workerID)


class TestWorkerManagerRun(TestCase):
    def setUp(self):
        self.mgr = taskqueue.WorkerManager()

    def tearDown(self):
        return self.mgr.shutdown()

    def testOneWorker(self):
        worker = MockWorker(0.2)
        N = 10

        def completed(null):
            self.failUnlessEqual(
                [type(x) for x in worker.ran], [MockTask]*N)

        self.mgr.hire(worker)
        dList = []
        for null in xrange(N):
            task = MockTask(lambda x: x, ('foo',), {}, 100, None)
            # For this test, we don't care about when assignments are accepted
            self.mgr.assignment(task)
            # We only care about when they are done
            dList.append(task.d)
        d = defer.DeferredList(dList)
        d.addCallback(completed)
        return d

    def testMultipleWorkers(self):
        N = 30
        mutable = []
        workerFast = MockWorker(0.1)
        workerSlow = MockWorker(0.2)

        def checkResults(null):
            self.failUnlessEqual(len(mutable), N)
            self.failUnlessAlmostEqual(
                2*len(workerSlow.ran), len(workerFast.ran))
            
        self.mgr.hire(workerFast)
        self.mgr.hire(workerSlow)
        dList = []
        for null in xrange(N):
            task = MockTask(lambda : mutable.append(None), (), {}, 100, None)
            # For this test, we don't care about when assignments are accepted
            self.mgr.assignment(task)
            # We only care about when they are done
            dList.append(task.d)
        d = defer.DeferredList(dList)
        d.addCallback(checkResults)
        return d


class TestTaskQueueGeneric(TestCase):
    def setUp(self):
        self.queue = taskqueue.TaskQueue()

    def tearDown(self):
        return self.queue.shutdown()

    def testOneTask(self):
        worker = MockWorker(0.5)
        self.queue.attachWorker(worker)
        d = self.queue.call(lambda x: 2*x, 15)
        d.addCallback(self.failUnlessEqual, 30)
        return d

    def testOneWorker(self):
        N = 30
        mutable = []

        def checkResults(null):
            self.failUnlessEqual(len(mutable), N)
            self.failUnlessEqual(
                sum(mutable),
                sum([2*x for x in xrange(N)]))

        worker = MockWorker(0.01)
        self.queue.attachWorker(worker)
        dList = []
        for x in xrange(N):
            d = self.queue.call(lambda y: 2*y, x)
            d.addCallback(lambda result: mutable.append(result))
            dList.append(d)
        d = defer.DeferredList(dList)
        d.addCallback(checkResults)
        return d

    def testMultipleWorkers(self):
        N = 100
        mutable = []

        def checkResults(null):
            self.failUnlessEqual(len(mutable), N)
            self.failUnlessEqual(
                sum(mutable),
                sum([2*x for x in xrange(N)]))

        for runDelay in (0.05, 0.1, 0.4):
            worker = MockWorker(runDelay)
            ID = self.queue.attachWorker(worker)
            worker.ID = ID
        dList = []
        for x in xrange(N):
            d = self.queue.call(lambda y: 2*y, x)
            d.addCallback(lambda result: mutable.append(result))
            dList.append(d)
        d = defer.DeferredList(dList)
        d.addCallback(checkResults)
        return d


class TestTaskQueueThreaded(TestCase):
    def setUp(self):
        self.queue = taskqueue.TaskQueue()

    def tearDown(self):
        return self.queue.shutdown()

    def _blockingTask(self, x):
        delay = random.uniform(0.1, 1.0)
        if VERBOSE:
            print "Running %f sec. task in thread %s" % \
                  (delay, threading.currentThread().getName())
        time.sleep(delay)
        return 2*x

    def testShutdown(self):
        worker = taskqueue.ThreadWorker()

        def checkShutdown(null):
            self.failIf(worker.thread.isAlive())

        self.queue.attachWorker(worker)
        d = self.queue.call(self._blockingTask, 0)
        d.addCallback(lambda _: worker.shutdown())
        d.addCallback(checkShutdown)
        return d

    def testOneTask(self):
        worker = taskqueue.ThreadWorker()
        self.queue.attachWorker(worker)
        d = self.queue.call(self._blockingTask, 15)
        d.addCallback(self.failUnlessEqual, 30)
        return d

    def testThreadWorkers(self):
        N = 20
        mutable = []

        def gotResult(result):
            if VERBOSE:
                print "Task result: %s" % result
            mutable.append(result)

        def checkResults(null):
            self.failUnlessEqual(len(mutable), N)
            self.failUnlessEqual(
                sum(mutable),
                sum([2*x for x in xrange(N)]))

        for null in xrange(3):
            worker = taskqueue.ThreadWorker()
            self.queue.attachWorker(worker)
        dList = []
        for x in xrange(N):
            d = self.queue.call(self._blockingTask, x)
            d.addCallback(gotResult)
            dList.append(d)
        d = defer.DeferredList(dList)
        d.addCallback(checkResults)
        return d
