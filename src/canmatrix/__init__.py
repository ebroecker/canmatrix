# -*- coding: utf-8 -*-
import logging


__version__ = "1.3.2"

# Set default logging handler to avoid "No handler found" warnings in python 2.
logging.getLogger(__name__).addHandler(logging.NullHandler())

from ._canmatrix import CanMatrix, matrix_class