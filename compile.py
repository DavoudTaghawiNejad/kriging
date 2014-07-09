from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
  name = 'lowest_value',
  ext_modules=[
    Extension('lowest_values', ['lowest_values.pyx'])
    ],
  cmdclass = {'build_ext': build_ext}
)
