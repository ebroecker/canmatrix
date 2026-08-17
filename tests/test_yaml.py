# -*- coding: utf-8 -*-

import io
import json as json_mod

import pytest
yaml = pytest.importorskip("yaml")

from canmatrix.CanMatrix import CanMatrix
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.Define import Define
import canmatrix.formats


@pytest.fixture
def default_matrix():
    matrix = CanMatrix()
    some_define = Define("INT 0 65535")
    matrix.add_value_table("Options", {0: "North", 1: "South", 2: "East", 3: "West"})

    frame = Frame(name="test_frame", arbitration_id=10)
    frame.add_attribute("my_attribute1", "my_value1")
    signal = Signal(name="test_signal", size=8)
    signal.add_values(0xFF, "Init")
    signal.add_attribute("my_attribute2", "my_value2")
    frame.add_signal(signal)

    signal = Signal(name="multi", multiplex=True, size=3, unit="attosecond")
    frame.add_signal(signal)

    matrix.add_frame(frame)
    matrix.frame_defines["my_attribute1"] = some_define
    matrix.signal_defines["my_attribute2"] = some_define
    return matrix


def test_yaml_export_all(default_matrix):
    out_file = io.BytesIO()
    canmatrix.formats.dump(default_matrix, out_file, "yaml", yamlExportAll=True)
    data = out_file.getvalue().decode("utf-8")
    assert "my_value1" in data
    assert "my_value2" in data
    assert "enumerations" in data
    assert "North" in data
    # structured YAML must NOT contain python-object tags
    assert "!!python/object" not in data


def test_yaml_round_trip(default_matrix):
    out_file = io.BytesIO()
    canmatrix.formats.dump(default_matrix, out_file, "yaml", yamlExportAll=True)
    new_matrix = canmatrix.formats.loads_flat(out_file.getvalue(), "yaml")
    assert new_matrix.frames[0].name == "test_frame"
    assert new_matrix.frames[0].signals[0].name == "test_signal"
    assert new_matrix.frames[0].attribute("my_attribute1") == "my_value1"


def test_yaml_json_structural_equivalence(default_matrix):
    # Same logical structure regardless of serialization. Align number types via
    # matching native flags. NOTE: JSON coerces integer dict keys (signal `values`
    # keys, enumeration keys) to strings, while YAML preserves ints — so normalize
    # the YAML structure by rounding it through JSON before comparing.
    json_out = io.BytesIO()
    canmatrix.formats.dump(default_matrix, json_out, "json", jsonExportAll=True, jsonNativeTypes=True)
    yaml_out = io.BytesIO()
    canmatrix.formats.dump(default_matrix, yaml_out, "yaml", yamlExportAll=True, yamlNativeTypes=True)

    json_struct = json_mod.loads(json_out.getvalue().decode("utf-8"))
    yaml_struct = yaml.safe_load(yaml_out.getvalue())
    assert json_struct == json_mod.loads(json_mod.dumps(yaml_struct))


def test_yaml_native_types_render_unquoted(default_matrix):
    out_file = io.BytesIO()
    canmatrix.formats.dump(default_matrix, out_file, "yaml", yamlExportAll=True)
    data = out_file.getvalue().decode("utf-8")
    # default yamlNativeTypes=True => numbers are not quoted strings
    assert "factor: '1'" not in data


def test_yaml_field_coverage_round_trip():
    matrix = CanMatrix()
    from canmatrix.CanMatrix import matrix_class
    from canmatrix.Ecu import Ecu
    matrix.type = matrix_class.SOMEIP
    matrix.vlan = 42

    ecu = Ecu(name="ECU1")
    ecu.add_attribute("role", "gateway")
    matrix.add_ecu(ecu)

    frame = Frame(name="f", arbitration_id=10)
    frame.receivers = ["ECU1"]
    frame.event_controlled_time = 5
    frame.debounce_time_range = 6
    frame.final_repetitions = 7
    frame.repeating_time_range = 8

    signal = Signal(name="s", size=8)
    signal.short_name = "shrt"
    signal.type_label = "tl"
    signal.enumeration = "Options"
    signal.cycle_time = 9
    signal.calc_min_for_none = False
    signal.calc_max_for_none = False
    frame.add_signal(signal)
    matrix.add_frame(frame)

    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "yaml", yamlExportAll=True)
    new_matrix = canmatrix.formats.loads_flat(out_file.getvalue(), "yaml")

    assert new_matrix.type == matrix_class.SOMEIP
    assert new_matrix.vlan == 42
    assert new_matrix.ecu_by_name("ECU1").attribute("role") == "gateway"
    new_frame = new_matrix.frames[0]
    assert new_frame.receivers == ["ECU1"]
    assert new_frame.event_controlled_time == 5
    assert new_frame.debounce_time_range == 6
    assert new_frame.final_repetitions == 7
    assert new_frame.repeating_time_range == 8
    new_signal = new_frame.signals[0]
    assert new_signal.short_name == "shrt"
    assert new_signal.type_label == "tl"
    assert new_signal.enumeration == "Options"
    assert new_signal.cycle_time == 9
    assert new_signal.calc_min_for_none is False
    assert new_signal.calc_max_for_none is False


def test_yaml_frame_id_as_hex():
    matrix = CanMatrix()
    matrix.add_frame(Frame(name="f", arbitration_id=26))

    # default: id stays an integer
    default_out = io.BytesIO()
    canmatrix.formats.dump(matrix, default_out, "yaml")
    default_struct = yaml.safe_load(default_out.getvalue())
    assert default_struct["messages"][0]["id"] == 26

    # with the flag: id is emitted as a hex string
    hex_out = io.BytesIO()
    canmatrix.formats.dump(matrix, hex_out, "yaml", yamlFrameIdAsHex=True)
    hex_struct = yaml.safe_load(hex_out.getvalue())
    assert hex_struct["messages"][0]["id"] == "0x1a"

    # and the hex export still round-trips back to the original integer id
    new_matrix = canmatrix.formats.loads_flat(hex_out.getvalue(), "yaml")
    assert new_matrix.frames[0].arbitration_id.id == 26
