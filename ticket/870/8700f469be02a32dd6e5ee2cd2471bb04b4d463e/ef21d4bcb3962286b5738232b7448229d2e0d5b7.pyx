"""
    A trivial extension that just raises an exception
"""

cdef class RaiseException:
    def __new__(self):
        raise TypeError("This class is intentionally broken")