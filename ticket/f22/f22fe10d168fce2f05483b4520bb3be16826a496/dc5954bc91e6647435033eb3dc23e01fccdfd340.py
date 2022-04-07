import pygtk
pygtk.require('2.0')
import gobject

import threading, time

loop = gobject.MainLoop()

running = True

def goGoGadgetThreads():
    def theThread():
        while running:
            time.sleep(2)
            print 'poow'
    threading.Thread(target=theThread).start()

n = 5
def timedCall():
    global n
    n -= 1
    if n == 0:
        gobject.threads_init()
        goGoGadgetThreads()
    print 'woop'
    if n < -10:
        print 'bye'
        loop.quit()
    gobject.timeout_add(250, timedCall)
timedCall()

try:
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
finally:
    running = False
