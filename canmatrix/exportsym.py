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
# this script exports sym-files from a canmatrix-object
# sym-files are the can-matrix-definitions of the Peak Systems Tools

from __future__ import division
from __future__ import absolute_import
from builtins import *
from .canmatrix import *
import math
import sys

enumDict = {}
enums = "{ENUMS}\n"

def createSignal(signal):
    global enums
    global enumDict
    output = ""
    output += "Var=%s " % (signal._name)
    if not signal._is_signed:
        output += "unsigned "
    else:
        output += "signed "
    if signal._is_little_endian == 0:
        #Motorola
        startBit = signal.getMsbReverseStartbit()
        output += "%d,%d -m " % (startBit, signal._signalsize)
    else:
        output += "%d,%d -i " % (signal.getMsbStartbit(), signal._signalsize)
    if len(signal._unit) > 0:
        output += "/u:%s " % ( signal._unit[0:16])
    if float(signal._factor) != 1:
        output += "/f:%g " % (float(signal._factor))
    if float(signal._offset) != 0:
        output += "/o:%g " % (float(signal._offset))
    output += "/min:{} /max:{} ".format(float(signal._min), float(signal._max))

    if "GenSigStartValue" in signal._attributes:
        default = float(signal._attributes["GenSigStartValue"]) * float(signal._factor)
        if default != 0 and default >= float(signal._min) and default <= float(signal._max):
            output += "/d:%g " % (default)

    if len(signal._values) > 0:
        valTabName = signal._name
        output += "/e:%s" % (valTabName)
        if valTabName not in enumDict:
            enums += "enum " + valTabName + "(" + ', '.join('%s="%s"' % (key,val) for (key,val) in sorted(signal._values.items())) + ")\n"
            enumDict[valTabName] = 1
    if signal._comment is not None and len(signal._comment) > 0:
        output += " // " + signal._comment.replace('\n',' ').replace('\r',' ')
    output += "\n"
    return output

def exportSym(db, filename, **options):
    """
    export canmatrix-object as .sym file (compatible to PEAK-Systems)
    """
    global enumDict
    global enums
    if 'symExportEncoding' in options:
        symEncoding=options["symExportEncoding"]
    else:
        symEncoding='iso-8859-1'

    enumDict = {}
    enums = "{ENUMS}\n"

    f = open(filename, 'wb')

    header = """FormatVersion=5.0 // Do not edit this line!
Title=\"canmatrix-Export\"
"""
    f.write( header.encode(symEncoding))
    


    #Frames
    output = "\n{SENDRECEIVE}\n"

    #trigger all frames
    for frame in db._fl._list:
        name = "[" + frame._name + "]\n"

        idType = "ID=%8Xh" % (frame._Id)
        if frame._comment is not None:
            idType += " // "+ frame._comment.replace('\n',' ').replace('\r',' ')
        idType += "\n"
        if frame._extended == 1:
            idType += "Type=Extended\n"
        else:
            idType += "Type=Standard\n"

        #check if frame has multiplexed signals
        multiplex = 0
        for signal in frame._signals:
            if signal._multiplex != None:
                multiplex = 1

        #if multiplex-signal:
        if multiplex == 1:
            #search for multiplexor in frame:
            for signal in frame._signals:
                if signal._multiplex == 'Multiplexor':
                    muxSignal = signal


            # ticker all possible mux-groups as i (0 - 2^ (number of bits of multiplexor))
            first = 0
            for i in range(0,1<<int(muxSignal._signalsize)):
                found = 0
                muxOut = ""
                #ticker all signals
                for signal in frame._signals:
                    # if signal is in mux-group i
                    if signal._multiplex == i:
                        muxOut = name
                        if first == 0:
                            muxOut += idType
                            first = 1
                        muxOut += "DLC=%d\n" % (frame._Size)


                        muxName = muxSignal._name + "%d" % i

                        muxOut += "Mux=" + muxName
                        if signal._is_little_endian == 0:
                            #Motorola
                            startBit = muxSignal.getMsbReverseStartbit()
                            muxOut += " %d,%d %d -m" % (startBit, muxSignal._signalsize, i)
                        else:
                            muxOut += " %d,%d %d" % (muxSignal.getMsbStartbit(), muxSignal._signalsize, i)
                        if muxSignal._values is not None and i in muxSignal._values:
                            muxOut += "// " + muxSignal._values[i].replace('\n','').replace('\r','')
                        muxOut += "\n"
                        found = 1
                        break

                if found == 1:
                    for signal in frame._signals:
                        if signal._multiplex == i or signal._multiplex == None:
                            muxOut += createSignal(signal)
                    output += muxOut + "\n"


        else:
            #no multiplex signals in frame, just 'normal' signals
            output += name
            output += idType
            output += "DLC=%d\n" % (frame._Size)
            if "GenMsgCycleTime" in frame._attributes:
                output += "CycleTime=" + frame._attributes["GenMsgCycleTime"] + "\n"
            for signal in frame._signals:
                output += createSignal(signal)
            output += "\n"
    #write outputfile
    f.write(enums.encode(symEncoding))
    f.write(output.encode(symEncoding))
