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

import logging
logger = logging.getLogger('root')

from builtins import *
import math
from .canmatrix import *
import re
import codecs


#dbcExportEncoding = 'iso-8859-1'
# CP1253


def normalizeName(name, whitespaceReplacement):
    name = re.sub('\s+', whitespaceReplacement, name)

    if ' ' in name:
        name = '"' + name + '"'

    return name


def dump(db, f, **options):
    if 'dbcExportEncoding' in options:
        dbcExportEncoding = options["dbcExportEncoding"]
    else:
        dbcExportEncoding = 'iso-8859-1'
    if 'dbcExportCommentEncoding' in options:
        dbcExportCommentEncoding = options["dbcExportCommentEncoding"]
    else:
        dbcExportCommentEncoding = dbcExportEncoding
    if 'whitespaceReplacement' in options:
        whitespaceReplacement = options["whitespaceReplacement"]
        if whitespaceReplacement in ['', None] or set(
                [' ', '\t']).intersection(whitespaceReplacement):
            print("Warning: Settings may result in whitespace in DBC variable names.  This is not supported by the DBC format.")
    else:
        whitespaceReplacement = '_'

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

    # ValueTables
    for table in db.valueTables:
        f.write(("VAL_TABLE_ " + table).encode(dbcExportEncoding))
        for row in db.valueTables[table]:
            f.write(
                (' ' +
                 row +
                 ' "' +
                 db.valueTables[table][row] +
                 '"').encode(dbcExportEncoding))
        f.write(";\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # Frames
    for bo in db.frames:
        if bo.transmitter.__len__() == 0:
            bo.addTransmitter("Vector__XXX")

        if bo.extended == 1:
            bo.id += 0x80000000

        f.write(
            ("BO_ %d " %
             bo.id +
             bo.name +
             ": %d " %
             bo.size +
             bo.transmitter[0] +
             "\n").encode(dbcExportEncoding))
        for signal in bo.signals:
            name = normalizeName(signal.name, whitespaceReplacement)
            f.write((" SG_ " + name).encode(dbcExportEncoding))
            if signal.multiplex == 'Multiplexor':
                f.write(' M '.encode(dbcExportEncoding))
            elif signal.multiplex is not None:
                f.write((" m%d " %
                         int(signal.multiplex)).encode(dbcExportEncoding))

            startbit = signal.getStartbit(bitNumbering=1)

            if signal.is_signed:
                sign = '-'
            else:
                sign = '+'
            f.write(
                (" : %d|%d@%d%c" %
                 (startbit,
                  signal.signalsize,
                  signal.is_little_endian,
                  sign)).encode(dbcExportEncoding))
            f.write(
                (" (%g,%g)" %
                 (signal.factor, signal.offset)).encode(dbcExportEncoding))
            f.write(
                (" [{}|{}]".format(
                    signal.min,
                    signal.max)).encode(dbcExportEncoding))
            f.write(' "'.encode(dbcExportEncoding))

            f.write(signal.unit.encode(dbcExportEncoding))
            f.write('" '.encode(dbcExportEncoding))
            if signal.receiver.__len__() == 0:
                signal.addReceiver('Vector__XXX')
            f.write((','.join(signal.receiver) + "\n").encode(dbcExportEncoding))
        f.write("\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # second Sender:
    for bo in db.frames:
        if bo.transmitter.__len__() > 1:
            f.write(
                ("BO_TX_BU_ %d : %s;\n" %
                 (bo.id, ','.join(
                     bo.transmitter))).encode(dbcExportEncoding))

    # frame comments
    for bo in db.frames:
        if bo.comment is not None and bo.comment.__len__() > 0:
            f.write(
                ("CM_ BO_ " +
                 "%d " %
                 bo.id +
                 ' "').encode(dbcExportEncoding))
            f.write(
                bo.comment.replace(
                    '"',
                    '\\"').encode(dbcExportCommentEncoding))
            f.write('";\n'.encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal comments
    for bo in db.frames:
        for signal in bo.signals:
            if signal.comment is not None and signal.comment.__len__() > 0:
                name = normalizeName(signal.name, whitespaceReplacement)
                f.write(
                    ("CM_ SG_ " +
                     "%d " %
                     bo.id +
                     name +
                     ' "').encode(dbcExportEncoding))
                f.write(
                    signal.comment.replace(
                        '"', '\\"').encode(dbcExportCommentEncoding))
                f.write('";\n'.encode(dbcExportEncoding))
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
                    '";\n').encode(dbcExportCommentEncoding))
    f.write("\n".encode(dbcExportEncoding))

    defaults = {}
    for (type, define) in sorted(list(db.frameDefines.items())):
        f.write(
            ('BA_DEF_ BO_ "' +
             type +
             '" ').encode(dbcExportEncoding) +
            define.definition.encode(
                dbcExportEncoding,
                'replace') +
            ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define.defaultValue is not None:
            defaults[type] = define.defaultValue
    for (type, define) in sorted(list(db.signalDefines.items())):
        f.write(
            ('BA_DEF_ SG_ "' +
             type +
             '" ').encode(dbcExportEncoding) +
            define.definition.encode(
                dbcExportEncoding,
                'replace') +
            ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define.defaultValue is not None:
            defaults[type] = define.defaultValue
    for (type, define) in sorted(list(db.buDefines.items())):
        f.write(
            ('BA_DEF_ BU_ "' +
             type +
             '" ').encode(dbcExportEncoding) +
            define.definition.encode(
                dbcExportEncoding,
                'replace') +
            ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define.defaultValue is not None:
            defaults[type] = define.defaultValue
    for (type, define) in sorted(list(db.globalDefines.items())):
        f.write(
            ('BA_DEF_ "' +
             type +
             '" ').encode(dbcExportEncoding) +
            define.definition.encode(
                dbcExportEncoding,
                'replace') +
            ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define.defaultValue is not None:
            defaults[type] = define.defaultValue

    for define in sorted(defaults):
        f.write(
            ('BA_DEF_DEF_ "' +
             define +
             '" ').encode(dbcExportEncoding) +
            defaults[define].encode(
                dbcExportEncoding,
                'replace') +
            ';\n'.encode(dbcExportEncoding))

    # boardunit-attributes:
    for bu in db.boardUnits:
        for attrib, val in sorted(bu.attributes.items()):
            if db.buDefines[attrib].type == "STRING":
                val = '"' + val + '"'
            elif not val:
                val = '""'
            f.write(
                ('BA_ "' +
                 attrib +
                 '" BU_ ' +
                 bu.name +
                 ' ' +
                 str(val) +
                    ';\n').encode(dbcExportEncoding))
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
    for bo in db.frames:
        for attrib, val in sorted(bo.attributes.items()):
            if db.frameDefines[attrib].type == "STRING":
                val = '"' + val + '"'
            elif not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BO_ %d ' %
                     bo.id + val + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal-attributes:
    for bo in db.frames:
        for signal in bo.signals:
            for attrib, val in sorted(signal.attributes.items()):
                name = normalizeName(signal.name, whitespaceReplacement)
                if db.signalDefines[attrib].type == "STRING":
                    val = '"' + val + '"'
                elif not val:
                    val = '""'
                f.write(
                    ('BA_ "' +
                     attrib +
                     '" SG_ %d ' %
                     bo.id +
                     name +
                     ' ' +
                     val +
                     ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal-values:
    for bo in db.frames:
        for signal in bo.signals:
            if signal.values:
                f.write(
                    ('VAL_ %d ' %
                     bo.id +
                     signal.name).encode(dbcExportEncoding))
                for attrib, val in sorted(
                        signal.values.items(), key=lambda x: int(x[0])):
                    f.write(
                        (' ' + str(attrib) + ' "' + val + '"').encode(dbcExportEncoding))
                f.write(";\n".encode(dbcExportEncoding))

    # signal-groups:
    for bo in db.frames:
        for sigGroup in bo.SignalGroups:
            f.write(("SIG_GROUP_ " + str(bo.id) + " " + sigGroup.name +
                     " " + str(sigGroup.id) + " :").encode(dbcExportEncoding))
            for signal in sigGroup.signals:
                f.write((" " + signal.name).encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))


def load(f, **options):
    if 'dbcImportEncoding' in options:
        dbcImportEncoding = options["dbcImportEncoding"]
    else:
        dbcImportEncoding = 'iso-8859-1'
    if 'dbcImportCommentEncoding' in options:
        dbcCommentEncoding = options["dbcImportCommentEncoding"]
    else:
        dbcCommentEncoding = dbcImportEncoding

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
        decoded = l.decode(dbcImportEncoding)
        if decoded.startswith("BO_ "):
            regexp = re.compile("^BO\_ (\w+) (\w+) *: (\w+) (\w+)")
            temp = regexp.match(decoded)
#            db._fl.addFrame(Frame(temp.group(1), temp.group(2), temp.group(3), temp.group(4)))
            db._fl.addFrame(Frame(temp.group(2),
                                  Id=temp.group(1),
                                  dlc=temp.group(3),
                                  transmitter=temp.group(4)))
        elif decoded.startswith("SG_ "):
            pattern = "^SG\_ (\w+) : (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)"
            regexp = re.compile(pattern)
            temp = regexp.match(decoded)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp_raw = regexp_raw.match(l)
            if temp:
                receiver = list(map(str.strip, temp.group(11).split(',')))

                tempSig = Signal(temp.group(1),
                                 startBit=temp.group(2),
                                 signalSize=temp.group(3),
                                 is_little_endian=(int(temp.group(4)) == 1),
                                 is_signed=(temp.group(5) == '-'),
                                 factor=temp.group(6),
                                 offset=temp.group(7),
                                 min=temp.group(8),
                                 max=temp.group(9),
                                 unit=temp_raw.group(10).decode(
                                     dbcImportEncoding),
                                 receiver=receiver)
                if not tempSig.is_little_endian:
                    # startbit of motorola coded signals are MSB in dbc
                    tempSig.setStartbit(int(temp.group(2)), bitNumbering=1)
                db._fl.addSignalToLastFrame(tempSig)
            else:
                pattern = "^SG\_ (\w+) (\w+) *: (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                receiver = list(map(str.strip, temp.group(12).split(',')))
                multiplex = temp.group(2)
                if multiplex == 'M':
                    multiplex = 'Multiplexor'
                else:
                    multiplex = int(multiplex[1:])
                tempSig = Signal(temp.group(1),
                                 startBit=temp.group(3),
                                 signalSize=temp.group(4),
                                 is_little_endian=(int(temp.group(5)) == 1),
                                 is_signed=(temp.group(6) == '-'),
                                 factor=temp.group(7),
                                 offset=temp.group(8),
                                 min=temp.group(9),
                                 max=temp.group(10),
                                 unit=temp_raw.group(11).decode(
                                     dbcImportEncoding),
                                 receiver=receiver,
                                 multiplex=multiplex)
                if not tempSig.is_little_endian:
                    # startbit of motorola coded signals are MSB in dbc
                    tempSig.setStartbit(int(temp.group(3)), bitNumbering=1)

                db._fl.addSignalToLastFrame(tempSig)

        elif decoded.startswith("BO_TX_BU_ "):
            regexp = re.compile("^BO_TX_BU_ ([0-9]+) *: *(.+);")
            temp = regexp.match(decoded)
            botschaft = db.frameById(temp.group(1))
            for bu in temp.group(2).split(','):
                botschaft.addTransmitter(bu)
        elif decoded.startswith("CM_ SG_ "):
            pattern = "^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)\";"
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
                pattern = "^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)"
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
            pattern = "^CM\_ BO\_ *(\w+) *\"(.*)\";"
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
                pattern = "^CM\_ BO\_ *(\w+) *\"(.*)"
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
            pattern = "^CM\_ BU\_ *(\w+) *\"(.*)\";"
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
                pattern = "^CM\_ BU\_ *(\w+) *\"(.*)"
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
            pattern = "^BU\_\:(.*)"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            if temp:
                myTempListe = temp.group(1).split(' ')
                for ele in myTempListe:
                    if len(ele.strip()) > 1:
                        db._BUs.add(BoardUnit(ele))

        elif decoded.startswith("VAL_ "):
            regexp = re.compile("^VAL\_ (\w+) (\w+) (.*);")
            temp = regexp.match(decoded)
            if temp:
                botschaftId = temp.group(1)
                signal = temp.group(2)
                tempList = temp.group(3).split('"')
                try:
                    for i in range(math.floor(len(tempList) / 2)):
                        bo = db.frameById(botschaftId)
                        sg = bo.signalByName(signal)
                        val = tempList[i * 2 + 1]
                        #[1:-1]

                        if sg:
                            sg.addValues(tempList[i * 2], val)
                except:
                    logger.error("Error with Line: " + str(tempList))

        elif decoded.startswith("VAL_TABLE_ "):
            regexp = re.compile("^VAL\_TABLE\_ (\w+) (.*);")
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
            pattern = "^BA\_DEF\_ SG\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addSignalDefines(temp.group(1),
                                    temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ BO_ "):
            pattern = "^BA\_DEF\_ BO\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addFrameDefines(temp.group(1),
                                   temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ BU_ "):
            pattern = "^BA\_DEF\_ BU\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addBUDefines(temp.group(1),
                                temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ "):
            pattern = "^BA\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addGlobalDefines(temp.group(1),
                                    temp_raw.group(2).decode(dbcImportEncoding))

        elif decoded.startswith("BA_ "):
            regexp = re.compile("^BA\_ +\"[A-Za-z0-9\-_]+\" +(.+)")
            tempba = regexp.match(decoded)

            if tempba.group(1).strip().startswith("BO_ "):
                regexp = re.compile("^BA\_ \"(.*)\" BO\_ (\w+) (.+);")
                temp = regexp.match(decoded)
                db.frameById(int(temp.group(2))).addAttribute(
                    temp.group(1), temp.group(3))
            elif tempba.group(1).strip().startswith("SG_ "):
                regexp = re.compile("^BA\_ \"(.*)\" SG\_ (\w+) (\w+) (.+);")
                temp = regexp.match(decoded)
                db.frameById(int(temp.group(2))).signalByName(
                    temp.group(3)).addAttribute(temp.group(1), temp.group(4))
            elif tempba.group(1).strip().startswith("BU_ "):
                regexp = re.compile("^BA\_ \"(.*)\" BU\_ (\w+) (.+);")
                temp = regexp.match(decoded)
                db._BUs.byName(
                    temp.group(2)).addAttribute(
                    temp.group(1),
                    temp.group(3))
            else:
                regexp = re.compile(
                    "^BA\_ \"([A-Za-z0-9\-\_]+)\" +([\"A-Za-z0-9\-\_]+);")
                temp = regexp.match(decoded)
                if temp:
                    db.addAttribute(temp.group(1), temp.group(2))

        elif decoded.startswith("SIG_GROUP_ "):
            regexp = re.compile("^SIG\_GROUP\_ +(\w+) +(\w+) +(\w+) +\:(.*);")
            temp = regexp.match(decoded)
            frame = db.frameById(temp.group(1))
            if frame is not None:
                signalArray = temp.group(4).split(' ')
                frame.addSignalGroup(temp.group(2), temp.group(3), signalArray)
        elif decoded.startswith("BA_DEF_DEF_ "):
            pattern = "^BA\_DEF\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+)\;"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addDefineDefault(temp.group(1),
                                    temp_raw.group(2).decode(dbcImportEncoding))
#               else:
#                       print "Unrecocniced line: " + l + " (%d) " % i

    for frame in db.frames:
        # receiver is only given in the signals, so do propagate the receiver
        # to the frame:
        frame.updateReceiver()
        # extended-flag is implicite in canid, thus repair this:
        if frame.id > 0x80000000:
            frame.id -= 0x80000000
            frame.extended = 1
    return db
