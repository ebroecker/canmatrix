import canmatrix.canmatrix
import canmatrix.copy


def test_merge():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2)
    matrix2.add_frame(frame2)

    matrix1.merge([matrix2])
    assert len(matrix1.frames) == 2


def test_copy_ecu_with_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2, transmitters=["ECU"])
    matrix2.add_frame(frame2)
    matrix2.update_ecu_list()

    canmatrix.copy.copy_ecu_with_frames("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 2
    assert len(matrix1.ecus) == 1


def test_copy_ecu_without_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.add_signal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.add_frame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2, transmitters=["ECU"])
    matrix2.add_frame(frame2)
    matrix2.update_ecu_list()
    matrix2.add_ecu_defines("attrib", "STRING")
    matrix2.ecu_by_name("ECU").add_attribute("attrib", "attribValue")

    canmatrix.copy.copy_ecu("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 1
    assert len(matrix1.ecus) == 1
    assert matrix1.ecu_by_name("ECU") is not None
