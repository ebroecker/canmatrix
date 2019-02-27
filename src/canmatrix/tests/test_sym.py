import io
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
    # the `FLOAT` type here is irrelevant at the moment...  at least for this
    matrix.add_signal_defines('GenSigStartValue', 'FLOAT -3.4E+038 3.4E+038')

    frame = canmatrix.canmatrix.Frame()
    matrix.add_frame(frame)

    signal = canmatrix.canmatrix.Signal(
        size=32,
        is_float=is_float,
        is_signed=False,
    )
    signal.add_attribute('GenSigStartValue', value)
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
