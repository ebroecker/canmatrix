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

if (sys.version_info > (3, 0)):
    import codecs

class csvRow:
    
    def __init__(self):
        self._linedict = defaultdict(str)
        
    def __getitem__(self, key):
        return self._linedict[key]



    def __setitem__(self, key, item):
        if (sys.version_info <= (3, 0)):
            if type(item).__name__ == "unicode": 
                item = item.encode('utf-8')
        self._linedict[key] = item
        
    def write(self, column, value):
        self._linedict[column] = value

    def toCSV(self, delimiter=','):
        text = delimiter.join([str(self._linedict[x]) for x in range(0, max(self._linedict) + 1)])
        return text.replace('\n', ' ') # TODO newline replacement OK?
        
    def __str__(self):
        return self.toCSV()


def writeFramex(frame, row):
    #frame-id
    row[0] =  "%3Xh" % frame._Id
    #frame-Name
    row[1] = frame._name
    
    #determine cycle-time
    if "GenMsgCycleTime" in frame._attributes:
        row[2]  = int(frame._attributes["GenMsgCycleTime"])
        
    #determine send-type
    if "GenMsgSendType" in frame._attributes:
        if frame._attributes["GenMsgSendType"] == "5":
            row[3] = "Cyclic+Change"
            if "GenMsgDelayTime" in frame._attributes:
                row[4] = int(frame._attributes["GenMsgDelayTime"])
        elif frame._attributes["GenMsgSendType"] == "0":
            row[3] = "Cyclic"
        elif frame._attributes["GenMsgSendType"] == "2":
            row[3] = "BAF"
            if "GenMsgNrOfRepetitions" in frame._attributes:        
                row[4] = int(frame._attributes["GenMsgNrOfRepetitions"])
        elif frame._attributes["GenMsgSendType"] == "8":
            row[3] = "DualCycle"
            if "GenMsgCycleTimeActive" in frame._attributes:
                row[4] = int(frame._attributes["GenMsgCycleTimeActive"])
        elif frame._attributes["GenMsgSendType"] == "10":
            row[3] = "None"
            if "GenMsgDelayTime" in frame._attributes:
                row[3] = int(frame._attributes["GenMsgDelayTime"])
        elif frame._attributes["GenMsgSendType"] == "9":
            row[3] = "OnChange"
            if "GenMsgNrOfRepetitions" in frame._attributes:        
                row[4] = int(frame._attributes["GenMsgNrOfRepetitions"])
        elif frame._attributes["GenMsgSendType"] == "1":
            row[3] = "Spontaneous"
            if "GenMsgDelayTime" in frame._attributes:
                row[4] = int(frame._attributes["GenMsgDelayTime"])
        else:
            pass


def writeBuMatrixx(buList, sig, frame, row, col):
    #iterate over boardunits:
    for bu in buList:
        # write "s" "r" "r/s" if signal is sent, received or send and received by boardunit
        if bu in sig._reciever and bu in frame._Transmitter:
            row[col] = "r/s"
        elif bu in sig._reciever:
            row[col] = "r"
        elif bu in frame._Transmitter:
            row[col] = "s"
        else:
            pass
        col += 1
    return col


def writeValuex(label, value, row, rearCol):
    row[rearCol] = value
    row[rearCol + 1] = label

def writeSignalx(db, sig, row, rearCol):
    #startbyte
    row[5] = int((sig.getMsbReverseStartbit())/8+1)
    #startbit
    row[6] = (sig.getMsbReverseStartbit())%8
    #signalname
    row[7] = sig._name

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
    row[8] = comment
    row[9] = sig._signalsize

    #startvalue of signal available
    if "GenSigStartValue" in sig._attributes:
        if db._signalDefines["GenSigStartValue"]._definition == "STRING":
            row[10] = sig._attributes["GenSigStartValue"]
        elif db._signalDefines["GenSigStartValue"]._definition == "INT" or db._signalDefines["GenSigStartValue"]._definition == "HEX":
            row[10] = "%Xh" % int(sig._attributes["GenSigStartValue"])

    #SNA-value of signal available
    if "GenSigSNA" in sig._attributes:
        row[11] = sig._attributes["GenSigSNA"][1:-1]

    # eval byteorder (intel == 1 / motorola == 0)
    if sig._byteorder == 1:
        row[12] = "i"
    else:
        row[12] = "m"

    # is a unit defined for signal?
    if sig._unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            row[rearCol+2] = "%g" % float(sig._factor) + "  " + sig._unit
        #factor == 1.0
        else:
            row[rearCol + 2] = sig._unit
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig._factor) != 1:
            row[rearCol + 2] = float(sig._factor)
    
def exportCsv(db, filename, delimiter=','):
    head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
    head_tail = ['Value',   'Name / Phys. Range', 'Function / Increment Unit']

    csvtable = list() # List holding all csv rows

    col = 0 # Column counter

    # -- headers start:
    headerrow = csvRow()

    # write first row (header) cols before frameardunits:
    for head in head_top:
        headerrow.write(col, head)
        col += 1

    # write frameardunits in first row:
    buList = []
    for bu in db._BUs._list:
        headerrow.write(col, bu._name)
        buList.append(bu._name)
        col += 1

    # write first row (header) cols after frameardunits:
    for head in head_tail:
        headerrow.write(col, head)
        col += 1

    csvtable.append(headerrow)
    # -- headers end...

    frameHash = {}
    for frame in db._fl._list:
        frameHash[int(frame._Id)] = frame

    # set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frameHash.keys()):
        frame = frameHash[idx]

        # sort signals:
        sigHash = {}
        for sig in frame._signals:
            sigHash["%02d" % int(sig.getMsbReverseStartbit()) + sig._name] = sig
        
        # iterate over signals
        for sig_idx in sorted(sigHash.keys()):
            sig = sigHash[sig_idx]      

            # value table available?
            if sig._values.__len__() > 0:
                # iterate over values in valuetable
                for val in sorted(sig._values.keys()):
                    signalRow = csvRow()
                    writeFramex(frame, signalRow)
                    col = head_top.__len__()
                    col = writeBuMatrixx(buList, sig, frame, signalRow, col)
                    # write Value
                    writeValuex(val, sig._values[val], signalRow, col)
                    writeSignalx(db, sig, signalRow, col)

                    # no min/max here, because min/max has same col as values...
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
            
                if float(sig._min) != 0 or float(sig._max) != 1.0:
                    signalRow[col+1] = str("%s..%s" %(sig._min, sig._max))

                # next row                  
                row += 1
                csvtable.append(signalRow)
                # set style to normal - without border
        # loop over signals ends here
    # loop over frames ends here

    finalTableString = "\n".join([row.toCSV(delimiter) for row in csvtable])
    
    if filename is not None:
        # save file
        if (sys.version_info > (3, 0)):
            with open(filename, 'w', encoding='utf8') as thefile:
                thefile.write(finalTableString)
        else:
            with open(filename, 'w') as thefile:
                thefile.write(finalTableString)

    else:
        # just print to stdout
        print(finalTableString)
