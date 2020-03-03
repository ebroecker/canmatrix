# -*- coding: utf-8 -*-
import canmatrix.utils


def test_utils_guess_value():
    assert canmatrix.utils.guess_value("true") == "1"
    assert canmatrix.utils.guess_value("True") == "1"
    assert canmatrix.utils.guess_value("TrUe") == "1"
    assert canmatrix.utils.guess_value("false") == "0"
    assert canmatrix.utils.guess_value("False") == "0"
    assert canmatrix.utils.guess_value("faLse") == "0"

def test_decode_number():
    assert canmatrix.utils.decode_number("0x10") == 16
    assert canmatrix.utils.decode_number("0b10") == 2
    assert canmatrix.utils.decode_number("10") == 10
