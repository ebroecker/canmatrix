import pytest
import canmatrix.formats
import os.path

def loadDbc():
    here = os.path.dirname(os.path.realpath(__file__))
    return canmatrix.formats.loadp(os.path.join(here ,"test_frame_decoding.dbc"), flatImport = True)


def test_decode_with_dbc_little_endian():
    cm = loadDbc()
    # 002#0C00057003CD1F83
    frame = cm.frameById(1)

    toEncode = dict()

    toEncode["sig0"] = 1
    toEncode["sig1"] = 35
    toEncode["sig2"] = 0
    toEncode["sig3"] = 2048
    toEncode["sig4"] = 256
    toEncode["sig5"] = 1
    toEncode["sig6"] = 0
    toEncode["sig7"] = 520
    toEncode["sig8"] = 0
    toEncode["sig9"] = 0
    toEncode["sig10"] = 0


    frameData = frame.encode(toEncode)
    assert frameData == bytearray([141, 0, 16, 1, 0, 130, 1, 0])

def test_encode_with_dbc_little_endian():
    cm = loadDbc()
    # 002#0C00057003CD1F83
    frame = cm.frameById(2)

    toEncode = dict()
    toEncode["secSig1"] = 0
    toEncode["secSig2"] = 0
    toEncode["secSig3"] = 0
    toEncode["secSig4"] = 2
    toEncode["secSig5"] = 0
    toEncode["secSig6"] = 0
    toEncode["secSig7"] = 0
    toEncode["secSig8"] = 3
    toEncode["secSig9"] = 1
    toEncode["secSig10"] = 1280
    toEncode["secSig11"] = -144
    toEncode["secSig12"] = 12

    frameData = frame.encode(toEncode)
    assert frameData == bytearray([12, 0, 5, 112, 3, 205, 31, 131])


def test_encode_with_dbc_float():
    cm = loadDbc()
    # 003#38638A7E58A8C540
    frame = cm.frameById(3)

    toEncode = dict()
    toEncode["floatSignal1"] = 5.424999835668132e-05
    toEncode["floatSignal2"] =  6.176799774169922
    frameData = frame.encode(toEncode)
    assert frameData == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])

def test_encode_with_dbc_multiplex():
    cm = loadDbc()

    frame = cm.frameById(4)
    toEncode1 = dict()
    toEncode1["myMuxer"] = 0
    toEncode1["muxSig9"] =  0x20
    toEncode1["muxSig1"] = 0x38
    toEncode1["muxSig2"] = 0x63
    toEncode1["muxSig3"] = 0x8A
    toEncode1["muxSig4"] = 0x3F
    toEncode1["muxSig9"] = 0x20

    frameData1 = frame.encode(toEncode1)
    assert frameData1 == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00])

    toEncode2 = dict()
    toEncode2["myMuxer"] = 1
    toEncode2["muxSig9"] = 0x20
    toEncode2["muxSig5"] =  -6
    toEncode2["muxSig6"] =  0x18
    toEncode2["muxSig7"] =  0x0C
    toEncode2["muxSig8"] =  -8
    toEncode2["muxSig9"] =  0x20
    frameData2 = frame.encode(toEncode2)
    assert frameData2 == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x18, 0x20, 0x20])
