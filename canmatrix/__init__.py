#!/usr/bin/env python

from __future__ import absolute_import

import canmatrix._version
__version__ = canmatrix._version.get_versions()['version']

import canmatrix.formats as formats
import canmatrix.cancluster as cancluster
import canmatrix.convert as convert
import canmatrix.copy as copy
from canmatrix.canmatrix import *
