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


import decimal

import pytest
from builtins import *


from canmatrix.ArbitrationId import ArbitrationId




def test_Arbitration_id():
    id_standard = ArbitrationId(id=0x1, extended=False)
    id_extended = ArbitrationId(id=0x1, extended=True)
    id_unknown = ArbitrationId(id=0x1, extended=None)  # Defaults to True

    id_from_int_standard = ArbitrationId.from_compound_integer(1)
    id_from_int_extended = ArbitrationId.from_compound_integer(1 | 1 << 31)

    assert id_standard.to_compound_integer() == 1
    assert id_extended.to_compound_integer() == (1 | 1 << 31)

    assert id_standard.id == 1
    assert id_extended.id == 1
    assert id_unknown.id == 1
    assert id_standard != id_extended
    assert id_standard != id_unknown
    assert id_extended == id_unknown
    assert id_from_int_standard == id_standard
    assert id_from_int_standard != id_extended
    assert id_from_int_extended == id_extended
    assert id_from_int_extended != id_standard

# J1939CanId tests
def test_canid_parse_values():
    can_id = ArbitrationId(id=0x01ABCD02, extended=True)
    assert can_id.j1939_source == 0x02
    assert can_id.j1939_destination == 0xcd
    assert can_id.j1939_pgn == 0x1AB00
    assert can_id.j1939_destination == 0xCD
    assert can_id.j1939_priority == 0
    assert can_id.j1939_tuple == (0xCD, 0x1AB00, 2)


def test_canid_repr():
    can_id = ArbitrationId(id=0x01ABCD02, extended=True)
    assert can_id.j1939_str == "DA:0xCD PGN:0x1AB00 SA:0x02"



