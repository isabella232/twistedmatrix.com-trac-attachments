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
Priority queueing of tasks to one or more threaded or asynchronous workers.
"""

# Imports
import copy, heapq, threading, sys
from zope.interface import implements, invariant, Interface, Attribute, Invalid
from twisted.python import failure
from twisted.internet import defer, reactor, interfaces, task


class QueueRunError(Exception):
    """
    An attempt was made to dispatch tasks when the dispatcher isn't running.
    """

class ImplementationError(Exception):
    """
    There was a problem implementing the required interface.
    """

class InvariantError(Invalid):
    """
    An invariant of the IWorker provider did not meet requirements.
    """
    def __repr__(self):
        return "InvariantError(%r)" % self.args


class _Task(object):
    """
    I represent a task that has been dispatched to a queue for running with a
    given scheduling I{niceness}. I generate a C{Deferred}, accessible as an
    attribute I{d}, firing it when the task is finally run and its result is
    obtained.
    
    @ivar d: A deferred to the eventual result of the task.

    @ivar series: A hashable object identifying the series of which this task
        is a part.

    """
    def __init__(self, f, args, kw, priority, series):
        if not isinstance(args, (tuple, list)):
            raise TypeError("Second argument 'args' isn't a sequence")
        if not isinstance(kw, dict):
            raise TypeError("Third argument 'kw' isn't a dict")
        self.callTuple = (f, args, kw)
        self.priority = priority
        self.series = series
        self.d = defer.Deferred()

    def __repr__(self):
        """
        Gives me an informative string representation
        """
        func = self.callTuple[0]
        args = ", ".join([str(x) for x in self.callTuple[1]])
        kw = "".join(
            [", %s=%s" % item for item in self.callTuple[2].iteritems()])
        if func.__class__.__name__ == "function":
            funcName = func.__name__
        elif callable(func):
            funcName = "%s.%s" % (func.__class__.__name__, func.__name__)
        else:
            funcName = "<worker call> "
            args = ("%s, " % func) + args
        return "Task: %s(%s%s)" % (funcName, args, kw)

    def __cmp__(self, other):
        """
        Numeric comparisons between tasks are based on their priority, with
        higher (lower-numbered) priorities being considered \"less\" and thus
        sorted first.

        A task will always have a higher priority, i.e., be comparatively
        \"less\", than a C{None} object, which is used as a shutdown signal
        instead of a task.
        """
        if other is None:
            return -1
        return cmp(self.priority, other.priority)


class _TaskFactory(object):
    """
    I generate L{_Task} instances with the right priority setting for effective
    scheduling between tasks in one or more concurrently running task series.
    """
    def __init__(self, TaskClass=_Task):
        # Setting a non-default TaskClass is mostly for testing
        self.TaskClass = TaskClass
        self.seriesNumbers = {}

    def new(self, func, args, kw, niceness, series=None):
        """
        Call this to obtain a L{Task} instance that will run in the specified
        I{series} at a priority reflecting the specified I{niceness}.

        The equation for priority has been empirically determined as follows::

            p = k * (1 + nn**2)

        where C{k} is an iterator that increments for each new task and C{nn}
        is niceness normalized from -20...+20 to the range 0...2.

        @param func: A callable object to run as the task, the result of which
            will be sent to the callback for the deferred of the task returned
            by this method when it fires.

        @param args: A tuple containing any arguments to include in the call.

        @param kw: A dict containing any keywords to include in the call.
        
        """
        if not isinstance(niceness, int) or abs(niceness) > 20:
            raise ValueError(
                "Niceness must be an integer between -20 and +20")
        positivized = niceness + 20
        priority = self._serial(series) * (1 + (float(positivized)/10)**2)
        return self.TaskClass(func, args, kw, priority, series)
    
    def _serial(self, series):
        """
        Maintains serial numbers for tasks in one or more separate series, such
        that the numbers in each series increment independently except that any
        new series starts at a value greater than the maximum serial number
        currently found in any series.
        """
        if series not in self.seriesNumbers:
            eachSeries = [0] + self.seriesNumbers.values()
            maxCurrentSN = max(eachSeries)
            self.seriesNumbers[series] = maxCurrentSN
        self.seriesNumbers[series] += 1
        return float(self.seriesNumbers[series])
    

class IWorker(Interface):
    """
    Provided by worker objects that can have tasks assigned to them for
    processing.

    All worker objects are considered qualified to run tasks of the default
    C{None} series. To indicate that subclasses or subclass instances are
    qualified to run tasks of user-defined series in addition to the default,
    the hashable object that identifies the additional series must be listed in
    the C{cQualified} or C{iQualified} class or instance attributes,
    respectively.
        
    """
    cQualified = Attribute(
        """
        A class-attribute list containing all series for which all instances of
        the subclass are qualified to run tasks.
        """)

    iQualified = Attribute(
        """
        An instance-attribute list containing all series for which the subclass
        instance is qualified to run tasks.
        """)

    def _check_qualifications(ob):
        """
        Qualification attributes must be lists, if present.
        """
        for attrName in ('cQualified', 'iQualified'):
            x = getattr(ob, attrName, [])
            if not isinstance(x, list):
                raise InvariantError(ob)
    invariant(_check_qualifications)

    def run(task):
        """
        Adds the task represented by the specified I{task} object to the list
        of tasks pending for this worker, to be run however and whenever the
        worker sees fit.

        Make sure that any callbacks you add to the task's internal deferred
        object C{task.d} return the callback argument. Otherwise, the result of
        your task will be lost in the callback chain.

        @return: A deferred that fires when the worker is ready to be assigned
            another task.

        """

    def shutdown():
        """
        Shuts down the worker, returning a deferred that fires when the worker
        is done with all assigned tasks and will not cause any errors if the
        reactor is stopped or its object is deleted.

        The deferred returned by your implementation of this method must not
        fire until B{after} the results of all pending tasks have been
        obtained. Thus the deferred must be chained to each C{task.d} somehow.

        Make sure that any callbacks you add to the task's internal deferred
        object C{task.d} return the callback argument. Otherwise, the result of
        your task will be lost in the callback chain.
        """


class Priority(object):
    """
    I provide simple, asynchronous access to a priority heap.
    """
    def __init__(self):
        self.heap = []
        self.pendingGetCalls = []

    def shutdown(self):
        """
        Shuts down the priority heap, firing errbacks of the deferreds of any
        get requests that will not be fulfilled.
        """
        if self.pendingGetCalls:
            msg = "No more items forthcoming"
            theFailure = failure.Failure(QueueRunError(msg))
            for d in self.pendingGetCalls:
                d.errback(theFailure)
    
    def get(self):
        """
        Gets an item with the highest priority (lowest value) from the heap,
        returning a deferred that fires when the item becomes available.
        """
        if len(self.heap):
            d = defer.succeed(heapq.heappop(self.heap))
        else:
            d = defer.Deferred()
            self.pendingGetCalls.insert(0, d)
        return d
    
    def put(self, item):
        """
        Adds the supplied I{item} to the heap, firing the oldest getter
        deferred if any L{get} calls are pending.
        """
        heapq.heappush(self.heap, item)
        if len(self.pendingGetCalls):
            d = self.pendingGetCalls.pop()
            d.callback(heapq.heappop(self.heap))


class LoadAverageProducer(object):
    """
    B{Not Tested!}

    Anyone interested in using this, please feel free and send me your updates
    to C{test_taskqueue}!
    
    """
    implements(interfaces.IPushProducer)

    expMinusOne = 0.36787944117144233

    def __init__(self, loadIndicator, updateInterval=5):
        self.loadIndicator = loadIndicator
        self.updateInterval = updateInterval
        self.consumers = []
        self.looper = task.LoopingCall(self.update)

    def attachConsumer(self, consumer):
        """
        Gives me a new consumer to update.
        """
        if interfaces.IFinishableConsumer.providedBy(consumer):
            msgProto = "'%s' doesn't provide "+\
                       "twisted.internet.interfaces.IFinishableConsumer"
            raise ImplementationError(msgProto % consumer)
        consumer.registerProducer(self, False)
        self.consumers.append(consumer)

    def resumeProducing(self):
        if not hasattr(self, 'd'):
            self.d = self.looper.start(self.updateInterval)
            self.d.addCallback(lambda _: delattr(self, 'd'))

    def pauseProducing(self):
        if hasattr(self, 'd'):
            self.looper.stop()
            return self.d
        
    def stopProducing(self):
        dList = [self.pauseProducing()]
        for consumer in self.consumers:
            dList.append(defer.maybeDeferred(consumer.finish))
        return defer.DeferredList(dList)

    def update(self):
        """
        Gets the current value of the load indicator and updates my consumers
        with the current load average value derived from it.
        """
        if callable(self.loadIndicator):
            indicatorValue = self.loadIndicator()
        else:
            indicatorValue = loadIndicator
        lastLoad = getattr(self, 'lastLoad', 0)
        thisLoad = lastLoad * self.expMinusOne + \
                   indicatorValue * (1 - self.expMinusOne)
        self.lastLoad = thisLoad
        for consumer in self.consumers:
            consumer.write(thisLoad)
        

class _Assignment(object):
    """
    I represent the assignment of a single task to whichever worker object
    accepts me. Deep down, my real role is to provide something to fire the
    callback of a deferred with instead of just another deferred.

    @ivar d: A deferred that is instantiated for a given instance of me, which
        fires when a worker accepts the assigment represented by that instance.
    
    """
    # We go through a lot of these objects and they're small, so let's make
    # them cheap to build
    __slots__ = ['task', 'd']
    
    def __init__(self, task):
        self.task = task
        self.d = defer.Deferred()

    def accept(self, worker):
        """
        Called when the worker accepts the assignment, firing my
        deferred.

        @return: Another deferred that fires when the worker is ready to accept
            B{another} assignment following this one.
        
        """
        self.d.callback(None)
        return worker.run(self.task)


class _AssignmentFactory(object):
    """
    I generate L{_Assignment} instances for workers to handle particular tasks.
    """
    def __init__(self):
        self.queues = {}

    def getQueue(self, series):
        """
        Returns the assignment request queue for the specified task I{series},
        creating a new one if necessary.
        """
        if series not in self.queues:
            self.queues[series] = defer.DeferredQueue()
        return self.queues[series]

    def request(self, worker, series):
        """
        Called to request a new assignment in the specified I{series} of tasks
        for the supplied I{worker}.

        When a new assignment in the series is finally ready in the queue for
        this worker, the deferred for the assignment request will fire with an
        instance of me that has been constructed with the task to be assigned.

        If the worker is still gainfully employed when it accepts the
        assignment, and is not just wrapping up its work after having been
        fired, the worker will request another assignment when it finishes the
        task.
        """
        def accept(assignment, d_get):
            worker.assignments[series].remove(d_get)
            if isinstance(assignment, _Assignment):
                d = assignment.accept(worker)
                if worker.hired:
                    d.addCallback(lambda _: self.request(worker, series))
                return d

        queue = self.getQueue(series)
        d = queue.get()
        assignments = getattr(worker, 'assignments', {})
        assignments.setdefault(series, []).append(d)
        worker.assignments = assignments
        # The callback is added to the deferred *after* being appended to the
        # worker's assignments list for this series. That way, we know that the
        # callback will be able to remove the deferred even if the deferred
        # fires immediately due to the queue having a surplus of assignments.
        d.addCallback(accept, d)

    def new(self, task):
        """
        Creates and queues a new assignment for the supplied I{task}, returning
        a deferred that fires when the assignment has been accepted.
        """
        assignment = _Assignment(task)
        queue = self.getQueue(task.series)
        queue.put(assignment)
        return assignment.d


class WorkerManager(object):
    """
    I manage one or more providers of L{IWorker} for a particular instance of
    L{TaskQueue}.

    When a new worker is hired with my L{hire} method, I run the
    L{Assignment.request} class method to request that the worker be assigned a
    task from the queue of each task series for which it is qualified.

    When the worker finally gets the assignment, it fires the L{Assignment}
    object's internal deferred with a reference to itself. That is my cue to
    have the worker run the assigned task and request another assignment of a
    task in the same series when it's done, unless I've terminated the worker
    in the meantime.

    Each worker object maintains a dictionary of deferreds for each of its
    outstanding assignment requests so that I can cancel them if I terminate
    the worker. Then I can effectively cancel the assignment requests by firing
    the deferreds with fake, no-task assignments. See my L{terminate} method.

    @ivar workers: A C{dict} of worker objects that are currently employed by
        me, keyed by a unique integer ID code for each worker.
    
    """
    def __init__(self):
        self.workers = {}
        self.assignmentFactory = _AssignmentFactory()

    def shutdown(self):
        """
        Shutdown all my workers, then fire them, in turn.

        @return: A deferred that fires when my entire work force has been
            terminated.
        
        """
        dList = []
        for workerID in self.workers.keys():
            dList.append(self.terminate(workerID))
        return defer.DeferredList(dList)

    def hire(self, worker):
        """
        Adds a new worker to my work force.

        Makes sure that there is an assignment request queue for each task
        series for which the worker is qualified, then has the new worker
        request an initial assignment from each queue.

        @return: An integer ID uniquely identifying the worker.
        
        """
        if not IWorker.providedBy(worker):
            raise ImplementationError(
                "'%s' doesn't provide the IWorker interface" % worker)
        IWorker.validateInvariants(worker)

        worker.hired = True
        worker.assignments = {}
        qualifications = [None] +\
                         getattr(worker, 'cQualified', []) +\
                         getattr(worker, 'iQualified', [])
        for series in qualifications:
            self.assignmentFactory.request(worker, series)
        workerID = getattr(self, '_workerCounter', 0) + 1
        self._workerCounter = workerID
        self.workers[workerID] = worker
        return workerID
    
    def terminate(self, workerID):
        """
        Removes a worker from my work force, disposing of all its unfullfilled
        assignment requests and then shutting it down.
        """
        worker = self.workers.pop(workerID, None)
        if worker is None:
            return defer.succeed(None)
        worker.hired = False
        for dList in getattr(worker, 'assignments', {}).values():
            for d in dList:
                if not d.called:
                    d.callback(None)
        return worker.shutdown()
    
    def assignment(self, task):
        """
        Generates a new assignment for the supplied I{task}.

        If the worker that runs the task is still working for me when it
        becomes ready for another task following this one, an assignment
        request will be entered for it to obtain another task of the same
        series.

        @return: A deferred that fires when the task has been assigned to a
            worker and it has accepted the assignment.
            
        """
        return self.assignmentFactory.new(task)


class TaskQueue(object):
    """
    I am a task queue for dispatching arbitrary callables to be run by one or
    more worker objects.

    You can construct me with one or more workers, or you can attach them later
    with L{attachWorker}, in which you'll receive an ID that you can use to
    detach the worker.

    """
    def __init__(self, *args):
        self._sessionAttributeNames = []
        self._taskFactory = _TaskFactory()
        self._mgr = WorkerManager()
        self._heap = Priority()
        self._loadAverageProducer = LoadAverageProducer(self._heap.heap)
        for worker in args:
            self.attachWorker(worker)
        self._startup()

    def __setattr__(self, name, value):
        """
        Registers externally set, session-specific attributes so that they can
        be wiped out when I am shut down.
        """
        if not name.startswith('_') and \
               name not in self._sessionAttributeNames:
            self._sessionAttributeNames.append(name)
        object.__setattr__(self, name, value)

    def _startup(self):
        """
        Starts up a L{defer.deferredGenerator} that runs the queue. This method
        can only be run once, by the constructor upon instantiation.
        """
        def runner():
            while True:
                wfd = defer.waitForDeferred(self._heap.get())
                yield wfd
                task = wfd.getResult()
                if task is None:
                    return
                wfd = defer.waitForDeferred(self._mgr.assignment(task))
                yield wfd

        if hasattr(self, '_alreadyStarted'):
            raise QueueRunError("Startup only occurs upon instantiation")
        self._alreadyStarted = True
        self._d = defer.deferredGenerator(runner)()
        self._triggerID = reactor.addSystemEventTrigger(
            'before', 'shutdown', self.shutdown)
        self._d.addCallback(lambda _: self._mgr.shutdown())
        self._d.addCallback(lambda _: self._heap.shutdown())

    def isRunning(self):
        """
        Returns C{True} if the queue is running, C{False} otherwise.
        """
        return hasattr(self, '_triggerID')
    
    def shutdown(self):
        """
        Initiates a shutdown of the queue by putting a lowest-possible priority
        C{None} object onto the priority heap instead of a task.

        @return: A deferred that fires when the queue has been flushed of all
            pending tasks and all the workers have shut down.
        
        """
        def cleanup(null):
            for attrName in self._sessionAttributeNames:
                if hasattr(self, attrName):
                    object.__delattr__(self, attrName)
            if hasattr(self, '_triggerID'):
                reactor.removeSystemEventTrigger(self._triggerID)
                del self._triggerID
        
        if self.isRunning():
            self._heap.put(None)
            d = self._d
        else:
            d = defer.succeed(None)
        d.addCallback(cleanup)
        return d

    def attachWorker(self, worker):
        """
        Registers a new provider of L{IWorker} for working on tasks from the
        queue, returning an integer ID that uniquely identifies the worker.

        See L{WorkerManager.hire}.
        """
        return self._mgr.hire(worker)

    def detachWorker(self, workerID):
        """
        Detaches and terminates the worker specified by the supplied
        I{workerID}.

        See L{WorkerManager.terminate}.
        """
        return self._mgr.terminate(workerID)
    
    def call(self, func, *args, **kw):
        """
        Puts a call to I{func} with any supplied arguments and keywords into
        the pipeline, returning a deferred to the eventual result of the call
        when it is eventually pulled from the pipeline and run.

        Scheduling of the call is impacted by the I{niceness} keyword that can
        be included in addition to any keywords for the call. As with UNIX
        niceness, the value should be an integer where 0 is normal scheduling,
        negative numbers are higher priority, and positive numbers are lower
        priority.

        Tasks in a series of tasks all having niceness N+10 are dequeued and
        run at approximately half the rate of tasks in another series with
        niceness N.
        
        @keyword niceness: Scheduling niceness, an integer between -20 and 20,
            with lower numbers having higher scheduling priority as in UNIX
            C{nice} and C{renice}.

        @keyword series: A hashable object uniquely identifying a series for
            this task. Tasks of multiple different series will be run with
            somewhat concurrent scheduling between the series even if they are
            dumped into the queue in big batches, whereas tasks within a single
            series will always run in sequence (except for niceness
            adjustments).

        @keyword doNext: Set C{True} to assign highest possible priority, even
            higher than a deeply queued task with niceness = -20.          

        @keyword doLast: Set C{True} to assign priority so low that any
            other-priority task gets run before this one, no matter how long
            this task has been queued up.
        
        """
        if not self.isRunning():
            raise QueueRunError(
                "Cannot call after the queue has been shut down")
        niceness = kw.pop('niceness', 0)
        series = kw.pop('series', None)
        task = self._taskFactory.new(func, args, kw, niceness, series)
        if kw.pop('doNext', False):
            task.priority = -1000000
        elif kw.pop('doLast', False):
            task.priority = 1000000
        self._heap.put(task)
        return task.d

    def loadAverage(self, consumer):
        """
        Registers I{consumer} to receive updates on the current queue load
        average.
        """
        self._loadAverageProducer.attachConsumer(consumer)


#--- Implementation of a thread queue follows ---------------------------------

class ThreadWorker:
    """
    I implement an L{IWorker} that runs tasks in a dedicated worker thread.
    """
    implements(IWorker)

    def __init__(self):
        self.event = threading.Event()
        self.thread = threading.Thread(target=self._loop)
        self.thread.start()

    def _loop(self):
        """
        Runs a loop in a dedicated thread that waits for new tasks. The loop
        exits when a C{None} object is supplied as a task.
        """
        while True:
            # Wait here on the threading.Event object
            self.event.wait()
            task = self.task
            if task is None:
                break
            # Ready for the task attribute to be set to another task object
            self.event.clear()
            reactor.callFromThread(self.d.callback, None)
            f, args, kw = task.callTuple
            try:
                result = f(*args, **kw)
            except Exception, e:
                reactor.callFromThread(task.d.errback, failure.Failure(e))
            else:
                reactor.callFromThread(task.d.callback, result)
        # Broken out of loop, ready for the thread to end
        reactor.callFromThread(self.d.callback, None)

    def run(self, task):
        """
        See L{IWorker.run}. Starts a thread for this worker if one not started
        already, along with a L{threading.Event} object for cross-thread
        signaling.
        """
        if hasattr(self, 'd') and not self.d.called:
            raise ImplementationError(
                "Task Loop not ready to deal with a task now")
        self.d = defer.Deferred()
        self.task = task
        self.event.set()
        return self.d
    
    def shutdown(self):
        """
        See L{IWorker.shutdown}. The returned deferred fires when the task
        loop has ended and its thread terminated.
        """
        if getattr(self, 'task', None) is None:
            return defer.succeed(None)
        else:
            d = defer.Deferred()
            if hasattr(self, 'd') and not self.d.called:
                d.addCallback(lambda _: self.shutdown())
                self.d.chainDeferred(d)
            else:
                d.addCallback(lambda _: self.thread.join())
                self.d = d
                self.task = None
                self.event.set()
            return d


class ThreadQueue(TaskQueue):
    """
    I am a task queue for dispatching arbitrary callables to be run by workers
    from a pool of I{N} worker threads, the number I{N} being specified as the
    sole argument of my constructor.
    """
    def __init__(self, N):
        TaskQueue.__init__(self)
        for null in xrange(N):
            worker = ThreadWorker()
            self.attachWorker(worker)


def deferToOneThread(func, *args, **kw):
    """
    Calls the supplied function I{func} in a dedicated thread with any supplied
    arguments or keywords.

    Scheduling of the task is impacted by the I{niceness} keyword that can be
    included in this method call. As with UNIX niceness, the value should be an
    integer where 0 is normal scheduling, negative numbers are higher priority,
    and positive numbers are lower priority. Tasks having niceness N+10 are
    dequeued and run at approximately half the rate of tasks with niceness N.
        
    @keyword niceness: Scheduling niceness, an integer between -20 and 20, with
        lower numbers having higher scheduling priority as in UNIX C{nice} and
        C{renice}.

    @return: A deferred to the eventual result of the call when it is
        eventually pulled from the single-threaded pipeline and run.
        
    """
    g = globals()
    if '_oneThreadQueue' not in g:
        g['_oneThreadQueue'] = ThreadQueue(1)
        _oneThreadQueue.startup()
    kw['series'] = None
    return _oneThreadQueue.task(func, *args, **kw)

        
        
        
