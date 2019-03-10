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

from __future__ import absolute_import
from __future__ import division

import collections
import decimal
import logging
import sys
import typing
from builtins import *

import attr

import canmatrix
import canmatrix.utils

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal

enumDict = {}  # type: typing.Dict[str, str]
enums = "{ENUMS}\n"


@attr.s
class ParsingError(Exception):
    line_number = attr.ib()
    line = attr.ib()
    message = attr.ib(default=None)
    original = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.message is None:
            self.message = self.line

        self.message = 'line {line_number}: {message}'.format(
            line_number=self.line_number,
            message=self.message
        )
        super(ParsingError, self).__init__(self.message)

    def __str__(self):
        return self.message


@attr.s
class DuplicateMuxIdError(ParsingError):
    id = attr.ib(default=None)
    old = attr.ib(default=None)
    new = attr.ib(default=None)

    def __attrs_post_init__(self):
        if None in (self.id, self.old, self.new):
            raise Exception('ack')

        self.message = (
            '{id:X}h already in use'
            ' (old: {old}, new: {new})'
        ).format(
            id=self.id,
            old=self.old,
            new=self.new,
        )
        super(DuplicateMuxIdError, self).__attrs_post_init__()


def format_float(f):
    s = str(f).upper()
    if s.endswith('.0'):
        s = s[:-2]

    if 'E' in s:
        tmp = s.split('E')
        s = '%sE%s%s' % (tmp[0], tmp[1][0], tmp[1][1:].rjust(3, '0'))

    return s.upper()


def create_signal(db, signal):
    global enums
    global enumDict
    output = ""
    output += "Var=%s " % (signal.name)
    if not signal.is_signed:
        output += "unsigned "
    else:
        output += "signed "
    startBit = signal.get_startbit()
    if signal.is_little_endian == 0:
        # Motorola
        output += "%d,%d -m " % (startBit, signal.size)
    else:
        output += "%d,%d " % (startBit, signal.size)
    if signal.attributes.get('HexadecimalOutput', False):
        output += "-h "
    if len(signal.unit) > 0:
        t = signal.unit[0:16]
        if " " in t:
            format_string = '/u:"%s" '
        else:
            format_string = '/u:%s '
        output += format_string % (t)
    if float(signal.factor) != 1:
        output += "/f:%s " % (format_float(signal.factor))
    if float(signal.offset) != 0:
        output += "/o:%s " % (format_float(signal.offset))

    if signal.min is not None:
        output += "/min:{} ".format(format_float(signal.min))

    if signal.max is not None:
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

    if "GenSigStartValue" in db.signal_defines:
        genSigStartVal = signal.attribute("GenSigStartValue", db=db)
        if genSigStartVal is not None:
            factory = (
                signal.float_factory
                if signal.is_float
                else int
            )
            default = factory(genSigStartVal) * signal.factor
            min_ok = signal.min is None or default >= signal.min
            max_ok = signal.max is None or default <= signal.max
            if min_ok and max_ok:
                output += "/d:{} ".format(default)

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
    symEncoding = options.get('symExportEncoding', 'iso-8859-1')

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

            if frame.arbitration_id.extended == 1:
                idType = "ID=%08Xh" % (frame.arbitration_id.id)
            else:
                idType = "ID=%03Xh" % (frame.arbitration_id.id)
            if frame.comment is not None and len(frame.comment) > 0:
                idType += "\t// " + \
                    frame.comment.replace('\n', ' ').replace('\r', ' ')
            idType += "\n"
            if frame.arbitration_id.extended == 1:
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
                for i in range(0, 1 << int(muxSignal.size)):
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
                            if "GenMsgCycleTime" in db.frame_defines:
                                cycleTime = frame.attribute("GenMsgCycleTime", db=db)
                                if cycleTime is not None:
                                    muxOut += "CycleTime=" + str(cycleTime) + "\n"

                            muxName = frame.mux_names.get(
                                i, muxSignal.name + "%d" % i)

                            muxOut += "Mux=" + muxName
                            startBit = muxSignal.get_startbit()
                            s = str(i)
                            if len(s) > 1:
                                length = len(
                                    '{:X}'.format(int(muxSignal.calc_max()))
                                )
                                s = '{:0{}X}h'.format(i, length)
                            if signal.is_little_endian == 0:
                                # Motorola
                                muxOut += " %d,%d %s -m" % (startBit,
                                                            muxSignal.size, s)
                            else:
                                muxOut += " %d,%d %s" % (startBit,
                                                         muxSignal.size, s)
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
                                muxOut += create_signal(db, signal)
                        output += muxOut + "\n"

            else:
                # no multiplex signals in frame, just 'normal' signals
                output += name
                output += idType
                output += "DLC=%d\n" % (frame.size)
                if "GenMsgCycleTime" in db.frame_defines:
                    cycleTime = frame.attribute("GenMsgCycleTime", db=db)
                    if cycleTime is not None:
                        output += "CycleTime=" + str(cycleTime) + "\n"
                for signal in frame.signals:
                    output += create_signal(db, signal)
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

    calc_min_for_none = options.get('calc_min_for_none')
    calc_max_for_none = options.get('calc_max_for_none')
    float_factory = options.get('float_factory', default_float_factory)

    class Mode(object):
        glob, enums, send, sendReceive, receive = list(range(5))
    mode = Mode.glob

    frameName = ""
    frame = None

    db = canmatrix.CanMatrix()
    db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
    db.add_frame_defines("Receivable", 'BOOL False True')
    db.add_frame_defines("Sendable", 'BOOL False True')
    db.add_signal_defines("GenSigStartValue", 'FLOAT -3.4E+038 3.4E+038')
    db.add_signal_defines("HexadecimalOutput", 'BOOL False True')
    db.add_signal_defines("DisplayDecimalPlaces", 'INT 0 65535')
    db.add_signal_defines("LongName", 'STR')

    for linecount, line in enumerate(f, 1):
        try:
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
                            line += ' ' + next(f).decode(symImportEncoding).strip()
                    line = line.split('//')[0]
                    tempArray = line[5:].strip().rstrip(')').split('(', 1)
                    valtabName = tempArray[0]
                    split = canmatrix.utils.quote_aware_space_split(tempArray[1])
                    tempArray = [s.rstrip(',') for s in split]
                    tempValTable = {}
                    for entry in tempArray:
                        tempValTable[entry.split('=')[0].strip()] = entry.split('=')[
                            1].replace('"', '').strip()
                    db.add_value_table(valtabName, tempValTable)

            elif mode in {Mode.send, Mode.sendReceive, Mode.receive}:
                if line.startswith('['):
                    multiplexor = None
                    # found new frame:
                    if frameName != line.replace('[', '').replace(']', '').replace('"','').strip():
                        frameName = line.replace('[', '').replace(']', '').replace('"','').strip()
                        # TODO: CAMPid 939921818394902983238
                        if frame is not None:
                            if len(frame.mux_names) > 0:
                                frame.signal_by_name(
                                    frame.name + "_MUX").values = frame.mux_names
                            db.add_frame(frame)

                        frame = canmatrix.Frame(frameName)

                        frame.add_attribute(
                            'Receivable',
                            mode in {Mode.receive, Mode.sendReceive}
                        )
                        frame.add_attribute(
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
                        split = line.split('//', 1)
                        comment = split[1].strip()
                        line = split[0].strip()
                    line = line.replace('  ', ' "" ')

                    tempArray = canmatrix.utils.quote_aware_space_split(line)
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
                        elif tempArray[1] in ['float', 'double']:
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
                    intel = True
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
                        if multiplexor in frame.mux_names:
                            raise DuplicateMuxIdError(
                                id=multiplexor,
                                old=frame.mux_names[multiplexor],
                                new=sigName,
                                line_number=linecount,
                                line=line,
                            )
                        frame.mux_names[multiplexor] = sigName
                        indexOffset = 2

                    for switch in tempArray[indexOffset + 2:]:
                        if switch == "-m":
                            intel = 0
                        elif switch == "-h":
                            hexadecimal_output = True
                        elif switch.startswith('/'):
                            s = switch[1:].split(':', 1)
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
                        signal = frame.signal_by_name(frameName + "_MUX")
                        if signal is None:
                            extras = {}
                            if calc_min_for_none is not None:
                                extras['calc_min_for_none'] = calc_min_for_none
                            if calc_max_for_none is not None:
                                extras['calc_max_for_none'] = calc_max_for_none
#                            if float_factory is not None:
#                                extras['float_factory'] = float_factory

                            signal = canmatrix.Signal(frameName + "_MUX",
                                            start_bit=int(startBit),
                                            size=int(signalLength),
                                            is_little_endian=intel,
                                            is_signed=is_signed,
                                            is_float=is_float,
                                            factor=factor,
                                            offset=offset,
                                            unit=unit,
                                            multiplex='Multiplexor',
                                            comment=comment,
                                            **extras)
                            if min is not None:
                                signal.min = float_factory(min)
                            if max is not None:
                                signal.max = float_factory(max)
    #                        signal.add_comment(comment)
                            if intel == 0:
                                # motorola set/convert startbit
                                signal.set_startbit(startBit)
                            frame.add_signal(signal)
                        signal.comments[multiplexor] = comment

                    else:
                     #                   signal = Signal(sigName, startBit, signalLength, intel, is_signed, factor, offset, min, max, unit, "", multiplexor)
                        extras = {}
                        if calc_min_for_none is not None:
                            extras['calc_min_for_none'] = calc_min_for_none
                        if calc_max_for_none is not None:
                            extras['calc_max_for_none'] = calc_max_for_none
#                        if float_factory is not None:
#                            extras['float_factory'] = float_factory

                        signal = canmatrix.Signal(sigName,
                                        start_bit=int(startBit),
                                        size=int(signalLength),
                                        is_little_endian=intel,
                                        is_signed=is_signed,
                                        is_float=is_float,
                                        factor=factor,
                                        offset=offset,
                                        unit=unit,
                                        multiplex=multiplexor,
                                         comment=comment,
                                         **extras)
                        if min is not None:
                            signal.min = float_factory(min)
                        if max is not None:
                            signal.max = float_factory(max)
    #
                        if intel == 0:
                            # motorola set/convert startbit
                            signal.set_startbit(startBit)
                        if valueTableName is not None:
                            signal.values = db.value_tables[valueTableName]
                            signal.enumeration = valueTableName
      #                  signal.add_comment(comment)
                        # ... (1 / ...) because this somehow made 59.8/0.1 be 598.0 rather than 597.9999999999999
                        if startValue is not None:
                            startValue = float_factory(startValue) * (1 / float_factory(factor))
                            signal.add_attribute("GenSigStartValue", str(startValue))
                        frame.add_signal(signal)
                    if longName is not None:
                        signal.add_attribute("LongName", longName)
                    if hexadecimal_output:
                        signal.add_attribute("HexadecimalOutput", str(True))
                    if displayDecimalPlaces is not None:
                        signal.add_attribute(
                            "DisplayDecimalPlaces", displayDecimalPlaces)
                    # variable processing
                elif line.startswith('ID'):
                    comment = ""
                    if '//' in line:
                        split = line.split('//', 1)
                        comment = split[1].strip()
                        line = split[0].strip()
                    frame.arbitration_id.id  = int(line.split('=')[1].strip()[:-1], 16)
                    frame.add_comment(comment)
                elif line.startswith('Type'):
                    if line.split('=')[1][:8] == "Extended":
                        frame.arbitration_id.extended = 1
                elif line.startswith('DLC'):
                    frame.size = int(line.split('=')[1])

                elif line.startswith('CycleTime'):
                    frame.add_attribute(
                        "GenMsgCycleTime",
                        line.split('=')[1].strip())
#                       else:
#                               print line
#               else:
#                       print "Unrecocniced line: " + l + " (%d) " % i
        except Exception as e:
            if not isinstance(e, ParsingError):
                ParsingError(
                    message=str(e),
                    line_number=linecount,
                    line=line,
                    original=e,
                )

            db.load_errors.append(e)

            logger.error("Error decoding line %d" % linecount)
            logger.error(line)
    # TODO: CAMPid 939921818394902983238
    if frame is not None:
        if len(frame.mux_names) > 0:
            frame.signal_by_name(frame.name + "_MUX").values = frame.mux_names
        db.add_frame(frame)

    return db
