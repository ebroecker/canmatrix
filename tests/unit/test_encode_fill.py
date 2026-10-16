import canmatrix
from canmatrix import Frame, Signal
# tests generated/assisted by AI (mistral-ai)


def _j1939_frame():
    frame = Frame("j1939_frame", size=8, is_j1939=True)
    frame.add_signal(Signal("some_signal", size=8, start_bit=0))
    return frame


def _can_frame():
    frame = Frame("can_frame", size=8)
    frame.add_signal(Signal("some_signal", size=8, start_bit=0))
    return frame


def test_j1939_encode_fills_unused_bits_with_one():
    """SAE J1939-71: bits of unset signals must be 'not available' (1)."""
    frame = _j1939_frame()
    result = frame.encode({"some_signal": 0x11})
    assert result == bytearray([0x11, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])


def test_j1939_encode_explicit_zero_fill():
    """fill_value=0 restores the old 0x00 fill for j1939 frames."""
    frame = _j1939_frame()
    result = frame.encode({"some_signal": 0x11}, fill_value=0)
    assert result == bytearray([0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


def test_can_encode_still_fills_with_zero():
    """non-j1939 frames keep the old behavior."""
    frame = _can_frame()
    result = frame.encode({"some_signal": 0x11})
    assert result == bytearray([0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


def test_can_encode_explicit_one_fill():
    """fill_value=1 enables 0xFF fill for plain can frames too."""
    frame = _can_frame()
    result = frame.encode({"some_signal": 0x11}, fill_value=1)
    assert result == bytearray([0x11, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])


def test_j1939_encode_roundtrip():
    """decode must yield the signal values regardless of the fill."""
    frame = _j1939_frame()
    encoded = frame.encode({"some_signal": 0x11})
    decoded = frame.decode(bytes(encoded))
    assert decoded["some_signal"].raw_value == 0x11


def test_j1939_fill_respects_partial_signals():
    """bits inside a byte not covered by the signal are filled too."""
    frame = Frame("j1939_nibble", size=1, is_j1939=True)
    frame.add_signal(Signal("low_nibble", size=4, start_bit=0))
    result = frame.encode({"low_nibble": 0x2})
    assert result == bytearray([0xF2])


def test_matrix_encode_fill_passthrough():
    db = canmatrix.CanMatrix()
    frame = _j1939_frame()
    db.add_frame(frame)
    result = db.encode(frame.arbitration_id, {"some_signal": 0x11})
    assert result == bytearray([0x11, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    result = db.encode(frame.arbitration_id, {"some_signal": 0x11}, fill_value=0)
    assert result == bytearray([0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
