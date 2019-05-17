# -*- coding: utf-8 -*-

import csv
import shlex
import sys
import typing


def quote_aware_space_split(in_line):  # type: (str) -> typing.List[str]
    if sys.version_info >= (3, 0):  # is there a clean way to to it?
        return shlex.split(in_line.strip())
    return [item.decode('utf-8') for item in shlex.split(in_line.strip().encode('utf-8'))]


def quote_aware_comma_split(string):  # type: (str) -> typing.List[str]
    if sys.version_info >= (3, 0):
        temp = list(csv.reader([string], skipinitialspace=True))
    else:
        temp = list(csv.reader([string.encode("utf8")], skipinitialspace=True))
    return temp[0]


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
