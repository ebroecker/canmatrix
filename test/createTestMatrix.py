#!/usr/bin/env python
# coding=utf-8

import canmatrix.exportall as ex
from canmatrix.canmatrix import *
import sys
import codecs

#
# create target Matrix
#

db = CanMatrix()

db._BUs.add(BoardUnit("testBU"))
db._BUs.add(BoardUnit("recBU"))

myFrame = Frame(0x123, "testFrame1", 8, "testBU" )

mySignal = Signal("someTestSignal", 3, 11, 0, "+", 5.0, 1.0, 0, 500, "specialCharUnit°$".decode("utf-8"), ["recBU"])
mySignal2 = Signal("Signal", 20, 3, 1, "+", 1.0, 0.0, 0, 6, "someUnit", ["recBU"])
mySignal2.addValues(1, "one")
mySignal2.addValues(2, "two")
mySignal2.addValues(3, "three")

mySignal.addComment("Multi \n Line \n Signal comment with a-umlaut: ä".decode("utf-8"))
myFrame.addComment("Multi \n Line \n Frame comment")

myFrame.addSignal(mySignal)
myFrame.addSignal(mySignal2)


db._fl.addFrame(myFrame)

db.boardUnitByName("testBU").addComment("sender ECU")
db.boardUnitByName("testBU").addAttribute("NetworkNode", 0x111)
db.boardUnitByName("recBU").addComment("reciever ECU")

db.frameByName("testFrame1").addAttribute("GenMsgCycleTime", 100)

db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')


#
#
# export the new (target)-Matrix for example as .dbc:
#

ex.exportDbc(db, "test.dbc", 'utf-8', 'utf-8')

