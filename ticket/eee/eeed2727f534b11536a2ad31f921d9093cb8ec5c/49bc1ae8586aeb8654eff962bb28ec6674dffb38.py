mport os,os.path
from cffi import FFI

cdp_include = '/home/vanandel/code/eol_spol_cdp/include'
rsm =  '/home/vanandel/code/eol_spol_cdp/rsm'
ffi = FFI()
txt = ""
cdef_files = ["iwrf_cdef.cffi", "iwrf_functions.cffi",]
for fname in cdef_files:
    fullname = os.path.join(os.path.dirname(__file__), fname)
    with open(fullname, 'r') as hfile:
        ffi.cdef(hfile.read())

ffi.C = ffi.dlopen(None)

class Library(object):

    def __init__(self, ffi):
        self.ffi = ffi
        self._lib = None
        
        extra_sources =[ 'iwrf_functions.c', 'swap.c', ]
        self.fullnames = []
        for f in extra_sources:
            self.fullnames.append(os.path.join(os.path.dirname(__file__), f))
            sources =['iwrf_verify.cffi',]
            
        self.txt = ""
        for fn in sources:
            fname = os.path.join(os.path.dirname(__file__), fn)
            with open(fname, 'r') as hfile:
                self.txt +=hfile.read()
        # This prevents the compile_module() from being called, the module
        # should have been compiled by setup.py
        #def _compile_module(*args, **kwargs):
            #raise RuntimeError("Cannot compile module during runtime")
        #self.ffi.verifier.compile_module = _compile_module

    def __getattr__(self, name):
        if self._lib is None:
#            self._lib = self.ffi.verifier.load_library()
            print 'iwrf_cffi.Library.__getattr__() calling self.ffi.verify for ',name
            includes = [cdp_include, rsm]
            
            self._lib = self.ffi.verify(self.txt, 
                              sources = self.fullnames, include_dirs=includes)
        else: 
            #print 'iwrf_cffi.Library.__getattr__() SKIPPING self.ffi.verify for ', name
            pass

        # redirect attribute access to the underlying lib
        return getattr(self._lib, name)

lib = Library(ffi)

