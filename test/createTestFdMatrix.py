#!/usr/bin/env python
# coding=utf-8
import codecs
import sys
sys.path.append('..')

import canmatrix
#
# create target Matrix
#

db = canmatrix.CanMatrix()

myFrame1 = canmatrix.Frame("canFdStandard1",Id=1,  dlc=24, is_fd = True)
myFrame2 = canmatrix.Frame("CanFdExtended2",Id=2,  dlc=16, extended = True, is_fd = True)
myFrame3 = canmatrix.Frame("CanExtended3", Id=3, dlc=8, extended = True)
myFrame4 = canmatrix.Frame("CanStandard4", Id=4,  dlc=8)

mySignal1 = canmatrix.Signal("signal1", signalSize=64, startBit=0, is_little_endian=True, min=0, max=0, is_signed=True)
mySignal2 = canmatrix.Signal("signal2", signalSize=64, startBit=64, is_little_endian=True, min=0, max=0, is_signed=True)
mySignal3 = canmatrix.Signal("signal3", signalSize=64, startBit=128, is_little_endian=True, min=0, max=0, is_signed=True)

myFrame1.addSignal(mySignal3)
myFrame1.addSignal(mySignal2)
myFrame1.addSignal(mySignal1)


myFrame2.addSignal(mySignal2)
myFrame2.addSignal(mySignal1)


db.frames.addFrame(myFrame1)
db.frames.addFrame(myFrame2)
db.frames.addFrame(myFrame3)
db.frames.addFrame(myFrame4)


#
#
# export the new (target)-Matrix for example as .dbc:
#

canmatrix.formats.dumpp({"": db}, "testfd.dbc", dbcExportEncoding='iso-8859-1',
             dbcExportCommentEncoding='iso-8859-1')
