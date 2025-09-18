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

import csv
import shlex
import sys
import typing
from string import hexdigits
from builtins import *
from itertools import zip_longest
import struct

from canmatrix.ArbitrationId import ArbitrationId

if sys.version_info >= (3, 5):
    import math
else:
    import fractions


def normalize_value_table(table):  # type: (typing.Mapping) -> typing.MutableMapping[int, typing.Any]
    return {int(k): v for k, v in table.items()}

def quote_aware_space_split(in_line):  # type: (str) -> typing.List[str]
    return shlex.split(in_line.strip())


# https://stackoverflow.com/questions/18092354/python-split-string-without-splitting-escaped-character
def escape_aware_split(string, delimiter):
    if len(delimiter) != 1:
        raise ValueError('Invalid delimiter: ' + delimiter)
    ln = len(string)
    i = 0
    j = 0
    while j < ln:
        if string[j] == '\\':
            if j + 1 >= ln:
                yield string[i:j]
                return
            j += 1
        elif string[j] == delimiter:
            yield string[i:j]
            i = j + 1
        j += 1
    yield string[i:j]


def quote_aware_comma_split(string):  # type: (str) -> typing.List[str]
    """
    Split a string containing comma separated list of fields.
    Removing surrounding whitespace, to allow fields to be separated by ", ".
    Preserves double quotes within fields, but not double quotes surrounding fields.
    Suppresses comma separators which are within double quoted sections.
    :param string: ('a,  b", c", "d"',
    :return: ['a', 'b", c"', 'd']),
    """
    fields = []
    quoted = False
    field = ""
    # Separate string by unquoted commas
    for char in string:
        if char == ',':
            if not quoted:
                fields.append(field)
                field = ""
                continue
        if char == '"':
            quoted = not quoted
        field += char
    if field:
        fields.append(field)
    # Remove surrounding whitespace from fields
    fields = [f.strip() for f in fields]
    # Remove "" that surround entire fields
    for i, f in enumerate(fields):
        if len(f) > 1:
            if f.startswith('"') and f.endswith('"'):
                fields[i] = f[1:-1]
    return fields


def guess_value(text_value):  # type: (str) -> str
    """
    Get string value for common strings.
    Method is far from complete but helping with odd arxml files.

    :param text_value: value in text like "true"
    :return: string for value like "1"
    """
    if sys.version_info >= (3, 0):
        text_value = text_value.casefold()
    else:
        text_value = text_value.lower()
    if text_value in ["false", "off"]:
        return "0"
    elif text_value in ["true", "on"]:
        return "1"
    elif text_value[:2] == "0b":
        if text_value[2:].isdecimal():
            return str(int(text_value[2:], 2))
    elif text_value[:2] == "0x":
        if all([f in hexdigits for f in text_value[2:]]):
            return str(int(text_value[2:], 16))
    return text_value


def get_gcd(value1, value2):  # type (int,int) -> (int)
    """
    Get greatest common divisor of value1 and value2

    :param value1: int value 1
    :param value2: int value 2
    :return: cvt of value 1 and value 2
    """

    if sys.version_info >= (3, 5):
        return math.gcd(value1, value2)
    else:
        return fractions.gcd(value1, value2)


def decode_number(value, float_factory):  # type(string) -> (int)
    """
    Decode string to integer and guess correct base
    :param value: string input value
    :return: integer
    """
    if value is None:
        return 0
    value = value.strip()

    if ('.' in value) or (value.lower() in ["inf", "+inf", "-inf"]):
        return float_factory(value)

    base = 10
    if len(value) > 1 and value[1] == 'b':  # bin coded
        base = 2
        value = value[2:]
    if len(value) > 1 and value[1] == 'x':  # hex coded
        base = 16
        value = value[2:]

    return int(value, base)

def arbitration_id_converter(source):  # type: (typing.Union[int, ArbitrationId]) -> ArbitrationId
    """Converter for attrs which accepts ArbitrationId itself or int."""
    return source if isinstance(source, ArbitrationId) else  ArbitrationId.from_compound_integer(source)

# https://docs.python.org/3/library/itertools.html
def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks."""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def unpack_bitstring(length, is_float, is_signed, bits):
    # type: (int, bool, bool, typing.Any) -> typing.Union[float, int]
    """
    returns a value calculated from bits
    :param length: length of signal in bits
    :param is_float: value is float
    :param bits: value as bits (array/iterable)
    :param is_signed: value is signed
    :return:
    """

    if is_float:
        types = {
            32: '>f',
            64: '>d'
        }

        float_type = types[length]
        value, = struct.unpack(float_type, bytearray(int(''.join(b), 2)  for b in grouper(bits, 8)))
    else:
        value = int(bits, 2)

        if is_signed and bits[0] == '1':
            value -= (1 << len(bits))

    return value


def pack_bitstring(length, is_float, value, signed):
    """
    returns a value in bits
    :param length: length of signal in bits
    :param is_float: value is float
    :param value: value to encode
    :param signed: value is signed
    :return:
    """
    if is_float:
        types = {
            32: '>f',
            64: '>d'
        }

        float_type = types[length]
        x = bytearray(struct.pack(float_type, value))
        bitstring = ''.join('{:08b}'.format(b) for b in x)
    else:
        b = '{:0{}b}'.format(int((2 << length) + value), length)
        bitstring = b[-length:]

    return bitstring

