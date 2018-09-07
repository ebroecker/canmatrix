import decimal

import canmatrix.canmatrix


def test_signal_defaults_to_decimal():
    signal = canmatrix.canmatrix.Signal(
        offset=4,
        factor=2,
    )

    assert isinstance(signal.offset, decimal.Decimal)
    assert isinstance(signal.factor, decimal.Decimal)
