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
import xlsxwriter
import sys
from .canmatrix import *
import os.path

#Font Size : 8pt * 20 = 160
#font = 'font: name Arial Narrow, height 160'
font = 'font: name Verdana, height 160'

sty_header = 0
sty_norm = 0
sty_first_frame = 0
sty_white = 0

sty_green = 0
sty_green_first_frame = 0
sty_sender = 0
sty_sender_first_frame = 0
sty_sender_green = 0
sty_sender_green_first_frame = 0

def writeFramex(frame, worksheet, row, mystyle):
    #frame-id
    worksheet.write(row, 0,  "%3Xh" % frame._Id, mystyle)
    #frame-Name
    worksheet.write(row, 1,  frame._name, mystyle)

    #determin cycle-time
    if "GenMsgCycleTime" in frame._attributes:
        worksheet.write(row, 2,  int(frame._attributes["GenMsgCycleTime"]), mystyle)
    else:
        worksheet.write(row, 2,  "", mystyle)

    #determin send-type
    if "GenMsgSendType" in frame._attributes:
        if frame._attributes["GenMsgSendType"] == "5":
            worksheet.write(row, 3,  "Cyclic+Change", mystyle )
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgDelayTime"]), mystyle )
            else:
                worksheet.write(row, 4,  "", mystyle)
        elif frame._attributes["GenMsgSendType"] == "0":
            worksheet.write(row, 3,  "Cyclic", mystyle )
            worksheet.write(row, 4,  "" , mystyle)
        elif frame._attributes["GenMsgSendType"] == "2":
            worksheet.write(row, 3,  "BAF", mystyle)
            if "GenMsgNrOfRepetitions" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgNrOfRepetitions"]) , mystyle)
            else:
                worksheet.write(row, 4,  "", mystyle)
        elif frame._attributes["GenMsgSendType"] == "8":
            worksheet.write(row, 3,  "DualCycle", mystyle )
            if "GenMsgCycleTimeActive" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgCycleTimeActive"]), mystyle )
            else:
                worksheet.write(row, 4,  "", mystyle)
        elif frame._attributes["GenMsgSendType"] == "10":
            worksheet.write(row, 3,  "None", mystyle)
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgDelayTime"]), mystyle)
            else:
                worksheet.write(row, 4,  "", mystyle)
        elif frame._attributes["GenMsgSendType"] == "9":
            worksheet.write(row, 3,  "OnChange" , mystyle)
            if "GenMsgNrOfRepetitions" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgNrOfRepetitions"]) , mystyle)
            else:
                worksheet.write(row, 4,  "", mystyle)
        elif frame._attributes["GenMsgSendType"] == "1":
            worksheet.write(row, 3,  "Spontaneous" , mystyle)
            if "GenMsgDelayTime" in frame._attributes:
                worksheet.write(row, 4,  int(frame._attributes["GenMsgDelayTime"]) , mystyle)
            else:
                worksheet.write(row, 4,  "", mystyle)
        else:
            worksheet.write(row, 3,  "", mystyle)
            worksheet.write(row, 4,  "", mystyle)
    else:
        worksheet.write(row, 3,  "", mystyle)
        worksheet.write(row, 4,  "", mystyle)


def writeSignalx(db, sig, worksheet, row, rearCol, mystyle, motorolaBitFormat):
    if motorolaBitFormat == "msb":
        startBit = sig.getMsbStartbit()
    elif motorolaBitFormat == "msbreverse":
        startBit = sig.getMsbReverseStartbit()
    else: # motorolaBitFormat == "lsb"
        startBit = sig.getLsbStartbit()

    #startbyte
    worksheet.write(row, 5,  math.floor(startBit/8)+1, mystyle)
    #startbit
    worksheet.write(row, 6,  (startBit)%8, mystyle)
    #signalname
    worksheet.write(row, 7,  sig._name, mystyle)

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
    worksheet.write(row, 8,  comment, mystyle)
    worksheet.write(row, 9,  sig._signalsize, mystyle)

    #startvalue of signal available
    if "GenSigStartValue" in sig._attributes:
        if db._signalDefines["GenSigStartValue"]._definition == "STRING":
            worksheet.write(row, 10,  sig._attributes["GenSigStartValue"], mystyle)
        elif db._signalDefines["GenSigStartValue"]._definition == "INT" or db._signalDefines["GenSigStartValue"]._definition == "HEX":
            worksheet.write(row, 10,  "%Xh" % int(sig._attributes["GenSigStartValue"]), mystyle)
    else:
        worksheet.write(row, 10,  " ", mystyle)


    #SNA-value of signal available
    if "GenSigSNA" in sig._attributes:
        sna = sig._attributes["GenSigSNA"][1:-1]
        worksheet.write(row, 11,  sna, mystyle)
    #no SNA-value of signal available / just for correct style:
    else:
        worksheet.write(row, 11,  " ", mystyle)

    # eval byteorder (intel == True / motorola == False)
    if sig._is_little_endian:
        worksheet.write(row, 12,  "i", mystyle)
    else:
        worksheet.write(row, 12,  "m", mystyle)

    # is a unit defined for signal?
    if sig._unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            worksheet.write(row, rearCol+2, "%g" % float(sig._factor) + "  " + sig._unit, mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol+2, sig._unit, mystyle)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            worksheet.write(row, rearCol+2,  "%g" % float(sig._factor), mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol+2,  "", mystyle)

def writeValuex(label, value, worksheet, row, rearCol, mystyle):
    # write value and lable in sheet
    worksheet.write(row, rearCol, label, mystyle)
    worksheet.write(row, rearCol+1,  value, mystyle)

def writeBuMatrixx(buList, sig, frame, worksheet, row, col, firstframe):
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
            worksheet.write(row, col, "r/s",  locStyleSender)
        elif bu in sig._receiver:
            worksheet.write(row, col, "r", locStyle)
        elif bu in frame._Transmitter:
            worksheet.write(row, col, "s", locStyleSender)
        else:
            worksheet.write(row, col, "", locStyle)
        col += 1
    # loop over boardunits ends here
    return col

def exportXlsx(db, filename, **options):
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
    head_tail = ['Value',   'Name / Phys. Range', 'Function / Increment Unit']

    workbook = xlsxwriter.Workbook(filename)
    wsname = os.path.basename(filename).replace('.xlsx','')
    worksheet = workbook.add_worksheet('K-Matrix ' + wsname[0:22])
    col = 0
    global sty_header
    sty_header = workbook.add_format({'bold': True, 'rotation': 90, 'font_name' : 'Verdana', 'font_size' : 8, 'align' : 'center', 'valign' : 'center'})
    global sty_first_frame
    sty_first_frame = workbook.add_format({'font_name' : 'Verdana', 'font_size' : 8,
'font_color' : 'black', 'top' : 1})
    global sty_white
    sty_white = workbook.add_format({'font_name' : 'Verdana', 'font_size' : 8,
'font_color' : 'white'})
    global sty_norm
    sty_norm = workbook.add_format({'font_name' : 'Verdana', 'font_size' : 8,
'font_color' : 'black'})

# BUMatrix-Styles
    global sty_green
    sty_green = workbook.add_format({'pattern': 1, 'fg_color': '#CCFFCC' })
    global sty_green_first_frame
    sty_green_first_frame = workbook.add_format({'pattern': 1, 'fg_color': '#CCFFCC', 'top':1 })
    global sty_sender
    sty_sender = workbook.add_format({'pattern': 0x04, 'fg_color': '#C0C0C0'})
    global sty_sender_first_frame
    sty_sender_first_frame = workbook.add_format({'pattern': 0x04, 'fg_color': '#C0C0C0', 'top' : 1})
    global sty_sender_green
    sty_sender_green = workbook.add_format({'pattern': 0x04, 'fg_color': '#C0C0C0', 'bg_color': '#CCFFCC'})
    global sty_sender_green_first_frame
    sty_sender_green_first_frame = workbook.add_format({'pattern': 0x04, 'fg_color': '#C0C0C0', 'bg_color': '#CCFFCC','top': 1})


    # write first row (header) cols before frameardunits:
    for head in head_top:
        worksheet.write(0, col, head, sty_header)
        worksheet.set_column(col, col, 3.57)
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db._BUs._list:
        worksheet.write(0, col, bu._name, sty_header)
        worksheet.set_column(col, col, 3.57)
        buList.append(bu._name)
        col += 1

    head_start = col

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        worksheet.write(0, col,  head, sty_header)
        worksheet.set_column(col, col, 6)
        col += 1

    # set width of selected Cols
    worksheet.set_column(0,0, 3.57)
    worksheet.set_column(1,1, 21)
    worksheet.set_column(3,3, 12.29)
    worksheet.set_column(7,7, 21)
    worksheet.set_column(8,8, 30)
    worksheet.set_column(head_start+1,head_start+1, 21)
    worksheet.set_column(head_start+2,head_start+2, 12)

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
                    writeFramex(frame, worksheet, row, framestyle)
                    if framestyle != sty_first_frame:
                        worksheet.set_row(row, None, None, {'level': 1})
                    col = head_top.__len__()
                    col = writeBuMatrixx(buList, sig, frame, worksheet, row, col, framestyle)
                    # write Value
                    writeValuex(val,sig._values[val], worksheet, row, col, valstyle)
                    writeSignalx(db, sig, worksheet, row, col, sigstyle, motorolaBitFormat)

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
                writeFramex(frame, worksheet, row, framestyle)
                if framestyle != sty_first_frame:
                    worksheet.set_row(row, None, None, {'level': 1})
                col = head_top.__len__()
                col = writeBuMatrixx(buList, sig, frame, worksheet, row, col, framestyle)
                writeSignalx(db, sig, worksheet, row, col, sigstyle, motorolaBitFormat)

                if float(sig._min) != 0 or float(sig._max) != 1.0:
                    worksheet.write(row, col+1, str("%g..%g" %(sig._min, sig._max)), sigstyle)
                else:
                    worksheet.write(row, col+1,  "", sigstyle)

                # just for border
                worksheet.write(row, col,  "", sigstyle)
                #next row
                row +=1
                # set style to normal - without border
                sigstyle = sty_white
                framestyle = sty_white
        # reset signal-Array
        signals = []
        #loop over signals ends here
    # loop over frames ends here

    worksheet.autofilter(0,0,row,len(head_top)+len(head_tail)+len(db._BUs._list))
    worksheet.freeze_panes(1,0)
    # save file
    workbook.close()
