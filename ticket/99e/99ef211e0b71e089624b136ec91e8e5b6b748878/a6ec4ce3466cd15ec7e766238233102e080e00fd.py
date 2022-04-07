import traceback
from twisted.internet import defer, task

def clean(e):
    while e.__context__:
        if isinstance(e.__context__, (defer._DefGen_Return, StopIteration)):
            e.__context__ = None
        else:
            e = e.__context__

@defer.inlineCallbacks
def some_func(reactor):
    yield task.deferLater(reactor, 0, lambda: None)
    # This can also be a return statement because
    # the StopIteration exception will do the same
    # thing as _DefGen_Return
    defer.returnValue('hello')
    # return 'hello'

@defer.inlineCallbacks
def run(reactor):
    try:
        yield some_func(reactor)
        raise Exception('Some actual error')
    except Exception as e:
        # Without this clean the _DefGen_Return exception
        # from returnValue or the StopIteration will show up
        # as context in the traceback
        # clean(e)
        traceback.print_exc()

task.react(run)
