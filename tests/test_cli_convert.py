# -*- coding: utf-8 -*-
import os
import sys
import tempfile

import pytest
import canmatrix.formats

from canmatrix.utils import arbitration_id_converter
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix._canmatrix import CanMatrix

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

pytest_plugins = ["pytester"]
here = Path(__file__).parent / "files"
tmp_dir = tempfile.mkdtemp()


@pytest.fixture
def run(testdir):
    def do_run(*args):
        args = [sys.executable, "-m", "canmatrix.cli.convert"] + list(args)
        return testdir.run(*args)
    return do_run

def test_silent(tmpdir, run):
    inputFile = str(here / "dbc" / "test_frame_decoding.dbc")

    normal_result = run(inputFile, "tmp.dbc")
    silent_result = run("-s", inputFile, "tmp.dbc")
    assert len(normal_result.errlines) > len(silent_result.errlines)

def test_verbose(tmpdir, run):
    inputFile = str(here / "arxml" / "ARXML_min_max.arxml")

    normal_result = run(inputFile, "tmp.dbc")
    verbose_result = run("-vv", inputFile, "tmp.dbc")
    assert len(normal_result.errlines) + len(normal_result.outlines) < len(verbose_result.errlines) + len(verbose_result.outlines)

def test_force_output_format(tmpdir, run):
    inputFile = str(here / "dbc" / "test_frame_decoding.dbc")
    outFile = tmp_dir + "/cli_convert_test_force.tmp"

    normal_result = run("-vv", "-f", "dbc", inputFile, outFile)
    assert 'INFO - convert - Export Done' in normal_result.errlines[-1]

    with open(outFile, "r") as fd:
        first_line = fd.readline()
        assert first_line == 'VERSION "created by canmatrix"\n'

def test_force_input_format(tmpdir, run):
    inputFile = tmp_dir + "/cli_convert_test_force.tmp"

    normal_result = run("-i", "dbc", inputFile, "tmp.dbc")
    assert 'INFO - convert - Export Done' in normal_result.errlines[-1]

def create_dbc_with_special_char():
    outFile = tmp_dir + "/output_cli_convert_tmp.dbc"

    myFrame = Frame("testFrame1", 
                              arbitration_id=arbitration_id_converter(0x123), 
                              size=8, 
                              transmitters=["testBU"])
    mySignal = Signal("someTestSignal",
                      size=11,
                      is_little_endian=False,
                      is_signed=False,
                      factor=5.0,
                      offset=1.0,
                      min=0,
                      max=500,
                      unit=u"specialCharUnit°$",  # .decode("utf-8"),
                      receivers=["recBU"])
    myFrame.add_signal(mySignal)

    db = CanMatrix()
    db.add_frame(myFrame)
    db.add_frame_defines("SomeUnneededDefine", 'INT 0 65535')
    canmatrix.formats.dumpp({"": db},
                            outFile, 
                            dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')
    return outFile

def test_ignore_encoding_errors(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    normal_result = run("--ignoreEncodingErrors", "--dbcExportEncoding", "ascii", inputFile, "tmp2.dbc")
    assert 'INFO - convert - Export Done' in normal_result.errlines[-1]

def test_delete_obsolete_defines(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteObsoleteDefines", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"SomeUnneededDefine" not in content
    normal_result = run(inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"SomeUnneededDefine" in content

def test_delete_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteEcu", "testBU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testBU" not in content

def test_rename_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameEcu", "testBU:renamedECU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testBU" not in content
        assert b"renamedECU" in content

def test_delete_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteSignal", "someTestSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"someTestSignal" not in content

def test_rename_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameSignal", "someTestSignal:renamedSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"someTestSignal" not in content
        assert b"renamedSignal" in content

def test_delete_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteFrame", "testFrame1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "testFrame1" not in content

def test_rename_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameFrame", "testFrame1:renamedFrame", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testFrame1" not in content
        assert b"renamedFrame" in content

def test_add_frame_receiver(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--addFrameReceiver", "testFrame1:newECU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"recBU,newECU" in content

def test_change_frame_id(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--changeFrameId", "291:666", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"BO_ 666" in content

def test_set_frame_fd(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--setFrameFd", "testFrame1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b'BA_ "VFrameFormat" BO_ 291 14' in content
    deleted_result = run("--unsetFrameFd", "testFrame1", "tmp2.dbc", "tmp3.dbc")
    with open("tmp3.dbc", "rb") as fd:
        content = fd.read()
        assert b'BA_ "VFrameFormat" BO_ 291 14' not in content

def test_recalc_dlc(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--recalcDLC", "max", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testFrame1: 8" in content

    result = run("--recalcDLC", "force", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testFrame1: 2" in content

def test_skip_long_dlc(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--skipLongDlc", "7", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content

def test_cut_long_frames(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--cutLongFrames", "1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content
    result = run("--cutLongFrames", "2", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"someTestSignal" in content

def test_copy_signals(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--signals", "someTestSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"someTestSignal" in content
        assert b"VECTOR__INDEPENDENT_SIG_MSG" in content

def create_dbc(additionalReceiver = []):
    tmp_dir = tempfile.mkdtemp()
    outFile = tmp_dir + "/output_cli_convert_tmpb.dbc"

    myFrame = Frame("testFrame3", arbitration_id=arbitration_id_converter(0x124), size=8, transmitters=["testBU"])
    mySignal = Signal("someTestSignal",
                      size=11,
                      is_little_endian=False,
                      is_signed=False,
                      factor=5.0,
                      offset=1.0,
                      min=0,
                      max=500,
                      receivers=["recBU"])
    myFrame.add_signal(mySignal)
    myFrame2 = Frame("testFrame2", arbitration_id=arbitration_id_converter(0x125), size=8, transmitters=["testBU2"])
    myFrame2.add_attribute("myAttribute", "42")
    mySignal2 = Signal("someTestSignal2",
                      start_bit=15,
                      size=11,
                      is_little_endian=False,
                      is_signed=False,
                      factor=5.0,
                      offset=1.0,
                      min=0,
                      max=500,
                      receivers=["recBU2"] + additionalReceiver)
    myFrame2.add_signal(mySignal2)
    mySignal3 = Signal("zeroSignal",
                      start_bit=20,
                      size=0,
                      is_little_endian=False,
                      is_signed=False,
                      factor=5.0,
                      offset=1.0,
                      min=0,
                      max=500,
                      receivers=["recBU2"])
    mySignal3.add_attribute("mySignalAttribute", "7")
    myFrame2.add_signal(mySignal3)

    db = CanMatrix()
    db.add_frame(myFrame)
    db.add_frame(myFrame2)
    db.add_frame_defines("myAttribute", "INT -5 10")
    db.add_signal_defines("mySignalAttribute", 'INT 0 65535')
    canmatrix.formats.dumpp({"": db}, outFile, dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')
    return outFile

def test_copy_ecus(tmpdir, run):
    inputFile = create_dbc()
    result = run("--ecus", "testBU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "testBU2" not in content
        assert "testBU" in content

def test_copy_ecus_rx(tmpdir, run):
    inputFile = create_dbc()
    result = run("--ecus", "recBU:rx", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "recBU2" not in content
        assert "recBU" in content

def test_copy_ecus_tx(tmpdir, run):
    inputFile = create_dbc(additionalReceiver = ["testBU"])
    result = run("--ecus", "testBU:tx", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert "testFrame2" not in content
        assert "testFrame3" in content

def test_copy_frames(tmpdir, run):
    inputFile = create_dbc()
    result = run("--frames", "testFrame3", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"testFrame2" not in content
        assert b"testFrame3" in content

def test_delete_frame_attributes(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteFrameAttributes", "myAttribute", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert 'BA_ "myAttribute"' not in content

def test_delete_zero_signals(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteZeroSignals", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert 'zeroSignal' not in content

def test_delete_signal_attributes(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteSignalAttributes", "mySignalAttribute", inputFile, "tmp2.dbc")
    with open("tmp2.dbc", "r") as fd:
        content = fd.read()
        assert 'BA_ "mySignalAttribute"' not in content

def test_merge(tmpdir, run):
    inputFile1 = create_dbc_with_special_char()
    inputFile2 = create_dbc()

    if inputFile1[1] == ":":
        inputFile1 = inputFile1[2:]
    result = run("--merge", inputFile1, inputFile2, "tmp2.dbc")
    with open("tmp2.dbc", "rb") as fd:
        content = fd.read()
        assert b"BO_ 291" in content
        assert b"BO_ 292" in content
        assert b"BO_ 293" in content

    result = run("--merge", inputFile1 + ":ecu=testBU", inputFile2, "tmp3.dbc")
    with open("tmp3.dbc", "rb") as fd:
        content = fd.read()
        assert b"BO_ 291" in content
        assert b"BO_ 292" in content
        assert b"BO_ 293" in content

    result = run("--merge", inputFile1 + ":frame=testFrame1", inputFile2, "tmp4.dbc")
    with open("tmp4.dbc", "rb") as fd:
        content = fd.read()
        assert b"BO_ 291" in content
        assert b"BO_ 292" in content
        assert b"BO_ 293" in content


@pytest.mark.parametrize(
    "module, command",
    [
        ("canmatrix.cli.convert", "cli_convert"),
        ("canmatrix.cli.compare", "cli_compare"),
    ],
)
def test_cli_no_duplicatie_options(
    module: str, command: str,
    recwarn: pytest.WarningsRecorder
) -> None:
    import importlib

    from click.testing import CliRunner

    module = importlib.import_module(module)
    cli = getattr(module, command)

    cli_runner = CliRunner()
    result = cli_runner.invoke(cli, ["--help"])

    assert result.exit_code == 0

    for warn in recwarn:
        if warn.category == UserWarning and "parameters should be unique" in str(
            warn.message
        ):
            pytest.fail(str(warn.message))


@pytest.fixture
def byte_base_dbc(tmp_path):
    source = tmp_path / "byte_base.dbc"
    source.write_text(
        'VERSION ""\n\nBU_: ECU\n\n'
        'BO_ 100 Frame: 8 ECU\n'
        ' SG_ LaterByte : 16|8@1+ (1,0) [0|255] "" ECU\n'
    )
    return source


def spreadsheet_signal_byte(path, file_format):
    if file_format == "xlsx":
        import openpyxl

        workbook = openpyxl.load_workbook(str(path), read_only=True)
        try:
            rows = list(workbook.active.iter_rows(values_only=True))
        finally:
            workbook.close()
    else:
        import xlrd

        workbook = xlrd.open_workbook(str(path))
        sheet = workbook.sheet_by_index(0)
        rows = [sheet.row_values(i) for i in range(sheet.nrows)]
        workbook.release_resources()
    return rows[1][rows[0].index("Signal Byte No.")]


@pytest.mark.parametrize("file_format", ["xls", "xlsx"])
def test_cli_zero_byte_base_round_trip(tmp_path, run, byte_base_dbc, file_format):
    spreadsheet = tmp_path / ("zero." + file_format)
    restored = tmp_path / "restored.dbc"
    result = run("--xlsExportByteBase", "0", str(byte_base_dbc), str(spreadsheet))
    assert result.ret == 0
    assert spreadsheet_signal_byte(spreadsheet, file_format) == 2

    result = run("--xlsImportByteBase", "0", str(spreadsheet), str(restored))
    assert result.ret == 0
    reloaded = canmatrix.formats.loadp(str(restored))[""]
    assert reloaded.frames[0].signals[0].start_bit == 16


@pytest.mark.parametrize("file_format", ["xls", "xlsx"])
def test_cli_independent_byte_bases(tmp_path, run, byte_base_dbc, file_format):
    one_based = tmp_path / ("one." + file_format)
    zero_based = tmp_path / ("zero." + file_format)
    assert run(str(byte_base_dbc), str(one_based)).ret == 0
    assert spreadsheet_signal_byte(one_based, file_format) == 3

    result = run(
        "--xlsImportByteBase", "1", "--xlsExportByteBase", "0",
        str(one_based), str(zero_based),
    )
    assert result.ret == 0
    assert spreadsheet_signal_byte(zero_based, file_format) == 2


@pytest.mark.parametrize("option", ["--xlsImportByteBase", "--xlsExportByteBase"])
@pytest.mark.parametrize("value", ["-1", "2"])
def test_cli_invalid_byte_base(tmp_path, run, byte_base_dbc, option, value):
    output = tmp_path / "invalid.xlsx"
    result = run(option, value, str(byte_base_dbc), str(output))
    assert result.ret != 0
    assert "Invalid value" in result.stderr.str()
    assert not output.exists()
