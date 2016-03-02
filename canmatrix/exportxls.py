#!/usr/bin/env python
#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the aframeve copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the aframeve copyright notice, this list of conditions and the
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
# this script exports xls-files from a canmatrix-object
# xls-files are the can-matrix-definitions displayed in Excel

from __future__ import division
from __future__ import absolute_import
from builtins import *
import math
import xlwt
import sys
from .canmatrix import *
import os.path

#Font Size : 8pt * 20 = 160
#font = 'font: name Arial Narrow, height 160'
font = 'font: name Verdana, height 160'

sty_header    = xlwt.easyxf(font + ', bold on; align: rota 90, vertical center, horizontal center','pattern: pattern solid, fore-colour rose')
sty_norm    = xlwt.easyxf(font + ', colour black')
sty_first_frame    = xlwt.easyxf(font + ', colour black; borders: top thin')
sty_white    = xlwt.easyxf(font + ', colour white')

# BUMatrix-Styles
sty_green = xlwt.easyxf('pattern: pattern solid, fore-colour light_green')
sty_green_first_frame = xlwt.easyxf('pattern: pattern solid, fore-colour light_green; borders: top thin')
sty_sender = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25')
sty_sender_first_frame = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25; borders: top thin')
sty_sender_green = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25, back-colour light_green')
sty_sender_green_first_frame = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25, back-colour light_green; borders: top thin')

def writeFrame(frame, worksheet, row, mystyle):
    #frame-id
    worksheet.write(row, 0, label = "%3Xh" % frame._Id, style=mystyle)
    #frame-Name
    worksheet.write(row, 1, label = frame._name, style=mystyle)

    #determin cycle-time
    if "GenMsgCycleTime" in frame._attributes:
        worksheet.write(row, 2, label = int(frame._attributes["GenMsgCycleTime"]) , style=mystyle)
    else:
        worksheet.write(row, 2, label = "", style=mystyle)

    #determin send-type
    if "GenMsgSendType" in frame._attributes:
        if frame._attributes["GenMsgSendType"] == "5":
            worksheet.write(row, 3, label = "Cyclic+Change" , style=mystyle)
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgDelayTime"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "0":
            worksheet.write(row, 3, label = "Cyclic" , style=mystyle)
            worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "2":
            worksheet.write(row, 3, label = "BAF" , style=mystyle)
            if "GenMsgNrOfRepetitions" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgNrOfRepetitions"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "8":
            worksheet.write(row, 3, label = "DualCycle" , style=mystyle)
            if "GenMsgCycleTimeActive" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgCycleTimeActive"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "10":
            worksheet.write(row, 3, label = "None" , style=mystyle)
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgDelayTime"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "9":
            worksheet.write(row, 3, label = "OnChange" , style=mystyle)
            if "GenMsgNrOfRepetitions" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgNrOfRepetitions"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        elif frame._attributes["GenMsgSendType"] == "1":
            worksheet.write(row, 3, label = "Spontaneous" , style=mystyle)
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4, label = int(frame._attributes["GenMsgDelayTime"]) , style=mystyle)
            else:
                worksheet.write(row, 4, label = "", style=mystyle)
        else:
            worksheet.write(row, 3, label = "", style=mystyle)
            worksheet.write(row, 4, label = "", style=mystyle)
    else:
        worksheet.write(row, 3, label = "", style=mystyle)
        worksheet.write(row, 4, label = "", style=mystyle)


def writeSignal(db, sig, worksheet, row, mystyle, rearCol, motorolaBitFormat):
    if motorolaBitFormat == "msb":
        startBit = sig.getMsbStartbit()
    elif motorolaBitFormat == "msbreverse":
        startBit = sig.getMsbReverseStartbit()
    else: # motorolaBitFormat == "lsb"
        startBit = sig.getLsbStartbit()

    #startbyte
    worksheet.write(row, 5, label = math.floor(startBit/8)+1, style=mystyle)
    #startbit
    worksheet.write(row, 6, label = (startBit)%8, style=mystyle)
    #signalname
    worksheet.write(row, 7, label = sig._name, style=mystyle)

    # eval comment:
    if sig._comment is None:
        comment = ""
    else:
        comment = sig._comment

    # eval multiplex-info
    if sig._multiplex == 'Multiplexor':
        comment = "Mode Signal: " + comment
    elif sig._multiplex is not None:
        comment = "Mode " + str(sig._multiplex) + ":" + comment

    #write comment and size of signal in sheet
    worksheet.write(row, 8, label = comment, style=mystyle)
    worksheet.write(row, 9, label = sig._signalsize, style=mystyle)

    #startvalue of signal available
    if "GenSigStartValue" in sig._attributes:
        if db._signalDefines["GenSigStartValue"]._definition == "STRING":
            worksheet.write(row, 10, label = sig._attributes["GenSigStartValue"], style=mystyle)
        elif db._signalDefines["GenSigStartValue"]._definition == "INT" or db._signalDefines["GenSigStartValue"]._definition == "HEX":
            worksheet.write(row, 10, label = "%Xh" % int(sig._attributes["GenSigStartValue"]), style=mystyle)
    else:
        worksheet.write(row, 10, label = " ", style=mystyle)


    #SNA-value of signal available
    if "GenSigSNA" in sig._attributes:
        sna = sig._attributes["GenSigSNA"][1:-1]
        worksheet.write(row, 11, label = sna, style=mystyle)
    #no SNA-value of signal available / just for correct style:
    else:
        worksheet.write(row, 11, label = " ", style=mystyle)

    # eval byteorder (little_endian: intel == True / motorola == 0)
    if sig._is_little_endian:
        worksheet.write(row, 12, label = "i", style=mystyle)
    else:
        worksheet.write(row, 12, label = "m", style=mystyle)

    # is a unit defined for signal?
    if sig._unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            worksheet.write(row, rearCol+2, label = "%g" % float(sig._factor) + "  " + sig._unit, style=mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol+2, label = sig._unit, style=mystyle)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            worksheet.write(row, rearCol+2, label = "%g" % float(sig._factor), style=mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol+2, label = "", style=mystyle)

def writeValue(label, value, worksheet, row, rearCol, mystyle):
    # write value and lable in sheet
    worksheet.write(row, rearCol, label = label, style=mystyle)
    worksheet.write(row, rearCol+1, label = value, style=mystyle)

def writeBuMatrix(buList, sig, frame, worksheet, row, col, firstframe):
    # first-frame - style with borders:
    if firstframe == sty_first_frame:
        norm = sty_first_frame
        sender = sty_sender_first_frame
        norm_green = sty_green_first_frame
        sender_green = sty_sender_green_first_frame
    # consecutive-frame - style without borders:
    else:
        norm = sty_norm
        sender = sty_sender
        norm_green = sty_green
        sender_green = sty_sender_green

    #iterate over boardunits:
    for bu in buList:
        #every second Boardunit with other style
        if col % 2 == 0:
            locStyle = norm
            locStyleSender = sender
        #every second Boardunit with other style
        else:
            locStyle = norm_green
            locStyleSender = sender_green

        # write "s" "r" "r/s" if signal is sent, recieved or send and recived by boardunit
        if bu in sig._receiver and bu in frame._Transmitter:
            worksheet.write(row, col, label = "r/s", style = locStyleSender)
        elif bu in sig._receiver:
            worksheet.write(row, col, label = "r", style = locStyle)
        elif bu in frame._Transmitter:
            worksheet.write(row, col, label = "s", style = locStyleSender)
        else:
            worksheet.write(row, col, label = "", style = locStyle)
        col += 1
    # loop over boardunits ends here
    return col

def exportXls(db, filename, **options):
    head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
    head_tail = ['Value',   'Name / Phys. Range', 'Function / Increment Unit']

    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    workbook = xlwt.Workbook(encoding = 'utf8')
    wsname = os.path.basename(filename).replace('.xls','')
    worksheet = workbook.add_sheet('K-Matrix ' + wsname[0:22])
    col = 0

    # write first row (header) cols before frameardunits:
    for head in head_top:
        worksheet.write(0, col, label = head, style=sty_header)
        worksheet.col(col).width = 1111
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db._BUs._list:
        worksheet.write(0, col, label = bu._name, style=sty_header)
        worksheet.col(col).width = 1111
        buList.append(bu._name)
        col += 1

    head_start = col

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        worksheet.write(0, col, label = head, style=sty_header)
        worksheet.col(col).width = 3333
        col += 1

    # set width of selected Cols
    worksheet.col(1).width = 5555
    worksheet.col(3).width = 3333
    worksheet.col(7).width = 5555
    worksheet.col(8).width = 7777
    worksheet.col(head_start).width = 1111
    worksheet.col(head_start+1).width = 5555


    frameHash = {}
    for frame in db._fl._list:
        frameHash[int(frame._Id)] = frame

    #set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frameHash.keys()):
        frame = frameHash[idx]
        framestyle = sty_first_frame

        #sort signals:
        sigHash ={}
        for sig in frame._signals:
            sigHash["%02d" % int(sig.getMsbReverseStartbit()) + sig._name] = sig

        #set style for first line with border
        sigstyle = sty_first_frame

        #iterate over signals
        for sig_idx in sorted(sigHash.keys()):
            sig = sigHash[sig_idx]

            # if not first Signal in Frame, set style
            if sigstyle != sty_first_frame:
                sigstyle = sty_norm

            # valuetable available?
            if sig._values.__len__() > 0:
                valstyle = sigstyle
                # iterate over values in valuetable
                for val in sorted(sig._values.keys()):
                    writeFrame(frame, worksheet, row, framestyle)
                    if framestyle != sty_first_frame:
                        worksheet.row(row).level = 1

                    col = head_top.__len__()
                    col = writeBuMatrix(buList, sig, frame, worksheet, row, col, framestyle)
                    # write Value
                    writeValue(val,sig._values[val], worksheet, row, col, valstyle)
                    writeSignal(db, sig, worksheet, row, sigstyle, col, motorolaBitFormat)

                    # no min/max here, because min/max has same col as values...
                    #next row
                    row +=1
                    # set style to normal - without border
                    sigstyle = sty_white
                    framestyle = sty_white
                    valstyle = sty_norm
                #loop over values ends here
            # no valuetable available
            else:
                writeFrame(frame, worksheet, row, framestyle)
                if framestyle != sty_first_frame:
                    worksheet.row(row).level = 1

                col = head_top.__len__()
                col = writeBuMatrix(buList, sig, frame, worksheet, row, col, framestyle)
                writeSignal(db, sig, worksheet, row, sigstyle, col, motorolaBitFormat)

                if float(sig._min) != 0 or float(sig._max) != 1.0:
                    worksheet.write(row, col+1, label = str("%g..%g" %(sig._min, sig._max)), style=sigstyle)
                else:
                    worksheet.write(row, col+1, label = "", style=sigstyle)

                # just for border
                worksheet.write(row, col, label = "", style=sigstyle)
                #next row
                row +=1
                # set style to normal - without border
                sigstyle = sty_white
                framestyle = sty_white
        # reset signal-Array
        signals = []
        #loop over signals ends here
    # loop over frames ends here


    # frozen headings instead of split panes
    worksheet.set_panes_frozen(True)
    # in general, freeze after last heading row
    worksheet.set_horz_split_pos(1)
    worksheet.set_remove_splits(True)
    # save file
    workbook.save(filename)
