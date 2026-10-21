# -*- coding: utf-8 -*-
import logging


__version__ = "1.3.3"

# Set default logging handler to avoid "No handler found" warnings in python 2.
logging.getLogger(__name__).addHandler(logging.NullHandler())

from ._canmatrix import CanMatrix, matrix_class
from .ArbitrationId import ArbitrationId
from .DecodedSignal import DecodedSignal
from .Define import Define
from .Ecu import Ecu
from .Endpoint import Endpoint
from .Frame import Frame
from .Pdu import Pdu
from .Signal import Signal
from .SignalGroup import SignalGroup
from .exceptions import (
    ExceptionTemplate,
    StartbitLowerZero,
    EncodingComplexMultiplexed,
    MissingMuxSignal,
    DecodingComplexMultiplexed,
    DecodingFrameLength,
    ArbitrationIdOutOfRange,
    J1939NeedsExtendedIdentifier,
    DecodingContainerPdu,
    EncodingContainerPdu,
)

# keep 1.2 behavior: submodules usable via the package namespace
from . import cancluster, formats  # noqa: F401
