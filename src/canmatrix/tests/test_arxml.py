# -*- coding: utf-8 -*-
import canmatrix.formats.arxml
import pathlib2
import io
import textwrap

def test_ecu_extract():
    here = pathlib2.Path(__file__).parent
    
    db = canmatrix.formats.arxml.load(str(here / "MyECU.ecuc.arxml"))['']
    assert db.frames is not None
    assert len(db.frames) == 2
    assert len(db.frames[0].signals) == 3
    assert len(db.frames[1].signals) == 1


def test_get_signals_from_container_i_pdu():
    here = pathlib2.Path(__file__).parent
    matrix = canmatrix.formats.arxml.load(str(here / "ARXMLContainerTest.arxml"))
    assert matrix["New_CanCluster"].frames[0].signals[0].name == 'Header_ID'
    assert matrix["New_CanCluster"].frames[0].signals[1].name == 'Header_DLC'
    assert matrix["New_CanCluster"].frames[0].signals[2].name == 'PDU_Contained_1_Signal1_905db81da40081cb'
    assert matrix["New_CanCluster"].frames[0].signalGroups[0].signals[0].name == 'PDU_Contained_1_Signal1_905db81da40081cb'

def test_get_signals_from_secured_pdu():
    here = pathlib2.Path(__file__).parent
    matrix = canmatrix.formats.arxml.load(str(here / "ARXMLSecuredPDUTest.arxml"))
    assert matrix["CAN"].frames[0].signals[0].name == 'someTestSignal'
    assert matrix["CAN"].frames[0].signals[1].name == 'Signal'

def test_min_max():
    here = pathlib2.Path(__file__).parent
    matrix = canmatrix.formats.arxml.load(str(here / "ARXML_min_max.arxml"))
    assert matrix["New_CanCluster"].frames[0].signals[0].is_signed == False