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
from __future__ import absolute_import

from collections import defaultdict
import sys
import csv
import logging
from canmatrix.xls_common import *

logger = logging.getLogger('root')

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

    def __add__(self, other):
        if len(self._rowdict.keys()) > 0:
            start = max(self._rowdict.keys()) +1
        else:
            start = 0
        i = 0
        for item in other:
            self[start+i] = item
            i += 1
        return self

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
    head_tail = ['Name / Phys. Range', 'Function / Increment Unit','Value']

    if "additionalAttributes" in options and len(options["additionalAttributes"]) > 0:
        additionalSignalCollums = options["additionalAttributes"].split(",")
    else:
        additionalSignalCollums = []#["attributes['DisplayDecimalPlaces']"]

    if "additionalFrameAttributes" in options and len(options["additionalFrameAttributes"]) > 0:
        additionalFrameCollums = options["additionalFrameAttributes"].split(",")
    else:
        additionalFrameCollums = []#["attributes['DisplayDecimalPlaces']"]

    if 'xlsMotorolaBitFormat' in options:
        motorolaBitFormat = options["xlsMotorolaBitFormat"]
    else:
        motorolaBitFormat = "msbreverse"

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

    for additionalCol in additionalFrameCollums:
        headerrow.write(col,"frame." + additionalCol)
        col += 1

    for additionalCol in additionalSignalCollums:
        headerrow.write(col,"signal." + additionalCol)
        col += 1

    csvtable.append(headerrow)
    # -- headers end...

    frameHash = {}
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
            continue
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

        additionalFrameInfo = []
        for frameInfo in additionalFrameCollums:
            try:
                temp = eval("frame." + frameInfo)
            except:
                temp = ""
            additionalFrameInfo.append(temp)


        # iterate over signals
        for sig_idx in sorted(sigHash.keys()):
            sig = sigHash[sig_idx]

            # value table available?
            if sig.values.__len__() > 0:
                # iterate over values in valuetable
                for val in sorted(sig.values.keys()):
                    signalRow = csvRow()
                    signalRow += getFrameInfo(db,frame)

                    (front, back) = getSignal(db,sig,motorolaBitFormat)
                    signalRow += front
                    signalRow += ("s" if sig.is_signed else "u")

                    col = head_top.__len__()
                    col = writeBuMatrixx(buList, sig, frame, signalRow, col)
                    signalRow += back
                    # write Value
                    signalRow += [val, sig.values[val]]

                    signalRow += additionalFrameInfo
                    for item in additionalSignalCollums:
                        try:
                            temp = eval("sig." + item)
                        except:
                            temp = ""
                        signalRow += [temp]

                    # next row
                    row += 1
                    csvtable.append(signalRow)
                # loop over values ends here
            # no value table available
            else:
                signalRow = csvRow()
                signalRow += getFrameInfo(db, frame)

                (front, back) = getSignal(db, sig, motorolaBitFormat)
                signalRow += front
                signalRow += ("s" if sig.is_signed else "u")

                col = head_top.__len__()
                col = writeBuMatrixx(buList, sig, frame, signalRow, col)
                signalRow += back

                if sig.min is not None or sig.max is not None:
                    signalRow += [str("{}..{}".format(sig.min, sig.max))]
                else:
                    signalRow += [""]

                signalRow += additionalFrameInfo
                for item in additionalSignalCollums:
                    try:
                        temp = eval("sig." + item)
                    except:
                        temp = ""
                    signalRow += [temp]

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
