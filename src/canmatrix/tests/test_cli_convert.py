import pytest
import pathlib2
import sys
import canmatrix.formats
pytest_plugins = ["pytester"]


here = pathlib2.Path(__file__).parent

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
    if sys.version_info > (3, 0):
        unit = u"specialCharUnit°$"
        comment = u"Multi \n Line \n Signal comment with a-umlaut: ä"
    else:
        unit = "specialCharUnit°$".decode("utf-8")
        comment = "Multi \n Line \n Signal comment with a-umlaut: ä".decode("utf-8")
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
    db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
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
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "BA_DEF_" not in content
    normal_result = run(inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "BA_DEF_" in content

def test_delete_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteEcu","testBU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testBU" not in content

def test_rename_ecu(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameEcu","testBU:renamedECU", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testBU" not in content
        assert "renamedECU" in content

def test_delete_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteSignal","someTestSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content

def test_rename_signal(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameSignal","someTestSignal:renamedSignal", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "someTestSignal" not in content
        assert "renamedSignal" in content

def test_delete_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--deleteFrame","testFrame1", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testFrame1" not in content

def test_rename_frame(tmpdir, run):
    inputFile = create_dbc_with_special_char()
    deleted_result = run("--renameFrame","testFrame1:renamedFrame", inputFile, "tmp2.dbc")
    with open("tmp2.dbc","r") as fd:
        content = fd.read()
        assert "testFrame1" not in content
        assert "renamedFrame" in content

#todo deleteZeroSignals
#todo deleteSignalAttributes
