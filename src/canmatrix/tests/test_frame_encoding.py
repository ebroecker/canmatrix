import io
import os.path
import textwrap

import attr
import pytest
import canmatrix.formats


def loadDbc():
    here = os.path.dirname(os.path.realpath(__file__))
    return canmatrix.formats.loadp(os.path.join(here ,"test_frame_decoding.dbc"), flatImport = True)


def test_encode_with_dbc_big_endian():
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
    assert frameData == bytearray([0x0c, 0x00, 0x05, 0x70, 0x03, 0x00, 0x10, 0x83])


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

    frameData1 = frame.encode(toEncode1)
    assert frameData1 == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00])

    toEncode2 = dict()
    toEncode2["myMuxer"] = 1
    toEncode2["muxSig9"] = 0x20
    toEncode2["muxSig5"] =  -6
    toEncode2["muxSig6"] =  0x18
    toEncode2["muxSig7"] =  0x0C
    toEncode2["muxSig8"] =  -8
    frameData2 = frame.encode(toEncode2)
    assert frameData2 == bytearray([0x38, 0x60, 0x80, 0x1E, 0x18, 0x20, 0x20])


def test_sym():
    """Test signal and frame encoding based on a .sym file

    The symbol file was created using the PCAN Symbol Editor.  The reference
    transmissions were created using PCAN Explorer.  The result message bytes
    were observed in PCAN-View.

    PCAN Symbol Editor v3.1.6.342
    PCAN Explorer v5.3.4.823
    PCAN-View v4.2.1.533
    """
    s = textwrap.dedent(
        u'''\
        FormatVersion=5.0 // Do not edit this line!
        Title="Untitled"

        {SENDRECEIVE}

        [Unsigned]
        ID=000h
        DLC=7
        Var=two_bit_big_endian unsigned 33,2 -m
        Var=two_bit_little_endian unsigned 30,2
        Var=seven_bit_big_endian unsigned 4,7 -m
        Var=seven_bit_little_endian unsigned 5,7
        Var=eleven_bit_big_endian unsigned 35,11 -m
        Var=eleven_bit_little_endian unsigned 18,11

        [Signed]
        ID=001h
        DLC=7
        Var=two_bit_big_endian signed 33,2 -m
        Var=two_bit_little_endian signed 30,2
        Var=seven_bit_big_endian signed 4,7 -m
        Var=seven_bit_little_endian signed 5,7
        Var=eleven_bit_big_endian signed 35,11 -m
        Var=eleven_bit_little_endian signed 18,11
        ''',
    )
    f = io.BytesIO(s.encode('utf-8'))

    matrix = canmatrix.formats.load(f, importType='sym', flatImport=True)
    unsigned_frame = matrix.frameByName('Unsigned')
    signed_frame = matrix.frameByName('Signed')

    @attr.s(frozen=True)
    class TestFrame(object):
        two_bit_big_endian = attr.ib(default=0)
        two_bit_little_endian = attr.ib(default=0)
        seven_bit_big_endian = attr.ib(default=0)
        seven_bit_little_endian = attr.ib(default=0)
        eleven_bit_big_endian = attr.ib(default=0)
        eleven_bit_little_endian = attr.ib(default=0)

        def encode(self, frame):
            return frame.encode(attr.asdict(self))

    unsigned_cases = {
        TestFrame(): b'\x00\x00\x00\x00\x00\x00\x00',
        TestFrame(two_bit_big_endian=1): b'\x00\x00\x00\x00\x20\x00\x00',
        TestFrame(two_bit_big_endian=2): b'\x00\x00\x00\x00\x40\x00\x00',
        TestFrame(two_bit_little_endian=1): b'\x00\x00\x00\x40\x00\x00\x00',
        TestFrame(two_bit_little_endian=2): b'\x00\x00\x00\x80\x00\x00\x00',
        TestFrame(seven_bit_big_endian=1): b'\x00\x20\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_big_endian=64): b'\x08\x00\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_little_endian=1): b'\x20\x00\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_little_endian=64): b'\x00\x08\x00\x00\x00\x00\x00',
        TestFrame(eleven_bit_big_endian=1): b'\x00\x00\x00\x00\x00\x04\x00',
        TestFrame(eleven_bit_big_endian=1024): b'\x00\x00\x00\x00\x10\x00\x00',
        TestFrame(eleven_bit_little_endian=1): b'\x00\x00\x04\x00\x00\x00\x00',
        TestFrame(eleven_bit_little_endian=1024): (
            b'\x00\x00\x00\x10\x00\x00\x00'
        ),
    }

    signed_cases = {
        TestFrame(): b'\x00\x00\x00\x00\x00\x00\x00',
        TestFrame(two_bit_big_endian=1): b'\x00\x00\x00\x00\x20\x00\x00',
        TestFrame(two_bit_big_endian=-2): b'\x00\x00\x00\x00\x40\x00\x00',
        TestFrame(two_bit_little_endian=1): b'\x00\x00\x00\x40\x00\x00\x00',
        TestFrame(two_bit_little_endian=-2): b'\x00\x00\x00\x80\x00\x00\x00',
        TestFrame(seven_bit_big_endian=1): b'\x00\x20\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_big_endian=-2): b'\x0F\xC0\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_little_endian=1): b'\x20\x00\x00\x00\x00\x00\x00',
        TestFrame(seven_bit_little_endian=-2): b'\xC0\x0F\x00\x00\x00\x00\x00',
        TestFrame(eleven_bit_big_endian=1): b'\x00\x00\x00\x00\x00\x04\x00',
        TestFrame(eleven_bit_big_endian=-2): b'\x00\x00\x00\x00\x1F\xF8\x00',
        TestFrame(eleven_bit_little_endian=1): b'\x00\x00\x04\x00\x00\x00\x00',
        TestFrame(eleven_bit_little_endian=-2): (
            b'\x00\x00\xF8\x1F\x00\x00\x00'
        ),
    }

    def h(b):
        return ' '.join('{:02X}'.format(c) for c in b)

    frame_case_pairs = (
        (unsigned_frame, unsigned_cases),
        (signed_frame, signed_cases),
    )
    for frame, cases in frame_case_pairs:
        for test_frame, expected in cases.items():
            expected = bytearray(expected)
            encoded = test_frame.encode(frame)
            print(test_frame)
            print(h(encoded))
            print(h(expected))
            assert encoded == expected
