from twisted.internet import task
from twisted.trial.unittest import TestCase

class ClockSortingTestCase(TestCase):

    def test_calllater_re_sorts_pending_calls(self):
        result = []
        expected = [('b', 2.0), ('a', 3.0)]
        clock = task.Clock()
        logtime = lambda n: result.append((n, clock.seconds()))

        call_a = clock.callLater(1.0, logtime, "a")
        call_a.reset(3.0)
        call_b = clock.callLater(2.0, logtime, "b")

        clock.pump([1]*3)
        self.assertEqual(result, expected)

    def test_delayedcall_reset_re_sorts_pending_calls(self):
        result = []
        expected = [('b', 2.0), ('a', 3.0)]
        clock = task.Clock()
        logtime = lambda n: result.append((n, clock.seconds()))

        call_a = clock.callLater(1.0, logtime, "a")
        call_b = clock.callLater(2.0, logtime, "b")
        call_a.reset(3.0)

        clock.pump([1]*3)
        self.assertEqual(result, expected)
