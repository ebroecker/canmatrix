import pytest
import decimal

import canmatrix.canmatrix


def test_signal_defaults_to_decimal():
    signal = canmatrix.canmatrix.Signal(
        offset=4,
        factor=2,
    )

    assert isinstance(signal.offset, decimal.Decimal)
    assert isinstance(signal.factor, decimal.Decimal)


# SignalGroup
def test_sinalgroup_add_remove():
    group = canmatrix.canmatrix.SignalGroup(name="TestGroup", id=1)
    signal = canmatrix.canmatrix.Signal(name="speed", size=8)
    group.addSignal(signal)
    group.addSignal(signal)
    assert len(group.signals) == 1
    assert [signal] == [s for s in group]
    assert signal == group.byName("speed")
    assert signal == group["speed"]
    assert group.byName("wrong") is None

    group.delSignal(signal)
    assert len(group.signals) == 0
    group.delSignal(canmatrix.canmatrix.Signal(name="wrong"))  # test it doesn't raise
    with pytest.raises(IndexError):
        _ = group["wrong"]
