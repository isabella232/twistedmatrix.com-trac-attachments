from twisted.python.failure import Failure


def _extractResult(testCase, d):
    """
    Extract the result from a Deferred that has fired or failed already.

    @type  testCase: L{twisted.trial.unittest.TestCase}
    @param testCase: The currently running test case.

    @type  d: L{twisted.internet.defer.Deferred}
    @param d: The deferred to test.
    """
    results = []
    def _cb(result):
        results.append(result)
    d.addBoth(_cb)
    if len(results) == 0:
        testCase.fail('%r has not fired yet' % (d,))
    [result] = results
    return result


def assertFired(testCase, d):
    """
    Return the value a Deferred has fired with, or fail.

    @type  testCase: L{twisted.trial.unittest.TestCase}
    @param testCase: The currently running test case.

    @type  d: L{twisted.internet.defer.Deferred}
    @param d: The deferred to test.

    @returns: The result, if there is one.
    """
    result = _extractResult(testCase, d)
    if isinstance(result, Failure):
        result.raiseException()
    return result


def assertFailed(testCase, d, *exc):
    """
    Assert that a deferred has failed with one of the given types, or fail.

    @type  testCase: L{twisted.trial.unittest.TestCase}
    @param testCase: The currently running test case.

    @type  d: L{twisted.internet.defer.Deferred}
    @param d: The deferred to test.

    @param *exc: The expected failure types.

    @returns: The matching failure.
    @rtype: L{twisted.python.failure.Failure}
    """
    result = _extractResult(testCase, d)
    if not isinstance(result, Failure):
        testcase.assertIsInstance(result, Failure, 'Received unexpected success')
    result.trap(*exc)
    return result