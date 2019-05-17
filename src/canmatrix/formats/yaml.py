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

import copy
import typing
from builtins import *

import yaml
from past.builtins import long, unicode

import canmatrix

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

_yaml_initialized = False


def dump(db, f, **options):  # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    __init_yaml()
    new_db = copy.deepcopy(db)

    for i, frame in enumerate(new_db.frames):
        for j, signal in enumerate(frame.signals):
            if not signal.is_little_endian:
                signal.start_bit = signal.get_startbit(bit_numbering=1, start_little=True)
                # new_db.frames[i].signals[j].start_bit = signal.start_bit

    # f = open(filename, "w")
    if representers:
        f.write(unicode(yaml.dump(new_db)))
    else:
        f.write(yaml.dump(new_db).encode('utf8'))


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    __init_yaml()
    db = yaml.load(f)
    return db


def _constructor(loader, node, cls, mapping=None):
    d = {k.lstrip('_'): v for k, v in loader.construct_mapping(node).items()}
    name = d.pop('name')
    if mapping:
        for old, new in mapping.items():
            d[new] = d.pop(old)
    return cls(name, **d)


def _frame_constructor(loader, node):
    return _constructor(
        loader=loader,
        node=node,
        cls=canmatrix.Frame,
        mapping={
            'size': 'dlc',
        },
    )


def _signal_constructor(loader, node):
    signal = _constructor(
        loader=loader,
        node=node,
        cls=canmatrix.Signal,
        mapping={
            'startbit': 'startBit',  # todo shall probably be updated to match current names like start_bit
            'signalsize': 'signalSize',
        },
    )  # type: canmatrix.Signal

    if not signal.is_little_endian:
        signal.set_startbit(
            loader.construct_mapping(node)['_startbit'],
            bitNumbering=1,
            startLittle=False)

    return signal


def _frame_representer(dumper, data):
    node = yaml.representer.Representer.represent_object(dumper, data)
    node.tag = '{}:Frame'.format(node.tag.partition(':python/object:')[0])

    return node


def __init_yaml():
    """Lazy init yaml because canmatrix might not be fully loaded when loading this format."""
    global _yaml_initialized
    if not _yaml_initialized:
        _yaml_initialized = True
        yaml.add_constructor(u'tag:yaml.org,2002:Frame', _frame_constructor)
        yaml.add_constructor(u'tag:yaml.org,2002:Signal', _signal_constructor)
        yaml.add_representer(canmatrix.Frame, _frame_representer)
