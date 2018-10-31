import io

import pathlib2

import canmatrix.dbc


here = pathlib2.Path(__file__).parent


def test_long_signal_name_imports():
    long_signal_name = "FAILURE_ZELL_UNTERTEMPERATUR_ENTLADEN_ALARM_IDX_01"
    assert len(long_signal_name) > 32
    dbc = io.BytesIO(b"""\
    BO_ 1 testFrame1: 1 TEST_ECU
     SG_ {} : 1|2@0+ (1,0) [0|0] ""  CCL_TEST
    """.format(long_signal_name))

    matrix = canmatrix.dbc.load(dbc)

    assert matrix.frames[0].signals[0].name == long_signal_name
