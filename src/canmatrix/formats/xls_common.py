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

import typing
import canmatrix


def get_frame_info(db, frame):
    # type: (canmatrix.CanMatrix, canmatrix.Frame) -> typing.List[str]
    ret_array = []  # type: typing.List[str]
    # frame-id
    if frame.arbitration_id.extended:
        ret_array.append("%3Xxh" % frame.arbitration_id.id)
    else:
        ret_array.append("%3Xh" % frame.arbitration_id.id)
    # frame-Name
    ret_array.append(frame.name)

    if "GenMsgCycleTime" in db.frame_defines:
        # determine cycle-time
        ret_array.append(frame.attribute("GenMsgCycleTime", db=db))

    # determine send-type
    if "GenMsgSendType" in db.frame_defines:
        ret_array.append(frame.attribute("GenMsgSendType", db=db))
        if "GenMsgDelayTime" in db.frame_defines:
            ret_array.append(frame.attribute("GenMsgDelayTime", db=db))
        else:
            ret_array.append("")
    else:
        ret_array.append("")
        ret_array.append("")
    return ret_array


def get_signal(db, sig, motorola_bit_format):
    # type: (canmatrix.CanMatrix, canmatrix.Signal, str) -> typing.Tuple[typing.List, typing.List]
    front_array = []  # type: typing.List[typing.Union[str, float]]
    back_array = []
    if motorola_bit_format == "msb":
        start_bit = sig.get_startbit(bit_numbering=1)
    elif motorola_bit_format == "msbreverse":
        start_bit = sig.get_startbit()
    else:  # motorolaBitFormat == "lsb"
        start_bit = sig.get_startbit(bit_numbering=1, start_little=True)

    # start byte
    front_array.append(int(start_bit / 8) + 1)
    # start bit
    front_array.append(start_bit % 8)
    # signal name
    front_array.append(sig.name)

    # eval comment:
    comment = sig.comment if sig.comment else ""

    # eval multiplex-info
    if sig.multiplex == 'Multiplexor':
        comment = "Mode Signal: " + comment
    elif sig.multiplex is not None:
        comment = "Mode " + str(sig.multiplex) + ":" + comment

    # write comment and size of signal in sheet
    front_array.append(comment)
    front_array.append(sig.size)

    # start-value of signal available
    if "GenSigStartValue" in db.signal_defines:
        if db.signal_defines["GenSigStartValue"].definition == "STRING":
            front_array.append(sig.attribute("GenSigStartValue", db=db))
        elif db.signal_defines["GenSigStartValue"].definition == "INT" \
                or db.signal_defines["GenSigStartValue"].definition == "HEX":
            front_array.append("%Xh" % sig.attribute("GenSigStartValue", db=db))
        else:
            front_array.append(" ")
    else:
        front_array.append(" ")

    # SNA-value of signal available
    if "GenSigSNA" in db.signal_defines:
        sna = sig.attribute("GenSigSNA", db=db)
        if sna is not None:
            sna = sna[1:-1]
        front_array.append(sna)
    # no SNA-value of signal available / just for correct style:
    else:
        front_array.append(" ")

    # eval byteorder (little_endian: intel == True / motorola == 0)
    if sig.is_little_endian:
        front_array.append("i")
    else:
        front_array.append("m")

    # is a unit defined for signal?
    if sig.unit.strip():
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            back_array.append("%g" % float(sig.factor) + "  " + sig.unit)
        # factor == 1.0
        else:
            back_array.append(sig.unit)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            back_array.append("%g -" % float(sig.factor))
        # factor == 1.0
        else:
            back_array.append("")
    return front_array, back_array
