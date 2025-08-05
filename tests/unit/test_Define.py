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
from canmatrix.Define import Define

# Define tests
def test_define_set_default():
    define = Define("")
    define.set_default("string")
    assert define.defaultValue == "string"
    define.set_default('"quoted_string"')
    assert define.defaultValue == "quoted_string"


def test_define_update_enum_definition():
    define = Define("")
    define.type = "ENUM"
    define.values = ["ready", "off"]
    define.update()
    assert define.definition == 'ENUM "ready","off"'


def test_define_update_ingored_non_enum():
    def_str = "INT 0 100"
    define = Define(def_str)
    define.update()
    assert define.definition == def_str


def test_define_for_int():
    define = Define("INT -5 10")
    assert define.type == "INT"
    assert define.min == -5
    assert define.max == 10


def test_define_for_hex():
    define = Define("HEX 0 255")
    assert define.type == "HEX"
    assert define.min == 0
    assert define.max == 255


def test_define_for_string():
    define = Define("STRING")
    assert define.type == "STRING"
    assert define.min is None
    assert define.max is None


def test_define_for_enum():
    define = Define('ENUM red, green')
    assert define.type == "ENUM"
    assert define.values == ["red", "green"]


def test_define_for_enum_strip_quotes():
    define = Define('ENUM "red", "green"')
    assert define.type == "ENUM"
    assert define.values == ["red", "green"]


def test_define_for_float():
    define = Define("FLOAT -2.2 111.11")
    assert define.type == "FLOAT"
    assert define.min == decimal.Decimal('-2.2')
    assert define.max == decimal.Decimal('111.11')