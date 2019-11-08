import  canmatrix.formats.wireshark
import io
import os

def test_wireshark_frame_exists():
    db = canmatrix.CanMatrix()
    db.add_frame(canmatrix.Frame("some_frame"))
    outlua = io.BytesIO()
    canmatrix.formats.dump(db, outlua, "wireshark")

    assert 'some_frame = Proto("some_frame", "some_frame")' in outlua.getvalue().decode("utf8")


def test_wireshark_muliplexed_frame():
    here = os.path.dirname(os.path.realpath(__file__))
    db = canmatrix.formats.loadp_flat(os.path.join(here, "test_frame_decoding.dbc"))
    outlua = io.BytesIO()
    canmatrix.formats.dump(db, outlua, "wireshark")
    assert "if muxer ==" in outlua.getvalue().decode("utf8")
    assert "if muxer == 0" in outlua.getvalue().decode("utf8")
    assert "if muxer == 1" in outlua.getvalue().decode("utf8")


def test_wireshark_signal_exists():
    db = canmatrix.CanMatrix()

    db.add_frame(canmatrix.Frame("some_frame"))
    db.frame_by_name("some_frame").add_signal(canmatrix.Signal("some_signal", start_bit=3, size=11, factor=1.5, offset=42, unit="cm" ))

    outlua = io.BytesIO()
    canmatrix.formats.dump(db, outlua, "wireshark")

    assert 'my_frame_tree:add(some_frame_some_signal, reversed_pdu:bitfield(-14,11))' in outlua.getvalue().decode("utf8")
    assert 'my_frame_tree:add(some_frame_some_signal, reversed_pdu:bitfield(-14,11) - 2048)' in outlua.getvalue().decode("utf8")

def test_wireshark_get_coorect_bits_for_signal():
    frame = canmatrix.Frame("some_frame")
    sig_big_endian = canmatrix.Signal("some_signal", is_little_endian=False,  start_bit=3, size=11, factor=1.5, offset=42, unit="cm")
    sig_little_endian = canmatrix.Signal("some_signal2", is_little_endian=True, start_bit=3, size=11, factor=1.5, offset=42, unit="cm")
    frame.add_signal(sig_big_endian)
    frame.add_signal(sig_little_endian)

    assert 'pdu:bitfield(3,11)' == canmatrix.formats.wireshark.get_coorect_bits_for_signal(frame, sig_big_endian)
    assert 'reversed_pdu:bitfield(-14,11)' == canmatrix.formats.wireshark.get_coorect_bits_for_signal(frame, sig_little_endian)
    assert 'pdu:bitfield(3,3)' == canmatrix.formats.wireshark.get_coorect_bits_for_signal(frame, sig_big_endian, 3)




