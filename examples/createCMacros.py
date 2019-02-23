#!/usr/bin/env python
# Copyright (c) 2016, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
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


import sys
sys.path.append('..')
import canmatrix.formats


def createStoreMacro(signal, prefix="", frame="frame"):
    startBit = signal.get_startbit(bit_numbering=1, start_little=1)
    byteOrder = signal.is_little_endian
    length = signal.size
    startByte = int(startBit / 8)
    startBitInByte = startBit % 8
    currentTargetLength = (8 - startBitInByte)
    mask = ((0xffffffffffffffff) >> (64 - length))

    code = "#define storeSignal%s%s(value) do{" % (prefix, signal.name)
    if signal.is_signed:
        code += "value|=((value&0x8000000000000000)>>(64-length));"

    code += "value&=0x%X;" % (mask)

    code += "%s[%d]|=value<<%d;" % (frame, startByte, startBitInByte)

    if byteOrder:
        endByte = int((startBit + length) / 8)
        for count in range(startByte + 1, endByte):
            code += "%s[%d]|=value<<%d;" % (frame, count, currentTargetLength)
            currentTargetLength += 8
    else:  # motorola / big-endian
        endByte = int((startByte * 8 + 8 - startBitInByte - length) / 8)
        for count in range(startByte - 1, endByte - 1, -1):
            code += "%s[%d]|=value<<%d;" % (frame, count, currentTargetLength)
            currentTargetLength += 8
    code += "}while(0);\n"
    return code


def createDecodeMacro(
        signal, prefix="", macrosource="source", source="source"):
    startBit = signal.get_startbit(bit_numbering=1, start_little=1)
    byteOrder = signal.is_little_endian
    length = signal.signalsize

    mask = ((0xffffffffffffffff) >> (64 - length))

    startByte = int(startBit / 8)
    startBitInByte = startBit % 8

    code = "#define getSignal%s%s(%s)  ((((%s[%d])>>%d" % (
        prefix, signal.name, macrosource, source, startByte, startBitInByte)
    currentTargetLength = (8 - startBitInByte)

    if byteOrder:
        endByte = int((startBit + length) / 8)
        if (startBit + length) % 8 == 0:
            endByte -= 1
        for count in range(startByte + 1, endByte + 1):
            code += "|(%s[%d])<<%d" % (source, count, currentTargetLength)
            currentTargetLength += 8

    else:  # motorola / big-endian
        endByte = int((startByte * 8 + 8 - startBitInByte - length) / 8)

        for count in range(startByte - 1, endByte - 1, -1):
            code += "|%s[%d]<<%d" % (source, count, currentTargetLength)
            currentTargetLength += 8

    code += ")&0x%X)" % (mask)

    if signal.is_signed:
        msb_sign_mask = 1 << (length - 1)
        code += "^0x%x)-0x%x " % (msb_sign_mask, msb_sign_mask)
    else:
        code += ")"
    code += "\n"
    return code


def createDecodeMacrosForFrame(
        Frame, prefix="", macrosource="source", source="source"):
    code = ""
    for signal in Frame.signals:
        code += createDecodeMacro(signal, prefix, macrosource, source)
    return code


def createStoreMacrosForFrame(Frame, prefix="", framename="frame"):
    code = ""
    for signal in Frame.signals:
        code += createStoreMacro(signal, prefix, frame=framename)
    return code


def main():
    from optparse import OptionParser

    usage = """
    %prog [options] canDatabaseFile targetFile.c

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.xls(x)|*.sym

    """

    parser = OptionParser(usage=usage)
    parser.add_option("", "--frame",
                      dest="exportframe", default=None,
                      help="create macros for Frame(s); Comma seperated list of Names ")
    parser.add_option("", "--ecu",
                      dest="exportecu", default=None,
                      help="create macros for Ecu(s) Comma seperated ")

    (cmdlineOptions, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    infile = args[0]
    outfile = args[1]

    dbs = canmatrix.formats.loadp(infile)
    db = next(iter(dbs.values()))

    sourceCode = ""
    if cmdlineOptions.exportframe is None and cmdlineOptions.exportecu is None:
        for frame in db.frames:
            sourceCode += createDecodeMacrosForFrame(
                frame, "_" + frame.name + "_")
            sourceCode += createStoreMacrosForFrame(
                frame, "_" + frame.name + "_")

    if cmdlineOptions.exportframe is not None:
        for frameId in cmdlineOptions.exportframe.split(','):
            try:
                frame = db.frame_by_id(int(frameId))
            except ValueError:
                frame = db.frame_by_name(frameId)
            if frame is not None:
                sourceCode += createDecodeMacrosForFrame(
                    frame, "_" + frame.name + "_")
                sourceCode += createStoreMacrosForFrame(
                    frame, "_" + frame.name + "_")

    if cmdlineOptions.exportecu is not None:
        ecuList = cmdlineOptions.exportecu.split(',')
        for frame in db.frames:
            for ecu in ecuList:
                if ecu in frame.transmitters:
                    sourceCode += createStoreMacrosForFrame(
                        frame, "_" + frame.name + "_")
                for signal in frame.signals:
                    if ecu in signal.receiver:
                        sourceCode += createDecodeMacro(signal,
                                                        "_" + frame.name + "_")

    cfile = open(outfile, "w")
    cfile.write(sourceCode)
    cfile.close()


if __name__ == '__main__':
    sys.exit(main())
