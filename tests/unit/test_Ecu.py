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
from canmatrix.Ecu import Ecu
from canmatrix.Define import Define


def test_ecu_find_attribute():
    ecu = Ecu(name="Gateway")
    ecu.add_attribute("attr1", 255)
    assert ecu.attribute("attr1") == '255'


def test_ecu_no_attribute():
    ecu = Ecu(name="Gateway")
    assert ecu.attribute("wrong") is None
    assert ecu.attribute("wrong", default=0) == 0


def test_ecu_default_attr_from_db():
    ecu = Ecu(name="Gateway")
    define = Define("INT 0 255")
    define.defaultValue = 33
    matrix = CanMatrix(ecu_defines={"temperature": define})
    assert ecu.attribute("temperature", db=matrix, default=2) == 33
    assert ecu.attribute("wrong", db=matrix, default=2) == 2


def test_ecu_repr():
    ecu = Ecu(name="Gateway")
    ecu.add_comment("with bug")
    assert str(ecu) == "Ecu(name='Gateway', comment='with bug')"
   