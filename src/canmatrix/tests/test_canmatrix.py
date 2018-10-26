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


def test_encode_signal():
    s1 = canmatrix.canmatrix.Signal('signal', size=8)
    assert s1.phys2raw() == 0
    assert s1.phys2raw(1) == 1
    assert s1.phys2raw(s1.max) == 127
    assert s1.phys2raw(s1.min) == -128

    s2 = canmatrix.canmatrix.Signal('signal', size=10, is_signed=False)
    assert s2.phys2raw() == 0
    assert s2.phys2raw(10) == 10
    assert s2.phys2raw(s2.max) == 1023
    assert s2.phys2raw(s2.min) == 0

    s3 = canmatrix.canmatrix.Signal('signal', size=8, factor=2)
    assert s3.phys2raw() == 0
    assert s3.phys2raw(10) == 5
    assert s3.phys2raw(s3.max) == 127
    assert s3.phys2raw(s3.min) == -128

    s4 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, factor=5)
    assert s4.phys2raw() == 0
    assert s4.phys2raw(10) == 2
    assert s4.phys2raw(s4.max) == 255
    assert s4.phys2raw(s4.min) == 0

    s5 = canmatrix.canmatrix.Signal('signal', size=8, offset=2)
    assert s5.phys2raw() == 0
    assert s5.phys2raw(10) == 8
    assert s5.phys2raw(s5.max) == 127
    assert s5.phys2raw(s5.min) == -128

    s6 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, offset=5)
    assert s6.phys2raw() == 0
    assert s6.phys2raw(10) == 5
    assert s6.phys2raw(s6.max) == 255
    assert s6.phys2raw(s6.min) == 0

    s7 = canmatrix.canmatrix.Signal('signal', size=8)
    s7.addAttribute('GenSigStartValue', '5')
    assert s7.phys2raw() == 5

    s8 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, offset=5)
    s8.addAttribute('GenSigStartValue', '5')
    assert s8.phys2raw() == 5

    s9 = canmatrix.canmatrix.Signal('signal', size=16, is_signed=False, factor='0.001')
    assert s9.phys2raw() == 0
    assert s9.phys2raw(s9.max) == 65535
    assert s9.phys2raw(s9.min) == 0
    assert s9.phys2raw(decimal.Decimal('50.123')) == 50123

    s10 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, factor='0.00005')
    assert s10.phys2raw() == 0
    assert s10.phys2raw(s10.max) == 255
    assert s10.phys2raw(s10.min) == 0
    assert s10.phys2raw(decimal.Decimal('0.005')) == 100
    assert s10.phys2raw(decimal.Decimal('0.003')) == 60


def test_decode_signal():
    s1 = canmatrix.canmatrix.Signal('signal', size=8)
    assert s1.raw2phys(1) == 1
    assert s1.raw2phys(127) == s1.max
    assert s1.raw2phys(-128) == s1.min

    s2 = canmatrix.canmatrix.Signal('signal', size=10, is_signed=False)
    assert s2.raw2phys(10) == 10
    assert s2.raw2phys(s2.max) == 1023
    assert s2.raw2phys(s2.min) == 0

    s3 = canmatrix.canmatrix.Signal('signal', size=8, factor=2)
    assert s3.raw2phys(5) == 10
    assert s3.raw2phys(127) == s3.max
    assert s3.raw2phys(-128) == s3.min

    s4 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, factor=5)
    assert s4.raw2phys(2) == 10
    assert s4.raw2phys(255) == s4.max
    assert s4.raw2phys(0) == s4.min

    s5 = canmatrix.canmatrix.Signal('signal', size=8, offset=2)
    assert s5.raw2phys(8) == 10
    assert s5.raw2phys(127) == s5.max
    assert s5.raw2phys(-128) == s5.min

    s6 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, offset=5)
    assert s6.raw2phys(5) == 10
    assert s6.raw2phys(255) == s6.max
    assert s6.raw2phys(0) == s6.min

    s7 = canmatrix.canmatrix.Signal('signal', size=16, is_signed=False, factor='0.001')
    assert s7.raw2phys(65535) == s7.max
    assert s7.raw2phys(0) == s7.min
    assert s7.raw2phys(50123) == decimal.Decimal('50.123')

    s8 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, factor='0.00005')
    assert s8.raw2phys(255) == s8.max
    assert s8.raw2phys(0) == s8.min
    assert s8.raw2phys(1) == decimal.Decimal('0.00005')
    assert s8.raw2phys(2) == decimal.Decimal('0.0001')
    assert s8.raw2phys(3) == decimal.Decimal('0.00015')


# BoardUnit
def test_ecu_find_attribute():
    ecu = canmatrix.canmatrix.BoardUnit(name="Gateway")
    ecu.addAttribute("attr1", 255)
    assert ecu.attribute("attr1") == 255


def test_ecu_no_attribute():
    ecu = canmatrix.canmatrix.BoardUnit(name="Gateway")
    assert ecu.attribute("wrong") is None
    assert ecu.attribute("wrong", default=0) == 0


def test_ecu_default_attr_from_db():
    ecu = canmatrix.canmatrix.BoardUnit(name="Gateway")
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(buDefines={"temperature": define})
    assert ecu.attribute("temperature", db=matrix, default=2) == 33
    assert ecu.attribute("wrong", db=matrix, default=2) == 2


def test_ecu_repr():
    ecu = canmatrix.canmatrix.BoardUnit(name="Gateway")
    ecu.addComment("with bug")
    assert str(ecu) == "BoardUnit(name='Gateway', comment='with bug')"


# Signal (generic functions)
def test_signal_has_comment(some_signal):
    comment = "comment01"
    some_signal.addComment(comment)
    assert some_signal.comment == comment


def test_signal_find_mandatory_attribute(some_signal):
    assert some_signal.attribute("is_float") == some_signal.is_float


def test_signal_find_optional_attribute(some_signal):
    some_signal.addAttribute("attr1", 255)
    assert some_signal.attribute("attr1") == 255


def test_signal_no_attribute(some_signal):
    assert some_signal.attribute("wrong") is None


def test_signal_no_attribute_with_default(some_signal):
    assert some_signal.attribute("wrong", default=0) == 0


def test_signal_default_attr_from_db(some_signal):
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(signalDefines={"from_db": define})
    assert some_signal.attribute("from_db", db=matrix, default=2) == 33
    assert some_signal.attribute("wrong", db=matrix, default=2) == 2


def test_signal_no_duplicate_receiver(some_signal):
    some_signal.addReceiver("GW01")
    some_signal.addReceiver("GW01")
    assert some_signal.receiver == ["GW01"]


def test_signal_delete_receiver(some_signal):
    some_signal.addReceiver("GW01")
    some_signal.addReceiver("ESP")
    some_signal.delReceiver("GW01")
    assert some_signal.receiver == ["ESP"]


def test_signal_delete_wrong_receiver_doesnt_raise(some_signal):
    some_signal.delReceiver("wrong")


def test_signal_has_attributes(some_signal):
    some_signal.addAttribute("attr1", "val1")
    assert some_signal.attributes == {"attr1": "val1"}


def test_signal_delete_attribute(some_signal):
    some_signal.addAttribute("attr1", "val1")
    some_signal.delAttribute("attr1")
    assert some_signal.attributes == {}


def test_signal_delete_wrong_attribute_doesnt_raise(some_signal):
    some_signal.delAttribute("wrong")


def test_signal_spn(some_signal):
    assert some_signal.spn is None
    some_signal.addAttribute("SPN", 10)
    assert some_signal.spn == 10


def test_signal_set_startbit():
    signal = canmatrix.canmatrix.Signal(size=16)
    signal.setStartbit(2)
    assert signal.startBit == 2


def test_signal_set_startbit_conversion():
    signal = canmatrix.canmatrix.Signal(size=16, is_little_endian=False)
    signal.setStartbit(20, startLittle=True)
    assert signal.startBit == 5  # lsb on 20, msb is 20-15 = 5
    # TODO add test for reversed endianning


def test_signal_set_startbit_raise():
    signal = canmatrix.canmatrix.Signal(size=16, is_little_endian=False)
    with pytest.raises(Exception):
        signal.setStartbit(5, startLittle=True)  # lsb would be on -10


def test_signal_get_startbit():
    signal_big = canmatrix.canmatrix.Signal(startBit=2, size=16, is_little_endian=True)
    assert signal_big.getStartbit() == 2


def test_signal_get_startbit_conversion():
    signal_big = canmatrix.canmatrix.Signal(startBit=2, size=16, is_little_endian=False)
    assert signal_big.getStartbit(startLittle=True) == 17  # looking for "end" of the signal: 2 + (16 - 1)
    # TODO add test for reversed endianning


def test_signal_range():
    unsigned = canmatrix.canmatrix.Signal(size=8, is_signed=False)
    assert unsigned.calculateRawRange() == (decimal.Decimal(0), decimal.Decimal(255))
    signed = canmatrix.canmatrix.Signal(size=8)
    assert signed.calculateRawRange() == (decimal.Decimal(-128), decimal.Decimal(127))


def test_signal_set_min_max():
    signal = canmatrix.canmatrix.Signal(size=8, offset=100)
    signal.setMin(-5)
    signal.setMax(30)
    assert signal.min == -5
    assert signal.max == 30


def test_signal_set_default_min_max():
    signal = canmatrix.canmatrix.Signal(size=8, offset=100, min=-5, max=10)
    signal.setMin(None)
    signal.setMax(None)
    assert signal.min == -128 + 100
    assert signal.max == 127 + 100


def test_signal_decode_named_value(some_signal):
    some_signal.addValues(255, "Init")
    some_signal.addValues(254, "Error")
    assert some_signal.raw2phys(254, decodeToStr=True) == "Error"
    assert some_signal.raw2phys(200, decodeToStr=True) == 200


def test_signal_encode_named_value(some_signal):
    some_signal.addValues(255, "Init")
    some_signal.addValues(254, "Error")
    assert some_signal.phys2raw("Error") == 254


def test_signal_encode_invalid_named_value(some_signal):
    with pytest.raises(ValueError):
        some_signal.phys2raw("wrong")


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


def test_encode_decode_frame():
    input_data = {'signal': decimal.Decimal('3.5')}

    s1 = canmatrix.canmatrix.Signal('signal', size=32, is_float=True)
    f1 = canmatrix.canmatrix.Frame('frame', id=1, size=4)
    f1.addSignal(s1)

    raw_bytes = f1.encode(input_data)
    decoded_data = f1.decode(raw_bytes)

    assert decoded_data == input_data
