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

import math

def getFrameInfo(frame):
    retArray = []
    # frame-id
    if frame.extended:
        retArray.append("%3Xxh" % frame.id)
    else:
        retArray.append("%3Xh" % frame.id)
    # frame-Name
    retArray.append(frame.name)

    # determin cycle-time
    if "GenMsgCycleTime" in frame.attributes:
        retArray.append(int(frame.attributes["GenMsgCycleTime"]))
    else:
        retArray.append("")

    # determin send-type
    if "GenMsgSendType" in frame.attributes:
        if frame.attributes["GenMsgSendType"] == "5":
            retArray.append("Cyclic+Change")
            if "GenMsgDelayTime" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgDelayTime"]))
            else:
                retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "0":
            retArray.append("Cyclic")
            retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "2":
            retArray.append("BAF")
            if "GenMsgNrOfRepetitions" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgNrOfRepetitions"]))
            else:
                retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "8":
            retArray.append("DualCycle")
            if "GenMsgCycleTimeActive" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgCycleTimeActive"]))
            else:
                retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "10":
            retArray.append("None")

            if "GenMsgDelayTime" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgDelayTime"]))
            else:
                retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "9":
            retArray.append("OnChange")
            if "GenMsgNrOfRepetitions" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgNrOfRepetitions"]))
            else:
                retArray.append("")
        elif frame.attributes["GenMsgSendType"] == "1":
            retArray.append("Spontaneous")
            if "GenMsgDelayTime" in frame.attributes:
                retArray.append(int(frame.attributes["GenMsgDelayTime"]))
            else:
                retArray.append("")
        else:
            retArray.append("")
            retArray.append("")
    else:
        retArray.append("")
        retArray.append("")
    return retArray

