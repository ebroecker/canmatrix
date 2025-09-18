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

from canmatrix.CanMatrix import CanMatrix
from canmatrix.Signal import Signal
from canmatrix.SignalGroup import SignalGroup
from canmatrix.Frame import Frame


# SignalGroup
@pytest.fixture
def the_group():
    return SignalGroup(name="TestGroup", id=1)


@pytest.fixture
def some_signal():
    return Signal(name="speed", size=8, factor=1.5)


def test_signalgroup_empty(the_group):
    assert [] == the_group.signals


def test_signalgroup_can_add(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_can_remove(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.del_signal(some_signal)
    assert len(the_group.signals) == 0


def test_signalgroup_no_duplicates(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.add_signal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_is_iterable(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert [some_signal] == [s for s in the_group]


def test_signalgroup_find_something(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert some_signal == the_group.by_name("speed")
    assert some_signal == the_group["speed"]


def test_signalgroup_find_nothing(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert the_group.by_name("wrong") is None
    with pytest.raises(KeyError):
        _ = the_group["wrong"]


def test_signalgroup_delete_nothing(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.del_signal(Signal())
    assert len(the_group.signals) == 1


#TODO: use fixture for signal
def test_encode_decode_frame():
    input_data = {'signal': decimal.Decimal('3.5')}

    s1 = Signal('signal', size=32, is_float=True)
    f1 = Frame('frame', arbitration_id=1, size=4)
    f1.add_signal(s1)

    raw_bytes = f1.encode(input_data)
    decoded_data = f1.decode(raw_bytes)

    assert decoded_data['signal'].raw_value == float(input_data['signal'])
