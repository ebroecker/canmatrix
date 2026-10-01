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
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix.DecodedSignal import DecodedSignal
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.Define import Define

# Frame tests
@pytest.fixture
def empty_frame():
    return Frame(name="test_frame")
    
@pytest.fixture
def some_signal():
    return Signal(name="speed", size=8, factor=1.5)


def test_frame_has_comment(empty_frame):
    empty_frame.add_comment("comm")
    assert empty_frame.comment == "comm"


def test_frame_compute_dlc():
    frame = Frame()
    frame.add_signal(Signal(start_bit=0, size=2))
    frame.add_signal(Signal(start_bit=8, size=1))
    frame.add_signal(Signal(start_bit=2, size=2))
    frame.calc_dlc()
    assert frame.size == 2

def test_frame_fit_dlc():
    frame = Frame()
    for i in range(1,9):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == i
    for i in range(9,13):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 12
    for i in range(13,17):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 16
    for i in range(17,21):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 20
    for i in range(21,25):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 24
    for i in range(25,33):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 32
    for i in range(33,49):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 48
    for i in range(49,65):
        frame.size = i
        frame.fit_dlc()
        assert frame.size == 64

def test_frame_find_unused_bits():
    frame = Frame(size=1)
    frame.add_signal(Signal(name="sig1", start_bit=0, size=3))
    frame.add_signal(Signal(name="sig2", start_bit=4, size=2))
    bit_usage = frame.get_frame_layout()
    assert bit_usage.count([]) == frame.size*8 - 3 - 2
    sig1 = frame.signal_by_name("sig1")
    sig2 = frame.signal_by_name("sig2")
    assert bit_usage == [[], [], [sig2], [sig2], [], [sig1], [sig1], [sig1]]


def test_frame_create_dummy_signals_covers_all_bits():
    frame = Frame(size=1)
    frame.add_signal(Signal(start_bit=0, size=3))
    frame.add_signal(Signal(start_bit=4, size=2))
    frame.create_dummy_signals()
    assert len(frame.signals) == 2 + 2
    assert frame.get_frame_layout().count([]) == 0


def test_frame_update_receivers():
    frame = Frame(size=1)
    frame.add_signal(Signal(start_bit=0, size=3, receivers=["GW", "Keyboard"]))
    frame.add_signal(Signal(start_bit=4, size=2, receivers=["GW", "Display"]))
    frame.update_receiver()
    assert frame.receivers == ["GW", "Keyboard", "Display"]


def test_frame_to_str():
    frame = Frame(size=1, name="tank_level")
    assert str(frame) == "tank_level"


def test_frame_is_multiplexed():
    frame = Frame(name="multiplexed_frame")
    signal = Signal(name="mx")
    signal.multiplex_setter("Multiplexor")
    frame.add_signal(signal)
    assert frame.is_multiplexed

def test_get_multiplexer():
    frame = Frame(name="multiplexed_frame")
    signal = Signal(name="mx")
    signal.multiplex_setter("Multiplexor")
    frame.add_signal(signal)
    assert frame.get_multiplexer == signal

def test_get_multiplexer_values():
    frame = Frame(name="multiplexed_frame")
    signal = Signal(name="mx")
    signal.multiplex_setter("Multiplexor")

    signal2 = Signal(name="s2")
    signal2.multiplex_setter(2)
    frame.add_signal(signal2)

    signal3 = Signal(name="s3")
    signal3.multiplex_setter(3)
    frame.add_signal(signal3)

    signal4 = Signal(name="s4")
    signal4.multiplex_setter(None)
    frame.add_signal(signal4)

    assert frame.get_signals_for_multiplexer_value(2)[0] == signal2
    assert frame.get_signals_for_multiplexer_value(2)[1] == signal4
    assert frame.get_signals_for_multiplexer_value(3)[0] == signal3
    assert frame.get_signals_for_multiplexer_value(3)[1] == signal4
    assert frame.get_signals_for_multiplexer_value(1)[0] == signal4

def test_get_multiplexer_values():
    frame = Frame(name="multiplexed_frame")
    signal = Signal(name="mx")
    signal.multiplex_setter("Multiplexor")

    signal2 = Signal(name="s2")
    signal2.multiplex_setter(2)
    frame.add_signal(signal2)

    signal3 = Signal(name="s3")
    signal3.multiplex_setter(3)
    frame.add_signal(signal3)

    signal4 = Signal(name="s4")
    signal4.multiplex_setter(None)
    frame.add_signal(signal4)

    assert frame.get_multiplexer_values == [2,3]


def test_frame_not_multiplexed():
    frame = Frame(name="not_multiplexed_frame")
    assert not frame.is_multiplexed
    frame.add_signal(Signal(name="some"))
    assert not frame.is_multiplexed

def test_frame_calc_j1939_id():
    # we have to set all j1939 properties in the __init__ otherwise the setters crash
    frame = Frame()
    frame.source = 0x22
    frame.pgn = 0xAAAA
    frame.priority = 3
    assert frame.arbitration_id.id == 0xCAAAA22

@pytest.mark.parametrize(
    'priority, pgn, source, id',
    (
        (0, 0, 0, 0),
        (1, 1, 1, 0x4000101),
        (2, 2, 2, 0x8000202),
        (3, 0xAAAA, 0x22, 0xCAAAA22),
        (0, 0x1F004, 0xEE, 0x1F004EE),
        (3, 0x1F004, 0xEE, 0xDF004EE),
        (7, 0x1FFFF, 0xFF, 0x1DFFFFFF),
        (3, 0, 0xB, 0xC00000B),
        (3, 0xEF27, 0xFD, 0xCEF27FD),
        (3, 0xFFCA, 0xFD, 0xCFFCAFD),
        (3, 0, 3, 0xC000003),
        (3, 0xF002, 3, 0xCF00203),
        (6, 0xFE4A, 3, 0x18FE4A03),
        (3, 0x103, 5, 0xC010305),
    ), )
def test_frame_j1939_id_from_components(priority, pgn, source, id):
    # we have to set all j1939 properties in the __init__ otherwise the setters crash
    frame = Frame()
    frame.source = source
    frame.pgn = pgn
    frame.priority = priority
    assert hex(frame.arbitration_id.id) == hex(id)

@pytest.mark.parametrize(
    'priority, pgn, source, id',
    (
        (0, 0, 0, 0),
        (1, 0, 1, 0x4000101),
        (2, 0, 2, 0x8000202),
        (3, 0xAA00, 0x22, 0xCAAAA22),
        (0, 0x1F004, 0xEE, 0x1F004EE),
        (3, 0x1F004, 0xEE, 0xDF004EE),
        (7, 0x1FFFF, 0xFF, 0x1DFFFFFF),
        (3, 0, 0xB, 0xC00000B),
        (3, 0xEF00, 0xFD, 0xCEF27FD),
        (3, 0xFFCA, 0xFD, 0xCFFCAFD),
        (3, 0, 3, 0xC000003),
        (3, 0xF002, 3, 0xCF00203),
        (6, 0xFE4A, 3, 0x18FE4A03),
        (3, 0x100, 5, 0xC010305),
    ), )
def test_frame_decode_j1939_id(source, pgn, priority, id):
    # we have to set all j1939 properties in the __init__ otherwise the setters crash
    frame = Frame(arbitration_id=ArbitrationId(id=id, extended=True))
    assert hex(frame.source) == hex(source)
    assert hex(frame.pgn) == hex(pgn)
    assert hex(frame.priority) == hex(priority)

def test_frame_add_transmitter(empty_frame):
    empty_frame.add_transmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_add_transmitter_no_duplicities(empty_frame):
    empty_frame.add_transmitter("BCM")
    empty_frame.add_transmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_transmitter(empty_frame):
    empty_frame.add_transmitter("MFL")
    empty_frame.add_transmitter("BCM")
    empty_frame.del_transmitter("MFL")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_wrong_transmitter_doesnt_raise(empty_frame):
    empty_frame.del_transmitter("wrong")


def test_frame_find_signal(empty_frame):
    empty_frame.add_signal(Signal("first"))
    second_signal = Signal("second")
    empty_frame.add_signal(second_signal)
    empty_frame.add_signal(Signal("third"))
    assert empty_frame.signal_by_name("second") == second_signal


def test_frame_find_missing_signal(empty_frame):
    assert empty_frame.signal_by_name("wrong") is None


def test_frame_glob_signals(empty_frame):
    audio_signal = Signal(name="front_audio_volume")
    empty_frame.add_signal(audio_signal)
    empty_frame.add_signal(Signal(name="display_dimming"))
    assert empty_frame.glob_signals("*audio*") == [audio_signal]


def test_frame_add_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "value1")
    assert empty_frame.attributes == {"attr1": "value1"}


def test_frame_del_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "value1")
    empty_frame.del_attribute("attr1")
    assert "attr1" not in empty_frame.attributes


def test_frame_del_missing_attribute_doesnt_raise(empty_frame):
    empty_frame.del_attribute("wrong")


def test_frame_is_iterable(empty_frame, some_signal):
    empty_frame.add_signal(some_signal)
    assert [s for s in empty_frame] == [some_signal]


def test_frame_find_mandatory_attribute(empty_frame):
    assert empty_frame.attribute("arbitration_id") == empty_frame.arbitration_id


def test_frame_find_optional_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "str1")
    assert empty_frame.attribute("attr1") == "str1"


def test_frame_no_attribute(empty_frame):
    assert empty_frame.attribute("wrong") is None


def test_frame_no_attribute_with_default(empty_frame):
    assert empty_frame.attribute("wrong", default=0) == 0


def test_frame_default_attr_from_db(empty_frame):
    define = Define("INT 0 255")
    define.defaultValue = 33
    matrix = CanMatrix(frame_defines={"from_db": define})
    assert empty_frame.attribute("from_db", db=matrix, default=2) == 33
    assert empty_frame.attribute("wrong", db=matrix, default=2) == 2


def test_frame_add_signal_group(empty_frame):
    signal_a = Signal(name="A")
    signal_b = Signal(name="B")
    signal_c = Signal(name="C")
    empty_frame.signals = [signal_a, signal_b, signal_c]
    empty_frame.add_signal_group("AB", 0, ["A", "B"])
    assert empty_frame.signalGroups[0].signals == [signal_a, signal_b]


def test_frame_add_signal_group_wrong_signal(empty_frame):
    signal_a = Signal(name="A")
    empty_frame.signals = [signal_a]
    empty_frame.add_signal_group("Aw", 0, ["A", "wrong", "\t"])
    assert empty_frame.signalGroups[0].signals == [signal_a]


def test_frame_find_signal_group(empty_frame):
    empty_frame.add_signal_group("G1", 1, [])
    assert empty_frame.signal_group_by_name("G1") is not None


def test_frame_find_wrong_signal_group(empty_frame):
    empty_frame.add_signal_group("G1", 1, [])
    assert empty_frame.signal_group_by_name("wrong") is None
