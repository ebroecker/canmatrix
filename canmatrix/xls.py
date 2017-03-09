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
from __future__ import print_function

from builtins import *
import math
import sys
import os.path
import codecs
import xlwt
import logging
logger = logging.getLogger('root')

from .canmatrix import *
import xlrd


# Font Size : 8pt * 20 = 160
#font = 'font: name Arial Narrow, height 160'
font = 'font: name Verdana, height 160'

if xlwt is not None:
    sty_header = xlwt.easyxf(font + ', bold on; align: rota 90, vertical center, horizontal center',
                             'pattern: pattern solid, fore-colour rose')
    sty_norm = xlwt.easyxf(font + ', colour black')
    sty_first_frame = xlwt.easyxf(font + ', colour black; borders: top thin')
    sty_white = xlwt.easyxf(font + ', colour white')

    # BUMatrix-Styles
    sty_green = xlwt.easyxf('pattern: pattern solid, fore-colour light_green')
    sty_green_first_frame = xlwt.easyxf(
        'pattern: pattern solid, fore-colour light_green; borders: top thin')
    sty_sender = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25')
    sty_sender_first_frame = xlwt.easyxf(
        'pattern: pattern 0x04, fore-colour gray25; borders: top thin')
    sty_sender_green = xlwt.easyxf(
        'pattern: pattern 0x04, fore-colour gray25, back-colour light_green')
    sty_sender_green_first_frame = xlwt.easyxf(
        'pattern: pattern 0x04, fore-colour gray25, back-colour light_green; borders: top thin')


def writeFrame(frame, worksheet, row, mystyle):
    # frame-id
    worksheet.write(row, 0, label="%3Xh" % frame.id, style=mystyle)
    # frame-Name
    worksheet.write(row, 1, label=frame.name, style=mystyle)

    # determin cycle-time
    if "GenMsgCycleTime" in frame.attributes:
        worksheet.write(
            row,
            2,
            label=int(
                frame.attributes["GenMsgCycleTime"]),
            style=mystyle)
    else:
        worksheet.write(row, 2, label="", style=mystyle)

    # determin send-type
    if "GenMsgSendType" in frame.attributes:
        if frame.attributes["GenMsgSendType"] == "5":
            worksheet.write(row, 3, label="Cyclic+Change", style=mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgDelayTime"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "0":
            worksheet.write(row, 3, label="Cyclic", style=mystyle)
            worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "2":
            worksheet.write(row, 3, label="BAF", style=mystyle)
            if "GenMsgNrOfRepetitions" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgNrOfRepetitions"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "8":
            worksheet.write(row, 3, label="DualCycle", style=mystyle)
            if "GenMsgCycleTimeActive" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgCycleTimeActive"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "10":
            worksheet.write(row, 3, label="None", style=mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgDelayTime"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "9":
            worksheet.write(row, 3, label="OnChange", style=mystyle)
            if "GenMsgNrOfRepetitions" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgNrOfRepetitions"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        elif frame.attributes["GenMsgSendType"] == "1":
            worksheet.write(row, 3, label="Spontaneous", style=mystyle)
            if "GenMsgDelayTime" in frame.attributes:
                worksheet.write(
                    row,
                    4,
                    label=int(
                        frame.attributes["GenMsgDelayTime"]),
                    style=mystyle)
            else:
                worksheet.write(row, 4, label="", style=mystyle)
        else:
            worksheet.write(row, 3, label="", style=mystyle)
            worksheet.write(row, 4, label="", style=mystyle)
    else:
        worksheet.write(row, 3, label="", style=mystyle)
        worksheet.write(row, 4, label="", style=mystyle)


def writeSignal(db, sig, worksheet, row, mystyle, rearCol, motorolaBitFormat):
    if motorolaBitFormat == "msb":
        startBit = sig.getStartbit(bitNumbering=1)
    elif motorolaBitFormat == "msbreverse":
        startBit = sig.getStartbit()
    else:  # motorolaBitFormat == "lsb"
        startBit = sig.getStartbit(bitNumbering=1, startLittle=True)

    # startbyte
    worksheet.write(row, 5, label=math.floor(startBit / 8) + 1, style=mystyle)
    # startbit
    worksheet.write(row, 6, label=(startBit) % 8, style=mystyle)
    # signalname
    worksheet.write(row, 7, label=sig.name, style=mystyle)

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
    worksheet.write(row, 8, label=comment, style=mystyle)
    worksheet.write(row, 9, label=sig.signalsize, style=mystyle)

    # startvalue of signal available
    if "GenSigStartValue" in sig.attributes:
        if db.signalDefines["GenSigStartValue"].definition == "STRING":
            worksheet.write(row, 10, label=sig.attributes[
                            "GenSigStartValue"], style=mystyle)
        elif db.signalDefines["GenSigStartValue"].definition == "INT" or db.signalDefines["GenSigStartValue"].definition == "HEX":
            worksheet.write(row, 10, label="%Xh" %
                            int(sig.attributes["GenSigStartValue"]), style=mystyle)
        else:
            worksheet.write(row, 10, label=" ", style=mystyle)
    else:
        worksheet.write(row, 10, label=" ", style=mystyle)

    # SNA-value of signal available
    if "GenSigSNA" in sig.attributes:
        sna = sig.attributes["GenSigSNA"][1:-1]
        worksheet.write(row, 11, label=sna, style=mystyle)
    # no SNA-value of signal available / just for correct style:
    else:
        worksheet.write(row, 11, label=" ", style=mystyle)

    # eval byteorder (little_endian: intel == True / motorola == 0)
    if sig.is_little_endian:
        worksheet.write(row, 12, label="i", style=mystyle)
    else:
        worksheet.write(row, 12, label="m", style=mystyle)

    # is a unit defined for signal?
    if sig.unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            worksheet.write(
                row,
                rearCol +
                2,
                label="%g" %
                float(
                    sig.factor) +
                "  " +
                sig.unit,
                style=mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol + 2, label=sig.unit, style=mystyle)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            worksheet.write(
                row,
                rearCol +
                2,
                label="%g" %
                float(
                    sig.factor),
                style=mystyle)
        #factor == 1.0
        else:
            worksheet.write(row, rearCol + 2, label="", style=mystyle)


def writeValue(label, value, worksheet, row, rearCol, mystyle):
    # write value and lable in sheet
    worksheet.write(row, rearCol, label=label, style=mystyle)
    worksheet.write(row, rearCol + 1, label=value, style=mystyle)


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
            worksheet.write(row, col, label="r/s", style=locStyleSender)
        elif bu in sig.receiver:
            worksheet.write(row, col, label="r", style=locStyle)
        elif bu in frame.transmitter:
            worksheet.write(row, col, label="s", style=locStyleSender)
        else:
            worksheet.write(row, col, label="", style=locStyle)
        col += 1
    # loop over boardunits ends here
    return col


def dump(db, file, **options):
    head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.',
                'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
    head_tail = ['Value',   'Name / Phys. Range', 'Function / Increment Unit']

    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    workbook = xlwt.Workbook(encoding='utf8')
#    wsname = os.path.basename(filename).replace('.xls', '')
#    worksheet = workbook.add_sheet('K-Matrix ' + wsname[0:22])
    worksheet = workbook.add_sheet('K-Matrix ')
    col = 0

    # write first row (header) cols before frameardunits:
    for head in head_top:
        worksheet.write(0, col, label=head, style=sty_header)
        worksheet.col(col).width = 1111
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db.boardUnits:
        worksheet.write(0, col, label=bu.name, style=sty_header)
        worksheet.col(col).width = 1111
        buList.append(bu.name)
        col += 1

    head_start = col

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        worksheet.write(0, col, label=head, style=sty_header)
        worksheet.col(col).width = 3333
        col += 1

    # set width of selected Cols
    worksheet.col(1).width = 5555
    worksheet.col(3).width = 3333
    worksheet.col(7).width = 5555
    worksheet.col(8).width = 7777
    worksheet.col(head_start).width = 1111
    worksheet.col(head_start + 1).width = 5555

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
                    writeFrame(frame, worksheet, row, framestyle)
                    if framestyle != sty_first_frame:
                        worksheet.row(row).level = 1

                    col = head_top.__len__()
                    col = writeBuMatrix(
                        buList, sig, frame, worksheet, row, col, framestyle)
                    # write Value
                    writeValue(
                        val,
                        sig.values[val],
                        worksheet,
                        row,
                        col,
                        valstyle)
                    writeSignal(
                        db,
                        sig,
                        worksheet,
                        row,
                        sigstyle,
                        col,
                        motorolaBitFormat)

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
                writeFrame(frame, worksheet, row, framestyle)
                if framestyle != sty_first_frame:
                    worksheet.row(row).level = 1

                col = head_top.__len__()
                col = writeBuMatrix(
                    buList, sig, frame, worksheet, row, col, framestyle)
                writeSignal(
                    db,
                    sig,
                    worksheet,
                    row,
                    sigstyle,
                    col,
                    motorolaBitFormat)

                if float(sig.min) != 0 or float(sig.max) != 1.0:
                    worksheet.write(
                        row,
                        col +
                        1,
                        label=str(
                            "%g..%g" %
                            (sig.min,
                             sig.max)),
                        style=sigstyle)
                else:
                    worksheet.write(row, col + 1, label="", style=sigstyle)

                # just for border
                worksheet.write(row, col, label="", style=sigstyle)
                # next row
                row += 1
                # set style to normal - without border
                sigstyle = sty_white
                framestyle = sty_white
        # reset signal-Array
        signals = []
        # loop over signals ends here
    # loop over frames ends here

    # frozen headings instead of split panes
    worksheet.set_panes_frozen(True)
    # in general, freeze after last heading row
    worksheet.set_horz_split_pos(1)
    worksheet.set_remove_splits(True)
    # save file
    workbook.save(file)


def load(file, **options):
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    wb = xlrd.open_workbook(file_contents=file.read())
    sh = wb.sheet_by_index(0)
    db = CanMatrix()

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
    index = {}
    for i in range(sh.ncols):
        value = sh.cell(0, i).value
        if value == "ID":
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

    # BoardUnits:
    for x in range(index['BUstart'], index['BUend']):
        db._BUs.add(BoardUnit(sh.cell(0, x).value))

    # initialize:
    frameId = None
    signalName = ""
    newBo = None

    for rownum in range(1, sh.nrows):
        # ignore empty row
        if sh.cell(rownum, index['ID']).value.__len__() == 0:
            break
        # new frame detected
        if sh.cell(rownum, index['ID']).value != frameId:
            sender = []
            # new Frame
            frameId = sh.cell(rownum, index['ID']).value
            frameName = sh.cell(rownum, index['frameName']).value
            cycleTime = sh.cell(rownum, index['cycle']).value
            launchType = sh.cell(rownum, index['launchType']).value
            dlc = 8
            launchParam = sh.cell(rownum, index['launchParam']).value
            if type(launchParam).__name__ != "float":
                launchParam = 0.0
            launchParam = str(int(launchParam))

#            newBo = Frame(int(frameId[:-1], 16), frameName, dlc, None)
            newBo = Frame(frameName, Id=int(frameId[:-1], 16), dlc=dlc)
            db._fl.addFrame(newBo)

            # eval launctype
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

            # eval cycletime
            if type(cycleTime).__name__ != "float":
                cycleTime = 0.0
            newBo.addAttribute("GenMsgCycleTime", str(int(cycleTime)))

        # new signal detected
        if sh.cell(rownum, index['signalName']).value != signalName:
            # new Signal
            receiver = []
            startbyte = int(sh.cell(rownum, index['startbyte']).value)
            startbit = int(sh.cell(rownum, index['startbit']).value)
            signalName = sh.cell(rownum, index['signalName']).value
            signalComment = sh.cell(
                rownum, index['signalComment']).value.strip()
            signalLength = int(sh.cell(rownum, index['signalLength']).value)
            signalDefault = sh.cell(rownum, index['signalDefault']).value
            signalSNA = sh.cell(rownum, index['signalSNA']).value
            multiplex = None
            if signalComment.startswith('Mode Signal:'):
                multiplex = 'Multiplexor'
                signalComment = signalComment[12:]
            elif signalComment.startswith('Mode '):
                mux, signalComment = signalComment[4:].split(':', 1)
                multiplex = int(mux.strip())

            if "byteorder" in index:
                signalByteorder = sh.cell(rownum, index['byteorder']).value

                if 'i' in signalByteorder:
                    is_little_endian = True
                else:
                    is_little_endian = False
            else:
                is_little_endian = True  # Default Intel

            is_signed = False

            if signalName != "-":
                for x in range(index['BUstart'], index['BUend']):
                    if 's' in sh.cell(rownum, x).value:
                        newBo.addTransmitter(sh.cell(0, x).value.strip())
                    if 'r' in sh.cell(rownum, x).value:
                        receiver.append(sh.cell(0, x).value.strip())
#                if signalLength > 8:
                newSig = Signal(signalName,
                                startBit=(startbyte - 1) * 8 + startbit,
                                signalSize=signalLength,
                                is_little_endian=is_little_endian,
                                is_signed=is_signed,
                                receiver=receiver,
                                multiplex=multiplex)
#               else:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                if not is_little_endian:
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
                function = sh.cell(rownum, index['function']).value
        value = str(sh.cell(rownum, index['Value']).value)
        valueName = sh.cell(rownum, index['ValueName']).value

        if valueName == 0:
            valueName = "0"
        elif valueName == 1:
            valueName = "1"
        test = valueName
        #.encode('utf-8')

        factor = 0
        unit = ""

        factor = sh.cell(rownum, index['function']).value
        if type(factor).__name__ == "unicode" or type(
                factor).__name__ == "str":
            factor = factor.strip()
            if " " in factor and factor[0].isdigit():
                (factor, unit) = factor.strip().split(" ", 1)
                factor = factor.strip()
                unit = unit.strip()
                newSig.unit = unit
                try:
                    newSig.factor = float(factor)
                except:
                    logger.warn(
                        "Some error occurred while decoding scale: Signal: %s; \"%s\"" %
                        (signalName, sh.cell(
                            rownum, index['function']).value))
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

        elif valueName.__len__() > 0:
            if value.strip().__len__() > 0:
                value = int(float(value))
                newSig.addValues(value, valueName)
            maxi = pow(2, signalLength) - 1
            newSig.max = float(maxi)
        else:
            newSig.offset = 0

    for frame in db.frames:
        frame.updateReceiver()
        frame.calcDLC()

    return db
