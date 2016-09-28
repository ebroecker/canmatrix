#!/usr/bin/env python
# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the aframeve copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the aframeve copyright notice, this list of conditions and the
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
# this script exports xls-files from a canmatrix-object
# xls-files are the can-matrix-definitions displayed in Excel


from __future__ import division
from __future__ import absolute_import
from builtins import *
import math
import sys
from .canmatrix import *
import os.path
import xlsxwriter

# Font Size : 8pt * 20 = 160
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
    # frame-id
    worksheet.write(row, 0, "%3Xh" % frame.id, mystyle)
    # frame-Name
    worksheet.write(row, 1, frame.name, mystyle)

    # determin cycle-time
    if "GenMsgCycleTime" in frame.attributes:
        worksheet.write(
            row, 2, int(
                frame.attributes["GenMsgCycleTime"]), mystyle)
    else:
        worksheet.write(row, 2, "", mystyle)

    # determin send-type
    if "GenMsgSendType" in frame.attributes:
        if frame.attributes["GenMsgSendType"] == "5":
            worksheet.write(row, 3, "Cyclic+Change", mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgDelayTime"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "0":
            worksheet.write(row, 3, "Cyclic", mystyle)
            worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "2":
            worksheet.write(row, 3, "BAF", mystyle)
            if "GenMsgNrOfRepetitions" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgNrOfRepetitions"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "8":
            worksheet.write(row, 3, "DualCycle", mystyle)
            if "GenMsgCycleTimeActive" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgCycleTimeActive"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "10":
            worksheet.write(row, 3, "None", mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgDelayTime"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "9":
            worksheet.write(row, 3, "OnChange", mystyle)
            if "GenMsgNrOfRepetitions" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgNrOfRepetitions"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        elif frame.attributes["GenMsgSendType"] == "1":
            worksheet.write(row, 3, "Spontaneous", mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row, 4, int(
                        frame.attributes["GenMsgDelayTime"]), mystyle)
            else:
                worksheet.write(row, 4, "", mystyle)
        else:
            worksheet.write(row, 3, "", mystyle)
            worksheet.write(row, 4, "", mystyle)
    else:
        worksheet.write(row, 3, "", mystyle)
        worksheet.write(row, 4, "", mystyle)


def writeSignalx(db, sig, worksheet, row, rearCol, mystyle, motorolaBitFormat):
    if motorolaBitFormat == "msb":
        startBit = sig.getStartbit(bitNumbering=1)
    elif motorolaBitFormat == "msbreverse":
        startBit = sig.getStartbit()
    else:  # motorolaBitFormat == "lsb"
        startBit = sig.getStartbit(bitNumbering=1, startLittle=True)

    # startbyte
    worksheet.write(row, 5, math.floor(startBit / 8) + 1, mystyle)
    # startbit
    worksheet.write(row, 6, (startBit) % 8, mystyle)
    # signalname
    worksheet.write(row, 7, sig.name, mystyle)

    # eval comment:
    if sig.comment is None:
        comment = ""
    else:
        comment = sig.comment

    # eval multiplex-info
    if sig.multiplex == 'Multiplexor':
        comment = "Mode Signal: " + comment
    elif sig.multiplex is not None:
        comment = "Mode " + str(sig.multiplex) + ":" + comment

    # write comment and size of signal in sheet
    worksheet.write(row, 8, comment, mystyle)
    worksheet.write(row, 9, sig.signalsize, mystyle)

    # startvalue of signal available
    if "GenSigStartValue" in sig.attributes:
        if db.signalDefines["GenSigStartValue"].definition == "STRING":
            worksheet.write(row, 10, sig.attributes[
                            "GenSigStartValue"], mystyle)
        elif db.signalDefines["GenSigStartValue"].definition == "INT" or db.signalDefines["GenSigStartValue"].definition == "HEX":
            worksheet.write(row, 10, "%Xh" %
                            int(sig.attributes["GenSigStartValue"]), mystyle)
        else:
            worksheet.write(row, 10, " ", mystyle)
    else:
        worksheet.write(row, 10, " ", mystyle)

    # SNA-value of signal available
    if "GenSigSNA" in sig.attributes:
        sna = sig.attributes["GenSigSNA"][1:-1]
        worksheet.write(row, 11, sna, mystyle)
    # no SNA-value of signal available / just for correct style:
    else:
        worksheet.write(row, 11, " ", mystyle)

    # eval byteorder (intel == True / motorola == False)
    if sig.is_little_endian:
        worksheet.write(row, 12, "i", mystyle)
    else:
        worksheet.write(row, 12, "m", mystyle)

    # is a unit defined for signal?
    if sig.unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            worksheet.write(
                row,
                rearCol +
                2,
                "%g" %
                float(
                    sig.factor) +
                "  " +
                sig.unit,
                mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol + 2, sig.unit, mystyle)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            worksheet.write(
                row, rearCol + 2, "%g" %
                float(
                    sig.factor), mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol + 2, "", mystyle)


def writeValuex(label, value, worksheet, row, rearCol, mystyle):
    # write value and lable in sheet
    worksheet.write(row, rearCol, label, mystyle)
    worksheet.write(row, rearCol + 1, value, mystyle)


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

    # iterate over boardunits:
    for bu in buList:
        # every second Boardunit with other style
        if col % 2 == 0:
            locStyle = norm
            locStyleSender = sender
        # every second Boardunit with other style
        else:
            locStyle = norm_green
            locStyleSender = sender_green
        # write "s" "r" "r/s" if signal is sent, recieved or send and recived
        # by boardunit
        if bu in sig.receiver and bu in frame.transmitter:
            worksheet.write(row, col, "r/s", locStyleSender)
        elif bu in sig.receiver:
            worksheet.write(row, col, "r", locStyle)
        elif bu in frame.transmitter:
            worksheet.write(row, col, "s", locStyleSender)
        else:
            worksheet.write(row, col, "", locStyle)
        col += 1
    # loop over boardunits ends here
    return col


def dump(db, filename, **options):
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    head_top = [
        'ID',
        'Frame Name',
        'Cycle Time [ms]',
        'Launch Type',
        'Launch Parameter',
        'Signal Byte No.',
        'Signal Bit No.',
        'Signal Name',
        'Signal Function',
        'Signal Length [Bit]',
        'Signal Default',
        ' Signal Not Available',
        'Byteorder']
    head_tail = ['Value', 'Name / Phys. Range', 'Function / Increment Unit']

    workbook = xlsxwriter.Workbook(filename)
#    wsname = os.path.basename(filename).replace('.xlsx', '')
#    worksheet = workbook.add_worksheet('K-Matrix ' + wsname[0:22])
    worksheet = workbook.add_worksheet('K-Matrix ')
    col = 0
    global sty_header
    sty_header = workbook.add_format({'bold': True,
                                      'rotation': 90,
                                      'font_name': 'Verdana',
                                      'font_size': 8,
                                      'align': 'center',
                                      'valign': 'center'})
    global sty_first_frame
    sty_first_frame = workbook.add_format({'font_name': 'Verdana',
                                           'font_size': 8,
                                           'font_color': 'black', 'top': 1})
    global sty_white
    sty_white = workbook.add_format({'font_name': 'Verdana',
                                     'font_size': 8,
                                     'font_color': 'white'})
    global sty_norm
    sty_norm = workbook.add_format({'font_name': 'Verdana',
                                    'font_size': 8,
                                    'font_color': 'black'})

# BUMatrix-Styles
    global sty_green
    sty_green = workbook.add_format({'pattern': 1, 'fg_color': '#CCFFCC'})
    global sty_green_first_frame
    sty_green_first_frame = workbook.add_format(
        {'pattern': 1, 'fg_color': '#CCFFCC', 'top': 1})
    global sty_sender
    sty_sender = workbook.add_format({'pattern': 0x04, 'fg_color': '#C0C0C0'})
    global sty_sender_first_frame
    sty_sender_first_frame = workbook.add_format(
        {'pattern': 0x04, 'fg_color': '#C0C0C0', 'top': 1})
    global sty_sender_green
    sty_sender_green = workbook.add_format(
        {'pattern': 0x04, 'fg_color': '#C0C0C0', 'bg_color': '#CCFFCC'})
    global sty_sender_green_first_frame
    sty_sender_green_first_frame = workbook.add_format(
        {'pattern': 0x04, 'fg_color': '#C0C0C0', 'bg_color': '#CCFFCC', 'top': 1})

    # write first row (header) cols before frameardunits:
    for head in head_top:
        worksheet.write(0, col, head, sty_header)
        worksheet.set_column(col, col, 3.57)
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db.boardUnits:
        worksheet.write(0, col, bu.name, sty_header)
        worksheet.set_column(col, col, 3.57)
        buList.append(bu.name)
        col += 1

    head_start = col

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        worksheet.write(0, col, head, sty_header)
        worksheet.set_column(col, col, 6)
        col += 1

    # set width of selected Cols
    worksheet.set_column(0, 0, 3.57)
    worksheet.set_column(1, 1, 21)
    worksheet.set_column(3, 3, 12.29)
    worksheet.set_column(7, 7, 21)
    worksheet.set_column(8, 8, 30)
    worksheet.set_column(head_start + 1, head_start + 1, 21)
    worksheet.set_column(head_start + 2, head_start + 2, 12)

    frameHash = {}
    for frame in db.frames:
        frameHash[int(frame.id)] = frame

    # set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frameHash.keys()):
        frame = frameHash[idx]
        framestyle = sty_first_frame

        # sort signals:
        sigHash = {}
        for sig in frame.signals:
            sigHash["%02d" % int(sig.getStartbit()) + sig.name] = sig

        # set style for first line with border
        sigstyle = sty_first_frame

        # iterate over signals
        for sig_idx in sorted(sigHash.keys()):
            sig = sigHash[sig_idx]

            # if not first Signal in Frame, set style
            if sigstyle != sty_first_frame:
                sigstyle = sty_norm
            # valuetable available?
            if sig.values.__len__() > 0:
                valstyle = sigstyle
                # iterate over values in valuetable
                for val in sorted(sig.values.keys()):
                    writeFramex(frame, worksheet, row, framestyle)
                    if framestyle != sty_first_frame:
                        worksheet.set_row(row, None, None, {'level': 1})
                    col = head_top.__len__()
                    col = writeBuMatrixx(
                        buList, sig, frame, worksheet, row, col, framestyle)
                    # write Value
                    writeValuex(
                        val,
                        sig.values[val],
                        worksheet,
                        row,
                        col,
                        valstyle)
                    writeSignalx(db, sig, worksheet, row, col,
                                 sigstyle, motorolaBitFormat)

                    # no min/max here, because min/max has same col as values...
                    # next row
                    row += 1
                    # set style to normal - without border
                    sigstyle = sty_white
                    framestyle = sty_white
                    valstyle = sty_norm
                # loop over values ends here
            # no valuetable available
            else:
                writeFramex(frame, worksheet, row, framestyle)
                if framestyle != sty_first_frame:
                    worksheet.set_row(row, None, None, {'level': 1})
                col = head_top.__len__()
                col = writeBuMatrixx(
                    buList, sig, frame, worksheet, row, col, framestyle)
                writeSignalx(db, sig, worksheet, row, col,
                             sigstyle, motorolaBitFormat)

                if float(sig.min) != 0 or float(sig.max) != 1.0:
                    worksheet.write(row, col + 1, str("%g..%g" %
                                                      (sig.min, sig.max)), sigstyle)
                else:
                    worksheet.write(row, col + 1, "", sigstyle)

                # just for border
                worksheet.write(row, col, "", sigstyle)
                # next row
                row += 1
                # set style to normal - without border
                sigstyle = sty_white
                framestyle = sty_white
        # reset signal-Array
        signals = []
        # loop over signals ends here
    # loop over frames ends here

    worksheet.autofilter(0, 0, row, len(head_top) +
                         len(head_tail) + len(db.boardUnits))
    worksheet.freeze_panes(1, 0)
    # save file
    workbook.close()


import codecs
import zipfile
from xml.etree.ElementTree import iterparse


def readXlsx(file, **args):
    # from: Hooshmand zandi http://stackoverflow.com/a/16544219
    import zipfile
    from xml.etree.ElementTree import iterparse

    if "sheet" in args:
        sheet = args["sheet"]
    else:
        sheet = 1
    if "header" in args:
        isHeader = args["header"]
    else:
        isHeader = False

    rows = []
    row = {}
    header = {}
    z = zipfile.ZipFile(file)

    # Get shared strings
    strings = [el.text for e, el
               in iterparse(z.open('xl/sharedStrings.xml'))
               if el.tag.endswith('}t')
               ]
    value = ''

    # Open specified worksheet
    for e, el in iterparse(z.open('xl/worksheets/sheet%d.xml' % (sheet))):
        # get value or index to shared strings
        if el.tag.endswith('}v'):                                   # <v>84</v>
            value = el.text
        if el.tag.endswith(
                '}c'):                                   # <c r="A3" t="s"><v>84</v></c>
            # If value is a shared string, use value as an index

            if el.attrib.get('t') == 's':
                value = strings[int(value)]

            # split the row/col information so that the row leter(s) can be
            # separate
            letter = el.attrib['r']                                   # AZ22
            while letter[-1].isdigit():
                letter = letter[:-1]

            # if it is the first row, then create a header hash for the names
            # that COULD be used
            if rows == []:
                header[letter] = value.strip()
            else:
                if value != '':

                    # if there is a header row, use the first row's names as
                    # the row hash index
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


def load(filename, **options):
    from sys import modules

    # use xlrd excel reader if available, because its more robust
    try:
        import canmatrix.xls
        return canmatrix.xls.load(filename, **options)
    except:
        pass

    # else use this hack to read xlsx
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    sheet = readXlsx(filename, sheet=1, header=True)
    db = CanMatrix()
    letterIndex = []
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        letterIndex.append(a)
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        for b in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            letterIndex.append("%s%s" % (a, b))

    # Defines not imported...
#       db.addBUDefines("NWM-Stationsadresse",  'HEX 0 63')
#       db.addBUDefines("NWM-Knoten",  'ENUM  "nein","ja"')
    db.addFrameDefines("GenMsgCycleTime", 'INT 0 65535')
    db.addFrameDefines("GenMsgDelayTime", 'INT 0 65535')
    db.addFrameDefines("GenMsgCycleTimeActive", 'INT 0 65535')
    db.addFrameDefines("GenMsgNrOfRepetitions", 'INT 0 65535')
#       db.addFrameDefines("GenMsgStartValue",  'STRING')
    db.addFrameDefines(
        "GenMsgSendType",
        'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
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
                _BUstart = letterIndex.index(key) + 1
                break
    else:
        for key in sheet[0]:
            if sheet[0][key].strip() == 'Signal Not Available':
                _BUstart = letterIndex.index(key) + 1

    for key in sheet[0]:
        if sheet[0][key].strip() == 'Value':
            _BUend = letterIndex.index(key)

    # BoardUnits:
    for x in range(_BUstart, _BUend):
        db._BUs.add(BoardUnit(sheet[0][letterIndex[x]]))

    # initialize:
    frameId = None
    signalName = ""
    newBo = None

    for row in sheet[1]:
        # ignore empty row
        if not 'ID' in row:
            continue
        # new frame detected
        if row['ID'] != frameId:
            sender = []
            # new Frame
            frameId = row['ID']
            frameName = row['Frame Name']
            cycleTime = getIfPossible(row, "Cycle Time [ms]")
            launchType = getIfPossible(row, 'Launch Type')
            dlc = 8
            launchParam = getIfPossible(row, 'Launch Parameter')
            if type(launchParam).__name__ != "float":
                launchParam = 0.0
            launchParam = str(int(launchParam))

#            newBo = Frame(int(frameId[:-1], 16), frameName, dlc, None)
            newBo = Frame(frameName, Id=int(frameId[:-1], 16), dlc=dlc)

            db._fl.addFrame(newBo)

            # eval launchtype
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

        # new signal detected
        if row['Signal Name'] != signalName:
            # new Signal
            receiver = []
            startbyte = int(row["Signal Byte No."])
            startbit = int(row['Signal Bit No.'])
            signalName = row['Signal Name']
            signalComment = getIfPossible(row, 'Signal Function')
            signalLength = int(row['Signal Length [Bit]'])
            signalDefault = getIfPossible(row, 'Signal Default')
            signalSNA = getIfPossible(row, 'Signal Not Available')
            multiplex = None
            if signalComment is not None and signalComment.startswith(
                    'Mode Signal:'):
                multiplex = 'Multiplexor'
                signalComment = signalComment[12:]
            elif signalComment is not None and signalComment.startswith('Mode '):
                mux, signalComment = signalComment[4:].split(':', 1)
                multiplex = int(mux.strip())

            signalByteorder = getIfPossible(row, 'Byteorder')
            if signalByteorder is not None:
                if 'i' in signalByteorder:
                    is_little_endian = True
                else:
                    is_little_endian = False
            else:
                is_little_endian = True  # Default Intel

            is_signed = False

            if signalName != "-":
                for x in range(_BUstart, _BUend):
                    buName = sheet[0][letterIndex[x]].strip()
                    buSenderReceiver = getIfPossible(row, buName)
                    if buSenderReceiver is not None:
                        if 's' in buSenderReceiver:
                            newBo.addTransmitter(buName)
                        if 'r' in buSenderReceiver:
                            receiver.append(buName)
#                if signalLength > 8:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                newSig = Signal(signalName,
                                startBit=(startbyte - 1) * 8 + startbit,
                                signalSize=signalLength,
                                is_little_endian=is_little_endian,
                                is_signed=is_signed,
                                receiver=receiver,
                                multiplex=multiplex)

#                else:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                if is_little_endian == False:
                    # motorola
                    if motorolaBitFormat == "msb":
                        newSig.setStartbit(
                            (startbyte - 1) * 8 + startbit, bitNumbering=1)
                    elif motorolaBitFormat == "msbreverse":
                        newSig.setStartbit((startbyte - 1) * 8 + startbit)
                    else:  # motorolaBitFormat == "lsb"
                        newSig.setStartbit(
                            (startbyte - 1) * 8 + startbit,
                            bitNumbering=1,
                            startLittle=True)

                newBo.addSignal(newSig)
                newSig.addComment(signalComment)
                function = getIfPossible(row, 'Function / Increment Unit')
        value = getIfPossible(row, 'Value')
        valueName = getIfPossible(row, 'Name / Phys. Range')

        if valueName == 0 or valueName is None:
            valueName = "0"
        elif valueName == 1:
            valueName = "1"
        test = valueName
        #.encode('utf-8')

        factor = 0
        unit = ""

        factor = getIfPossible(row, 'Function / Increment Unit')
        if type(factor).__name__ == "unicode" or type(
                factor).__name__ == "str":
            factor = factor.strip()
            if " " in factor and factor[0].isdigit():
                (factor, unit) = factor.strip().split(" ", 1)
                factor = factor.strip()
                unit = unit.strip()
                newSig.unit = unit
                newSig.factor = float(factor)
            else:
                unit = factor.strip()
                newSig.unit = unit
                newSig.factor = 1

        if ".." in test:
            (mini, maxi) = test.strip().split("..", 2)
            unit = ""
            try:
                newSig.offset = float(mini)
                newSig.min = float(mini)
                newSig.max = float(maxi)
            except:
                newSig.offset = 0
                newSig.min = None
                newSig.max = None

        elif valueName.__len__() > 0:
            if value is not None and value.strip().__len__() > 0:
                value = int(float(value))
                newSig.addValues(value, valueName)
            maxi = pow(2, signalLength) - 1
            newSig.max = float(maxi)
        else:
            newSig.offset = 0
            newSig.min = None
            newSig.max = None

    # dlc-estimation / dlc is not in xls, thus calculate a minimum-dlc:
    for frame in db.frames:
        frame.updateReceiver()
        frame.calcDLC()

    return db
