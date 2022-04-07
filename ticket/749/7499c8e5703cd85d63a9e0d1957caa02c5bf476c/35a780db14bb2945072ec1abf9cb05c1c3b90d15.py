from twisted.python.util import slowStringCompare

import time

LEN = 16

class B(object):
    def __init__(self):
        self.target = 'a'*LEN
        self.goodguess = 'a'*LEN
        self.baadguess = 'b'*LEN

    def time_guess(self, guess, cmpfunc, ITERS=2000):
        """ On my Macbook Pro 5,3 I have to do it 2000 times over in
        order to make it take long enough that we're able to detect it
        with our somewhat imprecise "time.time()"-based
        measurement. If your system has an even less precise or less
        accurate clock you may need to increase ITERS.

        Return the number of seconds as a float to do ITERS
        comparisons using cmpfunc between self.target and guess.
        """
        start = time.time()
        for i in range(ITERS):
            cmpfunc(self.target, guess)
        stop = time.time()
        return stop-start

    def time_guess_many_times(self, guess, cmpfunc, iters):
        """
        Measure many times in a row in order to get some assurance
        that the test isn't accidentally flagging it as a real timing
        difference when the times are actually taken from the same
        random distribution.

        Return the min and the max from executing time_guess() ITERS
        times.
        """
        x = self.time_guess(guess, cmpfunc)
        mini = x
        maxi = x
        for i in range(ITERS):
            x = self.time_guess(guess, cmpfunc)
            if x < mini:
                mini = x
            if x > maxi:
                maxi = x
        return (mini, maxi)

    def test_timing_leak(self, cmpfunc):
        mm_good_guess = self.time_guess_many_times(self.goodguess, cmpfunc, iters=20)
        mm_bad_guess = self.time_guess_many_times(self.badguess, cmpfunc, iters=20)

        # Note that even if cmpfunc takes exactly the same random
        # distribution for 2000 good guesses and 2000 bad guesses,
        # there is still a chance that the slowest goodguess might
        # still be slower than the fastest badguess. I'm not sure, but
        # I think that chance ought to be 1 in 2^40, because
        # if... uh... no wait I don't understand this.
