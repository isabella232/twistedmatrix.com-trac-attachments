#!/usr/bin/env python
import time
import ctypes

from twisted.python.runtime import platform

if platform.isMacOSX():
    # see http://developer.apple.com/library/mac/#qa/qa1398/_index.html
    libSystem = ctypes.CDLL('libSystem.dylib', use_errno=True)
    CoreServices = ctypes.CDLL(
        '/System/Library/Frameworks/CoreServices.framework/CoreServices',
        use_errno=True)
    mach_absolute_time = libSystem.mach_absolute_time
    mach_absolute_time.restype = ctypes.c_uint64
    AbsoluteToNanoseconds = CoreServices.AbsoluteToNanoseconds
    AbsoluteToNanoseconds.restype = ctypes.c_uint64
    AbsoluteToNanoseconds.argtypes = [ctypes.c_uint64]

    def monotonicTimeOSX():
        return AbsoluteToNanoseconds(mach_absolute_time()) * 1e-9
    monotonicTime = monotonicTimeOSX

elif platform.isLinux():
    # see http://stackoverflow.com/questions/1205722/how-do-i-get-monotonic-time-durations-in-python
    import os
    CLOCK_MONOTONIC = 1 # see <linux/time.h>

    class timespec(ctypes.Structure):
        _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]

    librt = ctypes.CDLL('librt.so.1', use_errno=True)
    clock_gettime = librt.clock_gettime
    clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

    def monotonicTimeLinux():
        t = timespec()
        if clock_gettime(CLOCK_MONOTONIC, ctypes.pointer(t)) != 0:
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))
        return t.tv_sec + t.tv_nsec * 1e-9
    monotonicTime = monotonicTimeLinux


if __name__ == "__main__":
    startMonotonic = monotonicTime()
    startWallclock = time.time()
    print 'Quick, change your clock!'
    time.sleep(7.2)
    endMonotonic = monotonicTime()
    endWallclock = time.time()
    print endMonotonic - startMonotonic
    print endWallclock - startWallclock

