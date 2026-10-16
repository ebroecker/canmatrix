import canmatrix
from canmatrix import ArbitrationId, Frame, Signal
# tests generated/assisted by AI (mistral-ai)


def _matrix_with_frames():
    db = canmatrix.CanMatrix()
    for i in range(10):
        frame = Frame("frame%d" % i, size=8, arbitration_id=ArbitrationId(i))
        frame.add_signal(Signal("sig%d" % i, size=8, start_bit=0))
        db.add_frame(frame)
    return db


def test_frame_by_id_found():
    db = _matrix_with_frames()
    frame = db.frame_by_id(ArbitrationId(5))
    assert frame is not None
    assert frame.name == "frame5"


def test_frame_by_id_not_found():
    db = _matrix_with_frames()
    assert db.frame_by_id(ArbitrationId(0x7ff)) is None


def test_frame_by_id_repeated_lookup():
    db = _matrix_with_frames()
    first = db.frame_by_id(ArbitrationId(3))
    second = db.frame_by_id(ArbitrationId(3))
    assert first is second
    assert first.name == "frame3"


def test_frame_by_id_standard_and_extended_are_distinct():
    db = canmatrix.CanMatrix()
    frame_std = Frame("std", size=8, arbitration_id=ArbitrationId(0x100, extended=False))
    frame_ext = Frame("ext", size=8, arbitration_id=ArbitrationId(0x100, extended=True))
    db.add_frame(frame_std)
    db.add_frame(frame_ext)
    assert db.frame_by_id(ArbitrationId(0x100, extended=False)) is frame_std
    assert db.frame_by_id(ArbitrationId(0x100, extended=True)) is frame_ext


def test_frame_by_id_fresh_after_direct_list_manipulation():
    """frame_by_id must never serve stale results (#872): no cache."""
    db = _matrix_with_frames()
    frame = db.frame_by_id(ArbitrationId(5))
    assert frame is not None
    db.frames.remove(frame)  # bypass remove_frame on purpose
    assert db.frame_by_id(ArbitrationId(5)) is None


def test_cached_lookup_found():
    db = _matrix_with_frames()
    frame = db.get_frame_by_arbitration_id(ArbitrationId(5))
    assert frame is not None
    assert frame.name == "frame5"


def test_cached_lookup_not_found():
    db = _matrix_with_frames()
    assert db.get_frame_by_arbitration_id(ArbitrationId(0x7ff)) is None


def test_cached_lookup_is_cached():
    """second lookup must return the very same frame (cache hit)."""
    db = _matrix_with_frames()
    first = db.get_frame_by_arbitration_id(ArbitrationId(3))
    second = db.get_frame_by_arbitration_id(ArbitrationId(3))
    assert first is second
    assert first.name == "frame3"


def test_cached_lookup_standard_and_extended_are_distinct():
    db = canmatrix.CanMatrix()
    frame_std = Frame("std", size=8, arbitration_id=ArbitrationId(0x100, extended=False))
    frame_ext = Frame("ext", size=8, arbitration_id=ArbitrationId(0x100, extended=True))
    db.add_frame(frame_std)
    db.add_frame(frame_ext)
    assert db.get_frame_by_arbitration_id(ArbitrationId(0x100, extended=False)) is frame_std
    assert db.get_frame_by_arbitration_id(ArbitrationId(0x100, extended=True)) is frame_ext


def test_cached_lookup_invalidation_on_add():
    db = canmatrix.CanMatrix()
    frame = Frame("late", size=8, arbitration_id=ArbitrationId(0x42))
    assert db.get_frame_by_arbitration_id(ArbitrationId(0x42)) is None
    db.add_frame(frame)
    assert db.get_frame_by_arbitration_id(ArbitrationId(0x42)) is frame


def test_cached_lookup_invalidation_on_remove():
    db = _matrix_with_frames()
    assert db.get_frame_by_arbitration_id(ArbitrationId(5)) is not None
    db.remove_frame(db.frames[5])
    assert db.get_frame_by_arbitration_id(ArbitrationId(5)) is None


def test_cached_lookup_invalidation_on_del_frame():
    db = _matrix_with_frames()
    assert db.get_frame_by_arbitration_id(ArbitrationId(5)) is not None
    db.del_frame("frame5")
    assert db.get_frame_by_arbitration_id(ArbitrationId(5)) is None


def test_cached_lookup_may_be_stale_after_direct_list_manipulation():
    """documented trade-off of the cached lookup (#872): bypassing the
    matrix methods is not detected; use frame_by_id for guaranteed freshness."""
    db = _matrix_with_frames()
    frame = db.get_frame_by_arbitration_id(ArbitrationId(5))
    assert frame is not None
    db.frames.remove(frame)  # bypass remove_frame on purpose
    assert db.frame_by_id(ArbitrationId(5)) is None
    assert db.get_frame_by_arbitration_id(ArbitrationId(5)) is frame


def test_cached_lookup_not_shared_between_matrices():
    """the cache must be per instance (was a class attribute before)."""
    db1 = _matrix_with_frames()
    db2 = _matrix_with_frames()
    assert db1.get_frame_by_arbitration_id(ArbitrationId(5)) is not None
    assert db1.get_frame_by_arbitration_id(ArbitrationId(5)) is not db2.get_frame_by_arbitration_id(ArbitrationId(5))
