#!/usr/bin/env python
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
# this script exports yaml-files from a canmatrix-object
# yaml-files are just object-dumps human readable.
# This export is complete, no information lost


from __future__ import absolute_import
from builtins import *

from .canmatrix import *
import copy
import codecs
import yaml

try:
    from yaml.representer import SafeRepresenter
except ImportError:
    yaml = None


representers = False
try:
    yaml.add_representer(int, SafeRepresenter.represent_int)
    yaml.add_representer(long, SafeRepresenter.represent_long)
    yaml.add_representer(unicode, SafeRepresenter.represent_unicode)
    yaml.add_representer(str, SafeRepresenter.represent_unicode)
    yaml.add_representer(list, SafeRepresenter.represent_list)
    representers = True
except:
    representers = False
    # some error with representers ... continue anyway


def dump(db, f, **options):
    newdb = copy.deepcopy(db)

    for i, frame in enumerate(newdb.frames):
        for j, signal in enumerate(frame.signals):
            if signal.is_little_endian == False:
                signal._startbit = signal.getStartbit(
                    bitNumbering=1, startLittle=True)
#                newdb.frames[i].signals[j]._startbit = signal._startbit

#    f = open(filename, "w")
    if representers:
        f.write(unicode(yaml.dump(newdb)))
    else:
        f.write(yaml.dump(newdb).encode('utf8'))


def load(f, **options):
    db = yaml.load(f)
    f.close()

    for i, frame in enumerate(db.frames):
        for j, signal in enumerate(frame.signals):
            if signal.is_little_endian == False:
                signal.setStartbit(
                    signal._startbit,
                    bitNumbering=1,
                    startLittle=True)
#                db.frames[i].signals[j]._startbit = signal._startbit

    return db
