from distutils.core import setup
from distutils.extension import Extension
try:
    from Pyrex.Distutils import build_ext
except ImportError:
    from Cython.Distutils import build_ext


raiser = Extension(
    "raiser", ["raiser.pyx"],
)

setup(
  name = "raiser",
  description = "trivial raising of exceptions",
  ext_modules= [raiser],
  cmdclass = {'build_ext': build_ext}
)