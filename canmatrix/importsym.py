from __future__ import division
from __future__ import absolute_import

import logging
logger = logging.getLogger('root')

from builtins import *
import math
import shlex
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
# this script imports sym-files to a canmatrix-object
# sym-files are the can-matrix-definitions of peak tools
#
#TODO : the signalname should be unique. If same signal-name is used in different mux-ids, the signal-name should be unified. maybe this is an dbc-export-issue not an sym-import-issue
#TODO : I don't know what to do with the "/p"-Options in the signal-definition
#TODO : what is the differenze between SEND and SENDRECEIVE ?
# currently only for FormatVersion=5.0
#TODO: support for title example: Title="some title"

from .canmatrix import *
import re
import codecs


def importSym(filename, **options):
    if 'symImportEncoding' in options:
        symImportEncoding=options["symImportEncoding"]
    else:
        symImportEncoding='iso-8859-1'


    class Mode(object):
        glob, enums, send, sendReceive = list(range(4))
    mode = Mode.glob
    valueTables = {}

    frameName = ""
    frame = None

    db = CanMatrix()
    db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')
    db.addSignalDefines("GenSigStartValue", 'FLOAT -3.4E+038 3.4E+038')
    f = open(filename, "rb")

    for line in f:
        line = line.decode(symImportEncoding).strip()
        #ignore emty line:
        if line.__len__() == 0:
            continue

        #switch mode:
        if line[0:7] == "{ENUMS}":
            mode = Mode.enums
            continue;
        if line[0:6] == "{SEND}":
            mode = Mode.send
            continue;
        if line[0:13] == "{SENDRECEIVE}":
            mode = Mode.sendReceive
            continue;


        if mode == Mode.glob:
            # just ignore headers...
            continue
        elif mode == Mode.enums:
            line = line.strip()
            if line.startswith('enum'):
                while not line[5:].strip().endswith(')'):
                    line = line.split('//')[0]
                    line += ' ' + f.readline().decode(symImportEncoding).strip()
                line = line.split('//')[0]
                tempArray = line[5:].replace(')','').split('(')
                valtabName = tempArray[0]
                split = shlex.split(tempArray[1])
                tempArray = [s.rstrip(',') for s in split]
                tempValTable = {}
                for entry in tempArray:
                    tempValTable[entry.split('=')[0].strip()] = entry.split('=')[1].replace('"','').strip()
                valueTables[valtabName] = tempValTable

        elif mode == Mode.send or mode == Mode.sendReceive:
            if line.startswith('['):
                multiplexor = None
                # found new frame:
                if frameName != line.replace('[','').replace(']','').strip():
                    frameName = line.replace('[','').replace(']','').strip()
                    if frame is not None:
                        if len(multiplexValTable) > 0:
                            frame.signalByName(frame._name + "_MUX")._values = multiplexValTable
                        db._fl.addFrame(frame)

                    frame = Frame(frameName)
                    multiplexValTable = {}

            #key value:
            elif line.startswith('Var') or line.startswith('Mux'):
                tmpMux = line[:3]
                line = line[4:]
                comment = ""
                indexOffset = 1
                if tmpMux == "Mux":
                    indexOffset = 0
                comment = ""
                if '//' in line:
                    comment = line.split('//')[1].strip()
                    line = line.split('//')[0]
                line = line.replace('  ', ' "" ')
                tempArray = shlex.split(line.strip())
                sigName = tempArray[0]

                if indexOffset != 1:
                    is_signed = True
                else:
                    if tempArray[1] == 'unsigned':
                        is_signed = False
                    elif tempArray[1] == 'signed':
                        is_signed = True
                    elif tempArray[1] == 'string':
                        # TODO: actually support string variables instead of skipping
                        print('Variable type \'string\' found and skipped')
                        continue
                    else:
                        raise ValueError('Unknown type \'{}\' found'.format(tempArray[1]))

                startBit = int(tempArray[indexOffset+1].split(',')[0])
                signalLength = int(tempArray[indexOffset+1].split(',')[1])
                intel = 1
                unit = ""
                factor = 1
                max = None
                min = None
                longName = None
                startValue = 0
                offset = 0
                valueTableName = None

                if tmpMux == "Mux":
                    multiplexor= tempArray[2]
                    if multiplexor[-1] == 'h':
                        multiplexor = int(multiplexor[:-1], 16)
                    else:
                        multiplexor = int(multiplexor)
                    multiplexor = str(multiplexor)
                    multiplexValTable[multiplexor] = sigName
                    indexOffset = 2

                for switch in tempArray[indexOffset+2:]:
                    if switch == "-m":
                        intel = 0
                    elif switch == "-h":
                        #hexadecimal output - not supported
                        pass
                    elif switch.startswith('/'):
                        if switch[1:].split(':')[0] == 'u':
                            unit = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'f':
                            factor = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'd':
                            startValue = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'p':
                            pass
                            #TODO /p ???
                        elif switch[1:].split(':')[0] == 'o':
                            offset = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'e':
                            valueTableName = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'max':
                            max = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'min':
                            min = switch[1:].split(':')[1]
                        elif switch[1:].split(':')[0] == 'ln':
                            longName = switch[1:].split(':')[1]
#                                               else:
#                                                       print switch
#                                       else:
#                                               print switch
                # ... (1 / ...) because this somehow made 59.8/0.1 be 598.0 rather than 597.9999999999999
                startValue = float(startValue) * (1 / float(factor))
                if tmpMux == "Mux":
                    signal = frame.signalByName(frameName + "_MUX")
                    if signal == None:
                        signal = Signal(frameName + "_MUX", 
                                          startBit = startBit, 
                                          signalSize = signalLength,
                                          is_little_endian=intel, 
                                          is_signed = is_signed, 
                                          factor=factor, 
                                          offset=offset,
                                          min=min,
                                          max=max,
                                          unit=unit,
                                          multiplex='Multiplexor',
                                          comment=comment)     
#                        signal.addComment(comment)
                        if intel == 0:
                            #motorola set/convert startbit
                            signal.setMsbReverseStartbit(startBit)
                        frame.addSignal(signal)

                else:
 #                   signal = Signal(sigName, startBit, signalLength, intel, is_signed, factor, offset, min, max, unit, "", multiplexor)
                    signal = Signal(sigName, 
                                      startBit = startBit, 
                                      signalSize = signalLength,
                                      is_little_endian=intel, 
                                      is_signed = is_signed, 
                                      factor=factor, 
                                      offset=offset,
                                      min=min,
                                      max=max,
                                      unit=unit,
                                      multiplex=multiplexor,
                                      comment=comment)     
#
                    if intel == 0:
                        #motorola set/convert startbit
                        signal.setMsbReverseStartbit(startBit)
                    if valueTableName is not None:
                        signal._values = valueTables[valueTableName]
  #                  signal.addComment(comment)
                    signal.addAttribute("GenSigStartValue", str(startValue))
                    frame.addSignal(signal)
                if longName is not None:
                    signal.addAttribute("LongName", longName)
                #variable processing
            elif line.startswith('ID'):
                comment = ""
                if '//' in line:
                    comment = line.split('//')[1].strip()
                    line = line.split('//')[0]
                frame._Id = int(line.split('=')[1].strip()[:-1], 16)
                frame.addComment(comment)
            elif line.startswith('Type'):
                if line.split('=')[1][:8] == "Extended":
                    frame._extended = 1
            elif line.startswith('DLC'):
                frame._Size = int(line.split('=')[1])

            elif line.startswith('CycleTime'):
                frame.addAttribute("GenMsgCycleTime", line.split('=')[1].strip())
#                       else:
#                               print line
#               else:
#                       print "Unrecocniced line: " + l + " (%d) " % i
    if frame is not None:
        db._fl.addFrame(frame)

    return db
