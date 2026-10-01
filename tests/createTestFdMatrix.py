#!/usr/bin/env python
# coding=utf-8
import codecs
import sys
sys.path.append('..')

from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix.Ecu import Ecu
from canmatrix.CanMatrix import CanMatrix
import canmatrix.formats

#
# create target Matrix
#

db = CanMatrix()

db.ecus.add(Ecu("testBU"))
db.ecus.add(Ecu("recBU"))

myFrame1 = Frame("canFdStandard1",Id=1,  dlc=24, is_fd = True, transmitter=["testBU"])
myFrame2 = Frame("CanFdExtended2",Id=2,  dlc=16, extended = True, is_fd = True, transmitter=["testBU"])
myFrame3 = Frame("CanExtended3", Id=3, dlc=8, extended = True, transmitter=["testBU"])
myFrame4 = Frame("CanStandard4", Id=4,  dlc=8)

mySignal1 = Signal("signal1", signalSize=64, startBit=0, is_little_endian=True, min=0, max=0, is_signed=True, receiver=["recBU"])
mySignal2 = Signal("signal2", signalSize=64, startBit=64, is_little_endian=True, min=0, max=0, is_signed=True, receiver=["recBU"])
mySignal3 = Signal("signal3", signalSize=64, startBit=128, is_little_endian=True, min=0, max=0, is_signed=True)

myFrame1.add_signal(mySignal3)
myFrame1.add_signal(mySignal2)
myFrame1.add_signal(mySignal1)


myFrame2.add_signal(mySignal2)
myFrame2.add_signal(mySignal1)


db.frames.add_frame(myFrame1)
db.frames.add_frame(myFrame2)
db.frames.add_frame(myFrame3)
db.frames.add_frame(myFrame4)


#
#
# export the new (target)-Matrix for example as .dbc:
#

canmatrix.formats.dumpp({"": db}, "testfd.dbc", dbcExportEncoding='iso-8859-1',
             dbcExportCommentEncoding='iso-8859-1')
