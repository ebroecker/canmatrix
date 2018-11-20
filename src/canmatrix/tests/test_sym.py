import io
import textwrap

import canmatrix.sym


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

    matrix = canmatrix.sym.load(f)
    error, = matrix.load_errors
    line_number = 16

    assert len(matrix.load_errors) == 1

    assert isinstance(error, canmatrix.sym.DuplicateMuxIdError)

    assert error.line_number == line_number

    error_string = str(error)
    assert error_string.startswith(
        'line {line_number}: '.format(line_number=line_number),
    )

    assert 'FirstMux' in error_string
    assert 'SecondMux' in error_string


def test_parse_longname():
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

    matrix = canmatrix.sym.load(f)
    for frame in matrix.frames:
        for s in frame.signals:
            ln = s.attributes.get('LongName')
            if ln:
                assert ln == 'Access Level : Password'
