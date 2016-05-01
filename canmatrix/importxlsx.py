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
# this script imports excel-files (xlsx) to a canmatrix-object
# these Excelfiles should have following collums:
# ID, Frame Name, Cycle Time [ms], Launch Type, Launch Parameter, Signal Byte No., Signal Bit No., Signal Name, Signal Function,  Signal Length [Bit], Signal Default, Signal Not Available, [LIST OF ECUS], Value,     Name / Phys. Range,     Function / Increment Unit
#

from __future__ import division
from builtins import *
import math
from .canmatrix import *
import codecs
import zipfile
from xml.etree.ElementTree import iterparse

def readXlsx( fileName, **args ):
    #from: Hooshmand zandi http://stackoverflow.com/a/16544219
    import zipfile
    from xml.etree.ElementTree import iterparse

    if "sheet" in args:
        sheet=args["sheet"]
    else:
        sheet=1
    if "header" in args:
        isHeader=args["header"]
    else:
        isHeader=False

    rows   = []
    row    = {}
    header = {}
    z      = zipfile.ZipFile( fileName )

    # Get shared strings
    strings = [ el.text for e, el
                        in  iterparse( z.open( 'xl/sharedStrings.xml' ) )
                        if el.tag.endswith( '}t' )
                        ]
    value = ''

    # Open specified worksheet
    for e, el in iterparse( z.open( 'xl/worksheets/sheet%d.xml'%( sheet ) ) ):
        # get value or index to shared strings
        if el.tag.endswith( '}v' ):                                   # <v>84</v>
            value = el.text
        if el.tag.endswith( '}c' ):                                   # <c r="A3" t="s"><v>84</v></c>
            # If value is a shared string, use value as an index

            if el.attrib.get( 't' ) == 's':
                value = strings[int( value )]

            # split the row/col information so that the row leter(s) can be separate
            letter = el.attrib['r']                                   # AZ22
            while letter[-1].isdigit():
                letter = letter[:-1]

            # if it is the first row, then create a header hash for the names
            # that COULD be used
            if rows ==[]:
                header[letter]=value.strip()
            else:
                if value != '':

                    # if there is a header row, use the first row's names as the row hash index
                    if isHeader == True and letter in header:
                        row[header[letter]] = value
                    else:
                        row[letter] = value

            value = ''
        if el.tag.endswith('}row'):
            rows.append(row)
            row = {}
    z.close()
    return [header, rows]

def getIfPossible(row, value):
    if value in row:
        return row[value].strip()
    else:
        return None

def importXlsx(filename, **options):
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    sheet = readXlsx( filename, sheet = 1, header = True )
    db = CanMatrix()
    letterIndex = []
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        letterIndex.append(a)
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        for b in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            letterIndex.append("%s%s" % (a,b))

    #Defines not imported...
#       db.addBUDefines("NWM-Stationsadresse",  'HEX 0 63')
#       db.addBUDefines("NWM-Knoten",  'ENUM  "nein","ja"')
    db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')
    db.addFrameDefines("GenMsgDelayTime",  'INT 0 65535')
    db.addFrameDefines("GenMsgCycleTimeActive",  'INT 0 65535')
    db.addFrameDefines("GenMsgNrOfRepetitions",  'INT 0 65535')
#       db.addFrameDefines("GenMsgStartValue",  'STRING')
    db.addFrameDefines("GenMsgSendType",  'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
#       db.addSignalDefines("GenSigStartValue", 'HEX 0 4294967295')
    db.addSignalDefines("GenSigSNA", 'STRING')

    # eval search for correct collums:
#       index = {}
#       for i in range(sh.ncols):
#               value = sh.cell(0,i).value
#               if  value == "ID":
#                       index['ID'] = i
#               elif "Frame Name" in value:
#                       index['frameName'] = i
#               elif "Cycle" in value:
#                       index['cycle'] = i
#               elif "Launch Type" in value:
#                       index['launchType'] = i
#               elif "Launch Parameter" in value:
#                       index['launchParam'] = i
#               elif "Signal Byte No." in value:
#                       index['startbyte'] = i
#               elif "Signal Bit No." in value:
#                       index['startbit'] = i
#               elif "Signal Name" in value:
#                       index['signalName'] = i
#               elif "Signal Function" in value:
#                       index['signalComment'] = i
#               elif "Signal Length" in value:
#                       index['signalLength'] = i
#               elif "Signal Default" in value:
#                       index['signalDefault'] = i
#               elif "Signal Not Ava" in value:
#                       index['signalSNA'] = i
#               elif "Value" in value:
#                       index['Value'] = i
#               elif "Name / Phys" in value:
#                       index['ValueName'] = i
#               elif "Function /" in value:
#                       index['function'] = i
#               elif "Byteorder" in value:
#                       index['byteorder'] = i
    if 'Byteorder' in list(sheet[0].values()):
        for key in sheet[0]:
            if sheet[0][key].strip() == 'Byteorder':
                _BUstart = letterIndex.index(key)+1
                break
    else:
        for key in sheet[0]:
            if sheet[0][key].strip() == 'Signal Not Available':
                _BUstart = letterIndex.index(key)+1

    for key in sheet[0]:
        if sheet[0][key].strip() == 'Value':
            _BUend = letterIndex.index(key)

    #BoardUnits:
    for x in range(_BUstart,_BUend):
        db._BUs.add(BoardUnit(sheet[0][letterIndex[x]]))

    #initialize:
    frameId = None
    signalName = ""
    newBo = None

    for row in sheet[1]:
        #ignore empty row
        if not 'ID' in row:
            continue
        # new frame detected
        if row['ID'] != frameId:
            sender = []
            # new Frame
            frameId = row['ID']
            frameName = row['Frame Name']
            cycleTime = getIfPossible(row,"Cycle Time [ms]")
            launchType = getIfPossible(row,'Launch Type')
            dlc = 8
            launchParam = getIfPossible(row,'Launch Parameter')
            if type(launchParam).__name__ != "float":
                launchParam = 0.0
            launchParam = str(int(launchParam))

#            newBo = Frame(int(frameId[:-1], 16), frameName, dlc, None)
            newBo = Frame(frameName, Id=int(frameId[:-1], 16), dlc=dlc)

            db._fl.addFrame(newBo)

            #eval launchtype
            if launchType is not None:
                if "Cyclic+Change" == launchType:
                    newBo.addAttribute("GenMsgSendType", "5")
                    newBo.addAttribute("GenMsgDelayTime", launchParam)
                elif "Cyclic" == launchType:
                    newBo.addAttribute("GenMsgSendType", "0")
                elif "BAF" == launchType:
                    newBo.addAttribute("GenMsgSendType", "2")
                    newBo.addAttribute("GenMsgNrOfRepetitions", launchParam)
                elif "DualCycle" == launchType:
                    newBo.addAttribute("GenMsgSendType", "8")
                    newBo.addAttribute("GenMsgCycleTimeActive", launchParam)
                elif "None" == launchType:
                    newBo.addAttribute("GenMsgSendType", "10")
                    newBo.addAttribute("GenMsgDelayTime", launchParam)
                elif "OnChange" == launchType:
                    newBo.addAttribute("GenMsgSendType", "9")
                    newBo.addAttribute("GenMsgNrOfRepetitions", launchParam)
                elif "Spontaneous" == launchType:
                    newBo.addAttribute("GenMsgSendType", "1")
                    newBo.addAttribute("GenMsgDelayTime", launchParam)

#                       #eval cycletime
            if type(cycleTime).__name__ != "float":
                cycleTime = 0.0
            newBo.addAttribute("GenMsgCycleTime", str(int(cycleTime)))

        #new signal detected
        if row['Signal Name'] != signalName:
            # new Signal
            receiver = []
            startbyte = int(row["Signal Byte No."])
            startbit = int(row['Signal Bit No.'])
            signalName = row['Signal Name']
            signalComment = getIfPossible(row,'Signal Function')
            signalLength = int(row['Signal Length [Bit]'])
            signalDefault = getIfPossible(row,'Signal Default')
            signalSNA = getIfPossible(row,'Signal Not Available')
            multiplex = None
            if signalComment is not None and signalComment.startswith('Mode Signal:'):
                multiplex = 'Multiplexor'
                signalComment = signalComment[12:]
            elif signalComment is not None and signalComment.startswith('Mode '):
                mux, signalComment = signalComment[4:].split(':',1)
                multiplex = int(mux.strip())

            signalByteorder = getIfPossible(row,'Byteorder')
            if signalByteorder is not None:
                if 'i' in signalByteorder:
                    is_little_endian = True
                else:
                    is_little_endian = False
            else:
                is_little_endian = True # Default Intel

            is_signed = False

            if signalName != "-":
                for x in range(_BUstart,_BUend):
                    buName = sheet[0][letterIndex[x]].strip()
                    buSenderReceiver = getIfPossible(row,buName)
                    if buSenderReceiver is not None:
                        if 's' in buSenderReceiver:
                            newBo.addTransmitter(buName)
                        if 'r' in buSenderReceiver:
                            receiver.append(buName)
#                if signalLength > 8:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                newSig = Signal(signalName, 
                          startBit = (startbyte-1)*8+startbit, 
                          signalSize = signalLength,
                          is_little_endian = is_little_endian, 
                          is_signed = is_signed, 
                          receiver=receiver,
                          multiplex=multiplex)     

#                else:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                if is_little_endian == False:
                    #motorola
                    if motorolaBitFormat == "msb":
                        newSig.setMsbStartbit((startbyte-1)*8+startbit)
                    elif motorolaBitFormat == "msbreverse":
                        newSig.setMsbReverseStartbit((startbyte-1)*8+startbit)
                    else: # motorolaBitFormat == "lsb"
                        newSig.setLsbStartbit((startbyte-1)*8+startbit)

                newBo.addSignal(newSig)
                newSig.addComment(signalComment)
                function = getIfPossible(row, 'Function / Increment Unit')
        value = getIfPossible(row,'Value')
        valueName = getIfPossible(row,'Name / Phys. Range')

        if valueName == 0 or valueName == None:
            valueName = "0"
        elif valueName == 1:
            valueName = "1"
        test = valueName
        #.encode('utf-8')

        factor = 0
        unit = ""

        factor = getIfPossible(row,'Function / Increment Unit')
        if type(factor).__name__ == "unicode" or  type(factor).__name__ == "str":
            factor = factor.strip()
            if " " in factor and factor[0].isdigit():
                (factor, unit) = factor.strip().split(" ",1)
                factor = factor.strip()
                unit = unit.strip()
                newSig._unit = unit
                newSig._factor = float(factor)
            else:
                unit = factor.strip()
                newSig._unit = unit
                newSig._factor = 1


        if ".." in test:
            (mini, maxi) = test.strip().split("..",2)
            unit = ""
            try:
                newSig._offset = float(mini)
                newSig._min = float(mini)
                newSig._max = float(maxi)
            except:
                newSig._offset = 0
                newSig._min = None
                newSig._max = None


        elif valueName.__len__() > 0:
            if value is not None and value.strip().__len__() > 0:
                value = int(float(value))
                newSig.addValues(value, valueName)
            maxi = pow(2,signalLength)-1
            newSig._max = float(maxi)
        else:
            newSig._offset = 0
            newSig._min = None
            newSig._max = None

    # dlc-estimation / dlc is not in xls, thus calculate a minimum-dlc:
    for frame in db._fl._list:
        frame.updateReceiver()
        frame.calcDLC()

    return db
