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
import canmatrix
import xlsxwriter
import canmatrix.xls_common

logger = canmatrix.logging.getLogger(__name__)

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


def writeBuMatrixx(ecu_list, signal, frame, worksheet, row, col, firstframe):
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
    for ecu in ecu_list:
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
        if signal is not None and ecu in signal.receivers and ecu in frame.transmitters:
            worksheet.write(row, col, "r/s", locStyleSender)
        elif signal is not None and ecu in signal.receivers:
            worksheet.write(row, col, "r", locStyle)
        elif ecu in frame.transmitters:
            worksheet.write(row, col, "s", locStyleSender)
        else:
            worksheet.write(row, col, "", locStyle)
        col += 1
    # loop over boardunits ends here
    return col



def writeExcelLine(worksheet, row, col, rowArray, style):
    for item in rowArray:
        worksheet.write(row, col, item, style)
        col += 1
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
        'Signal Not Available',
        'Byteorder']
    head_tail = ['Value', 'Name / Phys. Range', 'Function / Increment Unit']

    if "additionalAttributes" in options and len(options["additionalAttributes"]) > 0:
        additional_signal_colums = options["additionalAttributes"].split(",")
    else:
        additional_signal_colums = []#["attributes['DisplayDecimalPlaces']"]

    if "additionalFrameAttributes" in options and len(options["additionalFrameAttributes"]) > 0:
        additional_frame_colums = options["additionalFrameAttributes"].split(",")
    else:
        additional_frame_colums = []#["attributes['DisplayDecimalPlaces']"]


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

    rowArray = head_top
    head_start = len(rowArray)

    # write frameardunits in first row:
    ecu_list = []
    for ecu in db.ecus:
        ecu_list.append(ecu.name)

    rowArray += ecu_list

    for col in range(0,len(rowArray)):
        worksheet.set_column(col, col, 2)

    rowArray += head_tail

    additionalFrame_start = len(rowArray)

    # set width of selected Cols
    worksheet.set_column(0, 0, 3.57)
    worksheet.set_column(1, 1, 21)
    worksheet.set_column(3, 3, 12.29)
    worksheet.set_column(7, 7, 21)
    worksheet.set_column(8, 8, 30)

    for additionalCol in additional_frame_colums:
        rowArray.append("frame." + additionalCol)

    for additionalCol in additional_signal_colums:
        rowArray.append("signal." + additionalCol)

    writeExcelLine(worksheet,0,0,rowArray,sty_header)

    frameHash = {}
    logger.debug("DEBUG: Length of db.frames is %d" % len(db.frames))
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
            continue
        frameHash[int(frame.arbitration_id.id)] = frame

    # set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frameHash.keys()):

        frame = frameHash[idx]
        framestyle = sty_first_frame

        # sort signals:
        sigHash = {}
        for sig in frame.signals:
            sigHash["%02d" % int(sig.get_startbit()) + sig.name] = sig

        # set style for first line with border
        sigstyle = sty_first_frame

        additionalFrameInfo = []
        for frameInfo in additional_frame_colums:
            temp = frame.attribute(frameInfo, default="")
            additionalFrameInfo.append(temp)

        # iterate over signals
        rowArray = []
        if len(sigHash) == 0:
            rowArray += canmatrix.xls_common.get_frame_info(db, frame)
            for item in range(5, head_start):
                rowArray.append("")
            tempCol = writeExcelLine(worksheet, row, 0, rowArray, framestyle)
            tempCol = writeBuMatrixx(ecu_list, None, frame, worksheet, row, tempCol , framestyle)

            rowArray = []
            for col in range(tempCol, additionalFrame_start):
                rowArray.append("")
            rowArray += additionalFrameInfo
            for i in additional_signal_colums:
                rowArray.append("")
            writeExcelLine(worksheet, row, tempCol, rowArray, framestyle)
            row += 1
            continue

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
                    rowArray = canmatrix.xls_common.get_frame_info(db, frame)
                    frontcol = writeExcelLine(worksheet, row, 0, rowArray, framestyle)
                    if framestyle != sty_first_frame:
                        worksheet.set_row(row, None, None, {'level': 1})

                    col = head_start
                    col = writeBuMatrixx(ecu_list, sig, frame, worksheet, row, col, framestyle)

                    # write Value
                    (frontRow, backRow) = canmatrix.xls_common.get_signal(db, sig, motorolaBitFormat)
                    writeExcelLine(worksheet, row, frontcol, frontRow, sigstyle)
                    backRow += additionalFrameInfo
                    for item in additional_signal_colums:
                        temp = getattr(sig, item, "")
                        backRow.append(temp)

                    writeExcelLine(worksheet, row, col + 2, backRow, sigstyle)
                    writeExcelLine(worksheet, row, col, [val, sig.values[val]], valstyle)

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
                rowArray = canmatrix.xls_common.get_frame_info(db, frame)
                frontcol = writeExcelLine(worksheet, row, 0, rowArray, framestyle)
                if framestyle != sty_first_frame:
                    worksheet.set_row(row, None, None, {'level': 1})

                col = head_start
                col = writeBuMatrixx(
                    ecu_list, sig, frame, worksheet, row, col, framestyle)
                (frontRow,backRow)  = canmatrix.xls_common.get_signal(db, sig, motorolaBitFormat)
                writeExcelLine(worksheet, row, frontcol, frontRow, sigstyle)

                if float(sig.min) != 0 or float(sig.max) != 1.0:
                    backRow.insert(0,str("%g..%g" %(sig.min,sig.max)))
                else:
                    backRow.insert(0, "")
                backRow.insert(0,"")

                for item in additional_signal_colums:
                    temp = getattr(sig, item, "")
#s                backRow.append("")
                backRow += additionalFrameInfo
                for item in additional_signal_colums:
                    temp = getattr(sig, item, "")
                    backRow.append(temp)

                writeExcelLine(worksheet, row, col, backRow, sigstyle)

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
                         len(head_tail) + len(db.ecus))
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
    if 'xlsxLegacy' in options and options['xlsxLegacy'] == True:
        logger.error("xlsx: using legacy xlsx-reader - please get xlrd working for better results!")
    else:
        import canmatrix.xls
        return canmatrix.xls.load(filename, **options)

    # else use this hack to read xlsx
    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

    sheet = readXlsx(filename, sheet=1, header=True)
    db = canmatrix.CanMatrix()
    letterIndex = []
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        letterIndex.append(a)
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        for b in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            letterIndex.append("%s%s" % (a, b))

    # Defines not imported...
    db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
    db.add_frame_defines("GenMsgDelayTime", 'INT 0 65535')
    db.add_frame_defines("GenMsgCycleTimeActive", 'INT 0 65535')
    db.add_frame_defines("GenMsgNrOfRepetitions", 'INT 0 65535')
    launchTypes = []

    db.add_signal_defines("GenSigSNA", 'STRING')

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
        db.add_ecu(canmatrix.Ecu(sheet[0][letterIndex[x]]))

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

            if frameId.endswith("xh"):
                newBo = canmatrix.Frame(frameName, id=int(frameId[:-2], 16), size=dlc, extended=True)
            else:
                newBo = canmatrix.Frame(frameName, id=int(frameId[:-1], 16), size=dlc)

            db.add_frame(newBo)

            # eval launchtype
            if launchType is not None:
                newBo.add_attribute("GenMsgSendType", launchType)
                if launchType not in launchTypes:
                    launchTypes.append(launchType)

#                       #eval cycletime
            if type(cycleTime).__name__ != "float":
                cycleTime = 0.0
            newBo.add_attribute("GenMsgCycleTime", str(int(cycleTime)))

        # new signal detected
        if 'Signal Name' in row and row['Signal Name'] != signalName:
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
                            newBo.add_transmitter(buName)
                        if 'r' in buSenderReceiver:
                            receiver.append(buName)
#                if signalLength > 8:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                newSig = canmatrix.Signal(signalName,
                                startBit=(startbyte - 1) * 8 + startbit,
                                size=signalLength,
                                is_little_endian=is_little_endian,
                                is_signed=is_signed,
                                receiver=receiver,
                                multiplex=multiplex)

#                else:
#                    newSig = Signal(signalName, (startbyte-1)*8+startbit, signalLength, is_little_endian, is_signed, 1, 0, 0, 1, "", receiver, multiplex)
                if is_little_endian == False:
                    # motorola
                    if motorolaBitFormat == "msb":
                        newSig.set_startbit(
                            (startbyte - 1) * 8 + startbit, bitNumbering=1)
                    elif motorolaBitFormat == "msbreverse":
                        newSig.set_startbit((startbyte - 1) * 8 + startbit)
                    else:  # motorolaBitFormat == "lsb"
                        newSig.set_startbit(
                            (startbyte - 1) * 8 + startbit,
                            bitNumbering=1,
                            startLittle=True)

                newBo.add_signal(newSig)
                newSig.add_comment(signalComment)
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
                newSig.add_values(value, valueName)
            maxi = pow(2, signalLength) - 1
            newSig.max = float(maxi)
        else:
            newSig.offset = 0
            newSig.min = None
            newSig.max = None

    # dlc-estimation / dlc is not in xls, thus calculate a minimum-dlc:
    for frame in db.frames:
        frame.update_receiver()
        frame.calc_dlc()

    launchTypeEnum = "ENUM"
    for launchType in launchTypes:
        if len(launchType) > 0:
            launchTypeEnum += ' "' + launchType + '",'
    db.add_frame_defines("GenMsgSendType", launchTypeEnum[:-1])

    db.set_fd_type()
    return db
