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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from copy import deepcopy
import collections
import logging
import decimal

logger = logging.getLogger('root')
default_float_factory = decimal.Decimal

from builtins import *
from .canmatrix import *
import re


#dbcExportEncoding = 'iso-8859-1'
# CP1253


def normalizeName(name, whitespaceReplacement):
    name = re.sub('\s+', whitespaceReplacement, name)

    if ' ' in name:
        name = '"' + name + '"'

    return name


def format_float(f):
    s = str(f).upper()
    if s.endswith('.0'):
        s = s[:-2]

    if 'E' in s:
        s = s.split('E')
        s = '%sE%s%s' % (s[0], s[1][0], s[1][1:].rjust(3, '0'))

    return s.upper()


def dump(mydb, f, **options):
    # create copy because export changes database
    db = deepcopy(mydb)

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
            db.addGlobalDefines("BusType", "STRING")
            db.addAttribute("BusType", "CAN FD")
        elif db.contains_j1939:
            db.addGlobalDefines("ProtocolType", "STRING")
            db.addAttribute("ProtocolType", "J1939")
        db.addFrameDefines("VFrameFormat",'ENUM "StandardCAN","ExtendedCAN","StandardCAN_FD","ExtendedCAN_FD","J1939PG"')
        for frame in db.frames:
            if frame.is_fd:
                if frame.extended:
                    frame.addAttribute("VFrameFormat", "ExtendedCAN_FD")
                else:
                    frame.addAttribute("VFrameFormat", "StandardCAN_FD")
            elif frame.is_j1939:
                frame.addAttribute("VFrameFormat","J1939PG")
            else:
                if frame.extended:
                    frame.addAttribute("VFrameFormat", "ExtendedCAN")
                else:
                    frame.addAttribute("VFrameFormat", "StandardCAN")

    db.EnumAttribs2Keys()


    f.write("VERSION \"created by canmatrix\"\n\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    f.write("NS_ :\n\nBS_:\n\n".encode(dbcExportEncoding))


    # Boardunits
    f.write("BU_: ".encode(dbcExportEncoding))
    id = 1
    nodeList = {}
    for bu in db.boardUnits:
        f.write((bu.name + " ").encode(dbcExportEncoding))
    f.write("\n\n".encode(dbcExportEncoding))

    if writeValTable:
        # ValueTables
        for table in sorted(db.valueTables):
            f.write(("VAL_TABLE_ " + table).encode(dbcExportEncoding))
            for row in db.valueTables[table]:
                f.write(
                    (' ' +
                     str(row) +
                     ' "' +
                     db.valueTables[table][row] +
                     '"').encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))
        f.write("\n".encode(dbcExportEncoding))

    output_names = collections.defaultdict(dict)


    for frame in db.frames:
        normalized_names = collections.OrderedDict((
            (s, normalizeName(s.name, whitespaceReplacement))
            for s in frame.signals
        ))

        if compatibility and '-' in frame.name:
            frame.name = frame.name.replace("-", whitespaceReplacement)

        duplicate_signal_totals = collections.Counter(normalized_names.values())
        duplicate_signal_counter = collections.Counter()

        numbered_names = collections.OrderedDict()

        for signal in frame.signals:
            name = normalized_names[signal]
            if compatibility and '-' in name:
                name = name.replace("-", whitespaceReplacement)
            duplicate_signal_counter[name] += 1
            if duplicate_signal_totals[name] > 1:
                # TODO: pad to 01 in case of 10+ instances, for example?
                name += str(duplicate_signal_counter[name] - 1)

            output_names[frame][signal] = name

    # Frames
    for frame in db.frames:
        multiplex_written = False
        if frame.transmitters.__len__() == 0:
            frame.addTransmitter("Vector__XXX")

        if frame.extended == 1:
            frame.id += 0x80000000
        
        f.write(
            ("BO_ %d " %
             frame.id +
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

            f.write((" SG_ " + output_names[frame][signal] + " ").encode(dbcExportEncoding))
            if signal.mux_val is not None:
                f.write(("m%d" %
                         int(signal.mux_val)).encode(dbcExportEncoding))
                if signal.multiplex != 'Multiplexor':
                    f.write(' '.encode(dbcExportEncoding))

            if signal.multiplex == 'Multiplexor':
                f.write('M '.encode(dbcExportEncoding))
                multiplex_written = True



            startbit = signal.getStartbit(bitNumbering=1)

            if signal.is_signed:
                sign = '-'
            else:
                sign = '+'
            f.write(
                (": %d|%d@%d%c" %
                 (startbit,
                  signal.size,
                  signal.is_little_endian,
                  sign)).encode(dbcExportEncoding))
            f.write(
                (" (%s,%s)" %
                 (format_float(signal.factor), format_float(signal.offset))).encode(dbcExportEncoding))
            f.write(
                (" [{}|{}]".format(
                    format_float(signal.min),
                    format_float(signal.max))).encode(dbcExportEncoding))
            f.write(' "'.encode(dbcExportEncoding))

            if signal.unit is None:
                signal.unit = ""
            f.write(signal.unit.encode(dbcExportEncoding))
            f.write('" '.encode(dbcExportEncoding))
            if signal.receiver.__len__() == 0:
                signal.addReceiver('Vector__XXX')
            f.write((','.join(signal.receiver) + "\n").encode(dbcExportEncoding))
        f.write("\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # second Sender:
    for frame in db.frames:
        if frame.transmitters.__len__() > 1:
            f.write(
                ("BO_TX_BU_ %d : %s;\n" %
                 (frame.id, ','.join(
                     frame.transmitters))).encode(dbcExportEncoding))

    # frame comments
    for frame in db.frames:
        if frame.comment is not None and frame.comment.__len__() > 0:
            f.write(
                ("CM_ BO_ " +
                 "%d " %
                 frame.id +
                 ' "').encode(dbcExportEncoding))
            f.write(
                frame.comment.replace(
                    '"',
                    '\\"').encode(dbcExportCommentEncoding, 'ignore'))
            f.write('";\n'.encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal comments
    for frame in db.frames:
        for signal in frame.signals:
            if signal.comment is not None and signal.comment.__len__() > 0:
                name = output_names[frame][signal]
                f.write(
                    ("CM_ SG_ " +
                     "%d " %
                     frame.id +
                     name +
                     ' "').encode(dbcExportEncoding, 'ignore'))
                f.write(
                        signal.comment.replace(
                            '"', '\\"').encode(dbcExportCommentEncoding, 'ignore'))
                f.write('";\n'.encode(dbcExportEncoding, 'ignore'))

    f.write("\n".encode(dbcExportEncoding))

    # boarUnit comments
    for bu in db.boardUnits:
        if bu.comment is not None and bu.comment.__len__() > 0:
            f.write(
                ("CM_ BU_ " +
                 bu.name +
                 ' "' +
                 bu.comment.replace(
                     '"',
                     '\\"') +
                    '";\n').encode(dbcExportCommentEncoding,'ignore'))
    f.write("\n".encode(dbcExportEncoding))

    defaults = {}
    for (dataType, define) in sorted(list(db.frameDefines.items())):
        f.write(
            ('BA_DEF_ BO_ "' +  dataType + '" ').encode(dbcExportEncoding) + define.definition.encode(dbcExportEncoding, 'replace') + ';\n'.encode(dbcExportEncoding))
        if dataType not in defaults and define.defaultValue is not None:
            if define.type == "ENUM" or define.type == "STRING":
                defaults[dataType] = '"' + define.defaultValue + '"'
            else:
                defaults[dataType] = define.defaultValue

    for (dataType, define) in sorted(list(db.signalDefines.items())):
        f.write(
            ('BA_DEF_ SG_ "' + dataType + '" ').encode(dbcExportEncoding) +
            define.definition.encode(dbcExportEncoding, 'replace') + ';\n'.encode(dbcExportEncoding))
        if dataType not in defaults and define.defaultValue is not None:
            if define.type == "ENUM" or define.type == "STRING":
                defaults[dataType] = '"' + define.defaultValue + '"'
            else:
                defaults[dataType] = define.defaultValue
    for (dataType, define) in sorted(list(db.buDefines.items())):
        f.write(
            ('BA_DEF_ BU_ "' + dataType + '" ').encode(dbcExportEncoding) +
            define.definition.encode(dbcExportEncoding, 'replace') + ';\n'.encode(dbcExportEncoding))
        if dataType not in defaults and define.defaultValue is not None:
            if define.type == "ENUM" or define.type == "STRING":
                defaults[dataType] = '"' + define.defaultValue + '"'
            else:
                defaults[dataType] = define.defaultValue
    for (dataType, define) in sorted(list(db.globalDefines.items())):
        f.write(('BA_DEF_ "' + dataType + '" ').encode(dbcExportEncoding) + define.definition.encode(dbcExportEncoding, 'replace') + ';\n'.encode(dbcExportEncoding))
        if dataType not in defaults and define.defaultValue is not None:
            if define.type == "ENUM" or define.type == "STRING":
                defaults[dataType] = '"' + define.defaultValue + '"'
            else:
                defaults[dataType] = define.defaultValue

    for define in sorted(defaults):
        f.write(('BA_DEF_DEF_ "' + define + '" ').encode(dbcExportEncoding) +
            defaults[define].encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))

    # boardunit-attributes:
    for bu in db.boardUnits:
        for attrib, val in sorted(bu.attributes.items()):
            if db.buDefines[attrib].type == "STRING":
                val = '"' + val + '"'
            elif not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BU_ ' + bu.name + ' ' + str(val) + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # global-attributes:
    for attrib, val in sorted(db.attributes.items()):
        if db.globalDefines[attrib].type == "STRING":
            val = '"' + val + '"'
        elif not val:
            val = '""'
        f.write(('BA_ "' + attrib + '" ' + val +
                 ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # messages-attributes:
    for frame in db.frames:
        for attrib, val in sorted(frame.attributes.items()):
            if db.frameDefines[attrib].type == "STRING":
               val = '"' + val + '"'
            elif not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BO_ %d ' % frame.id + val + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal-attributes:
    for frame in db.frames:
        for signal in frame.signals:
            for attrib, val in sorted(signal.attributes.items()):
                name = output_names[frame][signal]
                if db.signalDefines[attrib].type == "STRING":
                    val = '"' + val + '"'
                elif not val:
                    val = '""'
                elif isinstance(val, float):
                    val = format_float(val)
                f.write(
                    ('BA_ "' + attrib + '" SG_ %d ' % frame.id + name + ' ' + val + ';\n').encode(dbcExportEncoding))

    f.write("\n".encode(dbcExportEncoding))

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
                     frame.id +
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
                    f.write(('SIG_VALTYPE_ %d %s : 2;\n' % (frame.id, output_names[frame][signal])).encode(
                        dbcExportEncoding))
                else:
                    f.write(('SIG_VALTYPE_ %d %s : 1;\n' % (frame.id, output_names[frame][signal])).encode(
                        dbcExportEncoding))

    # signal-groups:
    for frame in db.frames:
        for sigGroup in frame.signalGroups:
            f.write(("SIG_GROUP_ " + str(frame.id) + " " + sigGroup.name +
                     " " + str(sigGroup.id) + " :").encode(dbcExportEncoding))
            for signal in sigGroup.signals:
                f.write((" " + output_names[frame][signal]).encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))

    for frame in db.frames:
        if frame.is_complex_multiplexed:
            for signal in frame.signals:
                if signal.muxerForSignal is not None:
                    f.write(("SG_MUL_VAL_ %d %s %s %d-%d;\n" % (frame.id, signal.name, signal.muxerForSignal, signal.muxValMin, signal.muxValMax)).encode(dbcExportEncoding))

    for envVarName in db.envVars:
        envVar = db.envVars[envVarName]
        f.write("EV_ {0} : {1} [{2}|{3}] \"{4}\" {5} {6} {7} {8};\n".format(envVarName, envVar["varType"], envVar["min"],
                                                                            envVar["max"], envVar["unit"],envVar["initialValue"],
                                                                            envVar["evId"], envVar["accessType"],
                                                                            ",".join(envVar["accessNodes"])) )

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
    signal = None
    frame = None
    boardUnit = None
    db = CanMatrix()
    for line in f:
        i = i + 1
        l = line.strip()
        if l.__len__() == 0:
            continue
        try:
            if followUp == FollowUps.signalComment:
                try:
                    comment += "\n" + \
                        l.decode(dbcCommentEncoding).replace('\\"', '"')
                except:
                    logger.error("Error decoding line: %d (%s)" % (i, line))
                if l.endswith(b'";'):
                    followUp = FollowUps.nothing
                    if signal is not None:
                        signal.addComment(comment[0:-2])
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
                        frame.addComment(comment[0:-2])
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
                        boardUnit.addComment(comment[0:-2])
                continue
            decoded = l.decode(dbcImportEncoding).strip()
            if decoded.startswith("BO_ "):
                regexp = re.compile("^BO_ ([^\ ]+) ([^\ ]+) *: ([^\ ]+) ([^\ ]+)")
                temp = regexp.match(decoded)
    #            db.frames.addFrame(Frame(temp.group(1), temp.group(2), temp.group(3), temp.group(4)))
                frame = Frame(temp.group(2), id=int(temp.group(1)), size=int(temp.group(3)), transmitters=temp.group(4).split())
                db.frames.append(frame)
            elif decoded.startswith("SG_ "):
                pattern = "^SG_ +(\w+) *: *(\d+)\|(\d+)@(\d+)([\+|\-]) +\(([0-9.+\-eE]+),([0-9.+\-eE]+)\) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(.*)\" +(.*)"
                regexp = re.compile(pattern)
                temp = regexp.match(decoded)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp_raw = regexp_raw.match(l)
                if temp:
                    receiver = list(map(str.strip, temp.group(11).split(',')))

                    extras = {}
#                    if float_factory is not None:
#                        extras['float_factory'] = float_factory

                    tempSig = Signal(
                        temp.group(1),
                        startBit=int(temp.group(2)),
                        size=int(temp.group(3)),
                        is_little_endian=(int(temp.group(4)) == 1),
                        is_signed=(temp.group(5) == '-'),
                        factor=temp.group(6),
                        offset=temp.group(7),
                        min=temp.group(8),
                        max=temp.group(9),
                        unit=temp_raw.group(10).decode(dbcImportEncoding),
                        receiver=receiver,
                        **extras
                    )
                    if not tempSig.is_little_endian:
                        # startbit of motorola coded signals are MSB in dbc
                        tempSig.setStartbit(int(temp.group(2)), bitNumbering=1)
                    frame.addSignal(tempSig)
    #                db.frames.addSignalToLastFrame(tempSig)
                else:
                    pattern = "^SG_ +(\w+) +(\w+) *: *(\d+)\|(\d+)@(\d+)([\+|\-]) +\(([0-9.+\-eE]+),([0-9.+\-eE]+)\) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(.*)\" +(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    receiver = list(map(str.strip, temp.group(12).split(',')))
                    multiplex = temp.group(2)

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

                    tempSig = Signal(
                        temp.group(1),
                        startBit=int(temp.group(3)),
                        size=int(temp.group(4)),
                        is_little_endian=(int(temp.group(5)) == 1),
                        is_signed=(temp.group(6) == '-'),
                        factor=temp.group(7),
                        offset=temp.group(8),
                        min=temp.group(9),
                        max=temp.group(10),
                        unit=temp_raw.group(11).decode(dbcImportEncoding),
                        receiver=receiver,
                        multiplex=multiplex,
                        **extras
                    )

                    if is_complex_multiplexed:
                        tempSig.is_multiplexer = True
                        tempSig.multiplex = 'Multiplexor'

                    if not tempSig.is_little_endian:
                        # startbit of motorola coded signals are MSB in dbc
                        tempSig.setStartbit(int(temp.group(3)), bitNumbering=1)
                    frame.addSignal(tempSig)

                    if is_complex_multiplexed:
                        frame.is_complex_multiplexed = True


            elif decoded.startswith("BO_TX_BU_ "):
                regexp = re.compile("^BO_TX_BU_ ([0-9]+) *: *(.+);")
                temp = regexp.match(decoded)
                botschaft = db.frameById(temp.group(1))
                for bu in temp.group(2).split(','):
                    botschaft.addTransmitter(bu)
            elif decoded.startswith("CM_ SG_ "):
                pattern = "^CM_ +SG_ +(\w+) +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    botschaft = db.frameById(temp.group(1))
                    signal = botschaft.signalByName(temp.group(2))
                    if signal:
                        try:
                            signal.addComment(temp_raw.group(3).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = "^CM_ +SG_ +(\w+) +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        botschaft = db.frameById(temp.group(1))
                        signal = botschaft.signalByName(temp.group(2))
                        try:
                            comment = temp_raw.group(3).decode(
                                dbcCommentEncoding).replace('\\"', '"')
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                        followUp = FollowUps.signalComment

            elif decoded.startswith("CM_ BO_ "):
                pattern = "^CM_ +BO_ +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    frame = db.frameById(temp.group(1))
                    if frame:
                        try:
                            frame.addComment(temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = "^CM_ +BO_ +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        frame = db.frameById(temp.group(1))
                        try:
                            comment = temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"')
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                        followUp = FollowUps.frameComment
            elif decoded.startswith("CM_ BU_ "):
                pattern = "^CM_ +BU_ +(\w+) +\"(.*)\";"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    boardUnit = db.boardUnitByName(temp.group(1))
                    if boardUnit:
                        try:
                            boardUnit.addComment(temp_raw.group(2).decode(
                                dbcCommentEncoding).replace('\\"', '"'))
                        except:
                            logger.error(
                                "Error decoding line: %d (%s)" %
                                (i, line))
                else:
                    pattern = "^CM_ +BU_ +(\w+) +\"(.*)"
                    regexp = re.compile(pattern)
                    regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                    temp = regexp.match(decoded)
                    temp_raw = regexp_raw.match(l)
                    if temp:
                        boardUnit = db.boardUnitByName(temp.group(1))
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
                pattern = "^BU_\:(.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                if temp:
                    myTempListe = temp.group(1).split(' ')
                    for ele in myTempListe:
                        if len(ele.strip()) > 1:
                            db.boardUnits.append(BoardUnit(ele))

            elif decoded.startswith("VAL_ "):
                regexp = re.compile("^VAL_ +(\w+) +(\w+) +(.*);")
                temp = regexp.match(decoded)
                if temp:
                    botschaftId = temp.group(1)
                    signal = temp.group(2)
                    tempList = temp.group(3).split('"')
                    if botschaftId.isnumeric(): # value for Frame
                        try:
                            bo = db.frameById(botschaftId)
                            sg = bo.signalByName(signal)
                            for i in range(math.floor(len(tempList) / 2)):
                                val = tempList[i * 2 + 1]
                                if sg:
                                    sg.addValues(tempList[i * 2], val)
                        except:
                            logger.error("Error with Line: " + str(tempList))
                    else:
                        logger.info("Warning: enviroment variables currently not supported")

            elif decoded.startswith("VAL_TABLE_ "):
                regexp = re.compile("^VAL_TABLE_ +(\w+) +(.*);")
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
                    db.addValueTable(tableName, valHash)
                else:
                    logger.debug(l)

            elif decoded.startswith("BA_DEF_ SG_ "):
                pattern = "^BA_DEF_ +SG_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.addSignalDefines(temp.group(1),
                                        temp_raw.group(2).decode(dbcImportEncoding))
            elif decoded.startswith("BA_DEF_ BO_ "):
                pattern = "^BA_DEF_ +BO_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.addFrameDefines(temp.group(1),
                                       temp_raw.group(2).decode(dbcImportEncoding))
            elif decoded.startswith("BA_DEF_ BU_ "):
                pattern = "^BA_DEF_ +BU_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.addBUDefines(temp.group(1),
                                    temp_raw.group(2).decode(dbcImportEncoding))
            elif decoded.startswith("BA_DEF_ "):
                pattern = "^BA_DEF_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.addGlobalDefines(temp.group(1),
                                        temp_raw.group(2).decode(dbcImportEncoding))

            elif decoded.startswith("BA_ "):
                regexp = re.compile("^BA_ +\"[A-Za-z0-9[\-_ .]+\" +(.+)")
                tempba = regexp.match(decoded)

                if tempba.group(1).strip().startswith("BO_ "):
                    regexp = re.compile("^BA_ +\"(.*)\" +BO_ +(\w+) +(.+);")
                    temp = regexp.match(decoded)
                    db.frameById(int(temp.group(2))).addAttribute(
                        temp.group(1), temp.group(3))
                elif tempba.group(1).strip().startswith("SG_ "):
                    regexp = re.compile("^BA_ +\"(.*)\" +SG_ +(\w+) +(\w+) +(.+);")
                    temp = regexp.match(decoded)
                    if temp!=None:
                        db.frameById(int(temp.group(2))).signalByName(
                            temp.group(3)).addAttribute(temp.group(1), temp.group(4))
                elif tempba.group(1).strip().startswith("BU_ "):
                    regexp = re.compile("^BA_ +\"(.*)\" +BU_ +(\w+) +(.+);")
                    temp = regexp.match(decoded)
                    db.boardUnitByName(
                        temp.group(2)).addAttribute(
                        temp.group(1),
                        temp.group(3))
                else:
                    regexp = re.compile(
                        "^BA_ +\"([A-Za-z0-9\-_]+)\" +([\"A-Za-z0-9\-_\.]+);")
                    temp = regexp.match(decoded)
                    if temp:
                        db.addAttribute(temp.group(1), temp.group(2))

            elif decoded.startswith("SIG_GROUP_ "):
                regexp = re.compile("^SIG_GROUP_ +(\w+) +(\w+) +(\w+) +\:(.*);")
                temp = regexp.match(decoded)
                frame = db.frameById(temp.group(1))
                if frame is not None:
                    signalArray = temp.group(4).split(' ')
                    frame.addSignalGroup(temp.group(2), temp.group(3), signalArray)

            elif decoded.startswith("SIG_VALTYPE_ "):
                regexp = re.compile("^SIG_VALTYPE_ +(\w+) +(\w+)\s*\:(.*);")
                temp = regexp.match(decoded)
                frame = db.frameById(temp.group(1))
                if frame:
                    signal = frame.signalByName(temp.group(2))
                    signal.is_float = True
    #                SIG_VALTYPE_ 0 float : 1;

            elif decoded.startswith("BA_DEF_DEF_ "):
                pattern = "^BA_DEF_DEF_ +\"([A-Za-z0-9\-_\.]+)\" +(.+)\;"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    db.addDefineDefault(temp.group(1),
                                        temp_raw.group(2).decode(dbcImportEncoding))
            elif decoded.startswith("SG_MUL_VAL_ "):
                pattern = "^SG_MUL_VAL_ +([0-9]+) +([A-Za-z0-9\-_]+) +([A-Za-z0-9\-_]+) +([0-9]+)\-([0-9]+) *;"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    frameId = temp.group(1)
                    signalName = temp.group(2)
                    muxerForSignal = temp.group(3)
                    muxValMin = int(temp.group(4))
                    muxValMax = int(temp.group(4))
                    frame  = db.frameById(frameId)
                    if frame is not None:
                        signal = frame.signalByName(signalName)
                        frame.is_complex_multiplexed = True
                        signal.muxerForSignal = muxerForSignal
                        signal.muxValMin = muxValMin
                        signal.muxValMax = muxValMax
            elif decoded.startswith("EV_ "):
                pattern = "^EV_ +([A-Za-z0-9\-_]+) *\: +([0-9]+) +\[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] +\"(\w*)\" +([0-9.+\-eE]+) +([0-9.+\-eE]+) +([A-Za-z0-9\-_]+) +(.*);"
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
                db.addEnvVar( varName, {"varType": varType, "min" : min, "max" : max,
                              "unit" : unit, "initialValue" : initialValue, "evId" : evId,
                              "accessType" : accessType, "accessNodes" : accessNodes})


        except:
            print ("error with line no: %d" % i)
            print (line)
        #        else:
#            print("Unrecocniced line: " + l + " (%d) " % i)
# Backtracking

    for frame in db.frames:
        # receiver is only given in the signals, so do propagate the receiver
        # to the frame:
        frame.updateReceiver()
        # extended-flag is implicite in canid, thus repair this:
        if frame.id > 0x80000000:
            frame.id -= 0x80000000
            frame.extended = 1

        if "VFrameFormat" in frame.attributes and "_FD" in frame.attributes["VFrameFormat"]:
            frame.is_fd = True
    for define in db.globalDefines:
        if db.globalDefines[define].type == "STRING":
            if define in db.attributes:
                db.attributes[define] = db.attributes[define][1:-1]
    for define in db.buDefines:
        if db.buDefines[define].type == "STRING":
            for ecu in db.boardUnits:
                if define in ecu.attributes:
                    ecu.attributes[define] = ecu.attributes[define][1:-1]
    for define in db.frameDefines:
        if db.frameDefines[define].type == "STRING":
            for frame in db.frames:
                if define in frame.attributes:
                    frame.attributes[define] = frame.attributes[define][1:-1]
    for define in db.signalDefines:
        if db.signalDefines[define].type == "STRING":
            for frame in db.frames:
                for signal in frame.signals:
                    if define in signal.attributes:
                        signal.attributes[define] = signal.attributes[define][1:-1]

    db.EnumAttribs2Values()
    db.updateEcuList()
    db.delEcu("Vector__XXX")
    return db
