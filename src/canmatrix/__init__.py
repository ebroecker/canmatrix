# -*- coding: utf-8 -*-
import logging

import canmatrix.formats as formats
import canmatrix.cancluster as cancluster

from canmatrix.canmatrix import (
    Ecu,
    Signal,
    SignalGroup,
    DecodedSignal,
    ArbitrationId,
    Frame,
    Define,
    CanMatrix,
)

from canmatrix.canmatrix import (
    StartbitLowerZero,
    EncodingComplexMultiplexed,
    MissingMuxSignal,
    DecodingComplexMultiplexed,
    DecodingFrameLength,
    ArbitrationIdOutOfRange
)

# todo remove this later
from canmatrix.canmatrix import *

__version__ = "1.2.0"

# Set default logging handler to avoid "No handler found" warnings in python 2.
logging.getLogger(__name__).addHandler(logging.NullHandler())

