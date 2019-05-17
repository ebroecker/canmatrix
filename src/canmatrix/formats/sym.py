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
enum_dict = {}  # type: typing.Dict[str, str]
enums = "{ENUMS}\n"


def default_float_factory(value):  # type: (typing.Any) -> decimal.Decimal
    return decimal.Decimal(value)


@attr.s
class ParsingError(Exception):
    line_number = attr.ib()  # type: int
    line = attr.ib()  # type: str
    message = attr.ib(default=None)  # type: typing.Optional[str]
    original = attr.ib(default=None)  # type: typing.Optional[Exception]

    def __attrs_post_init__(self):  # type: () -> None
        if self.message is None:
            self.message = self.line

        self.message = 'line {line_number}: {message}'.format(
            line_number=self.line_number,
            message=self.message
        )
        super(ParsingError, self).__init__(self.message)

    def __str__(self):  # type: () -> str
        return self.message


@attr.s
class DuplicateMuxIdError(ParsingError):
    id = attr.ib(default=None)  # type: int
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


def format_float(f):  # type: (typing.Any) -> str
    s = str(f).upper()
    if s.endswith('.0'):
        s = s[:-2]

    if 'E' in s:
        tmp = s.split('E')
        s = '%sE%s%s' % (tmp[0], tmp[1][0], tmp[1][1:].rjust(3, '0'))

    return s.upper()


def create_signal(db, signal):  # type: (canmatrix.CanMatrix, canmatrix.Signal) -> str
    global enums
    global enum_dict
    output = ""
    output += "Var=%s " % signal.name
    if not signal.is_signed:
        output += "unsigned "
    else:
        output += "signed "
    start_bit = signal.get_startbit()
    if signal.is_little_endian == 0:
        # Motorola
        output += "%d,%d -m " % (start_bit, signal.size)
    else:
        output += "%d,%d " % (start_bit, signal.size)
    if signal.attributes.get('HexadecimalOutput', False):
        output += "-h "
    if len(signal.unit) > 0:
        t = signal.unit[0:16]
        if " " in t:
            format_string = '/u:"%s" '
        else:
            format_string = '/u:%s '
        output += format_string % t
    if float(signal.factor) != 1:
        output += "/f:%s " % (format_float(signal.factor))
    if float(signal.offset) != 0:
        output += "/o:%s " % (format_float(signal.offset))

    if signal.min is not None:
        output += "/min:{} ".format(format_float(signal.min))

    if signal.max is not None:
        output += "/max:{} ".format(format_float(signal.max))

    display_decimal_places = signal.attributes.get('DisplayDecimalPlaces')
    if display_decimal_places is not None:
        output += "/p:%d " % (int(display_decimal_places))

    if len(signal.values) > 0:
        val_tab_name = signal.enumeration
        if val_tab_name is None:
            val_tab_name = signal.name

        output += "/e:%s " % val_tab_name
        if val_tab_name not in enum_dict:
            enum_dict[val_tab_name] = "enum " + val_tab_name + "(" + ', '.join(
                '%s="%s"' %
                (key, val) for (
                    key, val) in sorted(
                    signal.values.items())) + ")"

    if "GenSigStartValue" in db.signal_defines:
        gen_sig_start_val = signal.attribute("GenSigStartValue", db=db)
        if gen_sig_start_val is not None:
            factory = (
                signal.float_factory
                if signal.is_float
                else int
            )
            default = factory(gen_sig_start_val) * signal.factor  # type: ignore
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


def dump(db, f, **options):  # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    """
    export canmatrix-object as .sym file (compatible to PEAK-Systems)
    """
    global enum_dict
    global enums
    sym_encoding = options.get('symExportEncoding', 'iso-8859-1')

    enum_dict = {}
    enums = "{ENUMS}\n"

    header = """FormatVersion=5.0 // Do not edit this line!
Title=\"canmatrix-Export\"
"""
    f.write(header.encode(sym_encoding))

    def send_receive(for_frame):
        return (
            for_frame.attributes.get('Sendable', 'True') == 'True',
            for_frame.attributes.get('Receivable', 'True') == 'True',
        )

    sections = collections.OrderedDict((
        ('SEND', tuple(f for f in db.frames if send_receive(f) == (True, False))),
        ('RECEIVE', tuple(f for f in db.frames if send_receive(f) == (False, True))),
        ('SENDRECEIVE', tuple(f for f in db.frames if send_receive(f) == (True, True))),
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
                id_type = "ID=%08Xh" % frame.arbitration_id.id
            else:
                id_type = "ID=%03Xh" % frame.arbitration_id.id
            if frame.comment is not None and len(frame.comment) > 0:
                id_type += "\t// " + \
                    frame.comment.replace('\n', ' ').replace('\r', ' ')
            id_type += "\n"
            if frame.arbitration_id.extended == 1:
                id_type += "Type=Extended\n"
            else:
                id_type += "Type=Standard\n"

            # check if frame has multiplexed signals
            multiplex = 0
            for signal in frame.signals:
                if signal.multiplex is not None:
                    multiplex = 1

            if multiplex == 1:
                # search for multiplexor in frame:
                for signal in frame.signals:
                    if signal.multiplex == 'Multiplexor':
                        mux_signal = signal

                # ticker all possible mux-groups as i (0 - 2^ (number of bits of multiplexor))
                first = 0
                for i in range(0, 1 << int(mux_signal.size)):
                    found = 0
                    mux_out = ""
                    # ticker all signals
                    for signal in frame.signals:
                        # if signal is in mux-group i
                        if signal.multiplex == i:
                            mux_out = name
                            if first == 0:
                                mux_out += id_type
                                first = 1
                            mux_out += "DLC=%d\n" % frame.size
                            if "GenMsgCycleTime" in db.frame_defines:
                                cycle_time = frame.attribute("GenMsgCycleTime", db=db)
                                if cycle_time is not None:
                                    mux_out += "CycleTime=" + str(cycle_time) + "\n"

                            mux_name = frame.mux_names.get(i, mux_signal.name + "%d" % i)

                            mux_out += "Mux=" + mux_name
                            start_bit = mux_signal.get_startbit()
                            s = str(i)
                            if len(s) > 1:
                                length = len(
                                    '{:X}'.format(int(mux_signal.calc_max()))
                                )
                                s = '{:0{}X}h'.format(i, length)
                            if not signal.is_little_endian:
                                # Motorola
                                mux_out += " %d,%d %s -m" % (start_bit, mux_signal.size, s)
                            else:
                                mux_out += " %d,%d %s" % (start_bit, mux_signal.size, s)
                            if not mux_out.endswith('h'):
                                mux_out += ' '
                            if i in mux_signal.comments:
                                comment = mux_signal.comments.get(i)
                                if len(comment) > 0:
                                    mux_out += '\t// ' + comment
                            mux_out += "\n"
                            found = 1
                            break

                    if found == 1:
                        for signal in frame.signals:
                            if signal.multiplex == i or signal.multiplex is None:
                                mux_out += create_signal(db, signal)
                        output += mux_out + "\n"

            else:
                # no multiplex signals in frame, just 'normal' signals
                output += name
                output += id_type
                output += "DLC=%d\n" % frame.size
                if "GenMsgCycleTime" in db.frame_defines:
                    cycle_time = frame.attribute("GenMsgCycleTime", db=db)
                    if cycle_time is not None:
                        output += "CycleTime=" + str(cycle_time) + "\n"
                for signal in frame.signals:
                    output += create_signal(db, signal)
                output += "\n"
    enums += '\n'.join(sorted(enum_dict.values()))
    # write output file
    f.write((enums + '\n').encode(sym_encoding))
    f.write(output.encode(sym_encoding))


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    if 'symImportEncoding' in options:
        sym_import_encoding = options["symImportEncoding"]
    else:
        sym_import_encoding = 'iso-8859-1'

    calc_min_for_none = options.get('calc_min_for_none')
    calc_max_for_none = options.get('calc_max_for_none')
    float_factory = options.get('float_factory', default_float_factory)

    class Mode(object):
        glob, enums, send, sendReceive, receive = list(range(5))
    mode = Mode.glob

    frame_name = ""
    frame = None

    db = canmatrix.CanMatrix()
    db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
    db.add_frame_defines("Receivable", 'BOOL False True')
    db.add_frame_defines("Sendable", 'BOOL False True')
    db.add_signal_defines("GenSigStartValue", 'FLOAT -3.4E+038 3.4E+038')
    db.add_signal_defines("HexadecimalOutput", 'BOOL False True')
    db.add_signal_defines("DisplayDecimalPlaces", 'INT 0 65535')
    db.add_signal_defines("LongName", 'STR')

    for line_count, line in enumerate(f, 1):
        try:
            line = line.decode(sym_import_encoding).strip()
            # ignore empty line:
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
                            line += ' ' + f.readline().decode(sym_import_encoding).strip()
                        else:
                            line += ' ' + next(f).decode(sym_import_encoding).strip()
                    line = line.split('//')[0]
                    temp_array = line[5:].strip().rstrip(')').split('(', 1)
                    val_table_name = temp_array[0]
                    split = canmatrix.utils.quote_aware_space_split(temp_array[1])
                    temp_array = [s.rstrip(',') for s in split]
                    temp_val_table = {}
                    for entry in temp_array:
                        temp_val_table[entry.split('=')[0].strip()] = entry.split('=')[
                            1].replace('"', '').strip()
                    db.add_value_table(val_table_name, temp_val_table)

            elif mode in {Mode.send, Mode.sendReceive, Mode.receive}:
                if line.startswith('['):
                    multiplexor = None
                    # found new frame:
                    if frame_name != line.replace('[', '').replace(']', '').replace('"', '').strip():
                        frame_name = line.replace('[', '').replace(']', '').replace('"', '').strip()
                        # TODO: CAMPid 939921818394902983238
                        if frame is not None:
                            if len(frame.mux_names) > 0:
                                frame.signal_by_name(
                                    frame.name + "_MUX").values = frame.mux_names
                            db.add_frame(frame)

                        frame = canmatrix.Frame(frame_name)

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
                    tmp_mux = line[:3]
                    line = line[4:]
                    # comment = ""
                    index_offset = 1
                    if tmp_mux == "Mux":
                        index_offset = 0
                    comment = ""
                    if '//' in line:
                        split = line.split('//', 1)
                        comment = split[1].strip()
                        line = split[0].strip()
                    line = line.replace('  ', ' "" ')

                    temp_array = canmatrix.utils.quote_aware_space_split(line)
                    sig_name = temp_array[0]

                    is_float = False
                    if index_offset != 1:
                        is_signed = True
                    else:
                        is_signed = False

                        if temp_array[1] == 'unsigned':
                            pass
                        elif temp_array[1] == 'bit':
                            # TODO: actually support bit instead of interpreting as
                            # an unsigned
                            pass
                        elif temp_array[1] == 'signed':
                            is_signed = True
                        elif temp_array[1] in ['float', 'double']:
                            is_float = True
                        elif temp_array[1] in ['string']:
                            # TODO: actually support these variable types instead
                            # of skipping
                            print('Variable type \'{}\' found and skipped'
                                  .format(temp_array[1]))
                            continue
                        else:
                            raise ValueError('Unknown type \'{}\' found'.format(temp_array[1]))

                    start_bit = int(temp_array[index_offset + 1].split(',')[0])
                    signal_length = int(temp_array[index_offset + 1].split(',')[1])
                    intel = True
                    unit = ""
                    factor = 1
                    max_value = None
                    min_value = None
                    long_name = None
                    start_value = None
                    offset = 0
                    value_table_name = None
                    hexadecimal_output = False
                    display_decimal_places = None

                    if tmp_mux == "Mux":
                        multiplexor = temp_array[2]
                        if multiplexor[-1] == 'h':
                            multiplexor = int(multiplexor[:-1], 16)
                        else:
                            multiplexor = int(multiplexor)
                        if multiplexor in frame.mux_names:
                            raise DuplicateMuxIdError(
                                id=multiplexor,
                                old=frame.mux_names[multiplexor],
                                new=sig_name,
                                line_number=line_count,
                                line=line,
                            )
                        frame.mux_names[multiplexor] = sig_name
                        index_offset = 2

                    for switch in temp_array[index_offset + 2:]:
                        if switch == "-m":
                            intel = False
                        elif switch == "-h":
                            hexadecimal_output = True
                        elif switch.startswith('/'):
                            s = switch[1:].split(':', 1)
                            if s[0] == 'u':
                                unit = s[1]
                            elif s[0] == 'f':
                                factor = s[1]
                            elif s[0] == 'd':
                                start_value = s[1]
                            elif s[0] == 'p':
                                display_decimal_places = s[1]
                            elif s[0] == 'o':
                                offset = s[1]
                            elif s[0] == 'e':
                                value_table_name = s[1]
                            elif s[0] == 'max':
                                max_value = s[1]
                            elif s[0] == 'min':
                                min_value = s[1]
                            elif s[0] == 'ln':
                                long_name = s[1]
    #                                               else:
    #                                                       print switch
    #                                       else:
    #                                               print switch
                    if tmp_mux == "Mux":
                        signal = frame.signal_by_name(frame_name + "_MUX")
                        if signal is None:
                            extras = {}
                            if calc_min_for_none is not None:
                                extras['calc_min_for_none'] = calc_min_for_none
                            if calc_max_for_none is not None:
                                extras['calc_max_for_none'] = calc_max_for_none
                            # if float_factory is not None:
                            #     extras['float_factory'] = float_factory

                            signal = canmatrix.Signal(
                                frame_name + "_MUX",
                                start_bit=int(start_bit),
                                size=int(signal_length),
                                is_little_endian=intel,
                                is_signed=is_signed,
                                is_float=is_float,
                                factor=factor,
                                offset=offset,
                                unit=unit,
                                multiplex='Multiplexor',
                                comment=comment,
                                **extras)
                            if min_value is not None:
                                signal.min = float_factory(min_value)
                            if max_value is not None:
                                signal.max = float_factory(max_value)
                            # signal.add_comment(comment)
                            if intel is False:
                                # motorola set/convert start bit
                                signal.set_startbit(start_bit)
                            frame.add_signal(signal)
                        signal.comments[multiplexor] = comment

                    else:
                        # signal = Signal(sigName, startBit, signalLength, intel, is_signed, factor, offset, min, max, unit, "", multiplexor)
                        extras = {}
                        if calc_min_for_none is not None:
                            extras['calc_min_for_none'] = calc_min_for_none
                        if calc_max_for_none is not None:
                            extras['calc_max_for_none'] = calc_max_for_none
                        # if float_factory is not None:
                        #     extras['float_factory'] = float_factory

                        signal = canmatrix.Signal(
                            sig_name,
                            start_bit=int(start_bit),
                            size=int(signal_length),
                            is_little_endian=intel,
                            is_signed=is_signed,
                            is_float=is_float,
                            factor=factor,
                            offset=offset,
                            unit=unit,
                            multiplex=multiplexor,
                            comment=comment,
                            **extras)
                        if min_value is not None:
                            signal.min = float_factory(min_value)
                        if max_value is not None:
                            signal.max = float_factory(max_value)
                        if intel is False:
                            # motorola set/convert start bit
                            signal.set_startbit(start_bit)
                        if value_table_name is not None:
                            signal.values = db.value_tables[value_table_name]
                            signal.enumeration = value_table_name
                        # signal.add_comment(comment)
                        # ... (1 / ...) because this somehow made 59.8/0.1 be 598.0 rather than 597.9999999999999
                        if start_value is not None:
                            start_value = float_factory(start_value) * (1 / float_factory(factor))
                            signal.add_attribute("GenSigStartValue", str(start_value))
                        frame.add_signal(signal)
                    if long_name is not None:
                        signal.add_attribute("LongName", long_name)
                    if hexadecimal_output:
                        signal.add_attribute("HexadecimalOutput", str(True))
                    if display_decimal_places is not None:
                        signal.add_attribute("DisplayDecimalPlaces", display_decimal_places)
                    # variable processing
                elif line.startswith('ID'):
                    comment = ""
                    if '//' in line:
                        split = line.split('//', 1)
                        comment = split[1].strip()
                        line = split[0].strip()
                    frame.arbitration_id.id = int(line.split('=')[1].strip()[:-1], 16)
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
                #        else:
                #                print line
                # else:
                #        print "Unrecognized line: " + l + " (%d) " % i
        except Exception as e:
            if not isinstance(e, ParsingError):
                ParsingError(
                    message=str(e),
                    line_number=line_count,
                    line=line,
                    original=e,
                )

            db.load_errors.append(e)

            logger.error("Error decoding line %d" % line_count)
            logger.error(line)
    # TODO: CAMPid 939921818394902983238
    if frame is not None:
        if len(frame.mux_names) > 0:
            frame.signal_by_name(frame.name + "_MUX").values = frame.mux_names
        db.add_frame(frame)

    return db
