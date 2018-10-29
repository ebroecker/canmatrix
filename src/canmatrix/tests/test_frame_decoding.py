import pytest
import canmatrix.formats
import os.path


def test_decode_from_dbc():
    here = os.path.dirname(os.path.realpath(__file__))
    cm = canmatrix.formats.loadp(os.path.join(here ,"test_frame_decoding.dbc"), flatImport = True)
    # 001#8d00100100820100
    frameData1 = bytes([141, 0, 16, 1, 0, 130, 1, 0])

    # 002#0C00057003CD1F83
    frameData2 = bytes([12, 0, 5, 112, 3, 205, 31, 131])

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
