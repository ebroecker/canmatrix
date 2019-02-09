#!/usr/bin/env python3
import canmatrix.formats
cm = canmatrix.CanMatrix()

#
# create frame Node604
#
frame1 = canmatrix.Frame("Node604", j1939_pgn = 0xff00, j1939_prio = 0x6,
                         j1939_source = 0x80,
                         comment = "J1939 packet containing >8 byte payload")
for i in range(1,9):
    sig = canmatrix.Signal("ch%d" % i, size = 32, is_float = True, is_little_endian = False, startBit = (i-1)*32)
    frame1.addSignal(sig)
cm.addFrame(frame1)

#
# create frame Node605
#
frame2 = canmatrix.Frame("Node605", j1939_pgn = 0xff01, j1939_prio = 0x6,
                         j1939_source = 0x80,
                         comment="J1939 packet containing 8 byte payload")

sig = canmatrix.Signal("ch1", size=32, is_float=True, is_little_endian=False, startBit=0)
sig2 = canmatrix.Signal("ch2", size=32, is_float=True, is_little_endian=False, startBit=32)
frame2.addSignal(sig)
frame2.addSignal(sig2)
cm.addFrame(frame2)


#
# create frame Node606
#
frame3 = canmatrix.Frame("Node606", j1939_pgn = 0xff02, j1939_prio = 0x6,
                         j1939_source = 0x80,
                         comment="J1939 packet containing <8 byte payload")
sig = canmatrix.Signal("ch1", size=32, is_float=True, is_little_endian=False, startBit=0)
frame3.addSignal(sig)
cm.addFrame(frame3)


cm.recalcDLC("force")

# save dbc
canmatrix.formats.dumpp({"":cm}, "example_j1939.dbc")
