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

from builtins import *
import canmatrix
import codecs
import json
import sys


extension = 'json'

def dump(db, f, **options):

    exportCanard = options.get('jsonCanard', False)
    motorolaBitFormat = options.get('jsonMotorolaBitFormat', "lsb")


    if 'jsonAll' in options:
        exportAll = options['jsonAll']
    else:
        exportAll = False

    if (sys.version_info > (3, 0)):
        mode = 'w'
    else:
        mode = 'wb'

    additionalFrameColums = []
    if "additionalFrameAttributes" in options and options["additionalFrameAttributes"]:
        additionalFrameColums = options["additionalFrameAttributes"].split(",")

    exportArray = []

    if exportCanard:
        for frame in db.frames:
            signals = {}
            for signal in frame.signals:
                signals[
                    signal.getStartbit(
                        bitNumbering=1,
                        startLittle=True)] = {
                    "name": signal.name,
                    "bit_length": signal.signalsize,
                    "factor": signal.factor,
                    "offset": signal.offset}
            exportArray.append(
                {"name": frame.name, "id": hex(frame.id), "signals": signals})

    elif exportAll == False:
        for frame in db.frames:
            signals = []
            for signal in frame.signals:
                if not signal.is_little_endian:
                    if motorolaBitFormat == "msb":
                        startBit = signal.getStartbit(bitNumbering=1)
                    elif motorolaBitFormat == "msbreverse":
                        startBit = signal.getStartbit()
                    else:  # motorolaBitFormat == "lsb"
                        startBit = signal.getStartbit(bitNumbering=1, startLittle=True)
                else:
                    startBit = signal.getStartbit(bitNumbering=1, startLittle=True)

                signals.append({
                    "name": signal.name,
                    "start_bit": startBit,
                    "bit_length": signal.size,
                    "factor": str(signal.factor),
                    "offset": str(signal.offset),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float
                })
            symbolic_frame = {"name": frame.name,
                              "id": int(frame.id),
                              "is_extended_frame": frame.extended == 1,
                              "signals": signals}
            frame_attributes = {}
            for frame_info in additionalFrameColums:  # Look for additional Frame Attributes
                if frame.attribute(frame_info) is not None:  # does the attribute exist? None value isn't exported.
                    frame_attributes[frame_info] = frame.attribute(frame_info)
            if frame_attributes:  # only add Attributes if there are any
                symbolic_frame["attributes"] = frame_attributes
            exportArray.append(symbolic_frame)
    else:  # exportAll
        for frame in db.frames:
            frameattribs = {}
            for attribute in db.frameDefines:
                frameattribs[attribute] = frame.attribute(attribute, db=db)
            signals = []
            for signal in frame.signals:
                attribs = {}
                for attribute in db.signalDefines:
                    attribs[attribute] = signal.attribute(attribute, db=db)

                values = {}
                for key in signal.values:
                    values[key] = signal.values[key]
                if not signal.is_little_endian:
                    if motorolaBitFormat == "msb":
                        startBit = signal.getStartbit(bitNumbering=1)
                    elif motorolaBitFormat == "msbreverse":
                        startBit = signal.getStartbit()
                    else:  # motorolaBitFormat == "lsb"
                        startBit = signal.getStartbit(bitNumbering=1, startLittle=True)
                else:  # motorolaBitFormat == "lsb"
                    startBit = signal.getStartbit(bitNumbering=1, startLittle=True)


                signalDict = {
                    "name": signal.name,
                    "start_bit": startBit,
                    "bit_length": signal.size,
                    "factor": str(signal.factor),
                    "offset": str(signal.offset),
                    "min": str(signal.min),
                    "max": str(signal.max),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float,
                    "comment": signal.comment,
                    "attributes": attribs,
                    "values": values
                }
                if signal.multiplex is not None:
                    signalDict["multiplex"] = signal.multiplex
                if signal.unit:
                    signalDict["unit"] = signal.unit
                signals.append(signalDict)


            exportArray.append(
                {"name": frame.name,
                 "id": int(frame.id),
                 "is_extended_frame": frame.extended == 1,
                 "signals": signals,
                 "attributes": frameattribs,
                 "comment": frame.comment,
                 "length": frame.size})
    if sys.version_info > (3, 0):
        import io
        temp = io.TextIOWrapper(f, encoding='UTF-8')
    else:
        temp = f

    try:
        json.dump({"messages": exportArray}, temp, sort_keys=True,
                  indent=4, separators=(',', ': '))
    finally:
        if sys.version_info > (3, 0):
            # When TextIOWrapper is garbage collected, it closes the raw stream
            # unless the raw stream is detached first
            temp.detach()


def load(f, **options):
    db = canmatrix.CanMatrix()

    if (sys.version_info > (3, 0)):
        import io
        jsonData = json.load(io.TextIOWrapper(f, encoding='UTF-8'))
    else:
        jsonData = json.load(f)

    if "messages" in jsonData:
        for frame in jsonData["messages"]:
            #            newframe = Frame(frame["id"],frame["name"],8,None)
            newframe = canmatrix.Frame(frame["name"],
                             id=frame["id"],
                             size=8)
            if "length" in frame:
                newframe.size = frame["length"]

            if "is_extended_frame" in frame and frame["is_extended_frame"]:
                newframe.extended = 1
            else:
                newframe.extended = 0

            for signal in frame["signals"]:
                is_little_endian = signal.get("is_big_endian", False)
                    is_little_endian = False
                else:
                    is_little_endian = True

                if signal.get("is_float", False):
                    is_float = True
                else:
                    is_float = False

                if signal.get("is_signed", False):
                    is_signed = True
                else:
                    is_signed = False
                newsignal = canmatrix.Signal(signal["name"],
                                   startBit=signal["start_bit"],
                                   size=signal["bit_length"],
                                   is_little_endian=is_little_endian,
                                   is_signed=is_signed,
                                   is_float = is_float,
                                   factor=signal["factor"],
                                   offset=signal["offset"])

                if signal.get("min", False):
                    newsignal.min = newsignal.float_factory(signal["min"])

                if signal.get("max", False):
                    newsignal.max = newsignal.float_factory(signal["max"])

                if signal.get("unit", False):
                    newsignal.unit = signal["unit"]

                if signal.get("multiplex", False):
                    newsignal.unit = signal["multiplex"]

                if signal.get("values", False):
                    for key in signal["values"]:
                        newsignal.addValues(key, signal["values"][key])
                if newsignal.is_little_endian == False:

                    newsignal.setStartbit(
                        newsignal.startBit, bitNumbering=1, startLittle=True)
                newframe.addSignal(newsignal)
            db.addFrame(newframe)
    f.close()
    return db
