#!/usr/bin/env python

# python module to get MONOTONIC time, borrowed here
# http://stackoverflow.com/questions/1205722/how-do-i-get-monotonic-time-durations-in-python

__all__ = ["monotonic_time"]

import os
import ctypes

if os.name == 'posix':

    CLOCK_MONOTONIC = 1 # see <linux/time.h>

    class timespec(ctypes.Structure):
        _fields_ = [
            ('tv_sec', ctypes.c_long),
            ('tv_nsec', ctypes.c_long)
        ]

    librt = ctypes.CDLL('librt.so.1', use_errno=True)
    clock_gettime = librt.clock_gettime
    clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

    def monotonic_time():
        t = timespec()
        if clock_gettime(CLOCK_MONOTONIC, ctypes.pointer(t)) != 0:
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))
        return t.tv_sec + t.tv_nsec * 1e-9

# this is platform dependent 
else:
    raise NotImplementedError

if __name__ == "__main__":
    print monotonic_time()

