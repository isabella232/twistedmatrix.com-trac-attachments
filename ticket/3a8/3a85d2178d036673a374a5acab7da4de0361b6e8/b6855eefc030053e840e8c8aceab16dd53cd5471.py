from twisted.internet import reactor, task
import threading
import time

# YMMV
length = 5
thread_count = 10

def twisted_thread():
    # queue up the stop command
    #reactor.callLater(1, reactor.stop)
    # I used this because it seems to kick-start the event loop
    t = task.LoopingCall(reactor.callLater, length, reactor.stop)
    t.start(1.0)

    reactor.run(installSignalHandlers=False)

# start twisted
twisted_loop = threading.Thread(target=twisted_thread)
twisted_loop.start()


# global status so we can record status and stop on the first failure
failed = 0

def dangerous():
    # this is something that needs to run in the twisted thread
    pass

def adding():
    global failed
    
    end = time.time() + length
    try:
        while (end > time.time()) and (not failed):
            # queue up our dangerous function - this should be thread safe
            reactor.callFromThread(dangerous)
            
    except IndexError:
        # bisect.insort often raises an IndexError if the list (in this case the
        # event list) is manipulated by two threads at once
        
        failed = 1
        
        reactor.callFromThread(reactor.stop)

threads = []

# start a pile of threads to increase the chance of an error            
for i in range(0, thread_count):
    a_thread = threading.Thread(target=adding)
    threads.append(a_thread)
    a_thread.start()

# join all the threads so we know they're done
for a_thread in threads:
    a_thread.join()
    
if failed:
    print "Failed"
else:
    print "Passed"


