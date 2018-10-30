import pytest
import canmatrix.formats
import os.path
import sys

def test_decode_from_dbc():
    here = os.path.dirname(os.path.realpath(__file__))
    cm = canmatrix.formats.loadp(os.path.join(here ,"test_frame_decoding.dbc"), flatImport = True)
    # 001#8d00100100820100
    if sys.version_info > (3, 0):
        frameData1 = bytes([141, 0, 16, 1, 0, 130, 1, 0])
    else:
        frameData1 = bytearray([141, 0, 16, 1, 0, 130, 1, 0])

    frame1 = cm.frameById(1)
    decoded1 = frame1.decode(frameData1)
    assert decoded1["sig0"].rawValue == 1
    assert decoded1["sig1"].rawValue == 35
    assert decoded1["sig2"].rawValue == 0
    assert decoded1["sig3"].rawValue == 2048
    assert decoded1["sig4"].rawValue == 256
    assert decoded1["sig5"].rawValue == 1
    assert decoded1["sig6"].rawValue == 0
    assert decoded1["sig7"].rawValue == 520
    assert decoded1["sig8"].rawValue == 0
    assert decoded1["sig9"].rawValue == 0
    assert decoded1["sig10"].rawValue == 0

    # 002#0C00057003CD1F83
    if sys.version_info > (3, 0):
        frameData2 = bytes([12, 0, 5, 112, 3, 205, 31, 131])
    else:
        frameData2 = bytearray([12, 0, 5, 112, 3, 205, 31, 131])
    frame2 = cm.frameById(2)
    decoded2 = frame2.decode(frameData2)
    assert decoded2["secSig1"].rawValue == 0
    assert decoded2["secSig2"].rawValue == 0
    assert decoded2["secSig3"].rawValue == 0
    assert decoded2["secSig4"].rawValue == 2
    assert decoded2["secSig5"].rawValue == 0
    assert decoded2["secSig6"].rawValue == 0
    assert decoded2["secSig7"].rawValue == 0
    assert decoded2["secSig8"].rawValue == 3
    assert decoded2["secSig9"].rawValue == 1
    assert decoded2["secSig10"].rawValue == 1280
    assert decoded2["secSig11"].rawValue == -144
    assert decoded2["secSig12"].rawValue == 12

    # 003#38638A7E58A8C540
    if sys.version_info > (3, 0):
        frameData3 = bytes([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])
    else:
        frameData3 = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])

    frame3 = cm.frameById(3)
    decoded3 = frame3.decode(frameData3)
    assert decoded3["floatSignal1"].rawValue == 5.424999835668132e-05
    assert decoded3["floatSignal2"].rawValue ==  6.176799774169922

    if sys.version_info > (3, 0):
        frameData4 = bytes([0x38, 0x63, 0x8A, 0x7E, 0x18, 0x20, 0x00])
    else:
        frameData4 = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x18, 0x20, 0x00])
    frame4 = cm.frameById(4)
    decoded4 = frame4.decode(frameData4)
    assert decoded4["myMuxer"].rawValue == 0
    assert decoded4["muxSig9"].rawValue ==  0x20
    assert decoded4["muxSig1"].rawValue == 0x38
    assert decoded4["muxSig2"].rawValue == 0x63
    assert decoded4["muxSig3"].rawValue == 0x8A
    assert decoded4["muxSig4"].rawValue == 0x3F
    assert decoded4["muxSig9"].rawValue == 0x20

    if sys.version_info > (3, 0):
        frameData4b = bytes([0x38, 0x63, 0x8A, 0x7E, 0x18, 0x20, 0x20])
    else:
        frameData4b = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x18, 0x20, 0x20])
    decoded4b = frame4.decode(frameData4b)
    assert decoded4b["myMuxer"].rawValue == 1
    assert decoded4b["muxSig9"].rawValue == 0x20
    assert decoded4b["muxSig5"].rawValue ==  -6
    assert decoded4b["muxSig6"].rawValue ==  0x18
    assert decoded4b["muxSig7"].rawValue ==  0x0C
    assert decoded4b["muxSig8"].rawValue ==  -8
    assert decoded4b["muxSig9"].rawValue ==  0x20
