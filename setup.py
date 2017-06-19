#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:55:28 2017

@author: mittelberger2
"""

from distutils.core import setup
from Cython.Build import cythonize

setup(
      name = 'analyze maxima',
      ext_modules = cythonize('analyze_maxima.pyx'),
)
