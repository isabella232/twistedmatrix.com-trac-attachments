# Squiddo's python noob attempts at optimization

# original patch
def _computeAllowedMethods_orig(resource):
    allowedMethods = []
    for name in dir(resource):
        parts = name.split('_')
        if (len(parts) == 2 and parts[0] == 'render' 
            and re.match(r'[A-Z]+', parts[1])):
            allowedMethods.append(parts[1])
    return allowedMethods


# use bound methods
def _computeAllowedMethods_orig_1(resource):
    allowedMethods = []
    re_match = re.match
    allowedMethods_append = allowedMethods.append
    for name in dir(resource):
        parts = name.split('_')
        if (len(parts) == 2 and parts[0] == 'render' 
            and re_match(r'[A-Z]+', parts[1])):
            allowedMethods_append(parts[1])
    return allowedMethods


# use re directly with bound methods
def _computeAllowedMethods_orig_2(resource):
    allowedMethods = []
    re_match = re.match
    am_append = allowedMethods.append
    for name in dir(resource):
        m = re_match(RE_RENDER_METHOD, name)
        if m:
            am_append(m.group(1))
    return allowedMethods


# use re and functional approach
import re

# Regex to find 'render_FOO' methods.
RE_RENDER_METHOD = re.compile(r'^render_([A-Z]+)$')

def __find_render(method):
    m = re.match(RE_RENDER_METHOD, method)
    return m.group(1) if m else False


def _computeAllowedMethods_new(resource):
    return filter(lambda a: a, map(lambda a:__find_render(a), dir(resource)))



if __name__=='__main__':
    from timeit import Timer

    class Resource(object):
        def a_1(self): pass
        def a_2(self): pass
        def a_3(self): pass
        def a_4(self): pass
        def a_5(self): pass
        def a_6(self): pass
        def a_7(self): pass
        def a_8(self): pass
        def a_10(self): pass
        def a_11(self): pass
        def a_12(self): pass
        def a_13(self): pass
        def a_14(self): pass
        def a_15(self): pass
        def a_16(self): pass
        def a_17(self): pass
        def a_18(self): pass
        def a_1a(self): pass
        def a_1b(self): pass
        def a_1c(self): pass
        def a_1d(self): pass
        def a_1e(self): pass
        def a_1f(self): pass
        def a_1g(self): pass
        def a_1h(self): pass
        def a_1i(self): pass
        def a_1j(self): pass
        def a_1k(self): pass
        def a_1l(self): pass
        def a_1m(self): pass
        def a_1n(self): pass
        def a_1o(self): pass
        def a_1p(self): pass
        def a_1q(self): pass
        def a_1r(self): pass
        def a_1s(self): pass
        def a_1t(self): pass
        def a_1u(self): pass
        def a_1b(self): pass
        def render_HEAD(self): pass
        def render_GET(self): pass
        def render_POST(self): pass

    # code based on template from Raymond Hettinger - stupidity is my own
    setup = "from __main__ import _computeAllowedMethods_orig, _computeAllowedMethods_new, _computeAllowedMethods_orig_1, _computeAllowedMethods_orig_2, Resource"
    for func in _computeAllowedMethods_orig, _computeAllowedMethods_orig_1,_computeAllowedMethods_orig_2, _computeAllowedMethods_new:
        methods = func(Resource())
        assert(set(methods) == set(['GET', 'HEAD', 'POST']))

        stmt = '{0.__name__}(Resource())'.format(func)
        print(func.__name__, min(Timer(stmt, setup).repeat(7, 20)))

    # for i in range(10):
    #     _computeAllowedMethods_orig_1(Resource())
