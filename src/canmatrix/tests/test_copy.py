# -*- coding: utf-8 -*-
import canmatrix.canmatrix
import canmatrix.copy


def test_merge():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", arbitration_id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", arbitration_id=2)
    matrix2.add_frame(frame2)

    matrix1.merge([matrix2])
    assert len(matrix1.frames) == 2


def test_copy_ecu_with_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", arbitration_id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", arbitration_id=2, transmitters= ["ECU"])
    matrix2.add_frame(frame2)
    matrix2.update_ecu_list()

    canmatrix.copy.copy_ecu_with_frames("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 2
    assert len(matrix1.ecus) == 1


def test_copy_ecu_without_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", arbitration_id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", arbitration_id=2, transmitters= ["ECU"])
    matrix2.add_frame(frame2)
    matrix2.update_ecu_list()
    matrix2.add_ecu_defines("attrib", "STRING")
    matrix2.ecu_by_name("ECU").add_attribute("attrib", "attribValue")

    canmatrix.copy.copy_ecu("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 1
    assert len(matrix1.ecus) == 1
    assert matrix1.ecu_by_name("ECU") is not None


def test_copy_ecu_with_attributes():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", arbitration_id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)
    matrix1.add_ecu_defines("some_ecu_define", "STRING")

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", arbitration_id=2, transmitters= ["ECU"])
    matrix2.add_frame(frame2)
    matrix2.update_ecu_list()
    matrix2.add_ecu_defines("Node Address", "INT 0 255")
    matrix2.add_ecu_defines("attrib", "STRING")
    matrix2.add_ecu_defines("some_ecu_define", "STRING")
    matrix2.add_define_default("some_ecu_define", "default_value")
    matrix2.ecu_by_name("ECU").add_attribute("attrib", "attribValue")
    matrix2.ecu_by_name("ECU").add_attribute("Node Address", 42)

    canmatrix.copy.copy_ecu("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 1
    assert len(matrix1.ecus) == 1
    assert matrix1.ecu_by_name("ECU") is not None
    assert matrix1.ecu_by_name("ECU").attribute("Node Address") == 42
    assert matrix1.ecu_by_name("ECU").attribute("some_ecu_define", matrix1) == "default_value"

def test_copy_frame_default_attributes():
    source = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", arbitration_id=1)
    signal = canmatrix.canmatrix.Signal("Signal1")
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    frame1.add_signal(signal)
    source.add_frame(frame1)
    source.add_frame_defines("some_attribute", "STRING")
    source.add_define_default("some_attribute", "source_frame_default")
    source.add_signal_defines("some_signal_attribute", "STRING")
    source.add_define_default("some_signal_attribute", "source_sig_default")
    source.add_frame_defines("some_attribute_without_default", "STRING")

    #test if default value only defined in source and copied to target
    target = canmatrix.canmatrix.CanMatrix()
    target.add_frame_defines("some_attribute_without_default", "STRING")
    target.add_define_default("some_attribute_without_default", "0")
    canmatrix.copy.copy_frame(frame1.arbitration_id, source, target)
    assert target.frames[0].attribute("some_attribute", target) == "source_frame_default"
    assert target.frames[0].signals[0].attribute("some_signal_attribute", target) == "source_sig_default"
    assert target.frames[0].attribute("some_attribute_without_default", target) == "0"

    # test if define already exists, but has another default value:
    target2 = canmatrix.canmatrix.CanMatrix()
    target2.add_frame_defines("some_attribute", "STRING")
    target2.add_define_default("some_attribute", "target_frame_default")
    target2.add_signal_defines("some_signal_attribute", "STRING")
    target2.add_define_default("some_signal_attribute", "target_sig_default")
    canmatrix.copy.copy_frame(frame1.arbitration_id, source, target2)
    assert target2.frames[0].attribute("some_attribute", target2) == "source_frame_default"
    assert target2.frames[0].signals[0].attribute("some_signal_attribute", target2) == "source_sig_default"
