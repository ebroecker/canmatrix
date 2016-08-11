from __future__ import absolute_import
from builtins import *
#!/usr/bin/env python

import logging
logger = logging.getLogger('root')
from .canmatrix import *

# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

#
# this script supplys some helperfunctions to parse arxml-files
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
#


class arTree(object):

    def __init__(self, name="", ref=None):
        self._name = name
        self._ref = ref
        self._array = []

    def new(self, name, child):
        temp = arTree(name, child)
        self._array.append(temp)
        return temp

    def getChild(self, path):
        for tem in self._array:
            if tem._name == path:
                return tem


def arParseTree(tag, ardict, namespace):
    for child in tag:
        name = child.find('./' + namespace + 'SHORT-NAME')
#               namel = child.find('./' + namespace + 'LONG-NAME')
        if name is not None and child is not None:
            arParseTree(child, ardict.new(name.text, child), namespace)
        if name is None and child is not None:
            arParseTree(child, ardict, namespace)
#
# some sort of X-Path in autosar-xml-files:
#


def arGetXchildren(root, path, arDict, ns):
    pathElements = path.split('/')
    ptr = root
    for element in pathElements[:-1]:
        ptr = arGetChild(ptr, element, arDict, ns)
    ptr = arGetChildren(ptr, pathElements[-1], arDict, ns)
    return ptr

#
# get path in tranlation-dictionary
#


def arGetPath(ardict, path):
    ptr = ardict
    for p in path.split('/'):
        if p.strip():
            if ptr is not None:
                ptr = ptr.getChild(p)
            else:
                return None
    if ptr is not None:
        return ptr._ref
    else:
        return None


def arGetChild(parent, tagname, arTranslationTable, namespace):
    #    logger.debug("getChild: " + tagname)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tagname)
    if ret is None:
        ret = parent.find('.//' + namespace + tagname + '-REF')
        if ret is not None:
            ret = arGetPath(arTranslationTable, ret.text)
    return ret


def arGetChildren(parent, tagname, arTranslationTable, namespace):
    if parent is None:
        return []
    ret = parent.findall('.//' + namespace + tagname)
    if ret.__len__() == 0:
        retlist = parent.findall('.//' + namespace + tagname + '-REF')
        rettemp = []
        for ret in retlist:
            rettemp.append(arGetPath(arTranslationTable, ret.text))
        ret = rettemp
    return ret


def arGetName(parent, ns):
    name = parent.find('./' + ns + 'SHORT-NAME')
    if name is not None:
        if name.text is not None:
            return name.text
    return ""
