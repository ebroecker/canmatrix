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
# this script exports sym-files from a canmatrix-object
# sym-files are the can-matrix-definitions of the Peak Systems Tools
from __future__ import division
from __future__ import absolute_import

import logging
logger = logging.getLogger('root')

from builtins import *
import collections
import math
import shlex
from .canmatrix import *
import re
import codecs
import sys

enumDict = {}
enums = "{ENUMS}\n"


def format_float(f):
    s = str(f).upper()
    if s.endswith('.0'):
        s = s[:-2]

    if 'E' in s:
        s = s.split('E')
        s = '%sE%s%s' % (s[0], s[1][0], s[1][1:].rjust(3, '0'))

    return s.upper()


def createSignal(signal):
    global enums
    global enumDict
    output = ""
    output += "Var=%s " % (signal.name)
    if not signal.is_signed:
        output += "unsigned "
    else:
        output += "signed "
    startBit = signal.getStartbit()
    if signal.is_little_endian == 0:
        # Motorola
        output += "%d,%d -m " % (startBit, signal.signalsize)
    else:
        output += "%d,%d " % (startBit, signal.signalsize)
    if signal.attributes.get('HexadecimalOutput', False):
        output += "-h "
    if len(signal.unit) > 0:
        output += "/u:%s " % (signal.unit[0:16])
    if float(signal.factor) != 1:
        output += "/f:%s " % (format_float(signal.factor))
    if float(signal.offset) != 0:
        output += "/o:%s " % (format_float(signal.offset))

    if signal.calcMin() != signal.min:
        output += "/min:{} ".format(format_float(signal.min))

    if signal.calcMax() != signal.max:
        output += "/max:{} ".format(format_float(signal.max))

    displayDecimalPlaces = signal.attributes.get('DisplayDecimalPlaces')
    if displayDecimalPlaces is not None:
        output += "/p:%d " % (int(displayDecimalPlaces))

    if len(signal.values) > 0:
        valTabName = signal.enumeration
        if valTabName is None:
            valTabName = signal.name

        output += "/e:%s " % (valTabName)
        if valTabName not in enumDict:
            enumDict[valTabName] = "enum " + valTabName + "(" + ', '.join(
                '%s="%s"' %
                (key, val) for (
                    key, val) in sorted(
                    signal.values.items())) + ")"

    if "GenSigStartValue" in signal.attributes:
        default = float(signal.attributes[
                        "GenSigStartValue"]) * float(signal.factor)
        if default >= float(
                signal.min) and default <= float(signal.max):
            output += "/d:%g " % (default)

    long_name = signal.attributes.get('LongName')
    if long_name is not None:
        output += '/ln:"{}" '.format(long_name)

    output = output.rstrip()
    if signal.comment is not None and len(signal.comment) > 0:
        output += "\t// " + signal.comment.replace('\n', ' ').replace('\r', ' ')
    output += "\n"
    return output


def dump(db, f, **options):
    """
    export canmatrix-object as .sym file (compatible to PEAK-Systems)
    """
    global enumDict
    global enums
    if 'symExportEncoding' in options:
        symEncoding = options["symExportEncoding"]
    else:
        symEncoding = 'iso-8859-1'

    enumDict = {}
    enums = "{ENUMS}\n"

    header = """FormatVersion=5.0 // Do not edit this line!
Title=\"canmatrix-Export\"
"""
    f.write(header.encode(symEncoding))

    def sendreceive(f):
        return (
            f.attributes.get('Sendable', 'True') == 'True',
            f.attributes.get('Receivable', 'True') == 'True',
        )

    sections = collections.OrderedDict((
        ('SEND', tuple(f for f in db.frames if sendreceive(f) == (True, False))),
        ('RECEIVE', tuple(f for f in db.frames if sendreceive(f) == (False, True))),
        ('SENDRECEIVE', tuple(f for f in db.frames if sendreceive(f) == (True, True))),
    ))

    output = '\n'

    for name, frames in sections.items():
        if len(frames) == 0:
            continue

        # Frames
        output += "{{{}}}\n\n".format(name)

        # trigger all frames
        for frame in frames:
            name = "[" + frame.name + "]\n"

            idType = "ID=%08Xh" % (frame.id)
            if frame.comment is not None and len(frame.comment) > 0:
                idType += "\t// " + \
                    frame.comment.replace('\n', ' ').replace('\r', ' ')
            idType += "\n"
            if frame.extended == 1:
                idType += "Type=Extended\n"
            else:
                idType += "Type=Standard\n"

            # check if frame has multiplexed signals
            multiplex = 0
            for signal in frame.signals:
                if signal.multiplex is not None:
                    multiplex = 1

            if multiplex == 1:
                # search for multiplexor in frame:
                for signal in frame.signals:
                    if signal.multiplex == 'Multiplexor':
                        muxSignal = signal

                # ticker all possible mux-groups as i (0 - 2^ (number of bits of
                # multiplexor))
                first = 0
                for i in range(0, 1 << int(muxSignal.signalsize)):
                    found = 0
                    muxOut = ""
                    # ticker all signals
                    for signal in frame.signals:
                        # if signal is in mux-group i
                        if signal.multiplex == i:
                            muxOut = name
                            if first == 0:
                                muxOut += idType
                                first = 1
                            muxOut += "DLC=%d\n" % (frame.size)
                            if "GenMsgCycleTime" in frame.attributes:
                                muxOut += "CycleTime=" + \
                                          frame.attributes[
                                              "GenMsgCycleTime"] + "\n"

                            muxName = frame.mux_names.get(
                                i, muxSignal.name + "%d" % i)

                            muxOut += "Mux=" + muxName
                            startBit = muxSignal.getStartbit()
                            s = str(i)
                            if len(s) > 1:
                                s = '{:04X}h'.format(i)
                            if signal.is_little_endian == 0:
                                # Motorola
                                muxOut += " %d,%d %s -m" % (startBit,
                                                            muxSignal.signalsize, s)
                            else:
                                muxOut += " %d,%d %s" % (startBit,
                                                         muxSignal.signalsize, s)
                            if not muxOut.endswith('h'):
                                muxOut += ' '
                            if i in muxSignal.comments:
                                comment = muxSignal.comments.get(i)
                                if len(comment) > 0:
                                    muxOut += '\t// ' + comment
                            muxOut += "\n"
                            found = 1
                            break

                    if found == 1:
                        for signal in frame.signals:
                            if signal.multiplex == i or signal.multiplex is None:
                                muxOut += createSignal(signal)
                        output += muxOut + "\n"

            else:
                # no multiplex signals in frame, just 'normal' signals
                output += name
                output += idType
                output += "DLC=%d\n" % (frame.size)
                if "GenMsgCycleTime" in frame.attributes:
                    output += "CycleTime=" + \
                        frame.attributes["GenMsgCycleTime"] + "\n"
                for signal in frame.signals:
                    output += createSignal(signal)
                output += "\n"
    enums += '\n'.join(sorted(enumDict.values()))
    # write outputfile
    f.write((enums + '\n').encode(symEncoding))
    f.write(output.encode(symEncoding))


def load(f, **options):
    if 'symImportEncoding' in options:
        symImportEncoding = options["symImportEncoding"]
    else:
        symImportEncoding = 'iso-8859-1'

    class Mode(object):
        glob, enums, send, sendReceive, receive = list(range(5))
    mode = Mode.glob

    frameName = ""
    frame = None

    db = CanMatrix()
    db.addFrameDefines("GenMsgCycleTime", 'INT 0 65535')
    db.addFrameDefines("Receivable", 'BOOL False True')
    db.addFrameDefines("Sendable", 'BOOL False True')
    db.addSignalDefines("GenSigStartValue", 'FLOAT -3.4E+038 3.4E+038')
    db.addSignalDefines("HexadecimalOutput", 'BOOL False True')
    db.addSignalDefines("DisplayDecimalPlaces", 'INT 0 65535')
    db.addSignalDefines("LongName", 'STR')

    for line in f:
        line = line.decode(symImportEncoding).strip()
        # ignore emty line:
        if line.__len__() == 0:
            continue

        # switch mode:
        if line[0:7] == "{ENUMS}":
            mode = Mode.enums
            continue
        if line[0:6] == "{SEND}":
            mode = Mode.send
            continue
        if line[0:13] == "{SENDRECEIVE}":
            mode = Mode.sendReceive
            continue
        if line[0:9] == "{RECEIVE}":
            mode = Mode.receive
            continue

        if mode == Mode.glob:
            # just ignore headers...
            continue
        elif mode == Mode.enums:
            line = line.strip()
            if line.startswith('enum'):
                while not line[5:].strip().endswith(')'):
                    line = line.split('//')[0]
                    if sys.version_info > (3, 0):  # is there a clean way to to it?
                        line += ' ' + f.readline().decode(symImportEncoding).strip()
                    else:
                        line += ' ' + f.next().decode(symImportEncoding).strip()
                line = line.split('//')[0]
                tempArray = line[5:].replace(')', '').split('(')
                valtabName = tempArray[0]
                split = shlex.split(tempArray[1])
                tempArray = [s.rstrip(',') for s in split]
                tempValTable = {}
                for entry in tempArray:
                    tempValTable[entry.split('=')[0].strip()] = entry.split('=')[
                        1].replace('"', '').strip()
                db.addValueTable(valtabName, tempValTable)

        elif mode in {Mode.send, Mode.sendReceive, Mode.receive}:
            if line.startswith('['):
                multiplexor = None
                # found new frame:
                if frameName != line.replace('[', '').replace(']', '').strip():
                    frameName = line.replace('[', '').replace(']', '').strip()
                    # TODO: CAMPid 939921818394902983238
                    if frame is not None:
                        if len(frame.mux_names) > 0:
                            frame.signalByName(
                                frame.name + "_MUX").values = frame.mux_names
                        db._fl.addFrame(frame)

                    frame = Frame(frameName)

                    frame.addAttribute(
                        'Receivable',
                        mode in {Mode.receive, Mode.sendReceive}
                    )
                    frame.addAttribute(
                        'Sendable',
                        mode in {Mode.send, Mode.sendReceive}
                    )

            # key value:
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

                is_float = False
                if indexOffset != 1:
                    is_signed = True
                else:
                    is_signed = False

                    if tempArray[1] == 'unsigned':
                        pass
                    elif tempArray[1] == 'bit':
                        # TODO: actually support bit instead of interpreting as
                        # an unsigned
                        pass
                    elif tempArray[1] == 'signed':
                        is_signed = True
                    elif tempArray[1] == 'float':
                        is_float = True
                    elif tempArray[1] in ['string']:
                        # TODO: actually support these variable types instead
                        # of skipping
                        print('Variable type \'{}\' found and skipped'
                              .format(tempArray[1]))
                        continue
                    else:
                        raise ValueError(
                            'Unknown type \'{}\' found'.format(
                                tempArray[1]))

                startBit = int(tempArray[indexOffset + 1].split(',')[0])
                signalLength = int(tempArray[indexOffset + 1].split(',')[1])
                intel = 1
                unit = ""
                factor = 1
                max = None
                min = None
                longName = None
                startValue = None
                offset = 0
                valueTableName = None
                hexadecimal_output = False
                displayDecimalPlaces = None

                if tmpMux == "Mux":
                    multiplexor = tempArray[2]
                    if multiplexor[-1] == 'h':
                        multiplexor = int(multiplexor[:-1], 16)
                    else:
                        multiplexor = int(multiplexor)
                    frame.mux_names[multiplexor] = sigName
                    indexOffset = 2

                for switch in tempArray[indexOffset + 2:]:
                    if switch == "-m":
                        intel = 0
                    elif switch == "-h":
                        hexadecimal_output = True
                    elif switch.startswith('/'):
                        s = switch[1:].split(':')
                        if s[0] == 'u':
                            unit = s[1]
                        elif s[0] == 'f':
                            factor = s[1]
                        elif s[0] == 'd':
                            startValue = s[1]
                        elif s[0] == 'p':
                            displayDecimalPlaces = s[1] 
                        elif s[0] == 'o':
                            offset = s[1]
                        elif s[0] == 'e':
                            valueTableName = s[1]
                        elif s[0] == 'max':
                            max = s[1]
                        elif s[0] == 'min':
                            min = s[1]
                        elif s[0] == 'ln':
                            longName = s[1]
#                                               else:
#                                                       print switch
#                                       else:
#                                               print switch
                if tmpMux == "Mux":
                    signal = frame.signalByName(frameName + "_MUX")
                    if signal is None:
                        signal = Signal(frameName + "_MUX",
                                        startBit=startBit,
                                        signalSize=signalLength,
                                        is_little_endian=intel,
                                        is_signed=is_signed,
                                        is_float=is_float,
                                        factor=factor,
                                        offset=offset,
                                        min=min,
                                        max=max,
                                        unit=unit,
                                        multiplex='Multiplexor',
                                        comment=comment)
#                        signal.addComment(comment)
                        if intel == 0:
                            # motorola set/convert startbit
                            signal.setStartbit(startBit)
                        frame.addSignal(signal)
                    signal.comments[multiplexor] = comment

                else:
                 #                   signal = Signal(sigName, startBit, signalLength, intel, is_signed, factor, offset, min, max, unit, "", multiplexor)
                    signal = Signal(sigName,
                                    startBit=startBit,
                                    signalSize=signalLength,
                                    is_little_endian=intel,
                                    is_signed=is_signed,
                                    is_float=is_float,
                                    factor=factor,
                                    offset=offset,
                                    min=min,
                                    max=max,
                                    unit=unit,
                                    multiplex=multiplexor,
                                    comment=comment)
#
                    if intel == 0:
                        # motorola set/convert startbit
                        signal.setStartbit(startBit)
                    if valueTableName is not None:
                        signal.values = db.valueTables[valueTableName]
                        signal.enumeration = valueTableName
  #                  signal.addComment(comment)
                    # ... (1 / ...) because this somehow made 59.8/0.1 be 598.0 rather than 597.9999999999999
                    if startValue is not None:
                        startValue = float(startValue) * (1 / float(factor))
                        signal.addAttribute("GenSigStartValue", str(startValue))
                    frame.addSignal(signal)
                if longName is not None:
                    signal.addAttribute("LongName", longName)
                if hexadecimal_output:
                    signal.addAttribute("HexadecimalOutput", str(True))
                if displayDecimalPlaces is not None:
                    signal.addAttribute(
                        "DisplayDecimalPlaces", displayDecimalPlaces)
                # variable processing
            elif line.startswith('ID'):
                comment = ""
                if '//' in line:
                    comment = line.split('//')[1].strip()
                    line = line.split('//')[0]
                frame.id = int(line.split('=')[1].strip()[:-1], 16)
                frame.addComment(comment)
            elif line.startswith('Type'):
                if line.split('=')[1][:8] == "Extended":
                    frame.extended = 1
            elif line.startswith('DLC'):
                frame.size = int(line.split('=')[1])

            elif line.startswith('CycleTime'):
                frame.addAttribute(
                    "GenMsgCycleTime",
                    line.split('=')[1].strip())
#                       else:
#                               print line
#               else:
#                       print "Unrecocniced line: " + l + " (%d) " % i
    # TODO: CAMPid 939921818394902983238
    if frame is not None:
        if len(frame.mux_names) > 0:
            frame.signalByName(frame.name + "_MUX").values = frame.mux_names
        db._fl.addFrame(frame)

    return db
