# -*- coding: utf-8 -*-
import io
import textwrap
import string
import pytest

import canmatrix.formats.dbc


def test_long_signal_name_imports():
    long_signal_name = u'FAILURE_ZELL_UNTERTEMPERATUR_ENTLADEN_ALARM_IDX_01'
    assert len(long_signal_name) > 32
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 1 testFrame1: 1 TEST_ECU
     SG_ someShortenedDummyName: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    BA_ "SystemSignalLongSymbol" SG_ 1 someShortenedDummyName "{}";  
    ''').format(long_signal_name).encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc)

    assert matrix.frames[0].signals[0].name == long_signal_name
    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    long_name_found = False
    name_found = False

    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.strip().startswith("SG_"):
            assert len(line.split()[1]) <= 32
            name_found = True
        if line.strip().startswith("BA_ "):
            assert line.split()[5][1:-2] == long_signal_name
            long_name_found = True
    assert long_name_found is True
    assert name_found is True


def test_create_define():
    defaults = {}
    test_string = canmatrix.formats.dbc.create_define("my_data_type", canmatrix.Define('ENUM "A","B"'), "BA_", defaults)
    assert test_string == 'BA_DEF_ BA_ "my_data_type" ENUM "A","B";\n'


def test_create_attribute_string():
    test_string = canmatrix.formats.dbc.create_attribute_string("my_attribute", "BO_", "name", "value", True)
    assert test_string == 'BA_ "my_attribute" BO_ name "value";\n'
    test_string = canmatrix.formats.dbc.create_attribute_string("my_attribute", "BO_", "name", 1.23, False)
    assert test_string == 'BA_ "my_attribute" BO_ name 1.23;\n'


def test_create_comment_string():
    test_string = canmatrix.formats.dbc.create_comment_string("BO_", "ident", "some comment", "utf8", "utf8")
    assert test_string == b'CM_ BO_ ident "some comment";\n'


def test_long_frame_name_imports():
    long_frame_name = u'A_VERY_LONG_FRAME_NAME_WHICH_SHOULD_BE_SPLIT_SOMEHOW'
    assert len(long_frame_name) > 32
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 1 shortendeFrameName: 1 someEcu
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    BA_ "SystemMessageLongSymbol" BO_ 1 "{}";  
    ''').format(long_frame_name).encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc)
    long_name_found = False
    name_found = False

    assert matrix.frames[0].name == long_frame_name
    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.strip().startswith("BO_"):
            assert len(line.split()[2][:-1]) <= 32
            name_found = True
        if line.strip().startswith("BA_ "):
            assert line.split()[4][1:-2] == long_frame_name
            long_name_found = True
    assert long_name_found is True
    assert name_found is True


def test_long_ecu_name_imports():
    long_ecu_name = u'A_VERY_LONG_ECU_NAME_WHICH_SHOULD_BE_SPLIT_SOMEHOW'
    assert len(long_ecu_name) > 32
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BU_: SoMEShortenedEcuName
    BO_ 1 testFrame1: 1 SoMEShortenedEcuName
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    BA_ "SystemNodeLongSymbol" BU_ SoMEShortenedEcuName "{}";  
    ''').format(long_ecu_name).encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc)
    long_name_found = False
    name_found = False

    assert matrix.ecus[0].name == long_ecu_name
    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.strip().startswith("BU_"):
            assert len(line.split()[1]) <= 32
            name_found = True
        if line.strip().startswith("BA_ "):
            assert line.split()[4][1:-2] == long_ecu_name
            long_name_found = True
    assert long_name_found is True
    assert name_found is True


def test_long_envvar_name_imports():
    long_envvar_name = u'A_VERY_LONG_ENVIROMENT_NAME_WHICH_SHOULD_BE_SPLIT_SOMEHOW'
    assert len(long_envvar_name) > 32
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 1 frameName: 1 someEcu
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    EV_ someShortendEnvVar: 0 [0|0] "" 0 2 DUMMY_NODE_VECTOR0 Vector__XXX;
    
    BA_ "SystemEnvVarLongSymbol" EV_ someShortendEnvVar "{}";  
    ''').format(long_envvar_name).encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc)

    assert list(matrix.env_vars)[0] == long_envvar_name
    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    long_name_found = False
    name_found = False

    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.strip().startswith("EV_"):
            assert len(line.split()[1]) <= 32
            name_found = True
        if line.strip().startswith("BA_ "):
            assert line.split()[3][1:-2] == long_envvar_name
            long_name_found = True
    assert long_name_found is True
    assert name_found is True


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
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    assert matrix.frame_defines[u'example1'].values == ["Val 1", "", ""] + list(" '()[]/-|{};:<>.?!@#$%^&=`~")
    assert matrix.signal_defines[u'example2'].values == ['Val1', ',']
    assert matrix.ecu_defines[u'example4'].values == ['Val1', ',']


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
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frame_defines[u'example1'].values == ["Val 1", character[0]]


def test_export_of_unknown_defines():
    db = canmatrix.CanMatrix()

    db.add_frame_defines("Receivable", 'BOOL False True')
    db.add_frame_defines("Sendable", 'BOOL False True')
    for (dataType, define) in db.frame_defines.items():
        orig_definition = define.definition
        canmatrix.formats.dbc.check_define(define)
        assert orig_definition != define.definition

    db.add_signal_defines("LongName", 'STR')
    for (dataType, define) in db.signal_defines.items():
        orig_definition = define.definition
        canmatrix.formats.dbc.check_define(define)
        assert orig_definition != define.definition
    frame = canmatrix.Frame("someFrame")
    signal = canmatrix.Signal("SomeSignal")
    signal.add_attribute("LongName", "EnableCalcIDCTrip Calc. IDC trip")
    frame.add_signal(signal)
    db.add_frame(frame)

    db.add_ecu_defines("someName", 'STRING')
    for (dataType, define) in db.ecu_defines.items():
        orig_definition = define.definition
        canmatrix.formats.dbc.check_define(define)
        assert orig_definition == define.definition

    db.add_global_defines("someGlobaName", 'BOOL')
    for (dataType, define) in db.global_defines.items():
        orig_definition = define.definition
        canmatrix.formats.dbc.check_define(define)
        assert orig_definition != define.definition

    outdbc = io.BytesIO()
    canmatrix.formats.dump(db, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if line.startswith("BA_DEF_ "):
            assert line.endswith("STRING;")
        if line.startswith("BA_ "):
            assert line.endswith('";')

def test_braces_in_attributes():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 20 frameName: 1 someEcu
    SG_ sometext: 1|2@0+ (1,0) [0|0] ""  someOtherEcu
    
    BA_ "Period [ms]" BO_ 20 3000;
    BA_ "Signal Age [ms]" SG_ 20 sometext 5000;
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
