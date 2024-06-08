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
