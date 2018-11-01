import pytest
import canmatrix.formats
import os.path

def loadDbc():
    here = os.path.dirname(os.path.realpath(__file__))
    return canmatrix.formats.loadp(os.path.join(here ,"test_frame_decoding.dbc"), flatImport = True)

def test_decode_with_dbc_big_endian():
    cm = loadDbc()
    # 001#8d00100100820100
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

def test_decode_with_dbc_little_endian():
    cm = loadDbc()
    # 002#0C00057003001F83
    frameData = bytearray([12, 0, 5, 112, 3, 0, 31, 131])
    frame = cm.frameById(2)
    decoded = frame.decode(frameData)
    assert decoded["secSig1"].rawValue == 0
    assert decoded["secSig2"].rawValue == 0
    assert decoded["secSig3"].rawValue == 0
    assert decoded["secSig4"].rawValue == 2
    assert decoded["secSig5"].rawValue == 0
    assert decoded["secSig6"].rawValue == 0
    assert decoded["secSig7"].rawValue == 0
    assert decoded["secSig8"].rawValue == 3
    assert decoded["secSig9"].rawValue == 1
    assert decoded["secSig10"].rawValue == 1280
    assert decoded["secSig11"].rawValue == -144
    assert decoded["secSig12"].rawValue == 12

def test_decode_with_dbc_float():
    cm = loadDbc()
    # 003#38638A7E58A8C540
    frameData = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])
    frame = cm.frameById(3)
    decoded = frame.decode(frameData)
    assert decoded["floatSignal1"].rawValue == 5.424999835668132e-05
    assert decoded["floatSignal2"].rawValue ==  6.176799774169922


def test_decode_with_dbc_multiplex():
    cm = loadDbc()
    frameData1 = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00])
    frame = cm.frameById(4)
    decoded1 = frame.decode(frameData1)
    assert decoded1["myMuxer"].rawValue == 0
    assert decoded1["muxSig9"].rawValue ==  0x20
    assert decoded1["muxSig1"].rawValue == 0x38
    assert decoded1["muxSig2"].rawValue == 0x63
    assert decoded1["muxSig3"].rawValue == 0x8A
    assert decoded1["muxSig4"].rawValue == 0x3F
    assert decoded1["muxSig9"].rawValue == 0x20

    frameData2 = bytearray([0x38, 0x63, 0x8A, 0x1E, 0x18, 0x20, 0x20])
    decoded2 = frame.decode(frameData2)
    assert decoded2["myMuxer"].rawValue == 1
    assert decoded2["muxSig9"].rawValue == 0x20
    assert decoded2["muxSig5"].rawValue ==  -6
    assert decoded2["muxSig6"].rawValue ==  0x18
    assert decoded2["muxSig7"].rawValue ==  0x0C
    assert decoded2["muxSig8"].rawValue ==  -8
    assert decoded2["muxSig9"].rawValue ==  0x20
