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

from .canmatrix import *


def copyBU(buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'BoardUnit':
        bu = buId
    else:
        bu = sourceDb.boardUnits.byName(buId)

    targetDb.boardUnits.add(bu)

    # copy all bu-defines
    for attribute in bu.attributes:
        targetDb.addBUDefines(
            attribute, sourceDb.buDefines[attribute].definition)
        targetDb.addDefineDefault(
            attribute, sourceDb.buDefines[attribute].defaultValue)


def copyBUwithFrames(buId, sourceDb, targetDb):
    """
    This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Frames and Defines
    """
    # check wether buId is object or symbolic name
    if type(buId).__name__ == 'instance':
        bu = buId
    else:
        bu = sourceDb.boardUnits.byName(buId)

    targetDb.boardUnits.add(bu)

    # copy tx-frames
    for frame in sourceDb.frames:
        if bu.name in frame.transmitter:
            copyFrame(frame, sourceDb, targetDb)

    # copy rx-frames
    for frame in sourceDb.frames:
        for signal in frame.signals:
            if bu.name in signal.receiver:
                copyFrame(frame, sourceDb, targetDb)
                break

    # copy all bu-defines
    for attribute in bu.attributes:
        targetDb.addBUDefines(
            attribute, sourceDb.buDefines[attribute].definition)
        targetDb.addDefineDefault(
            attribute, sourceDb.buDefines[attribute].defaultValue)


def copyFrame(frameId, sourceDb, targetDb):
    """
    This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Boardunits, and Defines
    """

    # check wether frameId is object, id or symbolic name
    if 'int' in type(frameId).__name__:
        frame = sourceDb.frameById(frameId)
    elif type(frameId).__name__ == 'Frame':
        frame = frameId
    else:
        frame = sourceDb.frameByName(frameId)

    if targetDb.frameById(frameId) is not None:
        # frame already in targetdb...
        return

    # copy Frame-Object:
    targetDb.frames.addFrame(frame)

    # Boardunits:
    # each transmitter of Frame could be ECU that is not listed already
    for transmitter in frame.transmitter:
        targetBU = targetDb.boardUnits.byName(transmitter)
        sourceBU = sourceDb.boardUnits.byName(transmitter)
        if sourceBU is not None and targetBU is None:
            copyBU(sourceBU, sourceDb, targetDb)

    # trigger all signals of Frame
    for sig in frame.signals:
        # each receiver of Signal could be ECU that is not listed already
        for receiver in sig.receiver:
            targetBU = targetDb.boardUnits.byName(transmitter)
            sourceBU = sourceDb.boardUnits.byName(transmitter)
            if sourceBU is not None and targetBU is None:
                copyBU(sourceBU, sourceDb, targetDb)

    # copy all frame-defines
    attributes = frame.attributes
    for attribute in attributes:
        targetDb.addFrameDefines(
            attribute, sourceDb.frameDefines[attribute].definition)
        targetDb.addDefineDefault(
            attribute, sourceDb.frameDefines[attribute].defaultValue)

    # trigger all signals of Frame
    for sig in frame.signals:
        # delete all 'unknown' attributes
        for attribute in sig.attributes:
            targetDb.addSignalDefines(
                attribute, sourceDb.signalDefines[attribute].definition)
            targetDb.addDefineDefault(
                attribute, sourceDb.signalDefines[attribute].defaultValue)
