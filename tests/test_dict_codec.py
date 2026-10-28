# -*- coding: utf-8 -*-

import io

import pytest
yaml = pytest.importorskip("yaml")

from canmatrix._canmatrix import CanMatrix
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.Ecu import Ecu
from canmatrix.compare import compare_db
import canmatrix.formats

EXPORT_ALL_OPTIONS = {"json": {"jsonExportAll": True}, "yaml": {"yamlExportAll": True}}


def round_trip(matrix, export_type):
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, export_type, **EXPORT_ALL_OPTIONS[export_type])
    return canmatrix.formats.loads_flat(out_file.getvalue(), export_type)


@pytest.fixture
def rich_matrix():
    matrix = CanMatrix()
    matrix.add_ecu(Ecu(name="testBU"))

    matrix.add_global_defines("BusType", "STRING")
    matrix.global_defines["BusType"].set_default("CAN")
    matrix.add_ecu_defines("NodeLayer", "STRING")
    matrix.ecu_defines["NodeLayer"].set_default("base")
    matrix.add_frame_defines("GenMsgCycleTime", "INT 0 65535")
    matrix.frame_defines["GenMsgCycleTime"].set_default("50")
    matrix.add_signal_defines("GenSigStartValue", "INT 0 65535")
    matrix.signal_defines["GenSigStartValue"].set_default("0")

    frame = Frame(name="test_frame", arbitration_id=ArbitrationId(0x123), size=8)
    frame.is_fd = True
    frame.add_attribute("GenMsgCycleTime", "100")
    frame.add_transmitter("testBU")

    multiplexer = Signal(name="muxer", start_bit=0, size=8, is_little_endian=True, multiplex="Multiplexor")
    frame.add_signal(multiplexer)
    muxed_zero = Signal(name="muxed_zero", start_bit=8, size=8, is_little_endian=True, multiplex=0)
    muxed_zero.add_attribute("GenSigStartValue", "5")
    frame.add_signal(muxed_zero)
    muxed_one = Signal(name="muxed_one", start_bit=8, size=8, is_little_endian=True, multiplex=1)
    frame.add_signal(muxed_one)

    frame.add_signal_group("test_group", 1, ["muxer", "muxed_zero"])
    matrix.add_frame(frame)
    matrix.update_ecu_list()
    return matrix


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_define_defaults_round_trip(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    assert new_matrix.global_defines["BusType"].defaultValue == "CAN"
    assert new_matrix.ecu_defines["NodeLayer"].defaultValue == "base"
    assert new_matrix.frame_defines["GenMsgCycleTime"].defaultValue == "50"
    assert new_matrix.signal_defines["GenSigStartValue"].defaultValue == "0"


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_only_explicit_attributes_round_trip(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    new_frame = new_matrix.frames[0]
    # the explicitly set attributes survive ...
    assert dict(new_frame.attributes) == {"GenMsgCycleTime": "100"}
    assert dict(new_frame.signal_by_name("muxed_zero").attributes) == {"GenSigStartValue": "5"}
    # ... and define defaults are not materialized as explicit attributes
    assert dict(new_frame.signal_by_name("muxed_one").attributes) == {}
    # defaults still apply through attribute lookup
    assert new_frame.signal_by_name("muxed_one").attribute("GenSigStartValue", db=new_matrix) == "0"


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_signal_group_round_trip(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    group = new_matrix.frames[0].signal_group_by_name("test_group")
    assert group is not None
    assert group.id == 1
    assert sorted(signal.name for signal in group.signals) == ["muxed_zero", "muxer"]


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_fd_flag_round_trip(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    assert new_matrix.frames[0].is_fd is True


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_multiplexing_round_trip(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    new_frame = new_matrix.frames[0]
    assert new_frame.signal_by_name("muxer").is_multiplexer is True
    # a selector value of 0 is falsy and must not be dropped
    assert new_frame.signal_by_name("muxed_zero").mux_val == 0
    assert new_frame.signal_by_name("muxed_one").mux_val == 1


def _collect_differences(result):
    differences = []
    if result.type is not None and result.result not in (None, "equal"):
        differences.append("%s %s" % (result.result, result.type))
    for child in result.children:
        differences.extend(_collect_differences(child))
    return differences


@pytest.mark.parametrize("export_type", ["json", "yaml"])
def test_round_trip_compares_equal(rich_matrix, export_type):
    new_matrix = round_trip(rich_matrix, export_type)
    assert _collect_differences(compare_db(rich_matrix, new_matrix)) == []
