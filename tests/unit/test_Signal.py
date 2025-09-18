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
from canmatrix.Define import Define

@pytest.fixture
def some_signal():
    return Signal(name="speed", size=8, factor=1.5)

def test_encode_signal():
    s1 = Signal('signal', size=8)
    assert s1.phys2raw() == 0
    assert s1.phys2raw(1) == 1
    assert s1.phys2raw(s1.max) == 127
    assert s1.phys2raw(s1.min) == -128

    s2 = Signal('signal', size=10, is_signed=False)
    assert s2.phys2raw() == 0
    assert s2.phys2raw(10) == 10
    assert s2.phys2raw(s2.max) == 1023
    assert s2.phys2raw(s2.min) == 0

    s3 = Signal('signal', size=8, factor=2)
    assert s3.phys2raw() == 0
    assert s3.phys2raw(10) == 5
    assert s3.phys2raw(s3.max) == 127
    assert s3.phys2raw(s3.min) == -128

    s4 = Signal('signal', size=8, is_signed=False, factor=5)
    assert s4.phys2raw() == 0
    assert s4.phys2raw(10) == 2
    assert s4.phys2raw(s4.max) == 255
    assert s4.phys2raw(s4.min) == 0

    s5 = Signal('signal', size=8, offset=2)
    assert s5.phys2raw() == -2
    assert s5.phys2raw(10) == 8
    assert s5.phys2raw(s5.max) == 127
    assert s5.phys2raw(s5.min) == -128

    s6 = Signal('signal', size=8, is_signed=False, offset=5)
    assert s6.phys2raw() == 0
    assert s6.phys2raw(10) == 5
    assert s6.phys2raw(s6.max) == 255
    assert s6.phys2raw(s6.min) == 0

    s7 = Signal('signal', size=8, initial_value=5)
    assert s7.phys2raw() == 5

    s8 = Signal('signal', size=8, is_signed=False, offset=5, initial_value=5)
    assert s8.phys2raw() == 0

    s9 = Signal('signal', size=16, is_signed=False, factor='0.001')
    assert s9.phys2raw() == 0
    assert s9.phys2raw(s9.max) == 65535
    assert s9.phys2raw(s9.min) == 0
    assert s9.phys2raw(decimal.Decimal('50.123')) == 50123

    s10 = Signal('signal', size=8, is_signed=False, factor='0.00005')
    assert s10.phys2raw() == 0
    assert s10.phys2raw(s10.max) == 255
    assert s10.phys2raw(s10.min) == 0
    assert s10.phys2raw(decimal.Decimal('0.005')) == 100
    assert s10.phys2raw(decimal.Decimal('0.003')) == 60
    
def test_decode_signal():
    s1 = Signal('signal', size=8)
    assert s1.raw2phys(1) == 1
    assert s1.raw2phys(127) == s1.max
    assert s1.raw2phys(-128) == s1.min

    s2 = Signal('signal', size=10, is_signed=False)
    assert s2.raw2phys(10) == 10
    assert s2.raw2phys(s2.max) == 1023
    assert s2.raw2phys(s2.min) == 0

    s3 = Signal('signal', size=8, factor=2)
    assert s3.raw2phys(5) == 10
    assert s3.raw2phys(127) == s3.max
    assert s3.raw2phys(-128) == s3.min

    s4 = Signal('signal', size=8, is_signed=False, factor=5)
    assert s4.raw2phys(2) == 10
    assert s4.raw2phys(255) == s4.max
    assert s4.raw2phys(0) == s4.min

    s5 = Signal('signal', size=8, offset=2)
    assert s5.raw2phys(8) == 10
    assert s5.raw2phys(127) == s5.max
    assert s5.raw2phys(-128) == s5.min

    s6 = Signal('signal', size=8, is_signed=False, offset=5)
    assert s6.raw2phys(5) == 10
    assert s6.raw2phys(255) == s6.max
    assert s6.raw2phys(0) == s6.min

    s7 = Signal('signal', size=16, is_signed=False, factor='0.001')
    assert s7.raw2phys(65535) == s7.max
    assert s7.raw2phys(0) == s7.min
    assert s7.raw2phys(50123) == decimal.Decimal('50.123')

    s8 = Signal('signal', size=8, is_signed=False, factor='0.00005')
    assert s8.raw2phys(255) == s8.max
    assert s8.raw2phys(0) == s8.min
    assert s8.raw2phys(1) == decimal.Decimal('0.00005')
    assert s8.raw2phys(2) == decimal.Decimal('0.0001')
    assert s8.raw2phys(3) == decimal.Decimal('0.00015')
    
 # Signal (generic functions)
def test_signal_has_comment(some_signal):
    comment = "comment01"
    some_signal.add_comment(comment)
    assert some_signal.comment == comment


def test_signal_find_mandatory_attribute(some_signal):
    assert some_signal.attribute("is_float") == some_signal.is_float


def test_signal_find_optional_attribute(some_signal):
    some_signal.add_attribute("attr1", 255)
    assert some_signal.attribute("attr1") == '255'


def test_signal_no_attribute(some_signal):
    assert some_signal.attribute("wrong") is None


def test_signal_no_attribute_with_default(some_signal):
    assert some_signal.attribute("wrong", default=0) == 0


def test_signal_default_attr_from_db(some_signal):
    define = Define("INT 0 255")
    define.defaultValue = 33
    matrix = CanMatrix(signal_defines={"from_db": define})
    assert some_signal.attribute("from_db", db=matrix, default=2) == 33
    assert some_signal.attribute("wrong", db=matrix, default=2) == 2


def test_signal_no_duplicate_receiver(some_signal):
    some_signal.add_receiver("GW01")
    some_signal.add_receiver("GW01")
    assert some_signal.receivers == ["GW01"]


def test_signal_delete_receiver(some_signal):
    some_signal.add_receiver("GW01")
    some_signal.add_receiver("ESP")
    some_signal.del_receiver("GW01")
    assert some_signal.receivers == ["ESP"]


def test_signal_delete_wrong_receiver_doesnt_raise(some_signal):
    some_signal.del_receiver("wrong")


def test_signal_has_attributes(some_signal):
    some_signal.add_attribute("attr1", "val1")
    assert some_signal.attributes == {"attr1": "val1"}


def test_signal_delete_attribute(some_signal):
    some_signal.add_attribute("attr1", "val1")
    some_signal.del_attribute("attr1")
    assert some_signal.attributes == {}


def test_signal_delete_wrong_attribute_doesnt_raise(some_signal):
    some_signal.del_attribute("wrong")


def test_signal_spn(some_signal):
    assert some_signal.spn is None
    some_signal.add_attribute("SPN", 10)
    assert some_signal.spn == '10'


def test_signal_set_startbit():
    signal = Signal(size=16)
    signal.set_startbit(2)
    assert signal.start_bit == 2


def test_signal_set_startbit_conversion():
    signal = Signal(size=16, is_little_endian=False)
    signal.set_startbit(20, startLittle=True)
    assert signal.start_bit == 5  # lsb on 20, msb is 20-15 = 5
    # TODO add test for reversed endianning


def test_signal_set_startbit_raise():
    signal = Signal(size=16, is_little_endian=False)
    with pytest.raises(Exception):
        signal.set_startbit(5, startLittle=True)  # lsb would be on -10


def test_signal_get_startbit():
    signal_big = Signal(start_bit=2, size=16, is_little_endian=True)
    assert signal_big.get_startbit() == 2


def test_signal_get_startbit_conversion():
    signal_big = Signal(start_bit=2, size=16, is_little_endian=False)
    assert signal_big.get_startbit(start_little=True) == 17  # looking for "end" of the signal: 2 + (16 - 1)

    signal_big = Signal(start_bit=32, size=4, is_little_endian=False)
    assert signal_big.get_startbit(bit_numbering=True, start_little=True) == 36
    # TODO add test for reversed endianning


def test_signal_range():
    unsigned = Signal(size=8, is_signed=False)
    assert unsigned.calculate_raw_range() == (decimal.Decimal(0), decimal.Decimal(255))
    signed = Signal(size=8)
    assert signed.calculate_raw_range() == (decimal.Decimal(-128), decimal.Decimal(127))


def test_signal_set_min_max():
    signal = Signal(size=8, offset=100)
    signal.set_min(-5)
    signal.set_max(30)
    assert signal.min == -5
    assert signal.max == 30


def test_signal_set_default_min_max():
    signal = Signal(size=8, offset=100, min=-5, max=10)
    signal.set_min(None)
    signal.set_max(None)
    assert signal.min == -128 + 100
    assert signal.max == 127 + 100


def test_signal_decode_named_value(some_signal):
    some_signal.add_values(255, "Init")
    some_signal.add_values(254, "Error")
    assert some_signal.raw2phys(254, decode_to_str=True) == "Error"
    assert some_signal.raw2phys(300, decode_to_str=True) == 450


def test_signal_encode_named_value(some_signal):
    some_signal.add_values(255, "Init")
    some_signal.add_values(254, "Error")
    assert some_signal.phys2raw("Error") == 254


def test_signal_encode_invalid_named_value(some_signal):
    with pytest.raises(decimal.InvalidOperation):
        some_signal.phys2raw("wrong")


def test_signal_min_unspecified_respects_calc_for_min_none_false():
    signal = Signal(calc_min_for_none=False)
    assert signal.min is None


def test_signal_min_unspecified_respects_calc_for_min_none_true():
    signal = Signal(size=8, is_signed=True, calc_min_for_none=True)
    assert signal.min == -128


def test_signal_min_specified_respects_calc_for_min_none_false():
    signal = Signal(min=42, calc_min_for_none=False)
    assert signal.min == 42


def test_signal_min_specified_respects_calc_for_min_none_true():
    signal = Signal(min=42, calc_min_for_none=True)
    assert signal.min == 42


def test_signal_max_unspecified_respects_calc_for_max_none_false():
    signal = Signal(calc_max_for_none=False)
    assert signal.max is None


def test_signal_max_unspecified_respects_calc_for_max_none_true():
    signal = Signal(size=8, is_signed=True, calc_max_for_none=True)
    assert signal.max == 127


def test_signal_max_specified_respects_calc_for_max_none_false():
    signal = Signal(max=42, calc_max_for_none=False)
    assert signal.max == 42


def test_signal_max_specified_respects_calc_for_max_none_true():
    signal = Signal(max=42, calc_max_for_none=True)
    assert signal.max == 42


def test_signal_range_type_int():
    signal = Signal(is_float=False)
    signal_min, signal_max = signal.calculate_raw_range()

    min_is = isinstance(signal_min, int)
    max_is = isinstance(signal_max, int)

    assert (min_is, max_is) == (True, True), str((type(signal_min), type(signal_max)))


def test_signal_range_type_float():
    signal = Signal(is_float=True)
    signal_min, signal_max = signal.calculate_raw_range()

    factory_type = type(signal.float_factory(0))

    min_is = isinstance(signal_min, factory_type)
    max_is = isinstance(signal_max, factory_type)

    assert (min_is, max_is) == (True, True), str((type(signal_min), type(signal_max)))

def test_signal_multiplexer_value_in_range():
    # test multiplexer ranges (complex multiplex)
    signal = Signal()
    signal.mux_val_grp.append([1, 2])
    signal.mux_val_grp.append([4, 5])
    assert signal.multiplexer_value_in_range(0) == False
    assert signal.multiplexer_value_in_range(1) == True
    assert signal.multiplexer_value_in_range(2) == True
    assert signal.multiplexer_value_in_range(3) == False
    assert signal.multiplexer_value_in_range(4) == True
    assert signal.multiplexer_value_in_range(5) == True
    assert signal.multiplexer_value_in_range(6) == False

    # test standard multiplexer
    signal2 = Signal()
    signal2.multiplex_setter(1)
    assert signal2.multiplexer_value_in_range(1) == True
    assert signal2.multiplexer_value_in_range(0) == False

    signal3 = Signal()
    signal3.multiplex_setter("Multiplexor")
    assert signal3.multiplexer_value_in_range(1) == False
    assert signal3.multiplexer_value_in_range(0) == False