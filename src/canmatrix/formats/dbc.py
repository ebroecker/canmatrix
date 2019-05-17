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
# this script exports dbc-files from a canmatrix-object
# dbc-files are the can-matrix-definitions of the CanOe (Vector Informatic)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import copy
import decimal
import logging
import math
import re
import typing
from builtins import *

import canmatrix

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal



def normalizeName(name, whitespaceReplacement):
    name = re.sub(r'\s+', whitespaceReplacement, name)

    if ' ' in name:
        name = '"' + name + '"'

    return name


def format_float(f):
    s = str(f).upper()
    if s.endswith('.0'):
        s = s[:-2]

    if 'E' in s:
        tmp = s.split('E')
        s = '%sE%s%s' % (tmp[0], tmp[1][0], tmp[1][1:].rjust(3, '0'))

    return s.upper()


def check_define(define):
    # check if define is compatible with dbc. else repace by STRING
    if define.type not in ["ENUM", "STRING", "INT", "HEX", "FLOAT"]:
        logger.warn("dbc export of attribute type {} not supported; replaced by STRING".format(define.type))
        define.definition = "STRING"
        define.type = "STRING"


def create_define(data_type, define, define_type, defaults):
    check_define(define)
    define_string = "BA_DEF_ " + define_type
    define_string += ' "' + data_type + '" '
    define_string += define.definition + ';\n'

    if data_type not in defaults and define.defaultValue is not None:
        if define.type == "ENUM" or define.type == "STRING":
            defaults[data_type] = '"' + define.defaultValue + '"'
        else:
            defaults[data_type] = define.defaultValue
    return define_string


def create_attribute_string(attribute, attribute_class, name, value, is_string):
    if is_string:
        value = '"' + value + '"'
    elif not value:
        value = '""'

    attribute_string = 'BA_ "' + attribute + '" ' + attribute_class + ' ' + name + ' ' + str(value) + ';\n'
    return attribute_string


def create_comment_string(comment_class, comment_ident, comment, dbcExportEncoding, dbcExportCommentEncoding):
    if len(comment) == 0:
        return b""
    comment_string = ("CM_ " + comment_class + " " + comment_ident + ' "').encode(dbcExportEncoding, 'ignore')
    comment_string += comment.replace('"', '\\"').encode(dbcExportCommentEncoding, 'ignore')
    comment_string += '";\n'.encode(dbcExportEncoding)
    return comment_string


def dump(mydb, f, **options):
    # create copy because export changes database
    db = copy.deepcopy(mydb)

    dbcExportEncoding = options.get("dbcExportEncoding", 'iso-8859-1')
    dbcExportCommentEncoding = options.get("dbcExportCommentEncoding",  dbcExportEncoding)
    writeValTable = options.get("writeValTable", True)
    compatibility = options.get('compatibility', True)

    whitespaceReplacement = options.get("whitespaceReplacement", '_')
    if whitespaceReplacement in ['', None] or set(
            [' ', '\t']).intersection(whitespaceReplacement):
        print("Warning: Settings may result in whitespace in DBC variable names.  This is not supported by the DBC format.")


    if db.contains_fd or db.contains_j1939:
        if db.contains_fd:
            db.add_global_defines("BusType", "STRING")
            db.add_attribute("BusType", "CAN FD")
        elif db.contains_j1939:
            db.add_global_defines("ProtocolType", "STRING")
            db.add_attribute("ProtocolType", "J1939")
        db.add_frame_defines("VFrameFormat", 'ENUM "StandardCAN","ExtendedCAN","StandardCAN_FD","ExtendedCAN_FD","J1939PG"')
        for frame in db.frames:
            if frame.is_fd:
                if frame.arbitration_id.extended:
                    frame.add_attribute("VFrameFormat", "ExtendedCAN_FD")
                else:
                    frame.add_attribute("VFrameFormat", "StandardCAN_FD")
            elif frame.is_j1939:
                frame.add_attribute("VFrameFormat", "J1939PG")
            else:
                if frame.arbitration_id.extended:
                    frame.add_attribute("VFrameFormat", "ExtendedCAN")
                else:
                    frame.add_attribute("VFrameFormat", "StandardCAN")

    db.enum_attribs_to_keys()

    # free signals are in special frame in dbc...
    if len(db.signals) > 0:
        free_signals_dummy_frame = canmatrix.Frame("VECTOR__INDEPENDENT_SIG_MSG")
        free_signals_dummy_frame.arbitration_id = canmatrix.ArbitrationId(0x40000000, extended=True)
        free_signals_dummy_frame.signals = db.signals
        db.addFrame(free_signals_dummy_frame)

    # shorten long enviroment variable names
    for envVarName in db.env_vars:
        if len(envVarName) > 32:
            db.add_env_attribute(envVarName, "SystemEnvVarLongSymbol", envVarName)
            db.env_vars[envVarName[:32]] = db.env_vars.pop(envVarName)
            db.add_env_defines("SystemEnvVarLongSymbol", "STRING")


    header = "VERSION \"created by canmatrix\"\n\n\nNS_ :\n\nBS_:\n\n"
    f.write(header.encode(dbcExportEncoding))

    # ECUs
    f.write("BU_: ".encode(dbcExportEncoding))

    for ecu in db.ecus:
        # fix long ecu names:
        if len(ecu.name) > 32:
            ecu.add_attribute("SystemNodeLongSymbol",  ecu.name)
            ecu.name = ecu.name[0:32]
            db.add_ecu_defines("SystemNodeLongSymbol", "STRING")

        f.write((ecu.name + " ").encode(dbcExportEncoding))

    f.write("\n\n".encode(dbcExportEncoding))

    if writeValTable:
        # ValueTables
        for table in sorted(db.value_tables):
            f.write(("VAL_TABLE_ " + table).encode(dbcExportEncoding))
            for row in db.value_tables[table]:
                f.write(
                    (' ' +
                     str(row) +
                     ' "' +
                     db.value_tables[table][row] +
                     '"').encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))
        f.write("\n".encode(dbcExportEncoding))

    output_names = collections.defaultdict(dict)


    for frame in db.frames:
        # fix long frame names
        if len(frame.name) > 32:
            frame.add_attribute("SystemMessageLongSymbol", frame.name)
            frame.name = frame.name[0:32]
            db.add_frame_defines("SystemMessageLongSymbol", "STRING")

        # fix long signal names
        for s in frame.signals:
            if len(s.name) > 32:
                s.add_attribute("SystemSignalLongSymbol", s.name)
                s.name = s.name[0:32]
                db.add_signal_defines("SystemSignalLongSymbol", "STRING")

        normalized_names = collections.OrderedDict((
            (s, normalizeName(s.name, whitespaceReplacement))
            for s in frame.signals
        ))

        # remove "-" from frame names
        if compatibility:
            frame.name = re.sub("[^A-Za-z0-9]", whitespaceReplacement, frame.name)


        duplicate_signal_totals = collections.Counter(normalized_names.values())
        duplicate_signal_counter = collections.Counter()

        numbered_names = collections.OrderedDict()

        for signal in frame.signals:
            name = normalized_names[signal]
            if compatibility:
                name = re.sub("[^A-Za-z0-9]",whitespaceReplacement, name)
            duplicate_signal_counter[name] += 1
            if duplicate_signal_totals[name] > 1:
                # TODO: pad to 01 in case of 10+ instances, for example?
                name += str(duplicate_signal_counter[name] - 1)
            output_names[frame][signal] = name

    # Frames
    for frame in db.frames:
        multiplex_written = False
        if frame.transmitters.__len__() == 0:
            frame.add_transmitter("Vector__XXX")

        f.write(
            ("BO_ %d " %
             frame.arbitration_id.to_compound_integer() +
             frame.name +
             ": %d " %
             frame.size +
             frame.transmitters[0] +
             "\n").encode(dbcExportEncoding))

        duplicate_signal_totals = collections.Counter(
            normalizeName(s.name, whitespaceReplacement) for s in frame.signals
        )
        duplicate_signal_counter = collections.Counter()
        for signal in frame.signals:
            if signal.multiplex == 'Multiplexor' and multiplex_written and not frame.is_complex_multiplexed:
                continue
            signal_line = " SG_ " + output_names[frame][signal] + " "

            if signal.mux_val is not None:
                signal_line += "m{}".format(int(signal.mux_val))
                if signal.multiplex != 'Multiplexor':
                    signal_line += " "

            if signal.multiplex == 'Multiplexor':
                signal_line += "M "
                multiplex_written = True


            startbit = signal.get_startbit(bit_numbering=1)

            if signal.is_signed:
                sign = '-'
            else:
                sign = '+'
            signal_line += (": %d|%d@%d%c" %
                 (startbit,
                  signal.size,
                  signal.is_little_endian,
                  sign))
            signal_line += " (%s,%s)" % (format_float(signal.factor), format_float(signal.offset))
            signal_line += " [{}|{}]".format(format_float(signal.min),format_float(signal.max))
            signal_line += ' "'

            if signal.unit is None:
                signal.unit = ""
            signal_line += signal.unit
            signal_line += '" '

            if signal.receivers.__len__() == 0:
                signal.add_receiver('Vector__XXX')
            signal_line += ','.join(signal.receivers) + "\n"
            f.write(signal_line.encode(dbcExportEncoding))

        f.write("\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # second Sender:
    for frame in db.frames:
        if frame.transmitters.__len__() > 1:
            f.write(("BO_TX_BU_ %d : %s;\n" % (frame.arbitration_id.to_compound_integer(), ','.join(frame.transmitters))).encode(dbcExportEncoding))

    # frame comments
    # wow, there are dbcs where comments are encoded with other coding than rest of dbc...
    for frame in db.frames:
        f.write(create_comment_string("BO_", "%d " % frame.arbitration_id.to_compound_integer(), frame.comment, dbcExportEncoding, dbcExportCommentEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal comments
    for frame in db.frames:
        for signal in frame.signals:
            if signal.comment is not None and signal.comment.__len__() > 0:
                name = output_names[frame][signal]
                f.write(create_comment_string("SG_", "%d " % frame.arbitration_id.to_compound_integer() + name, signal.comment, dbcExportEncoding,
                                              dbcExportCommentEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # ecu comments
    for ecu in db.ecus:
        if ecu.comment is not None and ecu.comment.__len__() > 0:
            f.write(create_comment_string("BU_", ecu.name, ecu.comment, dbcExportEncoding,
                                          dbcExportCommentEncoding))
    f.write("\n".encode(dbcExportEncoding))

    defaults = {}


    # write defines
    for (data_type, define) in sorted(list(db.frame_defines.items())):
        f.write(create_define(data_type, define, "BO_", defaults).encode(dbcExportEncoding, 'replace'))


    for (data_type, define) in sorted(list(db.signal_defines.items())):
        f.write(create_define(data_type, define, "SG_", defaults).encode(dbcExportEncoding, 'replace'))

    for (data_type, define) in sorted(list(db.ecu_defines.items())):
        f.write(create_define(data_type, define, "BU_", defaults).encode(dbcExportEncoding, 'replace'))

    for (data_type, define) in sorted(list(db.env_defines.items())):
        f.write(create_define(data_type, define, "EV_", defaults).encode(dbcExportEncoding, 'replace'))

    for (data_type, define) in sorted(list(db.global_defines.items())):
        f.write(create_define(data_type, define, "", defaults).encode(dbcExportEncoding, 'replace'))

    for define in sorted(defaults):
        f.write(('BA_DEF_DEF_ "' + define + '" ').encode(dbcExportEncoding) +
            defaults[define].encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))


    # ecu-attributes:
    for ecu in db.ecus:
        for attrib, val in sorted(ecu.attributes.items()):
            f.write(create_attribute_string(attrib, "BU_", ecu.name, val, db.ecu_defines[attrib].type == "STRING").encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # global-attributes:
    for attrib, val in sorted(db.attributes.items()):
        f.write(create_attribute_string(attrib, "", "", val, db.global_defines[attrib].type == "STRING").encode(
            dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # messages-attributes:
    for frame in db.frames:
        for attrib, val in sorted(frame.attributes.items()):
            f.write(create_attribute_string(attrib, "BO_", str(frame.arbitration_id.to_compound_integer()), val, db.frame_defines[attrib].type == "STRING").encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal-attributes:
    for frame in db.frames:
        for signal in frame.signals:
            for attrib, val in sorted(signal.attributes.items()):
                name = output_names[frame][signal]
                if isinstance(val, float):
                    val = format_float(val)
                f.write(create_attribute_string(attrib, "SG_", '%d ' % frame.arbitration_id.to_compound_integer() + name, val,
                                                db.signal_defines[attrib].type == "STRING").encode(dbcExportEncoding))

    f.write("\n".encode(dbcExportEncoding))

    for env_var_name, env_var in db.env_vars.items():
        if "attributes" in env_var:
            for attribute, value in env_var["attributes"].items():
                f.write(create_attribute_string(attribute, "EV_", "", value,
                                                db.env_defines[attribute].type == "STRING").encode(dbcExportEncoding))


    # signal-values:
    for frame in db.frames:
        multiplex_written = False
        for signal in frame.signals:
            if signal.multiplex == 'Multiplexor' and multiplex_written:
                continue

            multiplex_written = True

            if signal.values:
                f.write(
                    ('VAL_ %d ' %
                     frame.arbitration_id.to_compound_integer() +
                     output_names[frame][signal]).encode(dbcExportEncoding))
                for attrib, val in sorted(
                        signal.values.items(), key=lambda x: int(x[0])):
                    f.write(
                        (' ' + str(attrib) + ' "' + val + '"').encode(dbcExportEncoding))
                f.write(";\n".encode(dbcExportEncoding))

    # SIG_VALTYPE
    for frame in db.frames:
        for signal in frame.signals:
            if signal.is_float:
                if int(signal.size) > 32:
                    f.write(('SIG_VALTYPE_ %d %s : 2;\n' % (frame.arbitration_id.to_compound_integer(), output_names[frame][signal])).encode(
                        dbcExportEncoding))
                else:
                    f.write(('SIG_VALTYPE_ %d %s : 1;\n' % (frame.arbitration_id.to_compound_integer(), output_names[frame][signal])).encode(
                        dbcExportEncoding))

    # signal-groups:
    for frame in db.frames:
        for sigGroup in frame.signalGroups:
            f.write(("SIG_GROUP_ " + str(frame.arbitration_id.to_compound_integer()) + " " + sigGroup.name +
                     " " + str(sigGroup.id) + " :").encode(dbcExportEncoding))
            for signal in sigGroup.signals:
                f.write((" " + output_names[frame][signal]).encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))

    for frame in db.frames:
        if frame.is_complex_multiplexed:
            for signal in frame.signals:
                if signal.muxer_for_signal is not None:
                    f.write(("SG_MUL_VAL_ %d %s %s " % (frame.arbitration_id.to_compound_integer(), signal.name, signal.muxer_for_signal)).encode(dbcExportEncoding))
                    f.write((", ".join(["%d-%d" % (a, b) for a, b in signal.mux_val_grp])).encode(dbcExportEncoding))

                    f.write(";\n".encode(dbcExportEncoding))

    for envVarName in db.env_vars:
        envVar = db.env_vars[envVarName]
        f.write(("EV_ {0} : {1} [{2}|{3}] \"{4}\" {5} {6} {7} {8};\n".format(envVarName, envVar["varType"], envVar["min"],
                                                                            envVar["max"], envVar["unit"],envVar["initialValue"],
                                                                            envVar["evId"], envVar["accessType"],
                                                                            ",".join(envVar["accessNodes"])) ).encode(dbcExportEncoding))


def load(f, **options):
    dbcImportEncoding = options.get("dbcImportEncoding", 'iso-8859-1')
    dbcCommentEncoding = options.get("dbcImportCommentEncoding", dbcImportEncoding)
    float_factory = options.get('float_factory', default_float_factory)

    i = 0

    class FollowUps(object):
        nothing, signalComment, frameComment, boardUnitComment, globalComment = list(
            range(5))
    followUp = FollowUps.nothing
    comment = ""
    signal = None  # type: typing.Optional[canmatrix.Signal]
    frame = None
    boardUnit = None
    db = canmatrix.CanMatrix()
    framesById = {}  # type: typing.Dict[int, canmatrix.Frame]

    def hash_arbitration_id(arbitration_id):  # type: (canmatrix.ArbitrationId) -> int
        return hash((arbitration_id.id, arbitration_id.extended))

    def get_frame_by_id(arbitration_id):  # type: (canmatrix.ArbitrationId) -> typing.Optional[canmatrix.Frame]
        try:
            return framesById[hash_arbitration_id(arbitration_id)]
        except KeyError:
            return None

    def add_frame_by_id(frame):  # type: (canmatrix.Frame) -> None
        framesById[hash_arbitration_id(frame.arbitration_id)] = frame

    for line in f:
        i = i + 1
        l = line.strip()
        if l.__len__() == 0:
            continue
        try:
#        if 1==1:
            if followUp == FollowUps.signalComment:
                try:
                    comment += "\n" + \
                        l.decode(dbcCommentEncoding).replace('\\"', '"')
                except:
                    logger.error("Error decoding line: %d (%s)" % (i, line))
                if l.endswith(b'";'):
                    followUp = FollowUps.nothing
                    if signal is not None:
                        signal.add_comment(comment[0:-2])
                continue
            elif followUp == FollowUps.frameComment:
                try:
                    comment += "\n" + \
                        l.decode(dbcCommentEncoding).replace('\\"', '"')
                except:
                    logger.error("Error decoding line: %d (%s)" % (i, line))
                if l.endswith(b'";'):
                    followUp = FollowUps.nothing
                    if frame is not None:
                        frame.add_comment(comment[0:-2])
                continue
            elif followUp == FollowUps.boardUnitComment:
                try:
                    comment += "\n" + \
                        l.decode(dbcCommentEncoding).replace('\\"', '"')
                except:
                    logger.error("Error decoding line: %d (%s)" % (i, line))
                if l.endswith(b'";'):
                    followUp = FollowUps.nothing
                    if boardUnit is not None:
                        boardUnit.add_comment(comment[0:-2])
                continue
            decoded = l.decode(dbcImportEncoding).strip()
            if decoded.startswith("BO_ "):
                regexp = re.compile(r"^BO_ ([^\ ]+) ([^\ ]+) *: ([^\ ]+) ([^\ ]+)")
                temp = regexp.match(decoded)
    #            db.frames.addFrame(Frame(temp.group(1), temp.group(2), temp.group(3), temp.group(4)))
                frame = canmatrix.Frame(temp.group(2),arbitration_id = int(temp.group(1)),
                                        size=int(temp.group(3)), transmitters=temp.group(4).split())
                db.frames.append(frame)
                add_frame_by_id(frame)
            elif decoded.startswith("SG_ "):
                pattern = r"^SG_ +(\w+) *: *(\d+)\|(\d+)@(\d+)([\+|\-]) +\(([0-9.+\-eE]+), *([0-9.+\-eE]+)\) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(.*)\" +(.*)"
                regexp = re.compile(pattern)
                temp = regexp.match(decoded)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp_raw = regexp_raw.match(l)
                if temp:
                    receiver = [b.strip() for b in temp.group(11).split(',')]

                    extras = {}
#                    if float_factory is not None:
#                        extras['float_factory'] = float_factory

                    tempSig = canmatrix.Signal(
                        temp.group(1),
                        start_bit=int(temp.group(2)),
                        size=int(temp.group(3)),
                        is_little_endian=(int(temp.group(4)) == 1),
                        is_signed=(temp.group(5) == '-'),
                        factor=temp.group(6),
                        offset=temp.group(7),
                        min=temp.group(8),
                        max=temp.group(9),
                        unit=temp_raw.group(10).decode(dbcImportEncoding),
                        receivers=receiver,
                        **extras
                    )
                    if not tempSig.is_little_endian:
                        # startbit of motorola coded signals are MSB in dbc
                        tempSig.set_startbit(int(temp.group(2)), bitNumbering=1)
                    frame.add_signal(tempSig)
    #                db.frames.addSignalToLastFrame(tempSig)
                else:
                    pattern = r"^SG_ +(.+?) +(.+?) *: *(\d+)\|(\d+)@(\d+)([\+|\-]) +\(([0-9.+\-eE]+),([0-9.+\-eE]+)\) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(.*)\" +(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    receiver = [b.strip() for b in temp.group(12).split(',')]
                    multiplex = temp.group(2)  # type: typing.Union[str, int]

                    is_complex_multiplexed = False

                    if multiplex == 'M':
                        multiplex = 'Multiplexor'
                    elif multiplex.endswith('M'):
                        is_complex_multiplexed = True
                        multiplex = multiplex[:-1]

                    if multiplex != 'Multiplexor':
                        try:
                            multiplex = int(multiplex[1:])
                        except:
                            raise Exception('error decoding line',line)

                    extras = {}
#                    if float_factory is not None:
#                        extras['float_factory'] = float_factory

                    tempSig = canmatrix.Signal(
                        temp.group(1),
                        start_bit=int(temp.group(3)),
                        size=int(temp.group(4)),
                        is_little_endian=(int(temp.group(5)) == 1),
                        is_signed=(temp.group(6) == '-'),
                        factor=temp.group(7),
                        offset=temp.group(8),
                        min=temp.group(9),
                        max=temp.group(10),
                        unit=temp_raw.group(11).decode(dbcImportEncoding),
                        receivers=receiver,
                        multiplex=multiplex,
                        **extras
                    )

                    if is_complex_multiplexed:
                        tempSig.is_multiplexer = True
                        tempSig.multiplex = 'Multiplexor'

                    if not tempSig.is_little_endian:
                        # startbit of motorola coded signals are MSB in dbc
                        tempSig.set_startbit(int(temp.group(3)), bitNumbering=1)
                    frame.add_signal(tempSig)

                    if is_complex_multiplexed:
                        frame.is_complex_multiplexed = True


            elif decoded.startswith("BO_TX_BU_ "):
                regexp = re.compile(r"^BO_TX_BU_ ([0-9]+) *: *(.+);")
                temp = regexp.match(decoded)
                frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                for ecu_name in temp.group(2).split(','):
                    frame.add_transmitter(ecu_name)
            elif decoded.startswith("CM_ SG_ "):
                pattern = r"^CM_ +SG_ +(\w+) +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                    signal = frame.signal_by_name(temp.group(2))
                    if signal:
                        try:
                            signal.add_comment(temp_raw.group(3).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = r"^CM_ +SG_ +(\w+) +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                        signal = frame.signal_by_name(temp.group(2))
                        try:
                            comment = temp_raw.group(3).decode(
                                dbcCommentEncoding).replace('\\"', '"')
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                        followUp = FollowUps.signalComment

            elif decoded.startswith("CM_ BO_ "):
                pattern = r"^CM_ +BO_ +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                    if frame:
                        try:
                            frame.add_comment(temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = r"^CM_ +BO_ +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                        try:
                            comment = temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"')
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                        followUp = FollowUps.frameComment
            elif decoded.startswith("CM_ BU_ "):
                pattern = r"^CM_ +BU_ +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    boardUnit = db.ecu_by_name(temp.group(1))
                    if boardUnit:
                        try:
                            boardUnit.add_comment(temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = r"^CM_ +BU_ +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        boardUnit = db.ecu_by_name(temp.group(1))
                        if boardUnit:
                            try:
                                comment = temp_raw.group(2).decode(
                                    dbcCommentEncoding).replace('\\"', '"')
                            except:
                                logger.error(
                                    "Error decoding line: %d (%s)" %
                                    (i, line))
                            followUp = FollowUps.boardUnitComment
            elif decoded.startswith("BU_:"):
                pattern = r"^BU_\:(.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                if temp:
                    myTempListe = temp.group(1).split(' ')
                    for ele in myTempListe:
                        if len(ele.strip()) > 1:
                            db.ecus.append(canmatrix.Ecu(ele))

            elif decoded.startswith("VAL_ "):
                regexp = re.compile(r"^VAL_ +(\w+) +(\w+) +(.*);")
                temp = regexp.match(decoded)
                if temp:
                    frame_id = temp.group(1)
                    signal_name = temp.group(2)
                    tempList = temp.group(3).split('"')
                    if frame_id.isnumeric(): # value for Frame
                        try:
                            frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(frame_id)))
                            sg = frame.signal_by_name(signal_name)
                            for i in range(math.floor(len(tempList) / 2)):
                                val = tempList[i * 2 + 1]
                                if sg:
                                    sg.add_values(tempList[i * 2], val)
                        except:
                            logger.error("Error with Line: " + str(tempList))
                    else:
                        logger.info("Warning: enviroment variables currently not supported")

            elif decoded.startswith("VAL_TABLE_ "):
                regexp = re.compile(r"^VAL_TABLE_ +(\w+) +(.*);")
                temp = regexp.match(decoded)
                if temp:
                    tableName = temp.group(1)
                    tempList = temp.group(2).split('"')
                    try:
                        valHash = {}
                        for i in range(math.floor(len(tempList) / 2)):
                            val = tempList[i * 2 + 1]
                            valHash[tempList[i * 2].strip()] = val.strip()
                    except:
                        logger.error("Error with Line: " + str(tempList))
                    db.add_value_table(tableName, valHash)
                else:
                    logger.debug(l)

            elif decoded.startswith("BA_DEF_") and decoded[7:].strip()[:3] in ["SG_", "BO_", "BU_", "EV_"]:
                substring = decoded[7:].strip()
                define_type = substring[:3]
                substring = substring[3:].strip()
                pattern = r"^\"(.+?)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(substring)
                substring_line = l[7:].strip()[3:].strip()
                temp_raw = regexp_raw.match(substring_line)
                if temp:
                    if define_type == "SG_":
                        db.add_signal_defines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
                    elif define_type == "BO_":
                        db.add_frame_defines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
                    elif define_type == "BU_":
                        db.add_ecu_defines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
                    elif define_type == "EV_":
                        db.add_env_defines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))

            elif decoded.startswith("BA_DEF_ "):
                pattern = r"^BA_DEF_ +\"(.+?)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.add_global_defines(temp.group(1),
                                          temp_raw.group(2).decode(dbcImportEncoding))

            elif decoded.startswith("BA_ "):
                regexp = re.compile(r"^BA_ +\".+?\" +(.+)")
                tempba = regexp.match(decoded)

                if tempba.group(1).strip().startswith("BO_ "):
                    regexp = re.compile(r"^BA_ +\"(.+?)\" +BO_ +(\d+) +(.+);")
                    temp = regexp.match(decoded)
                    get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(2)))).add_attribute(
                        temp.group(1), temp.group(3))
                elif tempba.group(1).strip().startswith("SG_ "):
                    regexp = re.compile(r"^BA_ +\"(.+?)\" +SG_ +(\d+) +(\w+) +(.+);")
                    temp = regexp.match(decoded)
                    if temp != None:
                        get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(2)))).signal_by_name(
                            temp.group(3)).add_attribute(temp.group(1), temp.group(4))
                elif tempba.group(1).strip().startswith("EV_ "):
                    regexp = re.compile(r"^BA_ +\"(.+?)\" +EV_ +(\w+) +(.*);")
                    temp = regexp.match(decoded)
                    if temp != None:
                        db.add_env_attribute(temp.group(2),temp.group(1),temp.group(3))
                elif tempba.group(1).strip().startswith("BU_ "):
                    regexp = re.compile(r"^BA_ +\"(.*?)\" +BU_ +(\w+) +(.+);")
                    temp = regexp.match(decoded)
                    db.ecu_by_name(
                        temp.group(2)).add_attribute(
                        temp.group(1),
                        temp.group(3))
                else:
                    regexp = re.compile(
                        r"^BA_ +\"([A-Za-z0-9\-_]+)\" +([\"\w\-\.]+);")
                    temp = regexp.match(decoded)
                    if temp:
                        db.add_attribute(temp.group(1), temp.group(2))

            elif decoded.startswith("SIG_GROUP_ "):
                regexp = re.compile(r"^SIG_GROUP_ +(\w+) +(\w+) +(\w+) +\:(.*);")
                temp = regexp.match(decoded)
                frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                if frame is not None:
                    signalArray = temp.group(4).split(' ')
                    frame.add_signal_group(temp.group(2), temp.group(3), signalArray)  # todo wrong annotation in canmatrix? Id is a string?

            elif decoded.startswith("SIG_VALTYPE_ "):
                regexp = re.compile(r"^SIG_VALTYPE_ +(\w+) +(\w+)\s*\:(.*);")
                temp = regexp.match(decoded)
                frame = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(temp.group(1))))
                if frame:
                    signal = frame.signal_by_name(temp.group(2))
                    signal.is_float = True
    #                SIG_VALTYPE_ 0 float : 1;

            elif decoded.startswith("BA_DEF_DEF_ "):
                pattern = r"^BA_DEF_DEF_ +\"(.+?)\" +(.+?)\;"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.add_define_default(temp.group(1),
                                          temp_raw.group(2).decode(dbcImportEncoding))
            elif decoded.startswith("SG_MUL_VAL_ "):
                pattern = r"^SG_MUL_VAL_ +([0-9]+) +([\w\-]+) +([\w\-]+) +(.*) *;"
                regexp = re.compile(pattern)
                temp = regexp.match(decoded)
                if temp:
                    frameId = temp.group(1)
                    signalName = temp.group(2)
                    muxerForSignal = temp.group(3)
                    muxValGroups = temp.group(4).split(',')
                    frame  = get_frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(frameId)))
                    if frame is not None:
                        signal = frame.signal_by_name(signalName)
                        frame.is_complex_multiplexed = True
                        signal.muxer_for_signal = muxerForSignal
                        for muxVal in muxValGroups:
                            muxValMin, muxValMax = muxVal.split("-")
                            muxValMin = int(muxValMin)
                            muxValMax = int(muxValMax)
                            signal.mux_val_grp.append([muxValMin, muxValMax])
            elif decoded.startswith("EV_ "):
                pattern = r"^EV_ +([\w\-\_]+?) *\: +([0-9]+) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(.*?)\" +([0-9.+\-eE]+) +([0-9.+\-eE]+) +([\w\-]+?) +(.*);"
                regexp = re.compile(pattern)
                temp = regexp.match(decoded)

                varName = temp.group(1)
                varType = temp.group(2)
                min = temp.group(3)
                max = temp.group(4)
                unit = temp.group(5)
                initialValue  = temp.group(6)
                evId  = temp.group(7)
                accessType  = temp.group(8)
                accessNodes = temp.group(9).split(",")
                db.add_env_var(varName, {"varType": varType, "min" : min, "max" : max,
                              "unit" : unit, "initialValue" : initialValue, "evId" : evId,
                              "accessType" : accessType, "accessNodes" : accessNodes})


#        else:
        except:
            print ("error with line no: %d" % i)
            print (line)
# Backtracking

    for env_var_name, env_var in db.env_vars.items():
        if 'SystemEnvVarLongSymbol' in env_var.get("attributes", ""):
            long_name = env_var["attributes"]["SystemEnvVarLongSymbol"][1:-1]
            del(env_var["attributes"]["SystemEnvVarLongSymbol"])
            db.env_vars[long_name] = db.env_vars.pop(env_var_name)
    for ecu in db.ecus:
        if ecu.attributes.get("SystemNodeLongSymbol", None) is not None:
            ecu.name = ecu.attributes.get("SystemNodeLongSymbol")[1:-1]
            ecu.del_attribute("SystemNodeLongSymbol")
    for frame in db.frames:
        if frame.attributes.get("SystemMessageLongSymbol", None) is not None:
            frame.name = frame.attributes.get("SystemMessageLongSymbol")[1:-1]
            frame.del_attribute("SystemMessageLongSymbol")
        # receiver is only given in the signals, so do propagate the receiver
        # to the frame:
        frame.update_receiver()
        # extended-flag is implicite in canid, thus repair this:
        #if frame.id > 0x80000000:
        #    frame.id -= 0x80000000
        #    frame.extended = 1

        for signal in frame.signals:
            if signal.attribute("SystemSignalLongSymbol") is not None:
                signal.name = signal.attribute("SystemSignalLongSymbol")[1:-1]
                signal.del_attribute("SystemSignalLongSymbol")
    for define in db.global_defines:
        if db.global_defines[define].type == "STRING":
            if define in db.attributes:
                db.attributes[define] = db.attributes[define][1:-1]
    for define in db.ecu_defines:
        if db.ecu_defines[define].type == "STRING":
            for ecu in db.ecus:
                if define in ecu.attributes:
                    ecu.attributes[define] = ecu.attributes[define][1:-1]
    for define in db.frame_defines:
        if db.frame_defines[define].type == "STRING":
            for frame in db.frames:
                if define in frame.attributes:
                    frame.attributes[define] = frame.attributes[define][1:-1]
    for define in db.signal_defines:
        if db.signal_defines[define].type == "STRING":
            for frame in db.frames:
                for signal in frame.signals:
                    if define in signal.attributes:
                        signal.attributes[define] = signal.attributes[define][1:-1]

    db.enum_attribs_to_values()
    for frame in db.frames:
        if "_FD" in frame.attributes.get("VFrameFormat", ""):
            frame.is_fd = True
        if "J1939PG" in frame.attributes.get("VFrameFormat", ""):
            frame.is_j1939 = True

    db.update_ecu_list()
    db.del_ecu("Vector__XXX")
    free_signals_dummy_frame = db.frame_by_name("VECTOR__INDEPENDENT_SIG_MSG")
    if free_signals_dummy_frame is not None and free_signals_dummy_frame.arbitration_id.id == 0x40000000:
        db.signals = free_signals_dummy_frame.signals
        db.del_frame(free_signals_dummy_frame)

    return db
