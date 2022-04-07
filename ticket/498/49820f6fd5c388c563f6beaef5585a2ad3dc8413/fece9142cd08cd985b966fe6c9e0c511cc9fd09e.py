from twisted.trial import unittest

class TodoTest(Exception):
    pass

class ExtendedTestCase(unittest.TestCase):
    def _ebDeferTestMethod(self, f, result):
        if f.check(TodoTest):
            result.addExpectedFailure(self, f,
                                      unittest.makeTodo(f.getErrorMessage()))
        else:
            return unittest.TestCase._ebDeferTestMethod(self, f, result)


class MyExample(ExtendedTestCase):
    def test_foo(self):
        pass

    def test_bar(self):
        raise TodoTest("egads!")

    def test_baz(self):
        self.fail('badly')
