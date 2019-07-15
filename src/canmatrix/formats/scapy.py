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

extension = "py"
import textwrap



def get_fmt(signal):
    if signal.is_little_endian:
        if signal.is_float:
            fmt = "<f"
        elif signal.is_signed:
            fmt = "<b"
        else:
            fmt = "<B"
    else:
        if signal.is_float:
            fmt = ">f"
        elif signal.is_signed:
            fmt = ">b"
        else:
            fmt = ">B"

    return fmt



def dump(db, f, **options):
    scapy_decoder = textwrap.dedent("""    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    from scapy.packet import Packet
    from scapy.packet import bind_layers
    from scapy.fields import *
    from scapy.layers.can import *
    class DBC(CAN):
        name = 'DBC'
        fields_desc = [
            FlagsField('flags', 0, 3, ['error',
                                       'remote_transmission_request',
                                       'extended']),
            XBitField('arbitration_id', 0, 29),
            ByteField('length', None),
            ThreeBytesField('reserved', 0),
        ]
    """)

    for frame in db.frames:
        scapy_decoder += "class " + frame.name + "(Packet):\n"
        scapy_decoder += "    fields_desc = [ \n"
        signal_collection = []
        for signal_group in frame.signalGroups:
            for signal in signal_group.signals:
                signal_collection.append(signal)

        for signal in frame.signals:
            signal_collection.append(signal)

        for signal in signal_collection:
            scapy_decoder += '        SignalField("{}", default=0, start={}, size={}, scaling={}, offset={}, unit="{}", fmt="{}"),\n'.format(
                signal.name, signal.get_startbit(bit_numbering=1), signal.size, signal.factor, signal.offset,
                signal.unit, get_fmt(signal))
        scapy_decoder += "    ]\n\n"

    for frame in db.frames:
        if frame.arbitration_id.extended:
            scapy_decoder += "bind_layers(DBC, " + frame.name + ", arbitration_id = " + hex(
                frame.arbitration_id.id) + ", flags = extended)\n"
        else:
            scapy_decoder += "bind_layers(DBC, " + frame.name + ", arbitration_id = " + hex(
                frame.arbitration_id.id) + ")\n"

    f.write(scapy_decoder.encode("utf8"))
