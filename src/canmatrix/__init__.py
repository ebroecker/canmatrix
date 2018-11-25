#!/usr/bin/env python

from __future__ import absolute_import
import logging

import canmatrix._version
__version__ = canmatrix._version.get_versions()['version']

import canmatrix.formats as formats
import canmatrix.cancluster as cancluster
import canmatrix.convert as convert
import canmatrix.cmcopy as cmcopy
from canmatrix.canmatrix import *

# Set default logging handler to avoid "No handler found" warnings in python 2.
logging.getLogger(__name__).addHandler(logging.NullHandler())
