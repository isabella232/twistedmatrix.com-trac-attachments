from twisted.internet import reactor
import sys, os, random, hotshot
from hotshot import stats

global calls
calls = []

def modify_call(delayed_call_nr):
    global calls

    delayed_call = calls[delayed_call_nr]
    delay        = random.randint(0,5)

    choice = random.randint(1,10)
    if choice == 1:
        delayed_call.reset(delay)
    elif choice == 2:
        delayed_call.reset(delayed_call.getTime()+delay)
    elif choice in (3,4,5):
        delayed_call.delay(delay)
    else:
        delayed_call.cancel()
        calls[delayed_call_nr] = reactor.callLater(random.randint(1,10), chooser, delayed_call_nr)

def chooser(position):
    global calls

    calls[position] = reactor.callLater(random.randint(1,10), chooser, position)

    # reschedule or cancel one of the calls
    delayed_call_nr = random.randint(1, len(calls)) - 1
    modify_call(delayed_call_nr)


def prepare_test(count):
    global calls
    calls = []
    for i in range(count):
        calls.append( reactor.callLater(random.randint(0,10), chooser, i) )


def profile_reactor(profiling_time, callcount):
    prepare_test(callcount)
    reactor.callLater(profiling_time, reactor.stop)

    prof_file = '%s-profile.%04d.log' % (os.tempnam(), profiling_time)
    profiler = hotshot.Profile(prof_file, 0, 0)

    sys.stderr.write("\nProfiler run for %d calls started...\n" % callcount)

    profiler.runcall(reactor.run)
    profiler.close()

    sys.stderr.write("\nProfiler run for %d calls terminated.\n" % callcount)

    st = stats.load(prof_file)
    st.strip_dirs()

    print
    print "Times for %d calls:" % callcount
    print

    st.sort_stats('time', 'calls')
    st.print_stats()

    os.unlink(prof_file)


profiling_time = 60

stat_file = open('ReactorTimeBenchmark.%03dsec.stats'%profiling_time, 'w')
sys.stdout = stat_file

for callcount in (100,1000,3000,6000,10000):
    profile_reactor(profiling_time, callcount)

    calls = []

    for cl in reactor.getDelayedCalls():
        try:
            cl.cancel()
        except:
            pass

    #reactor.callLater(1, reactor.stop)
    #reactor.run()

sys.stdout = sys.__stdout__
stat_file.close()
