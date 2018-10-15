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
@pytest.fixture
def the_group():
    return canmatrix.canmatrix.SignalGroup(name="TestGroup", id=1)


@pytest.fixture
def some_signal():
    return canmatrix.canmatrix.Signal(name="speed", size=8)


def test_signalgroup_empty(the_group):
    assert [] == the_group.signals


def test_signalgroup_can_add(the_group, some_signal):
    the_group.addSignal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_can_remove(the_group, some_signal):
    the_group.addSignal(some_signal)
    the_group.delSignal(some_signal)
    assert len(the_group.signals) == 0


def test_signalgroup_no_duplicates(the_group, some_signal):
    the_group.addSignal(some_signal)
    the_group.addSignal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_is_iterable(the_group, some_signal):
    the_group.addSignal(some_signal)
    assert [some_signal] == [s for s in the_group]


def test_signalgroup_find_something(the_group, some_signal):
    the_group.addSignal(some_signal)
    assert some_signal == the_group.byName("speed")
    assert some_signal == the_group["speed"]


def test_signalgroup_find_nothing(the_group, some_signal):
    the_group.addSignal(some_signal)
    assert the_group.byName("wrong") is None
    with pytest.raises(KeyError):
        _ = the_group["wrong"]


def test_signalgroup_delete_nothing(the_group, some_signal):
    the_group.addSignal(some_signal)
    the_group.delSignal(canmatrix.canmatrix.Signal())
    assert len(the_group.signals) == 1
