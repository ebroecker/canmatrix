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


def getFrameInfo(db, frame):
    retArray = []
    # frame-id
    if frame.extended:
        retArray.append("%3Xxh" % frame.id)
    else:
        retArray.append("%3Xh" % frame.id)
    # frame-Name
    retArray.append(frame.name)

    if "GenMsgCycleTime" in db.frameDefines:
        # determin cycle-time
        retArray.append(frame.attribute("GenMsgCycleTime", db=db))

    # determin send-type
    if "GenMsgSendType" in db.frameDefines:
        retArray.append(frame.attribute("GenMsgSendType", db=db))
        if "GenMsgDelayTime" in db.frameDefines:
            retArray.append(frame.attribute("GenMsgDelayTime", db=db))
        else:
            retArray.append("")
    else:
        retArray.append("")
        retArray.append("")
    return retArray


def getSignal(db, sig, motorolaBitFormat):
    frontArray = []
    backArray = []
    if motorolaBitFormat == "msb":
        startBit = sig.getStartbit(bitNumbering=1)
    elif motorolaBitFormat == "msbreverse":
        startBit = sig.getStartbit()
    else:  # motorolaBitFormat == "lsb"
        startBit = sig.getStartbit(bitNumbering=1, startLittle=True)

    # startbyte
    frontArray.append(int(startBit / 8) + 1)
    # startbit
    frontArray.append((startBit) % 8)
    # signalname
    frontArray.append(sig.name)

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
    frontArray.append(comment)
    frontArray.append(sig.size)

    # startvalue of signal available
    if "GenSigStartValue" in db.signalDefines:
        if db.signalDefines["GenSigStartValue"].definition == "STRING":
            frontArray.append(sig.attribute("GenSigStartValue", db=db))
        elif db.signalDefines["GenSigStartValue"].definition == "INT" or db.signalDefines["GenSigStartValue"].definition == "HEX":
            frontArray.append("%Xh" % sig.attribute("GenSigStartValue", db=db))
        else:
            frontArray.append(" ")
    else:
        frontArray.append(" ")

    # SNA-value of signal available
    if "GenSigSNA" in db.signalDefines:
        sna = sig.attribute("GenSigSNA", db=db)
        if sna is not None:
            sna = sna[1:-1]
        frontArray.append(sna)
    # no SNA-value of signal available / just for correct style:
    else:
        frontArray.append(" ")

    # eval byteorder (little_endian: intel == True / motorola == 0)
    if sig.is_little_endian:
        frontArray.append("i")
    else:
        frontArray.append("m")

    # is a unit defined for signal?
    if sig.unit.strip().__len__() > 0:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            backArray.append("%g" % float(sig.factor) + "  " + sig.unit)
        #factor == 1.0
        else:
            backArray.append(sig.unit)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            backArray.append("%g -" % float(sig.factor))
        #factor == 1.0
        else:
            backArray.append("")
    return frontArray,backArray
