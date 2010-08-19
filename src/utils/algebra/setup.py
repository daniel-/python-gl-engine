# -*- coding: UTF-8 -*-
'''
Created on 03.08.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy

ext_modules = [
    Extension("frustum"
        , ["frustum.pyx"]
        , include_dirs=[numpy.get_include()]
        #, extra_compile_args = ["-O3", "-Wall"]
        #, extra_link_args = ['-g']
        #, libraries = ["dv",]
    ),
    Extension("vector"
        , ["vector.pyx"]
        , include_dirs=[numpy.get_include()]
        #, extra_compile_args = ["-O3", "-Wall"]
        #, extra_link_args = ['-g']
        #, libraries = ["dv",]
    ),
    Extension("matrix44"
        , ["matrix44.pyx"]
        , include_dirs=[numpy.get_include()]
        #, extra_compile_args = ["-O3", "-Wall"]
        #, extra_link_args = ['-g']
        #, libraries = ["dv",]
    )
]

setup(
    name = 'algebra',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)
