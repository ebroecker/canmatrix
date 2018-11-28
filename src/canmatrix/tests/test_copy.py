import pytest
import canmatrix.canmatrix
import canmatrix.copy

def test_merge():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.addSignal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.addFrame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2)
    matrix2.addFrame(frame2)


    matrix1.merge([matrix2])
    assert len(matrix1.frames) == 2


def test_copy_ECU_with_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.addSignal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.addFrame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2, transmitters= ["ECU"])
    matrix2.addFrame(frame2)
    matrix2.updateEcuList()

    canmatrix.copy.copyBUwithFrames("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 2
    assert len(matrix1.boardUnits) == 1

def test_copy_ECU_without_frames():
    matrix1 = canmatrix.canmatrix.CanMatrix()
    frame1 = canmatrix.canmatrix.Frame("Frame1", id=1)
    frame1.addSignal(canmatrix.canmatrix.Signal("SomeSignal"))
    matrix1.addFrame(frame1)

    matrix2 = canmatrix.canmatrix.CanMatrix()
    frame2 = canmatrix.canmatrix.Frame("Frame2", id=2, transmitters= ["ECU"])
    matrix2.addFrame(frame2)
    matrix2.updateEcuList()
    matrix2.addBUDefines("attrib", "STRING")
    matrix2.boardUnitByName("ECU").addAttribute("attrib", "attribValue")

    canmatrix.copy.copyBU("ECU", matrix2, matrix1)

    assert len(matrix1.frames) == 1
    assert len(matrix1.boardUnits) == 1
    assert matrix1.boardUnitByName("ECU") is not None