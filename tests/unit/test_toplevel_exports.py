import types

import canmatrix
# tests generated/assisted by AI (mistral-ai)


def test_toplevel_classes():
    """Top-level names must be the classes, not the equally named submodules."""
    names = [
        "CanMatrix",
        "ArbitrationId",
        "DecodedSignal",
        "Define",
        "Ecu",
        "Endpoint",
        "Frame",
        "Pdu",
        "Signal",
        "SignalGroup",
    ]
    for name in names:
        obj = getattr(canmatrix, name)
        assert isinstance(obj, type), name
        assert not isinstance(obj, types.ModuleType), name


def test_toplevel_class_identity():
    """Top-level classes are the same objects as in their defining modules."""
    import sys

    import canmatrix._canmatrix
    import canmatrix.Frame
    import canmatrix.Signal

    assert canmatrix.CanMatrix is canmatrix._canmatrix.CanMatrix
    assert canmatrix.Frame is sys.modules["canmatrix.Frame"].Frame
    assert canmatrix.Signal is sys.modules["canmatrix.Signal"].Signal


def test_toplevel_exceptions():
    """Exceptions must be importable from the package root."""
    names = [
        "ExceptionTemplate",
        "StartbitLowerZero",
        "EncodingComplexMultiplexed",
        "MissingMuxSignal",
        "DecodingComplexMultiplexed",
        "DecodingFrameLength",
        "ArbitrationIdOutOfRange",
        "J1939NeedsExtendedIdentifier",
        "DecodingContainerPdu",
        "EncodingContainerPdu",
    ]
    for name in names:
        obj = getattr(canmatrix, name)
        assert isinstance(obj, type), name


def test_toplevel_submodules():
    """1.2 behavior: formats and cancluster usable via the package namespace."""
    assert isinstance(canmatrix.formats, types.ModuleType)
    assert isinstance(canmatrix.cancluster, types.ModuleType)
    assert hasattr(canmatrix.formats, "loads")


def test_toplevel_import_without_deprecation_warning():
    """Importing from the package root must not raise the shim's DeprecationWarning."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        from canmatrix import CanMatrix, Frame, Signal  # noqa: F401

