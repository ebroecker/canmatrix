#!/usr/bin/env python

# Copyright (c) 2013, Eduard Broecker
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

from __future__ import absolute_import
import logging

from .canmatrix import *
from copy import deepcopy

logger = logging.getLogger(__name__)


def copyBU(buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'BoardUnit':
        buList = [buId]
    else:
        buList = sourceDb.globBoardUnits(buId)

    for bu in buList:
        targetDb.addEcu(deepcopy(bu))

        # copy all bu-defines
        for attribute in bu.attributes:
            if attribute not in targetDb.buDefines:
                targetDb.addBUDefines(
                    deepcopy(attribute), deepcopy(sourceDb.buDefines[attribute].definition))
                targetDb.addDefineDefault(
                    deepcopy(attribute), deepcopy(sourceDb.buDefines[attribute].defaultValue))
            # update enum-datatypes if needed:
            if sourceDb.buDefines[attribute].type == 'ENUM':
                tempAttr = bu.attribute(attribute, db=sourceDb)
                if tempAttr not in targetDb.buDefines[attribute].values:
                    targetDb.buDefines[attribute].values.append(deepcopy(tempAttr))
                    targetDb.buDefines[attribute].update()



def copyBUwithFrames(buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Frames and Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'instance':
        buList = [buId]
    else:
        buList = sourceDb.globBoardUnits(buId)

    for bu in buList:
        logger.info("Copying ECU " + bu.name)

        targetDb.addEcu(deepcopy(bu))

        # copy tx-frames
        for frame in sourceDb.frames:
            if bu.name in frame.transmitters:
                copyFrame(frame, sourceDb, targetDb)

        # copy rx-frames
        for frame in sourceDb.frames:
            for signal in frame.signals:
                if bu.name in signal.receiver:
                    copyFrame(frame, sourceDb, targetDb)
                    break

        # copy all bu-defines
        for attribute in bu.attributes:
            if attribute not in targetDb.buDefines:
                targetDb.addBUDefines(
                    deepcopy(attribute), deepcopy(sourceDb.buDefines[attribute].definition))
                targetDb.addDefineDefault(
                    deepcopy(attribute), deepcopy(sourceDb.buDefines[attribute].defaultValue))
            # update enum-datatypes if needed:
            if sourceDb.buDefines[attribute].type == 'ENUM':
                tempAttr = bu.attribute(attribute, db=sourceDb)
                if tempAttr not in targetDb.buDefines[attribute].values:
                    targetDb.buDefines[attribute].values.append(deepcopy(tempAttr))
                    targetDb.buDefines[attribute].update()



def copyFrame(frameId, sourceDb, targetDb):
    """
    This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Boardunits, and Defines
    """
    # check wether frameId is object, id or symbolic name
    if 'int' in type(frameId).__name__ or 'long' in type(frameId).__name__:
        frameList = [sourceDb.frameById(frameId)]
    elif type(frameId).__name__ == 'Frame':
        frameList = [frameId]
    else:
        frameList = sourceDb.globFrames(frameId)

    for frame in frameList:
        logger.info("Copying Frame " + frame.name)

        if targetDb.frameById(frame.id) is not None:
            # frame already in targetdb...
            return False

        # copy Frame-Object:
        targetDb.addFrame(deepcopy(frame))

        # Boardunits:
        # each transmitter of Frame could be ECU that is not listed already
        for transmitter in frame.transmitters:
            targetBU = targetDb.boardUnitByName(transmitter)
            sourceBU = sourceDb.boardUnitByName(transmitter)
            if sourceBU is not None and targetBU is None:
                copyBU(sourceBU, sourceDb, targetDb)

        # trigger all signals of Frame
        for sig in frame.signals:
            # each receiver of Signal could be ECU that is not listed already
            for receiver in sig.receiver:
                targetBU = targetDb.boardUnitByName(receiver)
                sourceBU = sourceDb.boardUnitByName(receiver)
                if sourceBU is not None and targetBU is None:
                    copyBU(sourceBU, sourceDb, targetDb)

        # copy all frame-defines
        attributes = frame.attributes
        for attribute in attributes:
            if attribute not in targetDb.frameDefines:
                targetDb.addFrameDefines(
                    deepcopy(attribute), deepcopy(sourceDb.frameDefines[attribute].definition))
                targetDb.addDefineDefault(
                    deepcopy(attribute), deepcopy(sourceDb.frameDefines[attribute].defaultValue))
            # update enum-datatypes if needed:
            if sourceDb.frameDefines[attribute].type == 'ENUM':
                tempAttr = frame.attribute(attribute, db=sourceDb)
                if tempAttr not in targetDb.frameDefines[attribute].values:
                    targetDb.frameDefines[attribute].values.append(deepcopy(tempAttr))
                    targetDb.frameDefines[attribute].update()

        # trigger all signals of Frame
        for sig in frame.signals:
            # delete all 'unknown' attributes
            for attribute in sig.attributes:
                targetDb.addSignalDefines(
                    deepcopy(attribute), deepcopy(sourceDb.signalDefines[attribute].definition))
                targetDb.addDefineDefault(
                    deepcopy(attribute), deepcopy(sourceDb.signalDefines[attribute].defaultValue))
                # update enum-datatypes if needed:
                if sourceDb.signalDefines[attribute].type == 'ENUM':
                    tempAttr = sig.attribute(attribute, db=sourceDb)
                    if tempAttr not in targetDb.signalDefines[attribute].values:
                        targetDb.signalDefines[attribute].values.append(deepcopy(tempAttr))
                        targetDb.signalDefines[attribute].update()

    return True
