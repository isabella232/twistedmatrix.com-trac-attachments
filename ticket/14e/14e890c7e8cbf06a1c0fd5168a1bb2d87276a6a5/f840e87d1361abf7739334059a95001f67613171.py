import twisted.spread.banana as banana

import time, sys

b1282int = banana.b1282int

def shifting_b1282int(st):
    e = 1
    i = 0
    for char in st:
        n = ord(char)
        i += (n * e)
        e <<= 7
    return i

def caching_b1282int(st, _powersOfOneTwentyEight=[]):
    i = 0
    if len(st) > len(_powersOfOneTwentyEight):
        _powersOfOneTwentyEight.extend([
            128 ** n for n in xrange(len(_powersOfOneTwentyEight), len(st))])
    for place, char in enumerate(st):
        num = ord(char)
        i = i + (num * _powersOfOneTwentyEight[place])
    return i

print "calls / second"
print "%13s %10s %10s %10s" % ("string length", "original", "caching", "bitshifting")
n = 10000
for l in 5, 10, 11, 12, 13, 14, 15, 50, 100:
    st = ("abcdefghijklmnopqrstuvwxyz" * l)[:l]
    assert shifting_b1282int(st) == b1282int(st)
    assert caching_b1282int(st) == b1282int(st)
    assert len(st) == l
    s = time.time()
    for i in range(n):
        shifting_b1282int(st)
    e = time.time()
    shifting_calls = float(n)/(e-s)

    s = time.time()
    for i in range(n):
        b1282int(st)
    e = time.time()
    orig_calls = float(n)/(e-s)

    s = time.time()
    for i in range(n):
        caching_b1282int(st)
    e = time.time()
    caching_calls = float(n)/(e-s)

    print "%(l)13i %(orig_calls)10i %(caching_calls)10i %(shifting_calls)10i" % locals()
