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
