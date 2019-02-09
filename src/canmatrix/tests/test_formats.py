import io
import textwrap

import canmatrix.formats


def test_dump_matrix():
    matrix = canmatrix.CanMatrix()

    codec = 'utf-8'

    f = io.BytesIO()
    canmatrix.formats.dump(matrix, f, 'sym', symExportEncoding=codec)

    result = f.getvalue()

    expected = textwrap.dedent(u'''\
    FormatVersion=5.0 // Do not edit this line!
    Title="canmatrix-Export"
    {ENUMS}


    ''').encode(codec)

    assert result == expected
