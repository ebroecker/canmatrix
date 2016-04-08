#!/usr/bin/env python
#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

#
# this script exports json-files from a canmatrix-object
# json-files are the can-matrix-definitions of the CANard-project (https://github.com/ericevenchick/CANard)

from builtins import *
from .canmatrix import *
import codecs
import json
import sys


def exportJson(db, filename, **options):
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
    f = open(filename, mode)

    exportArray = []

    if exportCanard:
        for frame in db._fl._list:
            signals = {}
            for signal in frame._signals:
                signals[signal.getLsbStartbit()]= {"name" : signal._name, "bit_length" : signal._signalsize, "factor":signal._factor, "offset":signal._offset}
            exportArray.append({"name" : frame._name, "id" :  hex(frame._Id), "signals": signals })

    elif exportAll == False:
        for frame in db._fl._list:
            signals = []
            for signal in frame._signals:
                signals.append({
                    "name" : signal._name,
                    "start_bit" : signal.getLsbStartbit(),
                    "bit_length" : signal._signalsize,
                    "factor":float(signal._factor),
                    "offset":float(signal._offset),
                    "is_big_endian":signal._is_little_endian == 0,
                    "is_signed":signal._is_signed
                })
            exportArray.append({"name" : frame._name, "id" : int(frame._Id), "is_extended_frame": frame._extended == 1,"signals": signals })
    else: # exportall
        for frame in db._fl._list:
            frameattribs = {}
            for attribute in frame._attributes:
                frameattribs[attribute] = frame._attributes[attribute]
            signals = []
            for signal in frame._signals:
                attribs = {}
                for attribute in signal._attributes:
                    attribs[attribute] = signal._attributes[attribute]
                signals.append({
                    "name" : signal._name,
                    "start_bit" : signal.getLsbStartbit(),
                    "bit_length" : signal._signalsize,
                    "factor":float(signal._factor),
                    "offset":float(signal._offset),
                    "is_big_endian":signal._is_little_endian == 0,
                    "is_signed":signal._is_signed,
                    "comment":signal._comment,
                    "attributes":attribs
                })
            exportArray.append(
                {"name" : frame._name, 
                 "id" : int(frame._Id),
                 "is_extended_frame": frame._extended == 1,
                 "signals": signals,
                 "attributes": frameattribs,
                 "comment": frame._comment })

    json.dump({"messages" : exportArray}, f, sort_keys=True, indent=4, separators=(',', ': '))
