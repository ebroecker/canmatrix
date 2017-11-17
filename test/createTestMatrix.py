#!/usr/bin/env python
# coding=utf-8
import codecs
import sys
sys.path.append('..')

import canmatrix.formats
from canmatrix.canmatrix import *
#
# create target Matrix
#

db = CanMatrix()

db.boardUnits.add(BoardUnit("testBU"))
db.boardUnits.add(BoardUnit("recBU"))

myFrame = Frame("testFrame1", Id=0x123, dlc=8, transmitter="testBU")

mySignal = Signal("someTestSignal",
                  signalSize=11,
                  is_little_endian=False,
                  is_signed=False,
                  factor=5.0,
                  offset=1.0,
                  min=0,
                  max=500,
                  unit="specialCharUnit°$".decode("utf-8"),
                  receiver=["recBU"])
mySignal.setStartbit(9, bitNumbering=1, startLittle=True)
mySignal2 = Signal("Signal",
                   startBit=20,
                   signalSize=3,
                   is_little_endian=True,
                   is_signed=False,
                   factor=1.0,
                   offset=0.0,
                   min=0,
                   max=6,
                   unit="someUnit",
                   receiver=["recBU"])

mySignal2.addValues(1, "one")
mySignal2.addValues(2, "two")
mySignal2.addValues(3, "three")

mySignal.addComment(
    "Multi \n Line \n Signal comment with a-umlaut: ä".decode("utf-8"))
myFrame.addComment("Multi \n Line \n Frame comment")

myFrame.addSignal(mySignal)
myFrame.addSignal(mySignal2)

myFrame2 = Frame("extendedFrame", Id=0x12,  dlc=8, transmitter="testBU")
myFrame2._extended = 1

db.frames.addFrame(myFrame)
db.frames.addFrame(myFrame2)

db.boardUnitByName("testBU").addComment("sender ECU")
db.boardUnitByName("testBU").addAttribute("NetworkNode", 0x111)
db.boardUnitByName("recBU").addComment("receiver ECU")

db.frameByName("testFrame1").addAttribute("GenMsgCycleTime", 100)

db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')
db.addBUDefines("NetworkNode", 'INT 0 65535')


#
#
# export the new (target)-Matrix for example as .dbc:
#

canmatrix.formats.dumpp({"myMatrix": db}, "test.dbc", dbcExportEncoding='iso-8859-1',
             dbcExportCommentEncoding='iso-8859-1')
