import canmatrix.formats.xls
import decimal


def test_parse_value_name_collumn():
    value_column = "1..5"
    (mini, maxi, offset, value_table) = canmatrix.formats.xls.parse_value_name_column(value_column, "5", 4, decimal.Decimal)
    assert maxi == 5
    assert mini == 1
    assert offset == 1
    assert value_table == dict()

    value_column = "LabelX"
    (mini, maxi, offset, value_table) = canmatrix.formats.xls.parse_value_name_column(value_column, "5", 4, decimal.Decimal)
    assert maxi == 15
    assert mini == 0
    assert offset == 0
    assert value_table == {5: "LabelX"}

