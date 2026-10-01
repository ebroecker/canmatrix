# -*- coding: utf-8 -*-
import logging


__version__ = "1.2.0"

# Set default logging handler to avoid "No handler found" warnings in python 2.
logging.getLogger(__name__).addHandler(logging.NullHandler())

