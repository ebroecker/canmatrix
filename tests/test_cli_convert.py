# -*- coding: utf-8 -*-
import sys

import canmatrix.formats
import pytest

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

pytest_plugins = ["pytester"]
here = Path(__file__).parent


@pytest.fixture
def run(testdir):
    def do_run(*args):
        args = [sys.executable,"-m","canmatrix.cli.convert"] + list(args)
        return testdir.run(*args)
    return do_run

def test_silent(tmpdir, run):
    inputFile = str(here / "test_frame_decoding.dbc")

    normal_result = run(inputFile ,"tmp.dbc")
    silent_result = run("-s", inputFile,"tmp.dbc")
    assert len(normal_result.errlines) > len(silent_result.errlines)

def test_verbose(tmpdir, run):
    inputFile = str(here / "ARXML_min_max.arxml")

    normal_result = run(inputFile ,"tmp.dbc")
    verbose_result = run("-vv", inputFile,"tmp.dbc")
    assert len(normal_result.errlines) < len(verbose_result.errlines)

def test_force_output_format(tmpdir, run):
    inputFile = str(here / "test_frame_decoding.dbc")
    outFile =  str(here / "tmp.tmp")
    normal_result = run("-v", "-f","dbc", inputFile, outFile)
    assert 'INFO - convert - done' in normal_result.errlines[-1]
    with open(outFile, "r") as fd:
        first_line = fd.readline()
        assert first_line == 'VERSION "created by canmatrix"\n'

def test_foce_input_format(tmpdir, run):
    #requires test_force_output to run first
    inputFile =  str(here / "tmp.tmp")
    normal_result = run("-i","dbc", inputFile, "tmp.dbc")
    assert 'INFO - convert - done' in normal_result.errlines[-1]

def create_dbc_with_special_char():
    outFile = str(here / "tmp.dbc")
    myFrame = canmatrix.Frame("testFrame1", arbitration_id=canmatrix.arbitration_id_converter(0x123), size=8, transmitters=["testBU"])
    mySignal = canmatrix.Signal("someTestSignal",
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

    db = canmatrix.CanMatrix()
    db.add_frame(myFrame)
    db.add_frame_defines("SomeUnneededDefine", 'INT 0 65535')
    canmatrix.formats.dumpp({"": db}, outFile, dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')
    return outFile

def test_ignore_encoding_errors(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    normal_result = run("--ignoreEncodingErrors","--dbcExportEncoding", "ascii", inputFile, "tmp2.dbc")
    assert 'INFO - convert - done' in normal_result.errlines[-1]

def test_delete_obsolete_defines(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteObsoleteDefines", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"BA_DEF_" not in content
    normal_result = run(inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"BA_DEF_" in content

def test_delete_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteEcu","testBU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testBU" not in content

def test_rename_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameEcu","testBU:renamedECU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testBU" not in content
        assert b"renamedECU" in content

def test_delete_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteSignal","someTestSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"someTestSignal" not in content

def test_rename_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameSignal","someTestSignal:renamedSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"someTestSignal" not in content
        assert b"renamedSignal" in content

def test_delete_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteFrame","testFrame1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testFrame1" not in content

def test_rename_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameFrame","testFrame1:renamedFrame", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testFrame1" not in content
        assert b"renamedFrame" in content

def test_add_frame_receiver(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--addFrameReceiver","testFrame1:newECU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"recBU,newECU" in content

def test_change_frame_id(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--changeFrameId","291:666", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"BO_ 666" in content

def test_set_frame_fd(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--setFrameFd","testFrame1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b'BA_ "VFrameFormat" BO_ 291 14' in content
    deleted_result = run("--unsetFrameFd","testFrame1", "tmp2.dbc", "tmp3.dbc")
    with open("tmp3.dbc","rb") as fd:
        content = fd.read()
        assert b'BA_ "VFrameFormat" BO_ 291 14' not in content

def test_recalc_dlc(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--recalcDLC","max", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testFrame1: 8" in content

    result = run("--recalcDLC","force", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testFrame1: 2" in content

def test_skip_long_dlc(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--skipLongDlc", "7", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content

def test_cut_long_frames(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--cutLongFrames", "1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content
    result = run("--cutLongFrames", "2", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"someTestSignal" in content

def test_copy_signals(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    result = run("--signals", "someTestSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"someTestSignal" in content
        assert b"VECTOR__INDEPENDENT_SIG_MSG" in content


def create_dbc(additionalReceiver = []):
    outFile = str(here / "tmpb.dbc")
    myFrame = canmatrix.Frame("testFrame3", arbitration_id=canmatrix.arbitration_id_converter(0x124), size=8, transmitters=["testBU"])
    mySignal = canmatrix.Signal("someTestSignal",
                      size=11,
                      is_little_endian=False,
                      is_signed=False,
                      factor=5.0,
                      offset=1.0,
                      min=0,
                      max=500,
                      receivers=["recBU"])
    myFrame.add_signal(mySignal)
    myFrame2 = canmatrix.Frame("testFrame2", arbitration_id=canmatrix.arbitration_id_converter(0x125), size=8, transmitters=["testBU2"])
    myFrame2.add_attribute("myAttribute","42")
    mySignal2 = canmatrix.Signal("someTestSignal2",
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
    mySignal3 = canmatrix.Signal("zeroSignal",
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

    db = canmatrix.CanMatrix()
    db.add_frame(myFrame)
    db.add_frame(myFrame2)
    db.add_frame_defines("myAttribute","INT -5 10")
    db.add_signal_defines("mySignalAttribute", 'INT 0 65535')
    canmatrix.formats.dumpp({"": db}, outFile, dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')
    return outFile

def test_copy_ecus(tmpdir, run):
    inputFile = create_dbc()
    result = run("--ecus", "testBU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testBU2" not in content
        assert "testBU" in content

def test_copy_ecus_rx(tmpdir, run):
    inputFile = create_dbc()
    result = run("--ecus", "recBU:rx", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "recBU2" not in content
        assert "recBU" in content

def test_copy_ecus_tx(tmpdir, run):
    inputFile = create_dbc(additionalReceiver = ["testBU"])
    result = run("--ecus", "testBU:tx", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testFrame2" not in content
        assert "testFrame3" in content

def test_copy_frames(tmpdir, run):
    inputFile = create_dbc()
    result = run("--frames", "testFrame3", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","rb") as fd:
        content = fd.read()
        assert b"testFrame2" not in content
        assert b"testFrame3" in content

def test_delete_frame_attributes(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteFrameAttributes", "myAttribute", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert 'BA_ "myAttribute"' not in content

def test_delete_zero_signals(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteZeroSignals", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert 'zeroSignal' not in content


def test_delete_signal_attributes(tmpdir, run):
    inputFile = create_dbc()
    result = run("--deleteSignalAttributes", "mySignalAttribute", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
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
