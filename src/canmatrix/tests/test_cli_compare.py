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
        args = [sys.executable,"-m","canmatrix.cli.compare"] + list(args)
        return testdir.run(*args)
    return do_run

def test_silent(tmpdir, run):
    inputFile1 = str(here / "test_frame_decoding.dbc")
    inputFile2 = str(here / "ARXML_min_max.arxml")

    normal_result = run(inputFile1 ,inputFile2)
    silent_result = run("-s", inputFile1 ,inputFile2)
    assert len(normal_result.errlines) > len(silent_result.errlines)

def test_verbose(tmpdir, run):
    inputFile1 = str(here / "test_frame_decoding.dbc")
    inputFile2 = str(here / "ARXML_min_max.arxml")

    normal_result = run(inputFile1, inputFile2)
    verbose_result = run("-vv", inputFile1 ,inputFile2)
    assert len(normal_result.errlines) < len(verbose_result.errlines)

def create_dbc():
    outFile1 = str(here / "tmpa.dbc")
    outFile2 = str(here / "tmpb.dbc")
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
    mySignal.add_values(1, "one")
    db = canmatrix.CanMatrix()
    db.add_frame(myFrame)
    canmatrix.formats.dumpp({"": db}, outFile1, dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')

    db.add_frame_defines("myAttribute","INT -5 10")
    db.add_signal_defines("mySignalAttribute", 'INT 0 65535')
    mySignal.add_attribute("mySignalAttribute", "7")
    myFrame.add_attribute("myAttribute", "42")
    mySignal.add_values(2, "two")
    myFrame.comment = "my Frame Comment"
    mySignal.comment = "my Signal Comment"
    canmatrix.formats.dumpp({"": db}, outFile2, dbcExportEncoding='iso-8859-1',
                            dbcExportCommentEncoding='iso-8859-1')
    return outFile1, outFile2

def test_frames(tmpdir, run):
    (inputFile1, inputFile2) = create_dbc()

    result = run("--frames", inputFile1, inputFile2)
    for line in result.outlines:
        assert line.startswith("Frames")

def test_attributes(tmpdir, run):
    (inputFile1, inputFile2) = create_dbc()

    reference = run(inputFile1, inputFile2)
    result = run("--attributes", inputFile1, inputFile2)
    assert len(reference.outlines) < len(result.outlines)
    assert "ATTRIBUTES" not in "".join(reference.outlines)
    assert "ATTRIBUTES" in "".join(result.outlines)

def test_value_tables(tmpdir, run):
    (inputFile1, inputFile2) = create_dbc()

    reference = run(inputFile1, inputFile2)
    result = run("--valueTable", inputFile1, inputFile2)
    assert len(reference.outlines) > len(result.outlines)
    assert "Valuetable" in "".join(reference.outlines)
    assert "Valuetable" not in "".join(result.outlines)

def test_comments(tmpdir, run):
    (inputFile1, inputFile2) = create_dbc()
    reference = run(inputFile1, inputFile2)
    result = run("--comments", inputFile1, inputFile2)
    assert len(reference.outlines) < len(result.outlines)
    assert "comment:" not in "".join(reference.outlines)
    assert "comment:" in "".join(result.outlines)

