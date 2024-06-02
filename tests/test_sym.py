# -*- coding: utf-8 -*-
import io
import sys
import textwrap
from itertools import chain
from pprint import pprint

import pytest

import canmatrix.canmatrix
import canmatrix.formats.sym


def test_colliding_mux_values():
    f = io.BytesIO(
        textwrap.dedent(
            '''\
            FormatVersion=5.0 // Do not edit this line!
            Title="a file"

            {SEND}

            [MuxedId]
            ID=0h
            Mux=TheMux 0,1 0h
            Var=Signal unsigned 1,1

            [MuxedId]
            Mux=FirstMux 0,1 1h
            Var=Signal unsigned 1,1

            [MuxedId]
            Mux=SecondMux 0,1 1h
            Var=Signal unsigned 1,1
            ''',
        ).encode('utf-8'),
    )

    matrix = canmatrix.formats.sym.load(f)
    error, = matrix.load_errors
    line_number = 16

    assert len(matrix.load_errors) == 1

    assert isinstance(error, canmatrix.formats.sym.DuplicateMuxIdError)

    assert error.line_number == line_number

    error_string = str(error)
    assert error_string.startswith(
        'line {line_number}: '.format(line_number=line_number),
    )

    assert 'FirstMux' in error_string
    assert 'SecondMux' in error_string


def test_parse_longname_with_colon():
    f = io.BytesIO(
        textwrap.dedent(
            '''\
            FormatVersion=5.0 // Do not edit this line!
            Title="a file"

            {SEND}

            [pass]
            DLC=8
            Var=Password unsigned 16,16 /ln:"Access Level : Password"
            ''',
        ).encode('utf-8'),
    )

    matrix = canmatrix.formats.sym.load(f)
    frame = matrix.frames[0]
    signal = frame.signals[0]
    assert signal.attributes['LongName'] == 'Access Level : Password'


@pytest.mark.parametrize(
    'is_float, value, expected',
    (
        (False, '37', '37'),
        (True, '37.1', '37.1'),
    ),
)
def test_export_default_decimal_places(is_float, value, expected):
    matrix = canmatrix.canmatrix.CanMatrix()

    frame = canmatrix.canmatrix.Frame()
    matrix.add_frame(frame)

    signal = canmatrix.canmatrix.Signal(
        size=32,
        is_float=is_float,
        is_signed=False,
        initial_value=value,
    )
    frame.add_signal(signal)

    s = canmatrix.formats.sym.create_signal(db=matrix, signal=signal)

    start = '/d:'

    d, = (
        segment
        for segment in s.split()
        if segment.startswith(start)
    )
    d = d[len(start):]

    assert d == expected


@pytest.mark.parametrize(
    'variable_type, bit_length',
    (
        ('float', 32),
        ('double', 64),
    )
)
def tests_parse_float(variable_type, bit_length):
    f = io.BytesIO(
        textwrap.dedent(
            '''\
            FormatVersion=5.0 // Do not edit this line!
            Title="Untitled"

            {{SENDRECEIVE}}

            [Symbol1]
            ID=000h
            DLC=8
            Var=a_signal {variable_type} 0,{bit_length}
            '''.format(
                variable_type=variable_type,
                bit_length=bit_length,
            ),
        ).encode('utf-8'),
    )

    matrix = canmatrix.formats.sym.load(f)
    assert matrix.load_errors == []
    frame = matrix.frames[0]
    signal = frame.signals[0]
    assert signal.is_float

def test_unterminated_enum():
    f = io.BytesIO(
        textwrap.dedent(
            '''\
            FormatVersion=5.0 // Do not edit this line!
            Title="Untitled
            
            {ENUMS}
            enum Categories(0="Animal", 1="Vegetable", 3="Mineral"
            
            {SENDRECEIVE}
            
            [Symbol1]
            ID=000h
            DLC=8
            Var=Signal unsigned 0,16
            
            '''
        ).encode('utf-8'),
    )
    # Missing ')' at the end of enum used to cause infinite loop

    matrix = canmatrix.formats.sym.load(f)

    assert len(matrix.load_errors) == 1
    if sys.version_info > (3, 0):
        assert isinstance(matrix.load_errors[0], EOFError)
    else:
        assert isinstance(matrix.load_errors[0], StopIteration)


def test_title_read_and_write():
    f = io.BytesIO(
        textwrap.dedent(
            '''\
            FormatVersion=5.0 // Do not edit this line!
            Title="An Example Title"

            '''
        ).encode('utf-8'),
    )

    matrix = canmatrix.formats.sym.load(f)
    assert matrix.attribute("Title") == "An Example Title"
    f_out = io.BytesIO()
    canmatrix.formats.sym.dump(matrix, f_out)
    assert f_out.getvalue().decode('utf-8').splitlines()[1] == 'Title="An Example Title"'

@pytest.mark.parametrize(
    'enum_str, enum_dict, enum_label',
    (
        ('enum Animal(0="Dog", 1="Cat", 2="Fox")', {"Animal": {0: "Dog", 1: "Cat", 2: "Fox"}}, "Simple enum"),
        ('''\
enum Animal(0="Dog", //A Comment
1="Cat",
2="Fox")''',
         {"Animal": {0: "Dog", 1: "Cat", 2: "Fox"}}, "Multiline enum"),
        ('enum Animal(0="Dog",1="Cat",2="Fox")', {"Animal": {0: "Dog", 1: "Cat", 2: "Fox"}}, "No Space  in Separator"),
    )
)
def test_enums_read(enum_str, enum_dict, enum_label):
        f = io.BytesIO('''\
FormatVersion=5.0 // Do not edit this line!
Title="An Example Title"

{{ENUMS}}
{}
'''.format(enum_str).encode('utf-8'),
    )

        matrix = canmatrix.formats.sym.load(f)
        assert matrix.load_errors == [], "Failed to load canmatrix, when testing enum case : '{}'".format(enum_label)
        assert matrix.value_tables == enum_dict, "Enum not parsed correctly : '{}'".format(enum_label)


def test_enums_export():
    f = io.BytesIO('''\
FormatVersion=5.0 // Do not edit this line!
Title="An Example Title"

{ENUMS}
enum Animal(0="Dog",1="Cat",2="Fox")

{SENDRECEIVE}

[Frame1]
ID=000h
DLC=8
Var=Signal1 unsigned 0,16
'''.encode('utf-8'),
    )

    matrix = canmatrix.formats.sym.load(f)
    assert matrix.load_errors == [], "Failed to load canmatrix"

    # Add an enum to Signal1
    matrix.frame_by_name("Frame1").signal_by_name("Signal1").enumeration = "Plants"
    matrix.frame_by_name("Frame1").signal_by_name("Signal1").values = {0: "Grass", 1: "Flower", 2: "Tree"}

    # Export and reimport
    f_out = io.BytesIO()
    canmatrix.formats.sym.dump(matrix, f_out)
    f_in = io.BytesIO(f_out.getvalue())
    new_matrix = canmatrix.formats.sym.load(f_in)

    # Check that Enums from Enums table exported and reimported correctly
    assert new_matrix.value_tables["Animal"] == {0: "Dog", 1: "Cat", 2: "Fox"}

    # Check that Enums from a Signal.Values property exported and reimported correctly
    assert new_matrix.value_tables["Plants"] == {0: "Grass", 1: "Flower", 2: "Tree"}



def test_types_read():
    f = io.BytesIO('''\
FormatVersion=5.0 // Do not edit this line!
Title="Types Test"

{ENUMS}
enum EnumAnimals(0="Cat", // An enum value for cats
  1="Dog", // An enum value for dogs
  2="Horse", 3="Monkey", 
  4="Lion")// An enum with a comment for the final value

{SENDRECEIVE}

[SymbolLengths]
ID=000h
DLC=8
Var="1Bit" unsigned 0,1
Var="3Bits" unsigned 1,3
Var="4Bits" unsigned 4,4
Var="21Bits" unsigned 8,21
Var="6Bits" unsigned 29,6
Var="29Bits" unsigned 35,29

[SymbolTypes]
ID=001h
DLC=8
Var=Bit bit 0,1
Var=Char char 1,8
Var=String string 16,16
Var=Signed signed 32,4
Var=Unsigned unsigned 36,4
Var=Enum EnumAnimals 40,4

Var=Raw raw 48,16

[SymbolDouble]
ID=002h
DLC=8
Var=Double double 0,64	// Must be 8 Bytes according to PCAN Symbol Editor V5

[SymbolFloat]
ID=003h
DLC=4
Var=Float float 0,32	// Must be 4 Bytes according to PCAN Symbol Editor V5
'''.encode('utf-8'),
                   )
    matrix = canmatrix.formats.sym.load(f)
    # Check no errors loading the matrix
    assert matrix.load_errors == []

    f_out = io.BytesIO()
    canmatrix.formats.sym.dump(matrix, f_out)
    f_out_bytes = f_out.getvalue()
    f_out_string = f_out_bytes.decode("utf-8")

    # Check that types are preserved when saving back to .SYM format
    assert "Var=Bit bit" in f_out_string
    assert "Var=Char char" in f_out_string
    assert "Var=String string" in f_out_string
    assert "Var=Signed signed" in f_out_string
    assert 'Var="21Bits" unsigned' in f_out_string
    assert 'Var=Float float' in f_out_string
    assert 'Var=Double double' in f_out_string

    # Read matrix back in to check all symbols/frames preserved
    f_in = io.BytesIO(f_out_bytes)
    new_matrix = canmatrix.formats.sym.load(f_in)

    # Check no errors loading the matrix
    assert new_matrix.load_errors == []

    # Check that both matrices have the same Frames
    frames = [f.name for f in matrix.frames]
    new_frames = [f.name for f in new_matrix.frames]
    assert sorted(frames) == sorted(new_frames)

    # Check that both matrices have the same signals, and that all the expected signals are present
    signals = chain(*[[s.name for s in frame.signals] for frame in matrix.frames])
    new_signals = chain(*[[s.name for s in frame.signals] for frame in new_matrix.frames])
    assert sorted(signals) == sorted(new_signals) == sorted([
                                                            "1Bit",
                                                            "3Bits",
                                                            "4Bits",
                                                            "21Bits",
                                                            "6Bits",
                                                            "29Bits",
                                                            "Bit",
                                                            "Char",
                                                            "String",
                                                            "Signed",
                                                            "Unsigned",
                                                            "Enum",
                                                            "Raw",
                                                            "Double",
                                                            "Float", ])

@pytest.mark.parametrize(
    'var_name,data,raw_value',
    (
        ('VarMux1',   bytearray([1,  12,  0,  0,  0,  0,  0,  0]), 12),
        ('VarMux2',   bytearray([2,  0,  0,  0,  23,  0,  0,  0]), 23),
        ('VarMux200', bytearray([200,  0,  0,  0,  0,  0,  34,  0]), 34),
    )
)
def test_mux_decode(var_name,data,raw_value):
    f = io.BytesIO('''\
    FormatVersion=5.0 // Do not edit this line!
    Title="Types Test"

FormatVersion=5.0 // Do not edit this line!
Title="Test Symbols File"

{SENDRECEIVE}

[MuxTestFrame]
ID=002h
DLC=8
Mux=Mux1 0,8 1 
Var=VarMux1 unsigned 8,8

[MuxTestFrame]
DLC=8
Mux=Mux2 0,8 2 
Var=VarMux2 unsigned 32,8

[MuxTestFrame]
DLC=8
Mux=Mux200 0,8 C8h
Var=VarMux200 unsigned 48,8
    '''.encode('utf-8'),
                   )

    matrix = canmatrix.formats.sym.load(f)
    # Check no errors loading the matrix
    assert matrix.load_errors == []

    frame = matrix.frame_by_name("MuxTestFrame")
    r = frame.decode(data)
    assert var_name in r.keys(), "Signal {}, not decoded. Only : {}".format(var_name, ','.join(r for r in r.keys()))
    assert r[var_name].raw_value == raw_value


def test_sym_val_table():
    sym = io.BytesIO(textwrap.dedent(u'''\
        FormatVersion=5.0 // Do not edit this line!
        Title="Test-CAN"

        {ENUMS}
        enum Status_val(0="R", 1="B", 2="E")

        {SENDRECEIVE}

        [Flow_extCAN]
        ID=700h
        DLC=6
        Var=status Status_val 36,2
        ''').encode('utf-8'))
    matrix = canmatrix.formats.sym.load(sym)
    assert matrix.frames[0].signals[0].values == {0: 'R', 1: 'B', 2: 'E'}