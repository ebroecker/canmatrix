# -*- coding: utf-8 -*-
import io
import textwrap
import string
import pytest
import decimal
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
    test_string = canmatrix.formats.dbc.create_comment_string("BO_", "ident", "some comment", "utf8", "utf8", "")
    assert test_string == b'CM_ BO_ ident "some comment";\n'

def test_parse_comment_from_dbc():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 1 someFrame: 1 someEcu
         SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

        CM_ SG_ 1 someSignal "resistance setting (0-100%)" ; 
        ''').encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc)
    assert matrix.frames[0].signals[0].comment == "resistance setting (0-100%)"

def test_parse_multi_line_comment():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 1 someFrame: 1 someEcu
         SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

        CM_ SG_ 1 someSignal "Debug request message from the ECU to the BMS.
** ignore for now, more definition to be provided in Rev 14 regarding which messages to change if we have this debug flag implemented. " ;
        ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc)
    assert matrix.frames[0].signals[0].comment == 'Debug request message from the ECU to the BMS.\n** ignore for now, more definition to be provided in Rev 14 regarding which messages to change if we have this debug flag implemented. '


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
    
    BA_ "Signal Age [ms]" SG_ 20 sometext 5000;
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

def test_defines_with_spaces():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BU_: someOtherEcu

    BO_ 123 someFrame: 1 someOtherEcu

    EV_ someEnvVar: 0 [0|0] "" 0 2 DUMMY_NODE_VECTOR0 Vector__XXX;

    BA_DEF_ BU_ "Node Address" INT 0 255;
    BA_DEF_ BO_ "Period [ms]" INT 0 5000;
    BA_DEF_ BU_ "Description X" STRING;
    BA_DEF_ EV_ "some attrib" STRING;
    BA_ "Node Address" BU_ someOtherEcu 42;
    BA_ "Description X" BU_ someOtherEcu "Some Some Text";
    BA_ "Period [ms]" BO_ 123 3000;
    BA_ "some attrib" EV_ someEnvVar "some space";
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.ecu_defines["Node Address"].type == "INT"
    assert matrix.ecu_defines["Node Address"].min == 0
    assert matrix.ecu_defines["Node Address"].max == 255
    assert matrix.frame_defines["Period [ms]"].min == 0
    assert matrix.frame_defines["Period [ms]"].max == 5000
    assert matrix.frames[0].attributes["Period [ms]"] == '3000'
    assert matrix.env_vars["someEnvVar"]["attributes"]["some attrib"] == '"some space"'
    assert matrix.ecus[0].attributes["Description X"] == "Some Some Text"

def test_writing_complex_multiplex():
    db = canmatrix.CanMatrix()
    frame = canmatrix.Frame("someFrame")
    frame.is_complex_multiplexed = True
    signal = canmatrix.Signal("mx")
    signal.mux_val_max = 5
    signal.mux_val_min = 1
    signal.muxer_for_signal = 4
    frame.add_signal(signal)
    db.add_frame(frame)
    outdbc = io.BytesIO()
    canmatrix.formats.dump(db, outdbc, "dbc")
    for line in outdbc.getvalue().decode('utf8').split('\n'):
        if "SG_MUL_VAL" in line:
            return True
    assert False


def test_defines_with_special_cars():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BU_: someOtherEcu

    BO_ 123 someFrame: 1 someOtherEcu
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    BA_DEF_ SG_ "Accuracy" STRING;
    BA_ "Accuracy" SG_ 123 someSignal "+/- 10.2 at 55.1%";
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].signals[0].attributes["Accuracy"] == "+/- 10.2 at 55.1%"

def test_j1939_frametype():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BU_: someOtherEcu

    BO_ 2147483648 someFrame: 1 someOtherEcu
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST
    
    BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","J1939PG";
    BA_ "VFrameFormat" BO_ 2147483648 2;
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].is_j1939 == True

    # negative test
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BU_: someOtherEcu

    BO_ 2147483648 someFrame: 1 someOtherEcu
     SG_ someSignal: 1|2@0+ (1,0) [0|0] ""  CCL_TEST

    BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","J1939PG";
    BA_ "VFrameFormat" BO_ 2147483648 0;
     ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].is_j1939 == False


def test_attributes_with_spaces_before_semicolumn():
    dbc = io.BytesIO(textwrap.dedent(u'''\
    BO_ 8 Frame_1: 8 Vector__XXX
    BO_ 9 Frame_2: 8 Vector__XXX
    BA_DEF_ BO_ "someAttribute" STRING ;
    BA_ "someAttribute" BO_ 8 "str" ;
    BA_DEF_DEF_ "someAttribute" "asd" ;
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].attributes["someAttribute"] == 'str'
    assert matrix.frames[1].attribute("someAttribute", matrix) == 'asd'

def test_cycle_time_handling():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ sig2 : 8|8@1- (1,0) [0|0] "" Vector__XXX
        SG_ sig1 : 0|8@1- (1,0) [0|0] "" Vector__XXX
        
        
        BA_DEF_ BO_  "GenMsgCycleTime" INT 0 3600000;
        BA_DEF_ SG_  "GenSigCycleTime" INT 0 3600000;
        BA_DEF_DEF_  "GenMsgCycleTime" 0;
        BA_DEF_DEF_  "GenSigCycleTime" 0;
        BA_ "GenMsgCycleTime" BO_ 17 100;
        BA_ "GenSigCycleTime" SG_ 17 sig2 20;
        BA_ "GenSigCycleTime" SG_ 17 sig1 10;
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    assert matrix.frames[0].cycle_time == 100
    assert matrix.frames[0].signal_by_name("sig1").cycle_time == 10
    assert matrix.frames[0].signal_by_name("sig2").cycle_time == 20


#    assert "GenMsgCycleTime" not in matrix.frame_defines
#    assert "GenSigCycleTime" not in matrix.signal_defines

    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")

    assert 'BA_ "GenMsgCycleTime" BO_ 17 100;' in outdbc.getvalue().decode('utf8')
    assert 'BA_ "GenSigCycleTime" SG_ 17 sig2 20;' in outdbc.getvalue().decode('utf8')
    assert 'BA_ "GenSigCycleTime" SG_ 17 sig1 10;' in outdbc.getvalue().decode('utf8')

    outdbc = io.BytesIO()
    canmatrix.formats.dump({"aa":matrix}, outdbc, "kcd")

def test_keep_cycle_time_defines():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ sig1 : 0|8@1- (1,0) [0|0] "" Vector__XXX
        
        BA_DEF_ BO_ "GenMsgCycleTime" INT 0 50000 ;
        BA_DEF_DEF_ "GenMsgCycleTime" 0 ;
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    assert 'BA_DEF_ BO_ "GenMsgCycleTime" INT 0 50000' in outdbc.getvalue().decode('utf8')
    assert 'BA_DEF_DEF_ "GenMsgCycleTime" 0' in outdbc.getvalue().decode('utf8')

def test_unique_signal_names():
    db = canmatrix.CanMatrix()
    frame = canmatrix.Frame("some Frame")
    frame.add_signal(canmatrix.Signal("signal_name", size=1, start_bit=1))
    frame.add_signal(canmatrix.Signal("signal_name", size=2, start_bit=9))
    db.add_frame(frame)
    outdbc = io.BytesIO()
    canmatrix.formats.dump(db, outdbc, "dbc")
    assert "signal_name0" in outdbc.getvalue().decode('utf8')
    assert "signal_name1" in outdbc.getvalue().decode('utf8')

    outdbc = io.BytesIO()
    canmatrix.formats.dump(db, outdbc, "dbc", dbcUniqueSignalNames=False)
    assert "signal_name0" not in outdbc.getvalue().decode('utf8')
    assert "signal_name1" not in outdbc.getvalue().decode('utf8')
    assert "signal_name" in outdbc.getvalue().decode('utf8')

def test_signal_inital_value():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ sig1 : 0|8@1- (1,0) [0|0] "" Vector__XXX


        BA_DEF_ SG_  "GenSigStartValue" FLOAT 0 100000000000;
        BA_ "GenSigStartValue" SG_ 17 sig1 2.7;
        
        SIG_VALTYPE_ 17 sig1 : 1;
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].signal_by_name("sig1").initial_value == decimal.Decimal("2.7")
#    assert "GenSigStartValue" not in matrix.signal_defines

    outdbc = io.BytesIO()
    canmatrix.formats.dump(matrix, outdbc, "dbc")
    assert 'BA_ "GenSigStartValue" SG_ 17 sig1 2.7;' in outdbc.getvalue().decode('utf8')


def test_candbpp_startbit():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 1809 MSG: 8 DEV2
 SG_ SIG1 : 39|4@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG2 : 52|1@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG3 : 51|12@0+ (0.1,0) [0|360] "°"  DEV1
 SG_ SIG4 : 6|1@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG5 : 5|1@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG6 : 23|3@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG7 : 7|1@0+ (1,0) [0|1] ""  DEV1
 SG_ SIG8 : 34|11@0+ (0.1,-102.4) [-32|32] "A"  DEV1
 SG_ SIG9 : 18|11@0+ (0.1,-102.4) [-62.5|62.5] "A"  DEV1
 SG_ SIG10 : 4|13@0+ (0.1,0) [350|450] "V"  DEV1
    ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    # Motorola forward LSB
    assert matrix.frames[0].signal_by_name("SIG1").get_startbit(True, True) == 36
    assert matrix.frames[0].signal_by_name("SIG2").get_startbit(True, True) == 52
    assert matrix.frames[0].signal_by_name("SIG3").get_startbit(True, True) == 56
    assert matrix.frames[0].signal_by_name("SIG4").get_startbit(True, True) == 6
    assert matrix.frames[0].signal_by_name("SIG5").get_startbit(True, True) == 5
    assert matrix.frames[0].signal_by_name("SIG6").get_startbit(True, True) == 21
    assert matrix.frames[0].signal_by_name("SIG7").get_startbit(True, True) == 7
    assert matrix.frames[0].signal_by_name("SIG8").get_startbit(True, True) == 40
    assert matrix.frames[0].signal_by_name("SIG9").get_startbit(True, True) == 24
    assert matrix.frames[0].signal_by_name("SIG10").get_startbit(True, True) == 8
    # Motorola forward MSB
    assert matrix.frames[0].signal_by_name("SIG1").get_startbit(True, False) == 39
    assert matrix.frames[0].signal_by_name("SIG2").get_startbit(True, False) == 52
    assert matrix.frames[0].signal_by_name("SIG3").get_startbit(True, False) == 51
    assert matrix.frames[0].signal_by_name("SIG4").get_startbit(True, False) == 6
    assert matrix.frames[0].signal_by_name("SIG5").get_startbit(True, False) == 5
    assert matrix.frames[0].signal_by_name("SIG6").get_startbit(True, False) == 23
    assert matrix.frames[0].signal_by_name("SIG7").get_startbit(True, False) == 7
    assert matrix.frames[0].signal_by_name("SIG8").get_startbit(True, False) == 34
    assert matrix.frames[0].signal_by_name("SIG9").get_startbit(True, False) == 18
    assert matrix.frames[0].signal_by_name("SIG10").get_startbit(True, False) == 4
    
    
def test_missing_space():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ sig1 : 0|8@1-(1,0)[0|0] "" Vector__XXX
        ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].signals[0].name == "sig1"

def test_escaped_quotes():
    dbc = io.BytesIO(textwrap.dedent(r'''
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ Signal : 0|8@1-(1,0)[0|0] "" Vector__XXX
        
        VAL_ 17 Signal 0 "zero" 1 "one " 2 "string with \"escaped\" double quotes";
        ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    assert matrix.frames[0].signals[0].values[2] == r'string with "escaped" double quotes'


def test_float_cycle_time():
    dbc = io.BytesIO(textwrap.dedent(u'''\
        BO_ 17 Frame_1: 8 Vector__XXX
        SG_ sig2 : 8|8@1- (1,0) [0|0] "" Vector__XXX
        SG_ sig1 : 0|8@1- (1,0) [0|0] "" Vector__XXX


        BA_DEF_ BO_  "GenMsgCycleTime" INT 10 3600000;
        BA_ "GenMsgCycleTime" BO_ 17 100.0;
''').encode('utf-8'))


    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    assert matrix.frames[0].cycle_time == 100


def test_without_ecu():
    dbc = io.BytesIO(textwrap.dedent(u'''\
            BO_ 17 Frame_1: 8 Vector__XXX
            SG_ A_B_C_D_E: 39|16@0+ (0.01,0) [0|655.35] "km/h"
    ''').encode('utf-8'))

    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")
    matrix.frames[0].signals[0].name == "A_B_C_D_E"
