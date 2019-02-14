# -*- coding: utf-8 -*-
import io
import textwrap
import string
import pytest

import canmatrix.dbc



def test_long_signal_name_imports():
    long_signal_name = u'FAILURE_ZELL_UNTERTEMPERATUR_ENTLADEN_ALARM_IDX_01'
    assert len(long_signal_name) > 32
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 1 testFrame1: 1 TEST_ECU
     SG_ someShortenedDummyName: 1|2@0+ (1,0) [0|0] ""  CCL_TEST
     
    BA_ "SystemSignalLongSymbol" SG_ 1 someShortenedDummyName "{}";  
    ''').format(long_signal_name).encode('utf-8'))

    matrix = canmatrix.dbc.load(dbc)

    assert matrix.frames[0].signals[0].name == long_signal_name
    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.strip().startswith("SG_"):
            assert len(line.split()[1]) <= 32
        if line.strip().startswith("BA_ "):
            assert line.split()[5][1:-2] == long_signal_name


def test_enum_with_comma():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BA_DEF_ "example0" ENUM "Val1",",";
    BA_DEF_ BO_ "example1" ENUM "Val 1","vector_leerstring",""," ","'","(",")","[","]","/","-","|","{","}",";",":","<",">",".","?","!","@","#","$","%","^","&","=","`","~";
    BA_DEF_ SG_ "example2" ENUM "Val1",",";
    BA_DEF_ EV_ "example3" ENUM "Val1",",";
    BA_DEF_ BU_ "example4" ENUM "Val1",",";
    BA_DEF_DEF_ "example0" ",";
    BA_DEF_DEF_ "example1" ",";
    BA_DEF_DEF_ "example2" ",";
    BA_DEF_DEF_ "example3" ",";
    BA_DEF_DEF_ "example4" ",";
    ''').encode('utf-8'))
    matrix = canmatrix.dbc.load(dbc, dbcImportEncoding="utf8")

    assert matrix.frameDefines[u'example1'].values == ["Val 1","",""," ","'","(",")","[","]","/","-","|","{","}",";",":","<",">",".","?","!","@","#","$","%","^","&","=","`","~"]
    assert matrix.signalDefines[u'example2'].values == ['Val1', ',']
    assert matrix.buDefines[u'example4'].values == ['Val1', ',']

@pytest.mark.parametrize(
    'character',
    [
        ['{}'.format(c if c != '"' else '\\"')]
        for c in string.punctuation
    ],
)

def test_enum_with_special_character(character):
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BA_DEF_ BO_ "example1" ENUM "Val 1","{}";
    ''').format(character[0]).encode('utf-8'))
    matrix = canmatrix.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frameDefines[u'example1'].values == ["Val 1",character[0]]

def test_export_of_unknown_defines():
    db = canmatrix.CanMatrix()

    db.addFrameDefines("Receivable", 'BOOL False True')
    db.addFrameDefines("Sendable", 'BOOL False True')
    for (dataType, define) in db.frameDefines.items():
        orig_definition = define.definition
        canmatrix.dbc.check_define(define)
        assert orig_definition != define.definition

    db.addSignalDefines("LongName", 'STR')
    for (dataType, define) in db.signalDefines.items():
        orig_definition = define.definition
        canmatrix.dbc.check_define(define)
        assert orig_definition != define.definition

    db.addBUDefines("someName", 'STRING')
    for (dataType, define) in db.buDefines.items():
        orig_definition = define.definition
        canmatrix.dbc.check_define(define)
        assert orig_definition == define.definition

    db.addGlobalDefines("someGlobaName", 'BOOL')
    for (dataType, define) in db.globalDefines.items():
        orig_definition = define.definition
        canmatrix.dbc.check_define(define)
        assert orig_definition == define.definition

    outdbc = io.BytesIO()
    canmatrix.formats.dump(db, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.startswith("BA_DEF_ "):
            assert line.endswith("STRING;")
