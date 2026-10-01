# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# With contributions 2025, Gabriele Omodeo Vanone
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,   PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR  OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import typing
import attr

from canmatrix.types import RawValue, PhysicalValue
from canmatrix.Signal import Signal

@attr.s
class DecodedSignal(object):
    """
    Contains a decoded signal (frame decoding)

    * rawValue : rawValue (value on the bus)
    * physValue: physical Value (the scaled value)
    * namedValue: value of Valuetable
    * signal: pointer signal (object) which was decoded
    """
    raw_value = attr.ib()  # type: RawValue
    signal = attr.ib()  # type: Signal

    @property
    def phys_value(self):  # type: () -> PhysicalValue
        """
        :return: physical Value (the scaled value)
        :rtype: typing.Union[int, decimal.Decimal]
        """
        return self.signal.raw2phys(self.raw_value)

    @property
    def named_value(self):
        """
        :return: value of Valuetable
        :rtype: typing.Union[str, int, decimal.Decimal]
        """
        return self.signal.raw2phys(self.raw_value, decode_to_str=True)