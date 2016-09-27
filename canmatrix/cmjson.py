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
from .canmatrix import *
import codecs
import json
import sys


extension = 'json'

def dump(db, f, **options):
    if 'jsonCanard' in options:
        exportCanard = options['jsonCanard']
    else:
        exportCanard = False
    if 'jsonAll' in options:
        exportAll = options['jsonAll']
    else:
        exportAll = False

    if (sys.version_info > (3, 0)):
        mode = 'w'
    else:
        mode = 'wb'
  
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
                signals.append({
                    "name": signal.name,
                    "start_bit": signal.getStartbit(bitNumbering=1, startLittle=True),
                    "bit_length": signal.signalsize,
                    "factor": float(signal.factor),
                    "offset": float(signal.offset),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed
                })
            exportArray.append({"name": frame.name,
                                "id": int(frame.id),
                                "is_extended_frame": frame.extended == 1,
                                "signals": signals})
    else:  # exportall
        for frame in db.frames:
            frameattribs = {}
            for attribute in frame.attributes:
                frameattribs[attribute] = frame.attributes[attribute]
            signals = []
            for signal in frame.signals:
                attribs = {}
                for attribute in signal.attributes:
                    attribs[attribute] = signal.attributes[attribute]
                signals.append({
                    "name": signal.name,
                    "start_bit": signal.getStartbit(bitNumbering=1, startLittle=True),
                    "bit_length": signal.signalsize,
                    "factor": float(signal.factor),
                    "offset": float(signal.offset),
                    "is_big_endian": signal.is_little_endian == 0,
                    "is_signed": signal.is_signed,
                    "comment": signal.comment,
                    "attributes": attribs
                })
            exportArray.append(
                {"name": frame.name,
                 "id": int(frame.id),
                 "is_extended_frame": frame.extended == 1,
                 "signals": signals,
                 "attributes": frameattribs,
                 "comment": frame.comment})
    if (sys.version_info > (3, 0)):
        import io
        temp = io.TextIOWrapper(f, encoding='UTF-8')
    else:
        temp = f


    json.dump({"messages": exportArray}, temp, sort_keys=True,
              indent=4, separators=(',', ': '))

def load(f, **options):
    db = CanMatrix()
    
    if (sys.version_info > (3, 0)):
        import io
        jsonData = json.load(io.TextIOWrapper(f, encoding='UTF-8'))
    else:
        jsonData = json.load(f)

    if "messages" in jsonData:
        for frame in jsonData["messages"]:
            #            newframe = Frame(frame["id"],frame["name"],8,None)
            newframe = Frame(frame["name"],
                             Id=frame["id"],
                             dlc=8)

            if "is_extended_frame" in frame and frame["is_extended_frame"]:
                newframe.extended = 1
            else:
                newframe.extended = 0

            for signal in frame["signals"]:
                if signal["is_big_endian"]:
                    is_little_endian = False
                else:
                    is_little_endian = True
                if signal["is_signed"]:
                    is_signed = True
                else:
                    is_signed = False
                newsignal = Signal(signal["name"],
                                   startBit=signal["start_bit"],
                                   signalSize=signal["bit_length"],
                                   is_little_endian=is_little_endian,
                                   is_signed=is_signed,
                                   factor=signal["factor"],
                                   offset=signal["offset"])

                if newsignal.is_little_endian == False:

                    newsignal.setStartbit(
                        newsignal._startbit, bitNumbering=1, startLittle=True)
                newframe.addSignal(newsignal)
            db._fl.addFrame(newframe)
    f.close()
    return db
