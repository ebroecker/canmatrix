# -*- coding: utf-8 -*-
import io
import sys
import textwrap

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
        f_out = io.BytesIO()
        canmatrix.formats.sym.dump(matrix, f_out)
