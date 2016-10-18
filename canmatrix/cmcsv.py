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
# this script exports canmatrix-objects to a CSV file. (Based on exportxlsx)
# Author: Martin Hoffmann (m8ddin@gmail.com)

from collections import defaultdict
import sys
import csv

if (sys.version_info > (3, 0)):
    import codecs


extension = 'csv'


class csvRow:

    def __init__(self):
        self._rowdict = defaultdict(str)

    def __getitem__(self, key):
        return self._rowdict[key]

    def __setitem__(self, key, item):
        if (sys.version_info <= (3, 0)):
            if type(item).__name__ == "unicode":
                item = item.encode('utf-8')
        self._rowdict[key] = item

    def write(self, column, value):
        self._rowdict[column] = value

    @property
    def as_list(self):
        # Generate list of single cells in the row till highest index (dictionary key)
        # Empty cells (non-existent keys) are generated as empty string
        return [str(self._rowdict[x])
                for x in range(0, max(self._rowdict) + 1)]

    def toCSV(self, delimiter=','):
        text = delimiter.join(self.as_list)
        return text.replace('\n', ' ')

    def __str__(self):
        return self.toCSV()


def writeFramex(frame, row):
    # frame-id
    row[0] = "%3Xh" % frame.id
    # frame-Name
    row[1] = frame.name

    # determine cycle-time
    if "GenMsgCycleTime" in frame.attributes:
        row[2] = int(frame.attributes["GenMsgCycleTime"])

    # determine send-type
    if "GenMsgSendType" in frame.attributes:
        if frame.attributes["GenMsgSendType"] == "5":
            row[3] = "Cyclic+Change"
            if "GenMsgDelayTime" in frame.attributes:
                row[4] = int(frame.attributes["GenMsgDelayTime"])
        elif frame.attributes["GenMsgSendType"] == "0":
            row[3] = "Cyclic"
        elif frame.attributes["GenMsgSendType"] == "2":
            row[3] = "BAF"
            if "GenMsgNrOfRepetitions" in frame.attributes:
                row[4] = int(frame.attributes["GenMsgNrOfRepetitions"])
        elif frame.attributes["GenMsgSendType"] == "8":
            row[3] = "DualCycle"
            if "GenMsgCycleTimeActive" in frame.attributes:
                row[4] = int(frame.attributes["GenMsgCycleTimeActive"])
        elif frame.attributes["GenMsgSendType"] == "10":
            row[3] = "None"
            if "GenMsgDelayTime" in frame.attributes:
                row[3] = int(frame.attributes["GenMsgDelayTime"])
        elif frame.attributes["GenMsgSendType"] == "9":
            row[3] = "OnChange"
            if "GenMsgNrOfRepetitions" in frame.attributes:
                row[4] = int(frame.attributes["GenMsgNrOfRepetitions"])
        elif frame.attributes["GenMsgSendType"] == "1":
            row[3] = "Spontaneous"
            if "GenMsgDelayTime" in frame.attributes:
                row[4] = int(frame.attributes["GenMsgDelayTime"])
        else:
            pass


def writeBuMatrixx(buList, sig, frame, row, col):
    # iterate over boardunits:
    for bu in buList:
        # write "s" "r" "r/s" if signal is sent, received or send and received
        # by boardunit
        if bu in sig.receiver and bu in frame.transmitter:
            row[col] = "r/s"
        elif bu in sig.receiver:
            row[col] = "r"
        elif bu in frame.transmitter:
            row[col] = "s"
        else:
            pass
        col += 1
    return col


def writeValuex(label, value, row, rearCol):
    row[rearCol] = value
    row[rearCol + 1] = label


def writeSignalx(db, sig, row, rearCol):
    # startbyte
    row[5] = int((sig.getStartbit()) / 8 + 1)
    # startbit
    row[6] = (sig.getStartbit()) % 8
    # signalname
    row[7] = sig.name

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
    row[8] = comment
    row[9] = sig.signalsize

    # startvalue of signal available
    if "GenSigStartValue" in sig.attributes:
        if db.signalDefines["GenSigStartValue"].definition == "STRING":
            row[10] = sig.attributes["GenSigStartValue"]
        elif db.signalDefines["GenSigStartValue"].definition == "INT" or db.signalDefines["GenSigStartValue"].definition == "HEX":
            row[10] = "%Xh" % int(sig.attributes["GenSigStartValue"])

    # SNA-value of signal available
    if "GenSigSNA" in sig.attributes:
        row[11] = sig.attributes["GenSigSNA"][1:-1]

    # eval byteorder (intel == 1 / motorola == 0)
    if sig.is_little_endian == True:
        row[12] = "i"
    else:
        row[12] = "m"

    # signed / unsigned
    if sig.is_signed == True:
        row[13] = "s"
    else:
        row[13] = "u"

    # is a unit defined for signal?
    if sig.unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            row[rearCol + 2] = "%g" % float(sig.factor) + "  " + sig.unit
        #factor == 1.0
        else:
            row[rearCol + 2] = sig.unit
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            row[rearCol + 2] = float(sig.factor)


def dump(db, thefile, delimiter=',', **options):
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
        'Byteorder',
        'is signed']
    head_tail = ['Value', 'Name / Phys. Range', 'Function / Increment Unit']

    csvtable = list()  # List holding all csv rows

    col = 0  # Column counter

    # -- headers start:
    headerrow = csvRow()

    # write first row (header) cols before frameardunits:
    for head in head_top:
        headerrow.write(col, head)
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db.boardUnits:
        headerrow.write(col, bu.name)
        buList.append(bu.name)
        col += 1

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        headerrow.write(col, head)
        col += 1

    csvtable.append(headerrow)
    # -- headers end...

    frameHash = {}
    for frame in db.frames:
        frameHash[int(frame.id)] = frame

    # set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frameHash.keys()):
        frame = frameHash[idx]

        # sort signals:
        sigHash = {}
        for sig in frame.signals:
            sigHash["%02d" % int(sig.getStartbit()) + sig.name] = sig

        # iterate over signals
        for sig_idx in sorted(sigHash.keys()):
            sig = sigHash[sig_idx]

            # value table available?
            if sig.values.__len__() > 0:
                # iterate over values in valuetable
                for val in sorted(sig.values.keys()):
                    signalRow = csvRow()
                    writeFramex(frame, signalRow)
                    col = head_top.__len__()
                    col = writeBuMatrixx(buList, sig, frame, signalRow, col)
                    # write Value
                    writeValuex(val, sig.values[val], signalRow, col)
                    writeSignalx(db, sig, signalRow, col)

                    # no min/max here, because min/max has same col as values.
                    # next row
                    row += 1
                    csvtable.append(signalRow)
                # loop over values ends here
            # no value table available
            else:
                signalRow = csvRow()
                writeFramex(frame, signalRow)
                col = head_top.__len__()
                col = writeBuMatrixx(buList, sig, frame, signalRow, col)
                writeSignalx(db, sig, signalRow, col)

                if sig.min is not None or sig.max is not None:
                    signalRow[col + 1] = str("{}..{}".format(sig.min, sig.max))

                # next row
                row += 1
                csvtable.append(signalRow)
                # set style to normal - without border
        # loop over signals ends here
    # loop over frames ends here

    if (sys.version_info > (3, 0)):
        import io
        temp = io.TextIOWrapper(thefile, encoding='UTF-8')
    else:
        temp = thefile

    writer = csv.writer(temp, delimiter=delimiter)
    for row in csvtable:
        writer.writerow(row.as_list)
#    else:
#        # just print to stdout
#        finalTableString = "\n".join(
#            [row.toCSV(delimiter) for row in csvtable])
#        print(finalTableString)
