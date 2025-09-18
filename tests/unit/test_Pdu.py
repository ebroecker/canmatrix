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

from canmatrix.Pdu import Pdu
from canmatrix.Signal import Signal

@pytest.fixture
def test_odo_signal():
    return Signal(name="odometer", size=8, factor=1)

@pytest.fixture
def test_wheelspeed_signal():
    return Signal(name="wheel speed", size=2, factor=5)

def test_pdu_default_creation():
    pdu = Pdu()
    assert pdu.name is ""
    assert pdu.size is 0
    assert pdu.id is 0
    assert pdu.triggering_name is ""
    assert pdu.pdu_type is ""
    assert pdu.port_type is ""
    assert pdu.signals == []            # "is" won't match lists
    assert pdu.signalGroups == []       # "is" won't match lists
    assert pdu.cycle_time is 0
    
def test_pdu_custom_creation():
    pdu = Pdu(name="testPdu", size=4, id=0xABCD, triggering_name="trigger", pdu_type="type", port_type="port", signals=[test_odo_signal,test_wheelspeed_signal] , signalGroups=['C'], cycle_time=350)
    assert pdu.name is "testPdu"
    assert pdu.size is 4
    assert pdu.id is 0xABCD
    assert pdu.triggering_name is "trigger"
    assert pdu.pdu_type is "type"
    assert pdu.port_type is "port"
    assert pdu.signals == [test_odo_signal,test_wheelspeed_signal]            # "is" won't match lists
    assert pdu.signalGroups == ['C']           # "is" won't match lists
    assert pdu.cycle_time is 350
    
def test_pdu_add_signal():
    pdu = Pdu()
    pdu.add_signal(test_odo_signal)
    assert len(pdu.signals) != 0
    assert test_odo_signal in pdu.signals

def test_pdu_get_signal_by_name():
    pdu = Pdu()
    pdu.add_signal(test_odo_signal)
    pdu.add_signal(test_wheelspeed_signal)
    assert pdu.signal_by_name("odometer") == test_odo_signal
