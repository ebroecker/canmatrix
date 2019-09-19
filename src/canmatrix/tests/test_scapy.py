import  canmatrix.formats.scapy
import io
import os

def test_scapy_frame_exists():
    db = canmatrix.CanMatrix()
    db.add_frame(canmatrix.Frame("some_frame"))
    outscapy = io.BytesIO()
    canmatrix.formats.dump(db, outscapy, "scapy")

    assert "class some_frame(SignalPacket):" in outscapy.getvalue().decode("utf8")


def test_scapy_muliplexed_frame():
    here = os.path.dirname(os.path.realpath(__file__))
    db = canmatrix.formats.loadp_flat(os.path.join(here, "test_frame_decoding.dbc"))
    outscapy = io.BytesIO()
    canmatrix.formats.dump(db, outscapy, "scapy")
    assert "ConditionalField" in outscapy.getvalue().decode("utf8")
    assert "myMuxer == 0" in outscapy.getvalue().decode("utf8")
    assert "myMuxer == 1" in outscapy.getvalue().decode("utf8")


def test_scapy_signal_exists():
    db = canmatrix.CanMatrix()

    db.add_frame(canmatrix.Frame("some_frame"))
    db.frame_by_name("some_frame").add_signal(canmatrix.Signal("some_signal", start_bit=3, size=11, factor=1.5, offset=42, unit="cm" ))

    outscapy = io.BytesIO()
    canmatrix.formats.dump(db, outscapy, "scapy")
    assert 'SignalField("some_signal", default=0, start=3, size=11, scaling=1.5, offset=42, unit="cm", fmt="<b")' in outscapy.getvalue().decode("utf8")

def test_scapy_get_fmt():
    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=True, is_float=True, is_signed=True)) == "<f"
    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=True, is_float=True, is_signed=False)) == "<f"

    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=True, is_float=False, is_signed=False)) == "<B"
    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=True, is_float=False, is_signed=True)) == "<b"

    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=False, is_float=True, is_signed=True)) == ">f"
    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=False, is_float=True, is_signed=False)) == ">f"

    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=False, is_float=False, is_signed=False)) == ">B"
    assert canmatrix.formats.scapy.get_fmt(canmatrix.Signal(is_little_endian=False, is_float=False, is_signed=True)) == ">b"


