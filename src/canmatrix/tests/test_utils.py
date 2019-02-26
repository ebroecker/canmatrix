import canmatrix.utils


def test_utils_guess_value():
    assert canmatrix.utils.guess_value("true") == "1"
    assert canmatrix.utils.guess_value("True") == "1"
    assert canmatrix.utils.guess_value("TrUe") == "1"
    assert canmatrix.utils.guess_value("false") == "0"
    assert canmatrix.utils.guess_value("False") == "0"
    assert canmatrix.utils.guess_value("faLse") == "0"

