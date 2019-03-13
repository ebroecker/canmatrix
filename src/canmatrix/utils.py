import sys
import shlex
import csv

def quote_aware_space_split(inLine):
    if sys.version_info >= (3, 0):  # is there a clean way to to it?
        return shlex.split(inLine.strip())
    return [item.decode('utf-8') for item in shlex.split(inLine.strip().encode('utf-8'))]


def quote_aware_comma_split(string):
    if sys.version_info >= (3, 0):
        temp = list(csv.reader([string], skipinitialspace=True))
    else:
        temp = list(csv.reader([string.encode("utf8")], skipinitialspace=True))
    return temp[0]


def guess_value(textValue):
    """
    returns a string value for common strings.
    method is far from complete but helping with odd arxmls
    :param textValue: value in text like "true"
    :return: string for value like "1"
    """
    if sys.version_info >= (3, 0):
        textValue = textValue.casefold()
    else:
        textValue = textValue.lower()
    if textValue in ["false", "off"]:
        return "0"
    elif textValue in ["true", "on"]:
        return "1"
    return textValue
