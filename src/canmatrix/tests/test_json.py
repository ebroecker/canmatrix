# -*- coding: utf-8 -*-

import io
import json

import pytest

import canmatrix.canmatrix
import canmatrix.formats


@pytest.fixture
def default_matrix():
    matrix = canmatrix.canmatrix.CanMatrix()
    some_define = canmatrix.Define("INT 0 65535")
    matrix.add_value_table("Options", {0: "North", 1: "South", 2: "East", 3: "West"})

    frame = canmatrix.canmatrix.Frame(name="test_frame", arbitration_id=10)
    frame.add_attribute("my_attribute1", "my_value1")
    signal = canmatrix.canmatrix.Signal(name="test_signal", size=8)
    signal.add_values(0xFF, "Init")
    signal.add_attribute("my_attribute2", "my_value2")
    frame.add_signal(signal)

    signal = canmatrix.canmatrix.Signal(name="multi", multiplex=True, size=3, unit="attosecond")
    frame.add_signal(signal)

    matrix.add_frame(frame)
    matrix.frame_defines["my_attribute1"] = some_define
    matrix.signal_defines["my_attribute2"] = some_define
    return matrix


def test_export_with_jsonall(default_matrix):
    """Check the jsonExportAll doesn't raise and export some additional field."""
    matrix = default_matrix
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", jsonExportAll=True)
    data = out_file.getvalue().decode("utf-8")
    assert "my_value1" in data
    assert "my_value2" in data
    assert "enumerations" in data
    assert "North" in data


def test_export_additional_frame_info(default_matrix):
    matrix = default_matrix
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", additionalFrameAttributes="my_attribute1")
    data = out_file.getvalue().decode("utf-8")
    assert "my_value1" in data


def test_export_long_signal_names():
    matrix = canmatrix.canmatrix.CanMatrix()
    frame = canmatrix.canmatrix.Frame(name="test_frame", arbitration_id=10)
    matrix.add_frame(frame)
    long_signal_name = "FAILURE_ZELL_UNTERTEMPERATUR_ENTLADEN_ALARM_IDX_01"
    assert len(long_signal_name) > 32
    signal = canmatrix.canmatrix.Signal(name=long_signal_name, size=8)
    frame.add_signal(signal)

    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", jsonExportAll=True)
    data = json.loads(out_file.getvalue().decode("utf-8"))

    assert data['messages'][0]['signals'][0]['name'] == long_signal_name


def test_export_min_max():
    matrix = canmatrix.canmatrix.CanMatrix()
    frame = canmatrix.canmatrix.Frame(name="test_frame", size=6, arbitration_id=10)
    signal = canmatrix.Signal(name="someSigName", size=40, min=-5, max=42)
    frame.add_signal(signal)
    matrix.add_frame(frame)
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", jsonExportAll=True)
    data = json.loads(out_file.getvalue().decode("utf-8"))
    assert(data['messages'][0]['signals'][0]['min'] == '-5')
    assert(data['messages'][0]['signals'][0]['max'] == '42')


def test_import_min_max():
    json_input = """{
        "messages": [
            {
                "attributes": {},
                "comment": "",
                "id": 10,
                "is_extended_frame": false,
                "is_fd": false,
                "length": 6,
                "name": "test_frame",
                "signals": [
                    {
                        "attributes": {},
                        "bit_length": 40,
                        "comment": null,
                        "factor": "1",
                        "is_big_endian": false,
                        "is_float": false,
                        "is_signed": true,
                        "max": "42",
                        "min": "-5",
                        "name": "someSigName",
                        "offset": "0",
                        "start_bit": 0,
                        "values": {}
                    }
                ]
            }
        ]
    }"""
    matrix = canmatrix.formats.loads_flat(json_input, "json", jsonExportAll=True)
    assert matrix.frames[0].signals[0].min == -5
    assert matrix.frames[0].signals[0].max == 42

def test_import_native():
    json_input = """{
        "messages": [
            {
                "attributes": {},
                "comment": "",
                "id": 10,
                "is_extended_frame": false,
                "is_fd": false,
                "length": 6,
                "name": "test_frame",
                "signals": [
                    {
                        "attributes": {},
                        "bit_length": 40,
                        "comment": null,
                        "factor": 0.123,
                        "is_big_endian": false,
                        "is_float": false,
                        "is_signed": true,
                        "max": 42,
                        "min": -4.2,
                        "name": "someSigName",
                        "offset": 1,
                        "start_bit": 0,
                        "values": {}
                    }
                ]
            }
        ]
    }"""
    matrix = canmatrix.formats.loads_flat(json_input, "json", jsonExportAll=True)
    assert matrix.frames[0].signals[0].min == -4.2
    assert matrix.frames[0].signals[0].max == 42
    assert matrix.frames[0].signals[0].factor == 0.123
    assert matrix.frames[0].signals[0].offset == 1


def test_import_export_enums():
    json_input = """{
        "enumerations": {
            "Options": {
                "0": "North",
                "1": "East",
                "2": "South",
                "3": "West"
            }
        },
        "messages": [
            {
                "attributes": {},
                "comment": "",
                "id": 10,
                "is_extended_frame": false,
                "is_fd": false,
                "length": 6,
                "name": "test_frame",
                "signals": [
                    {
                        "attributes": {},
                        "name": "someSigName",
                        "bit_length": 40,
                        "is_signed": true,
                        "start_bit": 0
                    }
                ]
            }
        ]
    }"""
    matrix = canmatrix.formats.loads_flat(json_input, "json")
    assert matrix.value_tables == {"Options": {0: "North", 1: "East", 2: "South", 3: "West"}}

    f_out = io.BytesIO()
    canmatrix.formats.json.dump(matrix, f_out, jsonExportAll=True)

    f_in = io.BytesIO(f_out.getvalue())
    new_matrix = canmatrix.formats.json.load(f_in)

    assert new_matrix.value_tables == {"Options": {0: "North", 1: "East", 2: "South", 3: "West"}}


def test_export_native():
    matrix = canmatrix.canmatrix.CanMatrix()
    frame = canmatrix.canmatrix.Frame(name="test_frame", size=6, arbitration_id=10)
    signal = canmatrix.Signal(name="test_sig", size=40, is_float=True, min="-4.2", max=42, factor="0.123", offset=1)
    frame.add_signal(signal)
    matrix.add_frame(frame)
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", jsonNativeTypes=True)
    data = json.loads(out_file.getvalue().decode("utf-8"))
    assert (data['messages'][0]['signals'][0]['factor'] == 0.123)
    assert (data['messages'][0]['signals'][0]['offset'] == 1)

def test_export_all_native():
    matrix = canmatrix.canmatrix.CanMatrix()
    frame = canmatrix.canmatrix.Frame(name="test_frame", size=6, arbitration_id=10)
    signal = canmatrix.Signal(name="test_sig", size=40, is_float=True, min="-4.2", max=42, factor="0.123", offset=1)
    frame.add_signal(signal)
    matrix.add_frame(frame)
    out_file = io.BytesIO()
    canmatrix.formats.dump(matrix, out_file, "json", jsonExportAll=True, jsonNativeTypes=True)
    data = json.loads(out_file.getvalue().decode("utf-8"))
    assert (data['messages'][0]['signals'][0]['min'] == -4.2)
    assert (data['messages'][0]['signals'][0]['max'] == 42)
    assert (data['messages'][0]['signals'][0]['factor'] == 0.123)
    assert (data['messages'][0]['signals'][0]['offset'] == 1)
    assert (data['messages'][0]['is_fd'] is False)
