# -*- coding: utf-8 -*-
import canmatrix.formats.arxml
import decimal

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


def test_ecu_extract():
    test_file = "tests/files/arxml/MyECU.ecuc.arxml"
    db = canmatrix.formats.arxml.load(test_file)['']
    assert db.frames is not None
    assert len(db.frames) == 2
    assert len(db.frames[0].signals) == 3
    assert len(db.frames[1].signals) == 1


def test_get_signals_from_container_i_pdu():
    test_file = "tests/files/arxml/ARXMLContainerTest.arxml"
    matrix = canmatrix.formats.arxml.load(test_file)
    assert matrix["New_CanCluster"].frames[0].signals[0].name == 'Header_ID'
    assert matrix["New_CanCluster"].frames[0].signals[1].name == 'Header_DLC'
    assert matrix["New_CanCluster"].frames[0].pdus[0].name == 'PDU_Contained_1'
    assert matrix["New_CanCluster"].frames[0].pdus[0].signals[0].name == 'PDU_Contained_1_Signal1'
    assert matrix["New_CanCluster"].frames[0].pdus[0].signals[0].attributes["SysSignalName"] == 'PDU_Contained_1_Signal1_905db81da40081cb'


def test_get_signals_from_secured_pdu():
    test_file = "tests/files/arxml/ARXMLSecuredPDUTest.arxml"
    matrix = canmatrix.formats.arxml.load(test_file)
    assert matrix["CAN"].frames[0].signals[0].name == 'someTestSignal'
    assert matrix["CAN"].frames[0].signals[1].name == 'Signal'


def test_min_max():
    test_file = "tests/files/arxml/ARXML_min_max.arxml"
    matrix = canmatrix.formats.arxml.load(test_file)
    assert matrix["New_CanCluster"].frames[0].signals[0].is_signed is False


def test_signal_group_system_name():
    """group name = I-SIGNAL-GROUP short name, sys_name = SHORT-NAME of the
    referenced SYSTEM-SIGNAL-GROUP; both must survive a re-export (#777)."""
    matrix = canmatrix.formats.arxml.load("tests/files/arxml/ARXMLSignalGroupTest.arxml")
    frames = [f for cluster in matrix.values() for f in cluster.frames]
    frame = [f for f in frames if f.name == "FRAME_testFrame1"][0]
    assert len(frame.signalGroups) == 1
    group = frame.signalGroups[0]
    assert group.name == "SIGGRP_auto"
    assert group.sys_name == "SIGGRP_system"
    assert len(group.signals) == 2

    # roundtrip: re-export keeps both names
    import io
    out = io.BytesIO()
    canmatrix.formats.dump(dict(matrix), out, "arxml")
    text = out.getvalue()
    assert b"SIGGRP_auto" in text
    assert b"SIGGRP_system" in text
    assert b"/Signal/SIGGRP_system" in text


def test_decode_compu_method_1():
    test_file = "tests/files/arxml/ARXMLCompuMethod1.arxml"
    ea = canmatrix.formats.arxml.Earxml()
    ea.open(test_file)
    compu_method = ea.find("COMPU-METHOD")
    # default_float_factory = decimal.Decimal
    values, factor, offset, unit, const = canmatrix.formats.arxml.decode_compu_method(compu_method, ea, float)
    assert values == {'0': 'no trailer detected', '1': 'trailer detected'}
    assert factor == 42
    assert offset == 17


def test_arxml_3_roundtrip():
    """dbc -> arxml 3.2.3 -> dbc must keep all frames (#813).

    AUTOSAR 3.x uses the generic PHYSICAL-CHANNEL element (CAN-PHYSICAL-CHANNEL
    exists only since AUTOSAR 4.x); the importer has to look for both.
    """
    import io

    with open("tests/files/dbc/test_frame_decoding.dbc", "rb") as dbc_file:
        db_source = canmatrix.formats.load(dbc_file, "dbc")
    out = io.BytesIO()
    canmatrix.formats.dump(db_source, out, "arxml", arVersion="3.2.3")

    matrix = canmatrix.formats.loads(out.getvalue(), "arxml")
    frames = {frame.name: frame for cluster in matrix.values() for frame in cluster.frames}
    assert len(frames) == 4
    assert "FRAME_testFrame1" in frames
    assert "FRAME_testFrame2" in frames
    assert "FRAME_testFrameFloat" in frames
    assert "FRAME_muxTestFrame" in frames
    assert frames["FRAME_testFrame1"].arbitration_id.id == 1
    assert frames["FRAME_testFrame2"].arbitration_id.id == 2
