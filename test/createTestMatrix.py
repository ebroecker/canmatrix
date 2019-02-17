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

db.ecus.add(ecu("testBU"))
db.ecus.add(ecu("recBU"))

myFrame = Frame("testFrame1", Id=0x123, dlc=8, transmitter="testBU")

if sys.version_info > (3, 0):
    unit = u"specialCharUnit°$"
    comment = u"Multi \n Line \n Signal comment with a-umlaut: ä"
else:
    unit = "specialCharUnit°$".decode("utf-8")
    comment = "Multi \n Line \n Signal comment with a-umlaut: ä".decode("utf-8")

mySignal = Signal("someTestSignal",
                  signalSize=11,
                  is_little_endian=False,
                  is_signed=False,
                  factor=5.0,
                  offset=1.0,
                  min=0,
                  max=500,
                  unit=u"specialCharUnit°$", #.decode("utf-8"),
                  receiver=["recBU"])
mySignal.set_startbit(9, bitNumbering=1, startLittle=True)
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

mySignal2.add_values(1, "one")
mySignal2.add_values(2, "two")
mySignal2.add_values(3, "three")

mySignal.add_comment(comment)
myFrame.add_comment("Multi \n Line \n Frame comment")

myFrame.add_signal(mySignal)
myFrame.add_signal(mySignal2)

myFrame2 = Frame("extendedFrame", Id=0x12,  dlc=8, transmitter="testBU")
myFrame2.extended = 1

db.frames.add_frame(myFrame)
db.frames.add_frame(myFrame2)

db.ecu_by_name("testBU").add_comment("sender ECU")
db.ecu_by_name("testBU").add_attribute("NetworkNode", 0x111)
db.ecu_by_name("recBU").add_comment("receiver ECU")

db.frame_by_name("testFrame1").add_attribute("GenMsgCycleTime", 100)

db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
db.add_ecu_defines("NetworkNode", 'INT 0 65535')


#
#
# export the new (target)-Matrix for example as .dbc:
#

canmatrix.formats.dumpp({"myMatrix": db}, "test.dbc", dbcExportEncoding='iso-8859-1',
             dbcExportCommentEncoding='iso-8859-1')
