from io import BytesIO

import openpyxl
import pytest
import xlrd

import canmatrix.formats
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix._canmatrix import CanMatrix


def make_matrix():
    matrix = CanMatrix()
    frame = Frame("Numbering", arbitration_id=0x123, size=8)
    frame.add_signal(Signal("Little", start_bit=0, size=8, is_signed=False,
                            values={0: "Off", 1: "On"}))
    frame.add_signal(Signal("Motorola", start_bit=11, size=16,
                            is_little_endian=False, is_signed=False))
    frame.add_signal(Signal("Late", start_bit=40, size=8, is_signed=False))
    matrix.add_frame(frame)
    matrix.add_frame(Frame("Empty", arbitration_id=0x124, size=8))
    return matrix


def sheet_values(path):
    if path.suffix == ".xls":
        book = xlrd.open_workbook(str(path))
        sheet = book.sheet_by_index(0)
        return [sheet.row_values(row) for row in range(sheet.nrows)]
    book = openpyxl.load_workbook(path)
    try:
        return [list(row) for row in book.active.iter_rows(values_only=True)]
    finally:
        book.close()


@pytest.mark.parametrize("format_name", ["xls", "xlsx"])
@pytest.mark.parametrize("motorola_format", ["msb", "msbreverse", "lsb"])
@pytest.mark.parametrize("separate_values", [False, True])
def test_spreadsheet_byte_bases(tmp_path, format_name, motorola_format, separate_values):
    matrix = make_matrix()
    options = {"xlsMotorolaBitFormat": motorola_format,
               "xlsValuesInSeperateLines": separate_values}
    default_path = tmp_path / ("default." + format_name)
    canmatrix.formats.dumpp({"": matrix}, str(default_path), **options)
    default_values = sheet_values(default_path)
    byte_column = default_values[0].index("Signal Byte No.")

    for byte_base in (0, 1):
        path = tmp_path / (str(byte_base) + "." + format_name)
        canmatrix.formats.dumpp({"": matrix}, str(path),
                               xlsExportByteBase=byte_base, **options)
        expected = [list(row) for row in default_values]
        for row in expected[1:]:
            if isinstance(row[byte_column], (int, float)):
                row[byte_column] += byte_base - 1
        assert sheet_values(path) == expected

        reloaded = canmatrix.formats.loadp_flat(str(path),
                                              xlsImportByteBase=byte_base, **options)
        assert [(signal.name, signal.start_bit, signal.size)
                for signal in reloaded.frames[0].signals] == [
                    (signal.name, signal.start_bit, signal.size)
                    for signal in matrix.frames[0].signals]


@pytest.mark.parametrize("format_name", ["xls", "xlsx"])
@pytest.mark.parametrize("direction", ["Import", "Export"])
@pytest.mark.parametrize("invalid_base", [-1, 2, 0.5, "0", True, None])
def test_invalid_spreadsheet_byte_base(tmp_path, format_name, direction, invalid_base):
    option = "xls" + direction + "ByteBase"
    path = tmp_path / ("matrix." + format_name)
    if direction == "Import":
        canmatrix.formats.dumpp({"": make_matrix()}, str(path))
        with pytest.raises(ValueError, match=option):
            canmatrix.formats.loadp_flat(str(path), **{option: invalid_base})
    else:
        with pytest.raises(ValueError, match=option):
            canmatrix.formats.dumpp({"": make_matrix()}, str(path),
                                   **{option: invalid_base})


def test_excel_byte_base_does_not_change_csv():
    def dump(**options):
        output = BytesIO()
        canmatrix.formats.dump(make_matrix(), output, "csv", **options)
        return output.getvalue()

    assert dump(xlsExportByteBase=0, xlsImportByteBase=0) == dump()
