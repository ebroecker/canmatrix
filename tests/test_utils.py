# -*- coding: utf-8 -*-
import pytest

import canmatrix.utils
import decimal

def test_utils_guess_value():
    assert canmatrix.utils.guess_value("true") == "1"
    assert canmatrix.utils.guess_value("True") == "1"
    assert canmatrix.utils.guess_value("TrUe") == "1"
    assert canmatrix.utils.guess_value("false") == "0"
    assert canmatrix.utils.guess_value("False") == "0"
    assert canmatrix.utils.guess_value("faLse") == "0"


def test_decode_number():
    assert canmatrix.utils.decode_number("0x10", decimal.Decimal) == 16
    assert canmatrix.utils.decode_number("0b10", decimal.Decimal) == 2
    assert canmatrix.utils.decode_number("10", decimal.Decimal) == 10
    assert canmatrix.utils.decode_number("1023.0", decimal.Decimal) == 1023.0

@pytest.mark.parametrize(
    'input_string, expected_list',
    (
            ('a,b,c,d',
             ["a", "b", "c", "d"]),

            ('a,  b, c, d',
             ["a", "b", "c", "d"]),

            ('a,  b", c", "d"',
             ['a', 'b", c"', 'd']),

            ('0="a",  1=b, 3="c"d, 4=e',
             ['0="a"',  '1=b', '3="c"d', '4=e']),

            ('"a,b",","b,c","\'\'d"e',
             ['a,b', '","b', 'c","\'\'d\"e']),
    )
)
def test_quote_aware_comma_split_function(input_string, expected_list):
    assert canmatrix.utils.quote_aware_comma_split(input_string) == expected_list
