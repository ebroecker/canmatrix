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
from createCMacros import *


typedef = """
typedef struct Mailbox {
uint8_t data[8];
} Mailbox_t;
"""

processFrame = """
void processFrame(uint32_t canId, uint8_t *framedata, uint8_t dlc)
{
    Mailbox_t *mailbox;

    mailbox = getRxCanMailBox(canId);

    if (mailbox != NULL)
    {
        memcpy(mailbox->data, framedata, (dlc>8)?8:dlc);
    }
}
"""

receiveIdArray = "uint32_t receiveFrameIds[COUNTRXMAILBOXES] = {%s};"
rxMailboxStruct = "Mailbox_t RxCanMailboxes[COUNTRXMAILBOXES];"
txMailboxStruct = "Mailbox_t TxCanMailboxes[COUNTTXMAILBOXES];"

getRxCanMailBox = """
struct Mailbox *getRxCanMailBox(uint32_t canId)
{
    uint32_t i;

    for(i = 0; i< COUNTRXMAILBOXES; i++)
    {
        if(canId == receiveFrameIds[i])
            return &(RxCanMailboxes[i]);
    }
    return 0;
}

"""


def main():
    if len(sys.argv) <= 2:
        print "not yet working script for generating a communication layer for dedicated ECU out of can database"
        print "! missing support for sending cyclic messages"
        print "! missing any TEST ! "
        print " this code is just proofe of concept \n"
        print "Usage: createccl.py CanDatabaseFile ECU_Name "
        exit()

    ccl_h = "#ifndef __CCL_H__\n#define __CCL_H__\n\n"
    ccl_h += "typedef unsigned char uint8;\ntypedef unsigned int uint32;\n\n"

    ccl_c = "#include <string.h>\n#include <stdint.h>\n#include \"ccl.h\"\n\n"
    infile = sys.argv[1]
    ecu = sys.argv[2]

    dbs = canmatrix.formats.loadp(infile)
    db = next(iter(dbs.values()))

    receiveArray = []
    receiveDict = {}
    receiveIndex = 0
    sendIndex = 0
    txDict = {}
    for frame in db.frames:
        if ecu in frame.receiver:
            receiveArray.append(frame.id)
            receiveDict[frame] = receiveIndex
            receiveIndex += 1

        if ecu in frame.transmitters:
            txDict[frame] = sendIndex
            sendIndex += 1
#            print frame.name
#            if "GenMsgCycleTime" in frame.attributes and int(frame.attributes["GenMsgCycleTime"]) != 0:
#                print frame.name,
#                print frame.attributes["GenMsgCycleTime"]
#            ccl_h += createStoreMacrosForFrame(frame, "_" + frame.name + "_")

    tempStr = ""
    for canid in receiveArray:
        tempStr += hex(canid) + ", "

    ccl_c += rxMailboxStruct + "\n"
    ccl_c += txMailboxStruct + "\n"
    ccl_c += receiveIdArray % (tempStr) + "\n"
    ccl_c += getRxCanMailBox + "\n"
    ccl_c += processFrame + "\n"

    ccl_h += "#define COUNTRXMAILBOXES %d" % (receiveArray.__len__()) + "\n"
    ccl_h += "#define COUNTTXMAILBOXES %d" % (txDict.__len__()) + "\n"
    ccl_h += typedef + "\n"
    ccl_h += "extern " + rxMailboxStruct + "\n"
    ccl_h += "extern " + txMailboxStruct + "\n"
    for frame in receiveDict:
        for signal in frame.signals:
            if ecu in signal.receiver:
                ccl_h += createDecodeMacro(signal, "_" +
                                           frame.name +
                                           "__", "", "RxCanMailboxes[%d].data" %
                                           (receiveDict[frame]))
# for complete frame:
#        ccl_h += createDecodeMacrosForFrame(frame, "_" + frame.name + "__", "", "RxCanMailboxes[%d].data" % (receiveDict[frame]))
    for frame in txDict:
        ccl_h += createStoreMacrosForFrame(frame, "_" +
                                           frame.name +
                                           "_", framename="TxCanMailboxes[%d].data" %
                                           txDict[frame])

    ccl_h += "\n\n#endif /*  __CCL_H___ */"

    cfile = open("ccl.c", "w")
    cfile.write(ccl_c)
    cfile.close()

    hfile = open("ccl.h", "w")
    hfile.write(ccl_h)
    hfile.close()

if __name__ == '__main__':
    sys.exit(main())
