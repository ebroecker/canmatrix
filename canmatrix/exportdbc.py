from __future__ import absolute_import
from builtins import *
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

from .canmatrix import *
import codecs
import re

#dbcExportEncoding = 'iso-8859-1'
# CP1253


def normalizeName(name, whitespaceReplacement):
    name = re.sub('\s+', whitespaceReplacement, name)

    if ' ' in name:
        name = '"' + name + '"'

    return name


def exportDbc(db, filename, **options):
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

    f = open(filename, "wb")

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
            if not val:
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
        if not val:
            val = '""'
        f.write(('BA_ "' + attrib + '" ' + val +
                 ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # messages-attributes:
    for bo in db.frames:
        for attrib, val in sorted(bo.attributes.items()):
            if not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BO_ %d ' %
                     bo.id + val + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    # signal-attributes:
    for bo in db.frames:
        for signal in bo.signals:
            for attrib, val in sorted(signal.attributes.items()):
                name = normalizeName(signal.name, whitespaceReplacement)
                if not val:
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
