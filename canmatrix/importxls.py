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
# this script imports excel-files to a canmatrix-object
# these Excelfiles should have following collums:
# ID, Frame Name, Cycle Time [ms], Launch Type, Launch Parameter, Signal Byte No., Signal Bit No., Signal Name, Signal Function,  Signal Length [Bit], Signal Default, Signal Not Available, [LIST OF ECUS], Value,     Name / Phys. Range,     Function / Increment Unit
#

from __future__ import division
from __future__ import print_function

import logging
logger = logging.getLogger('root')

from builtins import *
import math
from .canmatrix import *
import xlrd
import codecs

def importXls(filename, **options):
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    wb = xlrd.open_workbook(filename, formatting_info=True)
    sh = wb.sheet_by_index(0)
    db = CanMatrix()

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
    index = {}
    for i in range(sh.ncols):
        value = sh.cell(0,i).value
        if  value == "ID":
            index['ID'] = i
        elif "Frame Name" in value:
            index['frameName'] = i
        elif "Cycle" in value:
            index['cycle'] = i
        elif "Launch Type" in value:
            index['launchType'] = i
        elif "Launch Parameter" in value:
            index['launchParam'] = i
        elif "Signal Byte No." in value:
            index['startbyte'] = i
        elif "Signal Bit No." in value:
            index['startbit'] = i
        elif "Signal Name" in value:
            index['signalName'] = i
        elif "Signal Function" in value:
            index['signalComment'] = i
        elif "Signal Length" in value:
            index['signalLength'] = i
        elif "Signal Default" in value:
            index['signalDefault'] = i
        elif "Signal Not Ava" in value:
            index['signalSNA'] = i
        elif "Value" in value:
            index['Value'] = i
        elif "Name / Phys" in value:
            index['ValueName'] = i
        elif "Function /" in value:
            index['function'] = i
        elif "Byteorder" in value:
            index['byteorder'] = i

    if "byteorder" in index:
        index['BUstart'] = index['byteorder'] + 1
    else:
        index['BUstart'] = index['signalSNA'] + 1
    index['BUend'] = index['Value']

    #BoardUnits:
    for x in range(index['BUstart'],index['BUend']):
        db._BUs.add(BoardUnit(sh.cell(0,x).value))

    #initialize:
    frameId = None
    signalName = ""
    newBo = None

    for rownum in range(1,sh.nrows):
        #ignore empty row
        if sh.cell(rownum,index['ID']).value.__len__() == 0:
            break
        # new frame detected
        if sh.cell(rownum,index['ID']).value != frameId:
            sender = []
            # new Frame
            frameId = sh.cell(rownum,index['ID']).value
            frameName = sh.cell(rownum,index['frameName']).value
            cycleTime = sh.cell(rownum,index['cycle']).value
            launchType = sh.cell(rownum,index['launchType']).value
            dlc = 8
            launchParam = sh.cell(rownum,index['launchParam']).value
            if type(launchParam).__name__ != "float":
                launchParam = 0.0
            launchParam = str(int(launchParam))

#            newBo = Frame(int(frameId[:-1], 16), frameName, dlc, None)
            newBo = Frame(frameName, Id=int(frameId[:-1], 16), dlc=dlc)
            db._fl.addFrame(newBo)

            #eval launctype
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

            #eval cycletime
            if type(cycleTime).__name__ != "float":
                cycleTime = 0.0
            newBo.addAttribute("GenMsgCycleTime", str(int(cycleTime)))

        #new signal detected
        if sh.cell(rownum,index['signalName']).value != signalName:
            # new Signal
            receiver = []
            startbyte = int(sh.cell(rownum,index['startbyte']).value)
            startbit = int(sh.cell(rownum,index['startbit']).value)
            signalName = sh.cell(rownum,index['signalName']).value
            signalComment = sh.cell(rownum,index['signalComment']).value.strip()
            signalLength = int(sh.cell(rownum,index['signalLength']).value)
            signalDefault = sh.cell(rownum,index['signalDefault']).value
            signalSNA = sh.cell(rownum,index['signalSNA']).value
            multiplex = None
            if signalComment.startswith('Mode Signal:'):
                multiplex = 'Multiplexor'
                signalComment = signalComment[12:]
            elif signalComment.startswith('Mode '):
                mux, signalComment = signalComment[4:].split(':',1)
                multiplex = int(mux.strip())

            if "byteorder" in index:
                signalByteorder = sh.cell(rownum,index['byteorder']).value

                if 'i' in signalByteorder:
                    is_little_endian = True
                else:
                    is_little_endian = False
            else:
                is_little_endian = True # Default Intel

            is_signed = False

            if signalName != "-":
                for x in range(index['BUstart'],index['BUend']):
                    if 's' in sh.cell(rownum,x).value:
                        newBo.addTransmitter(sh.cell(0,x).value.strip())
                    if 'r' in sh.cell(rownum,x).value:
                        receiver.append(sh.cell(0,x).value.strip())
#                if signalLength > 8:
                newSig = Signal(signalName, 
                              startBit = (startbyte-1)*8+startbit, 
                              signalSize = signalLength,
                              is_little_endian = is_little_endian, 
                              is_signed = is_signed, 
                              receiver=receiver,
                              multiplex=multiplex)     
#               else:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                if not is_little_endian:
                    #motorola
                    if motorolaBitFormat == "msb":
                        newSig.setMsbStartbit((startbyte-1)*8+startbit)
                    elif motorolaBitFormat == "msbreverse":
                        newSig.setMsbReverseStartbit((startbyte-1)*8+startbit)
                    else: # motorolaBitFormat == "lsb"
                        newSig.setLsbStartbit((startbyte-1)*8+startbit)
                newBo.addSignal(newSig)
                newSig.addComment(signalComment)
                function = sh.cell(rownum,index['function']).value
        value = str(sh.cell(rownum,index['Value']).value)
        valueName = sh.cell(rownum,index['ValueName']).value

        if valueName == 0:
            valueName = "0"
        elif valueName == 1:
            valueName = "1"
        test = valueName
        #.encode('utf-8')

        factor = 0
        unit = ""

        factor = sh.cell(rownum,index['function']).value
        if type(factor).__name__ == "unicode" or type(factor).__name__ == "str" :
            factor = factor.strip()
            if " " in factor and factor[0].isdigit():
                (factor, unit) = factor.strip().split(" ",1)
                factor = factor.strip()
                unit = unit.strip()
                newSig._unit = unit
                try:
                    newSig._factor = float(factor)
                except:
                    logger.warn("Some error occurred while decoding scale: Signal: %s; \"%s\"" % (signalName, sh.cell(rownum,index['function']).value))
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


        elif valueName.__len__() > 0:
            if value.strip().__len__() > 0:
                value = int(float(value))
                newSig.addValues(value, valueName)
            maxi = pow(2,signalLength)-1
            newSig._max = float(maxi)
        else:
            newSig._offset = 0


    for frame in db._fl._list:
        frame.updateReceiver()
        frame.calcDLC()

    return db
