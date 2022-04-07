from multiprocessing import Process
import socket
import time
import sys

__author__ = 'nacim'

from select import epoll, EPOLLIN, EPOLLOUT

poller = epoll()


def register(epoll_obj, file_desc, events, who):
    print("[{0}] Register fd={1} flags={2} -- fd {3}"
        .format(who, file_desc.fileno(), events, repr(file_desc)))
    epoll_obj.register(file_desc.fileno(), events)


class WorkerProcessAndConnect(Process):
    def __init__(self, pipe):
        super(WorkerProcessAndConnect, self).__init__()
        self.pipe = pipe

    def run(self):
        #poller = epoll()
        self.pipe.setblocking(0)
        register(poller, self.pipe, EPOLLIN, "WORKER 1")
        # allow WORKER 2 to start although it's not guarantee it works fine
        # for our test.
        time.sleep(1)

        # reactor like loop
        while True:
            events = poller.poll(0.9)
            if events:
                if (self.pipe.fileno(), EPOLLIN) in events:
                    #print("[{0}] Poll worker 1 received events: {1}".format(os.getpid(), events))
                    data = self.pipe.recv(10)
                    # received an order to perform a connect from parent
                    if data == b"DO CONNECT":
                        cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        cl.setblocking(0)
                        print("[{0}] XXX WORKER 1 READWRITE FD={1} XXX".format("WORKER 1", cl.fileno()))
                        register(poller, cl, EPOLLIN | EPOLLOUT, "WORKER 1")

                        cl.connect_ex(("www.google.fr", 80))
                else:
                    pass


class WorkerProcess(Process):
    def __init__(self, pipe):
        super(WorkerProcess, self).__init__()
        self.pipe = pipe

    def run(self):
        #poller = epoll()
        self.pipe.setblocking(0)
        print("[{0}] XXX WORKER 2 READ ONLY FD={1} XXX".format("WORKER 2", self.pipe.fileno()))
        register(poller, self.pipe, EPOLLIN, "WORKER 2")

        while True:
            events = poller.poll(0.9)
            if events:
                if (self.pipe.fileno(), EPOLLOUT) in events:
                    #print("[{0}] poll worker 2 events: {1}".format(os.getpid(), events))
                    print("[{0}] XXX this should not happen (events={1})XXX".format("WORKER 2", events))
                    sys.exit(1)


## create first worker
p1, s1 = socket.socketpair()
w1 = WorkerProcessAndConnect(s1)
w1.start()

p1.setblocking(0)
register(poller, p1, EPOLLIN | EPOLLOUT, "ROOT")


# start the second worker
# if will register s2.fileno only for reading and
# will check for EPOLLOUT event on it ==> here where the error occured.
p2, s2 = socket.socketpair()
w2 = WorkerProcess(s2)
w2.start()

p2.setblocking(0)
register(poller, p2, EPOLLIN | EPOLLOUT, "ROOT")

# main loop.
# here wi will send some command to wroker 1
# when received worker 1 will initiate some connections.
# We do this to be sure that those connection are created and registered to poll object
# after the second worker has forked, and thus, in theory it should not be seen from worker 2 context.

# number of command to send
# just to be sure we will arrives to an fd that is the same that on used in worker 2
cmd = 3
while True:
    events = poller.poll(0.9)
    if events:
        #print(events)
        if (p1.fileno(), EPOLLOUT) in events:
            #send command to worker 1, so he can create some connections
            if cmd > 0:
                p1.send(b"DO CONNECT")
            cmd -= 1
        if (p2.fileno(), EPOLLOUT) in events:
            # nothing to send
            pass
