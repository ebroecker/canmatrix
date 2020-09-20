# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import csv
import shlex
import sys
import typing
from builtins import *

if sys.version_info >= (3, 5):
    import math
else:
    import fractions



def quote_aware_space_split(in_line):  # type: (str) -> typing.List[str]
    if sys.version_info >= (3, 0):  # is there a clean way to to it?
        return shlex.split(in_line.strip())
    return [item.decode('utf-8') for item in shlex.split(in_line.strip().encode('utf-8'))]


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

def decode_number(value):  # type(string) -> (int)
    """
    Decode string to integer and guess correct base
    :param value: string input value
    :return: integer
    """

    value = value.strip()
    base = 10
    if len(value) > 1 and value[1] == 'b':  # bin coded
        base = 2
        value = value[2:]
    if len(value) > 1 and value[1] == 'x':  # hex coded
        base = 16
        value = value[2:]

    return int(value, base)