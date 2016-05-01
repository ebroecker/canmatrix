#!/usr/bin/env python

from __future__ import division
from __future__ import absolute_import
from builtins import *
from .canmatrix import *
import codecs
import math

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
# this script exports dbf-files from a canmatrix-object
# dbf-files are the can-matrix-definitions of the busmaster-project (http://rbei-etas.github.io/busmaster/)


#CP1253

def exportDbf(db, filename, **options):
    if 'dbfExportEncoding' in options:
        dbfExportEncoding=options["dbfExportEncoding"]
    else:
        dbfExportEncoding='iso-8859-1'

    f = open(filename,"wb")
    outstr =  """//******************************BUSMASTER Messages and signals Database ******************************//

[DATABASE_VERSION] 1.3

[PROTOCOL] CAN

[BUSMASTER_VERSION] [1.7.2]
[NUMBER_OF_MESSAGES] """

    outstr += str(len(db._fl._list)) + "\n"

    #Frames
    for frame in db._fl._list:
    #Name unMsgId m_ucLength m_ucNumOfSignals m_cDataFormat m_cFrameFormat? m_txNode
    #m_cDataFormat If 1 dataformat Intel, 0- Motorola -- immer 1 original Converter macht das nach anzahl entsprechender Signale
    #cFrameFormat Standard 'S' Extended 'X'
        extended = 'S'
        if frame._extended == 1:
            extended = 'X'
        outstr += "[START_MSG] " + frame._name + ",%d,%d,%d,1,%c," % (frame._Id, frame._Size, len(frame._signals), extended)
        if frame._Transmitter.__len__() == 0:
            frame._Transmitter = ["Vector__XXX"]
#DBF does not support multiple Transmitters
        outstr +=  frame._Transmitter[0] + "\n"

        for signal in frame._signals:
    # m_acName ucLength m_ucWhichByte m_ucStartBit
    #m_ucDataFormat m_fOffset m_fScaleFactor m_acUnit m_acMultiplex m_rxNode
            #m_ucDataFormat
            whichbyte = int(math.floor(signal.getLsbStartbit() / 8) +1 )
            sign = 'S'

            if not signal._is_signed:
                sign = 'U'
            outstr += "[START_SIGNALS] " + signal._name + ",%d,%d,%d,%c," % (signal._signalsize,whichbyte,int(signal.getLsbStartbit())%8,sign) + '{},{}'.format(float(signal._max)/float(signal._factor),float(signal._min)/float(signal._factor))

            outstr += ",%d,%s,%s" % (signal._is_little_endian, signal._offset, signal._factor)
            multiplex = ""
            if signal._multiplex is not None:
                if signal._multiplex == 'Multiplexor':
                    multiplex = 'M'
                else:
                    multiplex = 'm' + str(signal._multiplex)

            outstr += "," + signal._unit + ",%s," % multiplex + ','.join(signal._receiver) + "\n"

            if len(signal._values) > 0:
                for attrib,val in sorted(list(signal._values.items())):
                    outstr += '[VALUE_DESCRIPTION] "' + val + '",' + str(attrib) + '\n'


        outstr += "[END_MSG]\n\n"

    #Boardunits
    outstr += "[NODE] "
    count = 1
    for bu in db._BUs._list:
        outstr += bu._name
        if count < len(db._BUs._list):
            outstr += ","
        count += 1
    outstr += "\n"


    outstr += "[START_DESC]\n\n"

    #BU-descriptions
    outstr += "[START_DESC_MSG]\n"
    for frame in db._fl._list:
        if frame._comment is not None:
            comment = frame._comment.replace("\n"," ")
            outstr += str(frame._Id) + ' S "' + comment + '";\n'

    outstr += "[END_DESC_MSG]\n"

    #Frame descriptions
    outstr += "[START_DESC_NODE]\n"
    for bu in db._BUs._list:
        if bu._comment is not None:
            comment = bu._comment.replace("\n"," ")
            outstr += bu._name  + ' "' + comment + '";\n'

    outstr += "[END_DESC_NODE]\n"


    #signal descriptions
    outstr += "[START_DESC_SIG]\n"
    for frame in db._fl._list:
        for signal in frame._signals:
            if signal._comment is not None:
                comment = signal._comment.replace("\n"," ")
                outstr += "%d S " % frame._Id + signal._name  + ' "' + comment + '";\n'

    outstr += "[END_DESC_SIG]\n"
    outstr += "[END_DESC]\n\n"

    outstr += "[START_PARAM]\n"
    # db-parameter
    outstr += "[START_PARAM_NET]\n"
    for (type,define) in list(db._globalDefines.items()):
        if define._defaultValue is not None:
            outstr += '"' + type + '",' + define._definition.replace(' ',',') + ',' + define._defaultValue + '\n'
    outstr += "[END_PARAM_NET]\n"

    # bu-parameter
    outstr += "[START_PARAM_NODE]\n"
    for (type,define) in list(db._buDefines.items()):
        if define._defaultValue is not None:
            outstr += '"' + type + '",' + define._definition.replace(' ',',') + ',' + define._defaultValue + '\n'
    outstr += "[END_PARAM_NODE]\n"

    # frame-parameter
    outstr += "[START_PARAM_MSG]\n"
    for (type,define) in list(db._frameDefines.items()):
        if define._defaultValue is not None:
            outstr += '"' + type + '",' + define._definition.replace(' ',',') + ',' + define._defaultValue + '\n'
    outstr += "[END_PARAM_MSG]\n"

    # signal-parameter
    outstr += "[START_PARAM_SIG]\n"
    for (type,define) in list(db._signalDefines.items()):
        if define._defaultValue is not None:
            outstr += '"' + type + '",' + define._definition.replace(' ',',') + ',' + define._defaultValue + '\n'
    outstr += "[END_PARAM_SIG]\n"

    outstr += "[START_PARAM_VAL]\n"
    #boardunit-attributes:
    outstr += "[START_PARAM_NODE_VAL]\n"
    for bu in db._BUs._list:
        for attrib,val in sorted(list(bu._attributes.items())):
            outstr += bu._name + ',"' + attrib + '","'  + val  + '"\n'
    outstr += "[END_PARAM_NODE_VAL]\n"

    #messages-attributes:
    outstr += "[START_PARAM_MSG_VAL]\n"
    for frame in db._fl._list:
        for attrib,val in sorted(list(frame._attributes.items())):
            outstr +=  str(frame._Id) + ',S,"' + attrib + '","'  + val  + '"\n'
    outstr += "[END_PARAM_MSG_VAL]\n"

    #signal-attributes:
    outstr += "[START_PARAM_SIG_VAL]\n"
    for frame in db._fl._list:
        for signal in frame._signals:
            for attrib,val in sorted(list(signal._attributes.items())):
                outstr +=  str(frame._Id) + ',S,' + signal._name + ',"'+ attrib  +  '","' + val  + '"\n'
    outstr += "[END_PARAM_SIG_VAL]\n"
    outstr += "[END_PARAM_VAL]\n"
    f.write(outstr.encode(dbfExportEncoding))
