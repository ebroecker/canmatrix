from __future__ import absolute_import
from builtins import *
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
# this script exports dbc-files from a canmatrix-object
# dbc-files are the can-matrix-definitions of the CanOe (Vector Informatic)

from .canmatrix import *
import codecs
import re

#dbcExportEncoding = 'iso-8859-1'
#CP1253

def normalizeName(name, whitespaceReplacement):
    name = re.sub('\s+', whitespaceReplacement, name)

    if ' ' in name:
        name = '"' + name + '"'

    return name


def exportDbc(db, filename, **options):
    if 'dbcExportEncoding' in options:
        dbcExportEncoding=options["dbcExportEncoding"]
    else:
        dbcExportEncoding='iso-8859-1'
    if 'dbcExportCommentEncoding' in options:
        dbcExportCommentEncoding=options["dbcExportCommentEncoding"]
    else:
        dbcExportCommentEncoding=dbcExportEncoding
    if 'whitespaceReplacement' in options:
        whitespaceReplacement=options["whitespaceReplacement"]
        if whitespaceReplacement in ['', None] or set([' ', '\t']).intersection(whitespaceReplacement):
            print("Warning: Settings may result in whitespace in DBC variable names.  This is not supported by the DBC format.")
    else:
        whitespaceReplacement='_'

    f = open(filename,"wb")

    f.write( "VERSION \"created by canmatrix\"\n\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    f.write("NS_ :\n\nBS_:\n\n".encode(dbcExportEncoding))


    #Boardunits
    f.write( "BU_: ".encode(dbcExportEncoding))
    id = 1
    nodeList = {};
    for bu in db._BUs._list:
        f.write((bu._name + " ").encode(dbcExportEncoding))
    f.write("\n\n".encode(dbcExportEncoding))

    #ValueTables
    for table in db._valueTables:
        f.write(("VAL_TABLE_ " + table).encode(dbcExportEncoding))
        for row in db._valueTables[table]:
            f.write((' ' + row + ' "' + db._valueTables[table][row] + '"').encode(dbcExportEncoding))
        f.write(";\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #Frames
    for bo in db._fl._list:
        if bo._Transmitter.__len__() == 0:
            bo._Transmitter = ["Vector__XXX"]

        if bo._extended == 1:
            bo._Id += 0x80000000

        f.write(("BO_ %d " % bo._Id + bo._name + ": %d " % bo._Size + bo._Transmitter[0] + "\n").encode(dbcExportEncoding))
        for signal in bo._signals:
            name = normalizeName(signal._name, whitespaceReplacement)
            f.write((" SG_ " + name).encode(dbcExportEncoding))
            if signal._multiplex == 'Multiplexor':
                f.write(' M '.encode(dbcExportEncoding))
            elif signal._multiplex is not None:
                f.write((" m%d " % int(signal._multiplex)).encode(dbcExportEncoding))

            startbit = signal.getMsbStartbit()

            if signal._is_signed:
                sign = '-'
            else:
                sign = '+'
            f.write((" : %d|%d@%d%c" % (startbit, signal._signalsize,signal._is_little_endian, sign)).encode(dbcExportEncoding))
            f.write((" (%g,%g)" % (signal._factor, signal._offset)).encode(dbcExportEncoding))
            f.write((" [{}|{}]".format(signal._min, signal._max)).encode(dbcExportEncoding))
            f.write(' "'.encode(dbcExportEncoding))

            f.write(signal._unit.encode(dbcExportEncoding))
            f.write('" '.encode(dbcExportEncoding))
            if signal._receiver.__len__() == 0:
                signal._receiver = ['Vector__XXX']
            f.write((','.join(signal._receiver) + "\n").encode(dbcExportEncoding))
        f.write("\n".encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #second Sender:
    for bo in db._fl._list:
        if bo._Transmitter.__len__() > 1:
            f.write(("BO_TX_BU_ %d : %s;\n" % (bo._Id,','.join(bo._Transmitter))).encode(dbcExportEncoding))

    #frame comments
    for bo in db._fl._list:
        if bo._comment is not None and bo._comment.__len__() > 0:
            f.write(("CM_ BO_ " + "%d " % bo._Id + ' "').encode(dbcExportEncoding))
            f.write(bo._comment.replace('"','\\"').encode(dbcExportCommentEncoding))
            f.write('";\n'.encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #signal comments
    for bo in db._fl._list:
        for signal in bo._signals:
            if signal._comment is not None and signal._comment.__len__() > 0:
                name = normalizeName(signal._name, whitespaceReplacement)
                f.write(("CM_ SG_ " + "%d " % bo._Id + name  + ' "').encode(dbcExportEncoding))
                f.write(signal._comment.replace('"','\\"').encode(dbcExportCommentEncoding))
                f.write('";\n'.encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #boarUnit comments
    for bu in db._BUs._list:
        if bu._comment is not None and bu._comment.__len__() > 0:
            f.write(("CM_ BU_ " + bu._name + ' "' + bu._comment.replace('"','\\"') + '";\n').encode(dbcExportCommentEncoding))
    f.write("\n".encode(dbcExportEncoding))

    defaults = {}
    for (type,define) in sorted(list(db._frameDefines.items())):
        f.write(('BA_DEF_ BO_ "' + type + '" ').encode(dbcExportEncoding) + define._definition.encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define._defaultValue is not None:
            defaults[type] = define._defaultValue
    for (type,define) in sorted(list(db._signalDefines.items())):
        f.write(('BA_DEF_ SG_ "' + type + '" ').encode(dbcExportEncoding) + define._definition.encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define._defaultValue is not None:
            defaults[type] = define._defaultValue
    for (type,define) in sorted(list(db._buDefines.items())):
        f.write(('BA_DEF_ BU_ "' + type + '" ').encode(dbcExportEncoding) + define._definition.encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define._defaultValue is not None:
            defaults[type] = define._defaultValue
    for (type,define) in sorted(list(db._globalDefines.items())):
        f.write(('BA_DEF_ "' + type + '" ').encode(dbcExportEncoding) + define._definition.encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))
        if type not in defaults and define._defaultValue is not None:
            defaults[type] = define._defaultValue

    for define in sorted(defaults):
        f.write(('BA_DEF_DEF_ "' + define + '" ').encode(dbcExportEncoding) + defaults[define].encode(dbcExportEncoding,'replace') + ';\n'.encode(dbcExportEncoding))


    #boardunit-attributes:
    for bu in db._BUs._list:
        for attrib,val in sorted(bu._attributes.items()):
            if not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BU_ ' + bu._name + ' ' + str(val)  + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #global-attributes:
    for attrib,val in sorted(db._attributes.items()):
        if not val:
            val = '""'
        f.write(('BA_ "' + attrib + '" ' + val  + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #messages-attributes:
    for bo in db._fl._list:
        for attrib,val in sorted(bo._attributes.items()):
            if not val:
                val = '""'
            f.write(('BA_ "' + attrib + '" BO_ %d ' % bo._Id + val + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #signal-attributes:
    for bo in db._fl._list:
        for signal in bo._signals:
            for attrib,val in sorted(signal._attributes.items()):
                name = normalizeName(signal._name, whitespaceReplacement)
                if not val:
                    val = '""'
                f.write(('BA_ "' + attrib + '" SG_ %d ' % bo._Id + name + ' ' + val  + ';\n').encode(dbcExportEncoding))
    f.write("\n".encode(dbcExportEncoding))

    #signal-values:
    for bo in db._fl._list:
        for signal in bo._signals:
            if signal._values:
                f.write(('VAL_ %d ' % bo._Id + signal._name).encode(dbcExportEncoding))
                for attrib,val in sorted(signal._values.items(), key=lambda x: int(x[0])):
                    f.write((' ' + str(attrib) + ' "' + val + '"').encode(dbcExportEncoding))
                f.write(";\n".encode(dbcExportEncoding));


    #signal-groups:
    for bo in db._fl._list:
        for sigGroup in bo._SignalGroups:
            f.write(("SIG_GROUP_ " + str(bo._Id) + " " + sigGroup._name + " " + str(sigGroup._Id)+ " :").encode(dbcExportEncoding))
            for signal in sigGroup._members:
                f.write((" " + signal._name).encode(dbcExportEncoding))
            f.write(";\n".encode(dbcExportEncoding))
