import io
import os.path
import textwrap

import attr
import canmatrix.formats


def load_dbc():
    here = os.path.dirname(os.path.realpath(__file__))
    return canmatrix.formats.loadp_flat(os.path.join(here, "test_frame_decoding.dbc"))


def test_encode_with_dbc_big_endian():
    cm = load_dbc()
    # 002#0C00057003CD1F83
    frame = cm.frame_by_id(canmatrix.ArbitrationId(1))

    to_encode = dict()

    to_encode["sig0"] = 1
    to_encode["sig1"] = 35
    to_encode["sig2"] = 0
    to_encode["sig3"] = 2048
    to_encode["sig4"] = 256
    to_encode["sig5"] = 1
    to_encode["sig6"] = 0
    to_encode["sig7"] = 520
    to_encode["sig8"] = 0
    to_encode["sig9"] = 0
    to_encode["sig10"] = 0

    frame_data = frame.encode(to_encode)
    assert frame_data == bytearray([141, 0, 16, 1, 0, 130, 1, 0])


def test_encode_with_dbc_little_endian():
    cm = load_dbc()
    # 002#0C00057003CD1F83
    frame = cm.frame_by_id(canmatrix.ArbitrationId(2))

    to_encode = dict()
    to_encode["secSig1"] = 0
    to_encode["secSig2"] = 0
    to_encode["secSig3"] = 0
    to_encode["secSig4"] = 2
    to_encode["secSig5"] = 0
    to_encode["secSig6"] = 0
    to_encode["secSig7"] = 0
    to_encode["secSig8"] = 3
    to_encode["secSig9"] = 1
    to_encode["secSig10"] = 1280
    to_encode["secSig11"] = -144
    to_encode["secSig12"] = 12

    frame_data = frame.encode(to_encode)
    assert frame_data == bytearray([0x0c, 0x00, 0x05, 0x70, 0x03, 0x00, 0x10, 0x83])


def test_encode_with_dbc_float():
    cm = load_dbc()
    # 003#38638A7E58A8C540
    frame = cm.frame_by_id(canmatrix.ArbitrationId(3))

    to_encode = dict()
    to_encode["floatSignal1"] = 5.424999835668132e-05
    to_encode["floatSignal2"] = 6.176799774169922
    frame_data = frame.encode(to_encode)
    assert frame_data == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x58, 0xA8, 0xC5, 0x40])


def test_encode_with_dbc_multiplex():
    cm = load_dbc()

    frame = cm.frame_by_id(canmatrix.ArbitrationId(4))
    to_encode1 = dict()
    to_encode1["myMuxer"] = 0
    to_encode1["muxSig9"] = 0x20
    to_encode1["muxSig1"] = 0x38
    to_encode1["muxSig2"] = 0x63
    to_encode1["muxSig3"] = 0x8A
    to_encode1["muxSig4"] = 0x3F

    frame_data1 = frame.encode(to_encode1)
    assert frame_data1 == bytearray([0x38, 0x63, 0x8A, 0x7E, 0x00, 0x20, 0x00])

    to_encode2 = dict()
    to_encode2["myMuxer"] = 1
    to_encode2["muxSig9"] = 0x20
    to_encode2["muxSig5"] = -6
    to_encode2["muxSig6"] = 0x18
    to_encode2["muxSig7"] = 0x0C
    to_encode2["muxSig8"] = -8
    frame_data2 = frame.encode(to_encode2)
    assert frame_data2 == bytearray([0x38, 0x60, 0x80, 0x1E, 0x18, 0x20, 0x20])


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

    matrix = canmatrix.formats.load_flat(f, import_type='sym')
    unsigned_frame = matrix.frame_by_name('Unsigned')
    signed_frame = matrix.frame_by_name('Signed')

    @attr.s(frozen=True)
    class TestFrame(object):
        two_bit_big_endian = attr.ib(default=0)
        two_bit_little_endian = attr.ib(default=0)
        seven_bit_big_endian = attr.ib(default=0)
        seven_bit_little_endian = attr.ib(default=0)
        eleven_bit_big_endian = attr.ib(default=0)
        eleven_bit_little_endian = attr.ib(default=0)

        def encode(self, frame_to_encode):
            return frame_to_encode.encode(attr.asdict(self))

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
