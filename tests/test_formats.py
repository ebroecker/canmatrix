# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
import textwrap

import pytest

import canmatrix.formats
from canmatrix._canmatrix import CanMatrix


def test_dump_matrix():
    matrix = CanMatrix()

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


@pytest.mark.parametrize("path_type", [str, Path, os.fsencode])
def test_loadp_paths(tmp_path, path_type):
    path = tmp_path / "input.DBC"
    path.write_bytes(b'BO_ 100 TestFrame: 1 Vector__XXX\n')

    for import_type in (None, "dbc"):
        matrix = canmatrix.formats.loadp(path_type(path), import_type)[""]
        assert matrix.frames[0].name == "TestFrame"

    matrix = canmatrix.formats.loadp_flat(path_type(path))
    assert matrix.frames[0].name == "TestFrame"


@pytest.mark.parametrize("path_type", [str, Path, os.fsencode])
def test_dumpp_paths(tmp_path, path_type):
    matrix = canmatrix.formats.loads_flat(
        b'BO_ 100 TestFrame: 1 Vector__XXX\n', "dbc"
    )
    path = tmp_path / "output.DBC"

    canmatrix.formats.dumpp({"CAN": matrix}, path_type(path))

    reloaded = canmatrix.formats.loadp(str(tmp_path / "output_CAN.DBC"))[""]
    assert reloaded.frames[0].name == "TestFrame"
