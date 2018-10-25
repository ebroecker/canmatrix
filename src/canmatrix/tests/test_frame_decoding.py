import pytest
import canmatrix.formats


def test_decode_from_dbc():
    cm = canmatrix.formats.loadp("test_frame_decoding.dbc", flatImport = True)
    # 001#8d00100100820100
    frameData1 = bytes([141, 0, 16, 1, 0, 130, 1, 0])

    # 002#0C00057003CD1F83
    frameData2 = bytes([12, 0, 5, 112, 3, 205, 31, 131])

    frame1 = cm.frameById(1)
    decoded1 = frame1.decode(frameData1)
    assert decoded1["sig0"] == 1
    assert decoded1["sig1"] == 35
    assert decoded1["sig2"] == 0
    assert decoded1["sig3"] == 2048
    assert decoded1["sig4"] == 256
    assert decoded1["sig5"] == 1
    assert decoded1["sig6"] == 0
    assert decoded1["sig7"] == 520
    assert decoded1["sig8"] == 0
    assert decoded1["sig9"] == 0
    assert decoded1["sig10"] == 0

    frame2 = cm.frameById(2)
    decoded2 = frame2.decode(frameData2)
    assert decoded2["secSig1"] == 0
    assert decoded2["secSig2"] == 0
    assert decoded2["secSig3"] == 0
    assert decoded2["secSig4"] == 2
    assert decoded2["secSig5"] == 0
    assert decoded2["secSig6"] == 0
    assert decoded2["secSig7"] == 0
    assert decoded2["secSig8"] == 3
    assert decoded2["secSig9"] == 1
    assert decoded2["secSig10"] == 1280
    assert decoded2["secSig11"] == -144
    assert decoded2["secSig12"] == 12