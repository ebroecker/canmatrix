import pytest
import canmatrix.formats
import os.path
import textwrap
import io

def load_dbc():
    here = os.path.dirname(os.path.realpath(__file__))
    return canmatrix.formats.loadp_flat(os.path.join(here, "test_frame_decoding.dbc"))


def test_decode_with_dbc_big_endian():
    cm = load_dbc()
    # 001#8d00100100820100
    frame_data_1 = bytearray([141, 0, 16, 1, 0, 130, 1, 0])

    frame1 = cm.frame_by_id(canmatrix.ArbitrationId(1))
    decoded1 = frame1.decode(frame_data_1)
    assert decoded1["sig0"].raw_value == 1
    assert decoded1["sig1"].raw_value == 35
    assert decoded1["sig2"].raw_value == 0
    assert decoded1["sig3"].raw_value == 2048
    assert decoded1["sig4"].raw_value == 256
    assert decoded1["sig5"].raw_value == 1
    assert decoded1["sig6"].raw_value == 0
    assert decoded1["sig7"].raw_value == 520
    assert decoded1["sig8"].raw_value == 0
    assert decoded1["sig9"].raw_value == 0
    assert decoded1["sig10"].raw_value == 0


def test_decode_with_dbc_little_endian():
    cm = load_dbc()
    # 002#0C00057003001F83
    frame_data = bytearray([12, 0, 5, 112, 3, 0, 31, 131])
    frame = cm.frame_by_id(canmatrix.ArbitrationId(2))
    decoded = frame.decode(frame_data)
    assert decoded["secSig1"].raw_value == 0
    assert decoded["secSig2"].raw_value == 0
    assert decoded["secSig3"].raw_value == 0
    assert decoded["secSig4"].raw_value == 2
    assert decoded["secSig5"].raw_value == 0
    assert decoded["secSig6"].raw_value == 0
    assert decoded["secSig7"].raw_value == 0
    assert decoded["secSig8"].raw_value == 3
    assert decoded["secSig9"].raw_value == 1
    assert decoded["secSig10"].raw_value == 1280
    assert decoded["secSig11"].raw_value == -144
    assert decoded["secSig12"].raw_value == 12


def test_decode_with_too_little_dlc():
    cm = load_dbc()
    # 002#0C00057003001F83
    frame_data = bytearray([12, 0, 5, 112, 3, 0, 31])
    frame = cm.frame_by_id(canmatrix.ArbitrationId(2))
    with pytest.raises(canmatrix.DecodingFrameLength):
        frame.decode(frame_data)


def test_decode_with_too_big_dlc():
    cm = load_dbc()
    frame_data1 = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00, 0x00])
    frame = cm.frame_by_id(canmatrix.ArbitrationId(4))
    with pytest.raises(canmatrix.DecodingFrameLength):
        frame.decode(frame_data1)


def test_decode_with_dbc_float():
    cm = load_dbc()
    # 003#38638A7E58A8C540
    frame_data = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])
    frame = cm.frame_by_id(canmatrix.ArbitrationId(3))
    decoded = frame.decode(frame_data)
    assert decoded["floatSignal1"].raw_value == 5.424999835668132e-05
    assert decoded["floatSignal2"].raw_value == 6.176799774169922


def test_decode_with_dbc_multiplex():
    cm = load_dbc()
    frame_data1 = bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00])
    frame = cm.frame_by_id(canmatrix.ArbitrationId(4))
    decoded1 = frame.decode(frame_data1)
    assert decoded1["myMuxer"].raw_value == 0
    assert decoded1["muxSig9"].raw_value == 0x20
    assert decoded1["muxSig1"].raw_value == 0x38
    assert decoded1["muxSig2"].raw_value == 0x63
    assert decoded1["muxSig3"].raw_value == 0x8A
    assert decoded1["muxSig4"].raw_value == 0x3F
    assert decoded1["muxSig9"].raw_value == 0x20

    frame_data2 = bytearray([0x38, 0x63, 0x8A, 0x1E, 0x18, 0x20, 0x20])
    decoded2 = frame.decode(frame_data2)
    assert decoded2["myMuxer"].raw_value == 1
    assert decoded2["muxSig9"].raw_value == 0x20
    assert decoded2["muxSig5"].raw_value == -6
    assert decoded2["muxSig6"].raw_value == 0x18
    assert decoded2["muxSig7"].raw_value == 0x0C
    assert decoded2["muxSig8"].raw_value == -8
    assert decoded2["muxSig9"].raw_value == 0x20

def test_decode_complex_multiplexed():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 2024 OBD2: 8 Vector__XXX
    SG_ ParameterID_Service01 m1M : 23|8@0+ (1,0) [0|0] "" Vector__XXX
    SG_ Vehicle_speed m13 : 31|8@0+ (1,0) [0|0] "" Vector__XXX
    SG_ service M : 11|4@0+ (1,0) [0|0] "" Vector__XXX
    SG_ MAF_air_flow_rate m16 : 31|16@0+ (0.01,0) [0|0] "grams/sec" Vector__XXX
 
    SG_MUL_VAL_ 2024 ParameterID_Service01 service 1-1;
    SG_MUL_VAL_ 2024 Vehicle_speed ParameterID_Service01 13-13;
    SG_MUL_VAL_ 2024 MAF_air_flow_rate ParameterID_Service01 16-16;
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    decoded = matrix.decode(canmatrix.ArbitrationId(2024),bytearray([0x03,0x41,0x0d,0x00,0xaa,0xaa,0xaa,0xaa]))
    assert decoded["Vehicle_speed"].raw_value == 0
    assert "MAF_air_flow_rate" not in decoded
