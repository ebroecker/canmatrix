# Copyright (c) 2019, Eduard Broecker
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
# this script exports scapy python files
# https://scapy.readthedocs.io/en/latest/advanced_usage.html#automotive-usage

from __future__ import absolute_import, division, print_function

import textwrap
import typing
from builtins import *

import canmatrix

extension = "py"


def get_fmt(signal):  # type: (canmatrix.Signal) -> str

    if signal.is_little_endian:
        fmt = "<"
    else:
        fmt = ">"

    if signal.is_float:
        fmt += "f"
    elif signal.is_signed:
        fmt += "b"
    else:
        fmt += "B"
    return fmt

def signal_field_line(signal):
    return   u'SignalField("{}", default=0, start={}, size={}, scaling={}, offset={}, unit="{}", fmt="{}"),'.format(
        signal.name, signal.get_startbit(bit_numbering=1), signal.size, signal.factor, signal.offset,
        signal.unit, get_fmt(signal))

def dump(db, f, **options):  # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    scapy_decoder = textwrap.dedent("""    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    from scapy.packet import Packet
    from scapy.packet import bind_layers
    from scapy.fields import *
    from scapy.layers.can import *
    """)

    for frame in db.frames:
        scapy_decoder += "class " + frame.name + "(SignalPacket):\n"
        scapy_decoder += "    fields_desc = [ \n"

        if frame.is_multiplexed and not frame.is_complex_multiplexed:
            multiplexer = frame.get_multiplexer
            scapy_decoder += u'        ' + signal_field_line(multiplexer) + '\n'
            for signal in frame.signals:
                if signal != multiplexer and signal.mux_val is not None:
                    scapy_decoder += u'        ConditionalField(' + signal_field_line(signal) + ' lambda p: p.{} == {}),\n'.format(multiplexer.name, signal.mux_val)
                elif signal != multiplexer:
                    scapy_decoder += u'        ' + signal_field_line(signal) + '\n'

        else:
            for signal in frame.signals:
                scapy_decoder += u'        ' + signal_field_line(signal) + '\n'
        scapy_decoder += "    ]\n\n"

    for frame in db.frames:
        if frame.arbitration_id.extended:
            scapy_decoder += "bind_layers(SignalHeader, " + frame.name + ", identifier  = " + hex(
                frame.arbitration_id.id) + ", flags = extended)\n"
        else:
            scapy_decoder += "bind_layers(SignalHeader, " + frame.name + ", identifier  = " + hex(
                frame.arbitration_id.id) + ")\n"

    f.write(scapy_decoder.encode("utf8"))
