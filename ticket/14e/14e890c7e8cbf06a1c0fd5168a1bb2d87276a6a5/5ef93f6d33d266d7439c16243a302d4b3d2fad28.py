#!/usr/bin/python
from time import clock
from twisted.spread.banana import b1282int as b1282int_orig

ITERATIONS=100000

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

def timeFunc(fn, *args, **kwargs):
	start = clock()
	for i in xrange(ITERATIONS):
		fn(*args, **kwargs)

	return ITERATIONS, (clock() - start)

funcs = {
		"original": b1282int_orig,
		"caching": caching_b1282int,
		"bitshifting": shifting_b1282int,
	}

for length in (1, 5, 10, 50, 100):
	for desc, func in funcs.items():
		iterations, elapsed = timeFunc(func, "\xff" * length)
		print "Function %15r, %3d byte string: %10d cps" % (
				desc, length, iterations / elapsed)
