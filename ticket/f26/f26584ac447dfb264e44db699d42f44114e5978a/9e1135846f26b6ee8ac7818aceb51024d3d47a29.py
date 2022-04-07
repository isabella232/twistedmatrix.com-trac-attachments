#!/usr/bin/python3

import asyncio

from twisted.internet import asyncioreactor
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.task import react


asyncioreactor.install(asyncio.get_event_loop())


def as_deferred(f):
    return Deferred.fromFuture(asyncio.ensure_future(f))


async def ag():
    yield 1
    yield 2
    await asyncio.sleep(0.1)
    yield 3


def cb(result):
    print(result)


def eb(failure):
    failure.trap(StopAsyncIteration)
    print('stop')


def _main(_):
    ag_ = ag()
    L = []
    for _ in range(5):
        n = ag_.__anext__()
        d = as_deferred(n)
        d.addCallbacks(cb, eb)
        L.append(d)
    return DeferredList(L)


react(_main)
