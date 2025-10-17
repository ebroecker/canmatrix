# -*- coding: utf-8 -*-
import decimal

import pytest
from builtins import *

from canmatrix.CanMatrix import CanMatrix
from canmatrix.Signal import Signal
from canmatrix.Frame import Frame
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.Ecu import Ecu

@pytest.fixture
def empty_frame():
    return Frame(name="test_frame")


def test_signal_defaults_to_decimal():
    signal = Signal(
        offset=4,
        factor=2,
    )

    assert isinstance(signal.offset, decimal.Decimal)
    assert isinstance(signal.factor, decimal.Decimal)


def test_enum_defines_from_decimal():
    db = CanMatrix()
    db.add_frame_defines("test_enum", 'ENUM  "eins","zwei","drei","vier"')
    s1 = Signal('signal', size=32, is_float=True)
    f1 = Frame('frame', arbitration_id=1, size=4)
    f1.add_signal(s1)
    f1.add_attribute("test_enum", "2.00001")
    db.add_frame(f1)
    db.enum_attribs_to_values()
 

def test_arbitration_id_is_instance():
    frame1 = Frame(name = "Frame1")
    frame2 = Frame(name = "Frame1")

    frame1.arbitration_id.id = 42

    assert frame1.arbitration_id.id == 42
    assert frame2.arbitration_id.id == 0

#@pytest.mark.skip(reason="J1939 functionality is only partially implemented and currently breaks test chain")
def test_arbitration_id_j1939_direct_setters():
    arb_id = ArbitrationId(0)
    arb_id.pgn = 0xF1AA
    arb_id.j1939_source = 0x22
    arb_id.j1939_priority = 3
    assert arb_id.pgn == 0xF1AA
    assert arb_id.j1939_source == 0x22
    assert arb_id.j1939_priority == 3

def test_arbitration_id_comparators():
    id_standard_1 = ArbitrationId(id=0x1, extended=False)
    id_standard_2 = ArbitrationId(id=0x2, extended=False)
    id_extended_1 = ArbitrationId(id=0x1, extended=True)
    id_extended_2 = ArbitrationId(id=0x2, extended=True)

    sorting_results = sorted((
        id_extended_1, id_standard_2, id_extended_2, id_standard_1))
    assert sorting_results[0] == id_standard_1
    assert sorting_results[1] == id_extended_1
    assert sorting_results[2] == id_standard_2
    assert sorting_results[3] == id_extended_2

@pytest.fixture
def empty_matrix():
    return CanMatrix()


def test_canmatrix_add_attribure(empty_matrix):
    empty_matrix.add_attribute("name1", "value1")
    assert empty_matrix.attributes == {"name1": "value1"}


def test_canmatrix_get_frame_by_glob(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    f2 = Frame(name="nm_osek_esp")
    empty_matrix.add_frame(f2)
    assert empty_matrix.glob_frames("*osek*") == [f2]


def test_canmatrix_get_frame_by_name(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_name(empty_frame.name) == empty_frame


def test_canmatrix_get_frame_by_wrong_name(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_name("wrong") is None


def test_canmatrix_get_frame_by_pgn(empty_matrix, empty_frame):
    empty_frame.arbitration_id.id = 0xA123456
    empty_frame.arbitration_id.extended = True
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_pgn(0x21234) == empty_frame

def test_canmatrix_get_frame_by_wrong_pgn(empty_matrix, empty_frame):
    empty_frame.arbitration_id.id = 0xAB123456
    empty_frame.arbitration_id.extended = True
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_pgn(0xAB34) is None


def test_canmatrix_iterate_over_frames(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert [f for f in empty_matrix] == [empty_frame]


def test_canmatrix_remove_frame(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    empty_matrix.add_frame(Frame())
    empty_matrix.remove_frame(empty_frame)
    assert len(empty_matrix.frames) == 1


def test_canmatrix_rename_ecu_by_name(empty_matrix):
    ecu = Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu("old_name", "new name")
    assert ecu.name == "new name"


def test_canmatrix_rename_ecu_by_wrong_name(empty_matrix):
    ecu = Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu("wrong", "new name")
    assert ecu.name == "old_name"


def test_canmatrix_rename_ecu_check_frame(empty_matrix):
    ecu = Ecu(name="old_name")
    frame = Frame(name="test_frame")
    signal = Signal(name="test_signal")
    signal.add_receiver("old_name")
    frame.add_signal(signal)
    frame.update_receiver()
    assert "old_name" in frame.receivers
    
    empty_matrix.add_ecu(ecu)
    empty_matrix.add_frame(frame)
    empty_matrix.rename_ecu("old_name", "new_name")
    assert "old_name" not in frame.receivers
    assert "new_name" in frame.receivers

def test_canmatrix_rename_ecu_by_instance(empty_matrix):
    ecu = Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu(ecu, "new name")
    assert ecu.name == "new name"


def test_canmatrix_del_ecu_by_glob(empty_matrix):
    ecu1 = Ecu(name="ecu1")
    ecu2 = Ecu(name="ecu2")
    frame = Frame(transmitters=["ecu2", "ecu3"])
    empty_matrix.add_ecu(ecu1)
    empty_matrix.add_ecu(ecu2)
    frame.add_signal(Signal(receivers=["ecu1", "ecu2"]))
    empty_matrix.add_frame(frame)
    empty_matrix.del_ecu("*2")
    assert empty_matrix.ecus == [ecu1]
    assert frame.receivers == ["ecu1"]
    assert frame.transmitters == ["ecu3"]


def test_canmatrix_del_ecu_by_instance(empty_matrix):
    ecu1 = Ecu(name="ecu1")
    ecu2 = Ecu(name="ecu2")
    empty_matrix.add_ecu(ecu1)
    empty_matrix.add_ecu(ecu2)
    empty_matrix.del_ecu(ecu1)
    assert empty_matrix.ecus == [ecu2]


def test_canmatrix_del_obsolete_ecus(empty_matrix):
    empty_matrix.add_ecu(Ecu(name="Ecu1"))
    empty_matrix.add_ecu(Ecu(name="Ecu2"))
    frame1 = Frame(name="frame1", transmitters=["Ecu1"])
    frame1.add_signal(Signal("signal1", receivers=["Ecu2"]))
    empty_matrix.add_frame(frame1)
    empty_matrix.delete_obsolete_ecus()
    assert "Ecu1" in [ecu.name for ecu in empty_matrix.ecus]
    assert "Ecu2" in [ecu.name for ecu in empty_matrix.ecus]
    frame1.del_transmitter("Ecu1")
    empty_matrix.delete_obsolete_ecus()
    assert "Ecu1" not in [ecu.name for ecu in empty_matrix.ecus]
    assert "Ecu2" in [ecu.name for ecu in empty_matrix.ecus]


def test_canmatrix_rename_frame_by_name(empty_matrix):
    f = Frame(name="F1")
    empty_matrix.add_frame(f)
    empty_matrix.rename_frame("F1", "F2")
    assert f.name == "F2"
    empty_matrix.rename_frame("X*", "G")
    assert f.name == "F2"
    empty_matrix.rename_frame("F*", "G")
    assert f.name == "G2"
    empty_matrix.rename_frame("*0", "9")
    assert f.name == "G2"
    empty_matrix.rename_frame("*2", "9")
    assert f.name == "G9"


def test_canmatrix_rename_frame_by_instance(empty_matrix):
    f = Frame(name="F1")
    empty_matrix.add_frame(f)
    empty_matrix.rename_frame(f, "F2")
    assert f.name == "F2"


def test_canmatrix_del_frame_by_name(empty_matrix):
    f1 = Frame(name="F1")
    f2 = Frame(name="F2")
    empty_matrix.add_frame(f1)
    empty_matrix.add_frame(f2)
    empty_matrix.del_frame("F1")
    empty_matrix.del_frame("bad_one")
    assert empty_matrix.frames == [f2]


def test_canmatrix_del_frame_by_instance(empty_matrix):
    f1 = Frame(name="F1")
    f2 = Frame(name="F2")
    empty_matrix.add_frame(f1)
    empty_matrix.add_frame(f2)
    empty_matrix.del_frame(f1)
    assert empty_matrix.frames == [f2]

def test_effective_cycle_time():
    frame = Frame()
    sig1 = Signal(name = "s1", cycle_time=1)
    sig2 = Signal(name = "s2", cycle_time=0)
    frame.add_signal(sig1)
    frame.add_signal(sig2)
    assert frame.effective_cycle_time == 1

    sig2.cycle_time = 2
    assert frame.effective_cycle_time == 1

    sig1.cycle_time = 4
    assert frame.effective_cycle_time == 2

    sig1.cycle_time = 3
    assert frame.effective_cycle_time == 1

    frame.cycle_time = 1
    assert frame.effective_cycle_time == 1

    frame.cycle_time = 0
    sig1.cycle_time = 0
    sig2.cycle_time = 0
    assert frame.effective_cycle_time == 0

def test_baudrate():
    cm = CanMatrix()
    cm.baudrate = 500000
    assert cm.baudrate == 500000
    cm.fd_baudrate = 1000000
    assert cm.fd_baudrate == 1000000

def test_frame_compress():
    frame = Frame("my_frame", size=8)
    frame.add_signal(Signal(name = "Sig1", start_bit = 2, size = 13, is_little_endian=False ))
    frame.add_signal(Signal(name = "Sig2", start_bit = 17, size = 14, is_little_endian=False))
    frame.add_signal(Signal(name = "Sig3", start_bit = 35, size = 6, is_little_endian=False))
    frame.add_signal(Signal(name = "Sig4", start_bit = 49, size = 8, is_little_endian=False))
    frame.compress()
    assert frame.signal_by_name("Sig1").start_bit == 0
    assert frame.signal_by_name("Sig2").start_bit == 13
    assert frame.signal_by_name("Sig3").start_bit == 27
    assert frame.signal_by_name("Sig4").start_bit == 33

    frame = Frame("my_frame", size=8)
    # some signals overlap!
    frame.add_signal(Signal(name = "Sig1", start_bit = 12, size = 12, is_little_endian=True))
    frame.add_signal(Signal(name = "Sig2", start_bit = 17, size = 9, is_little_endian=True))
    frame.add_signal(Signal(name = "Sig3", start_bit = 33, size = 5, is_little_endian=True))
    frame.add_signal(Signal(name = "Sig4", start_bit = 48, size = 9, is_little_endian=True))
    frame.compress()
    assert frame.signal_by_name("Sig1").start_bit == 0
    assert frame.signal_by_name("Sig2").start_bit == 12
    assert frame.signal_by_name("Sig3").start_bit == 21
    assert frame.signal_by_name("Sig4").start_bit == 26
