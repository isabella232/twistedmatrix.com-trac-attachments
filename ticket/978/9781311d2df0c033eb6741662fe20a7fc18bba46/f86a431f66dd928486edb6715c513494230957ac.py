from __future__ import print_function

from os import (
    fork,
    waitpid,
)
from time import (
    sleep,
    time,
)

from twisted.python import lockfile


lock = lockfile.FilesystemLock("foo")
start = time()


def now():
    return int(1000 * (time() - start))


def log(*message):
    print("%4d:" % now(), *message)


def forkfunc(func):
    pid = fork()
    if pid == 0:
        func()
        raise AssertionError(
            func.__name__ + " should have exited")
    else:
        return pid


def waitfor(pid, name):
    _, status = waitpid(pid, 0)
    if status == 0:
        log(name, "has exited okay")
    else:
        log(name, "has exited NON-ZERO")


def p1():
    # Starts, takes lock, exits. Does NOT release lock.
    if lock.lock():
        log("p1 has the lock")
        raise SystemExit(0)
    else:
        raise SystemExit(1)


def p2():
    # Starts, tries to take lock, finds that lock is stale, attempts to clean
    # lock but is delayed by 1 second, finally gets lock, sleeps for 1 second,
    # then releases lock.
    rmlink = lockfile.rmlink

    def rmlink_delayed(path):
        sleep(1)  # This is when the race happens.
        rmlink(path)  # Remove the link as usual.
        lockfile.rmlink = rmlink  # Only sleep once.

    lockfile.rmlink = rmlink_delayed

    if lock.lock():
        log("p2 has the lock")
        sleep(1)  # Try removing this; p3's unlock will fail with ENOENT.
        log("p2 will release the lock...")
        lock.unlock()
        log("p2 has released the lock")
        raise SystemExit(0)
    else:
        raise SystemExit(1)


def p3():
    # Starts, takes the lock, sleeps for 1 second, then releases lock.
    if lock.lock():
        log("p3 has the lock")
        sleep(1)
        log("p3 will release the lock...")
        lock.unlock()
        log("p3 has released the lock")
        raise SystemExit(0)
    else:
        raise SystemExit(1)


# Fork p1 and wait for it to exit.
waitfor(forkfunc(p1), "p1")

# Fork p2. This should notice that the lock is stale and attempt to remove it.
# However, we've inserted a 1 second sleep at the top of `rmlink`. When it
# wakes up it will remove the lock, not realising that it is now clobbering a
# fresh lock created by p3.
p2pid = forkfunc(p2)

# Wait 500ms to bring us into the middle of p2's sleep.
sleep(0.500)

# Fork p3. This should also notice that the lock is stale and attempt to
# remove it. There's no sleep in `rmlink` here so this will remove the lock
# right away. As this is running 500ms after the start of p2, during p2's
# sleep, it will remove the stale lock and replace it with a fresh lock before
# p2 wakes up.
p3pid = forkfunc(p3)

# Wait for p2 and p3 to exit; p3 ought to exit first.
waitfor(p3pid, "p3")
waitfor(p2pid, "p2")
