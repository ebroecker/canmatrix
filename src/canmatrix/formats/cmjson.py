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
# this script exports json-files from a canmatrix-object
# json-files are the can-matrix-definitions of the CANard-project
# (https://github.com/ericevenchick/CANard)

from __future__ import absolute_import

import json
import sys
import typing
from builtins import *

import canmatrix

extension = 'json'


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.BinaryIO, **str) -> None

    export_canard = options.get('jsonCanard', False)
    motorola_bit_format = options.get('jsonMotorolaBitFormat', "lsb")
    export_all = options.get('jsonAll', False)
    additional_frame_columns = [x for x in options.get("additionalFrameAttributes", "").split(",") if x]


    export_array = []  # type: typing.List[typing.Union[str, float, list, dict]]


    if export_canard:
        for frame in db.frames:
            signals = {}
            for signal in frame.signals:
                signals[
                    signal.get_startbit(
                        bit_numbering=1,
                        start_little=True)] = {
                    "name": signal.name,
                    "bit_length": signal.size,
                    "factor": signal.factor,
                    "offset": signal.offset}
            export_array.append(
                {"name": frame.name, "id": hex(frame.arbitration_id.id), "signals": signals})

    elif export_all is False:
        for frame in db.frames:
            symbolic_signals = []
            for signal in frame.signals:
                if not signal.is_little_endian:
                    if motorola_bit_format == "msb":
                        start_bit = signal.get_startbit(bit_numbering=1)
                    elif motorola_bit_format == "msbreverse":
                        start_bit = signal.get_startbit()
                    else:  # motorola_bit_format == "lsb"
                        start_bit = signal.get_startbit(bit_numbering=1, start_little=True)
                else:
                    start_bit = signal.get_startbit(bit_numbering=1, start_little=True)

                symbolic_signals.append({
                    "name": signal.name,
                    "start_bit": start_bit,
                    "bit_length": signal.size,
                    "factor": str(signal.factor),
                    "offset": str(signal.offset),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float
                })
            symbolic_frame = {"name": frame.name,
                              "id": int(frame.arbitration_id.id),
                              "is_extended_frame": frame.arbitration_id.extended,
                              "signals": symbolic_signals}
            frame_attributes = {
                attr: frame.attribute(attr)
                for attr in additional_frame_columns
                if frame.attribute(attr) is not None  # don't export None parameters
            }
            if frame_attributes:  # only add attributes if there are any
                symbolic_frame["attributes"] = frame_attributes
            export_array.append(symbolic_frame)
    else:  # export_all
        for frame in db.frames:
            frame_attributes = {attribute: frame.attribute(attribute, db=db) for attribute in db.frame_defines}
            symbolic_signals = []
            for signal in frame.signals:
                attributes = {attribute: signal.attribute(attribute, db=db) for attribute in db.signal_defines}
                values = {key: signal.values[key] for key in signal.values}
                if not signal.is_little_endian:
                    if motorola_bit_format == "msb":
                        start_bit = signal.get_startbit(bit_numbering=1)
                    elif motorola_bit_format == "msbreverse":
                        start_bit = signal.get_startbit()
                    else:  # motorola_bit_format == "lsb"
                        start_bit = signal.get_startbit(bit_numbering=1, start_little=True)
                else:  # motorola_bit_format == "lsb"
                    start_bit = signal.get_startbit(bit_numbering=1, start_little=True)

                symbolic_signal = {
                    "name": signal.name,
                    "start_bit": start_bit,
                    "bit_length": signal.size,
                    "factor": str(signal.factor),
                    "offset": str(signal.offset),
                    "min": str(signal.min),
                    "max": str(signal.max),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float,
                    "comment": signal.comment,
                    "attributes": attributes,
                    "values": values
                }
                if signal.multiplex is not None:
                    symbolic_signal["multiplex"] = signal.multiplex
                if signal.unit:
                    symbolic_signal["unit"] = signal.unit
                symbolic_signals.append(symbolic_signal)

            export_array.append(
                {"name": frame.name,
                 "id": int(frame.arbitration_id.id),
                 "is_extended_frame": frame.arbitration_id.extended,
                 "signals": symbolic_signals,
                 "attributes": frame_attributes,
                 "comment": frame.comment,
                 "length": frame.size})
    if sys.version_info > (3, 0):
        import io
        temp = io.TextIOWrapper(f, encoding='UTF-8')
    else:
        temp = f

    try:
        json.dump({"messages": export_array}, temp, sort_keys=True,
                  indent=4, separators=(',', ': '))
    finally:
        if sys.version_info > (3, 0):
            # When TextIOWrapper is garbage collected, it closes the raw stream
            # unless the raw stream is detached first
            temp.detach()


def load(f, **_options):
    # type: (typing.BinaryIO, **str) -> canmatrix.CanMatrix

    db = canmatrix.CanMatrix()

    if sys.version_info > (3, 0):
        import io
        json_data = json.load(io.TextIOWrapper(f, encoding='UTF-8'))
    else:

        json_data = json.load(f)

    if "messages" in json_data:
        for frame in json_data["messages"]:
            # new_frame = Frame(frame["id"],frame["name"],8,None)
            new_frame = canmatrix.Frame(frame["name"], arbitration_id=frame["id"], size=8)
            if "length" in frame:
                new_frame.size = frame["length"]

            new_frame.arbitration_id.extended = frame.get("is_extended_frame", False)

            for signal in frame["signals"]:
                is_little_endian = not signal.get("is_big_endian", False)
                is_float = signal.get("is_float", False)
                is_signed = signal.get("is_signed", False)

                new_signal = canmatrix.Signal(
                    signal["name"],
                    start_bit=signal["start_bit"],
                    size=signal["bit_length"],
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    is_float=is_float,
                    factor=signal["factor"],
                    offset=signal["offset"]
                )

                if signal.get("min") is not None:
                    new_signal.min = new_signal.float_factory(signal["min"])

                if signal.get("max", False):
                    new_signal.max = new_signal.float_factory(signal["max"])

                if signal.get("unit", False):
                    new_signal.unit = signal["unit"]

                if signal.get("multiplex", False):
                    new_signal.unit = signal["multiplex"]

                if signal.get("values", False):
                    for key in signal["values"]:
                        new_signal.add_values(key, signal["values"][key])
                if new_signal.is_little_endian is False:
                    new_signal.set_startbit(
                        new_signal.start_bit, bitNumbering=1, startLittle=True)
                new_frame.add_signal(new_signal)
            db.add_frame(new_frame)
    f.close()
    return db
