from __future__ import absolute_import

#!/usr/bin/env python

#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

from .canmatrix import *

def copyBU (buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'BoardUnit':
        bu = buId
    else:
        bu = sourceDb._BUs.byName(buId)

    targetDb._BUs.add(bu)

    # copy all bu-defines
    attributes = bu._attributes
    for attribute in attributes:
        targetDb.addBUDefines(attribute, sourceDb._buDefines[attribute]._definition)
        targetDb.addDefineDefault(attribute, sourceDb._buDefines[attribute]._defaultValue)

def copyBUwithFrames (buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Frames and Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'instance':
        bu = buId
    else:
        bu = sourceDb._BUs.byName(buId)

    targetDb._BUs.add(bu)

    #copy tx-frames
    for frame in sourceDb._fl._list:
        if bu._name in frame._Transmitter:
            copyFrame (frame, sourceDb, targetDb)

    #copy rx-frames
    for frame in sourceDb._fl._list:
        for signal in frame._signals:
            if bu._name in signal._receiver:
                copyFrame (frame, sourceDb, targetDb)
                break

    # copy all bu-defines
    attributes = bu._attributes
    for attribute in attributes:
        targetDb.addBUDefines(attribute, sourceDb._buDefines[attribute]._definition)
        targetDb.addDefineDefault(attribute, sourceDb._buDefines[attribute]._defaultValue)




def copyFrame (frameId, sourceDb, targetDb):
    """
    This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Boardunits, and Defines
    """
    # check wether frameId is object, id or symbolic name
    if type(frameId).__name__ == 'int':
        frame = sourceDb.frameById(frameId)
    elif type(frameId).__name__ == 'Frame':
        frame = frameId
    else:
        frame = sourceDb.frameByName(frameId)

    if targetDb.frameById(frame._Id) != None:
        #frame already in targetdb...    
        return
 
    # copy Frame-Object:
    targetDb._fl.addFrame(frame)

    ## Boardunits:
    # each transmitter of Frame could be ECU that is not listed already
    for transmitter in frame._Transmitter:
        targetBU = targetDb._BUs.byName(transmitter)
        sourceBU = sourceDb._BUs.byName(transmitter)
        if sourceBU is not None and targetBU is None:
            copyBU(sourceBU, sourceDb, targetDb)

    #trigger all signals of Frame
    for sig in frame._signals:
        # each receiver of Signal could be ECU that is not listed already
        for receiver in sig._receiver:
            targetBU = targetDb._BUs.byName(transmitter)
            sourceBU = sourceDb._BUs.byName(transmitter)
            if sourceBU is not None and targetBU is None:
                copyBU(sourceBU, sourceDb, targetDb)

    # copy all frame-defines
    attributes = frame._attributes
    for attribute in attributes:
        targetDb.addFrameDefines(attribute, sourceDb._frameDefines[attribute]._definition)
        targetDb.addDefineDefault(attribute, sourceDb._frameDefines[attribute]._defaultValue)

    #trigger all signals of Frame
    for sig in frame._signals:
        # delete all 'unknown' attributes
        attributes = sig._attributes
        for attribute in attributes:
            targetDb.addSignalDefines(attribute, sourceDb._signalDefines[attribute]._definition)
            targetDb.addDefineDefault(attribute, sourceDb._signalDefines[attribute]._defaultValue)
