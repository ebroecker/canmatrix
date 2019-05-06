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
    s7.add_attribute('GenSigStartValue', '5')
    assert s7.phys2raw() == 5

    s8 = canmatrix.canmatrix.Signal('signal', size=8, is_signed=False, offset=5)
    s8.add_attribute('GenSigStartValue', '5')
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
    ecu = canmatrix.canmatrix.Ecu(name="Gateway")
    ecu.add_attribute("attr1", 255)
    assert ecu.attribute("attr1") == 255


def test_ecu_no_attribute():
    ecu = canmatrix.canmatrix.Ecu(name="Gateway")
    assert ecu.attribute("wrong") is None
    assert ecu.attribute("wrong", default=0) == 0


def test_ecu_default_attr_from_db():
    ecu = canmatrix.canmatrix.Ecu(name="Gateway")
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(ecu_defines={"temperature": define})
    assert ecu.attribute("temperature", db=matrix, default=2) == 33
    assert ecu.attribute("wrong", db=matrix, default=2) == 2


def test_ecu_repr():
    ecu = canmatrix.canmatrix.Ecu(name="Gateway")
    ecu.add_comment("with bug")
    assert str(ecu) == "Ecu(name='Gateway', comment='with bug')"


# Signal (generic functions)
def test_signal_has_comment(some_signal):
    comment = "comment01"
    some_signal.add_comment(comment)
    assert some_signal.comment == comment


def test_signal_find_mandatory_attribute(some_signal):
    assert some_signal.attribute("is_float") == some_signal.is_float


def test_signal_find_optional_attribute(some_signal):
    some_signal.add_attribute("attr1", 255)
    assert some_signal.attribute("attr1") == 255


def test_signal_no_attribute(some_signal):
    assert some_signal.attribute("wrong") is None


def test_signal_no_attribute_with_default(some_signal):
    assert some_signal.attribute("wrong", default=0) == 0


def test_signal_default_attr_from_db(some_signal):
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(signal_defines={"from_db": define})
    assert some_signal.attribute("from_db", db=matrix, default=2) == 33
    assert some_signal.attribute("wrong", db=matrix, default=2) == 2


def test_signal_no_duplicate_receiver(some_signal):
    some_signal.add_receiver("GW01")
    some_signal.add_receiver("GW01")
    assert some_signal.receivers == ["GW01"]


def test_signal_delete_receiver(some_signal):
    some_signal.add_receiver("GW01")
    some_signal.add_receiver("ESP")
    some_signal.del_receiver("GW01")
    assert some_signal.receivers == ["ESP"]


def test_signal_delete_wrong_receiver_doesnt_raise(some_signal):
    some_signal.del_receiver("wrong")


def test_signal_has_attributes(some_signal):
    some_signal.add_attribute("attr1", "val1")
    assert some_signal.attributes == {"attr1": "val1"}


def test_signal_delete_attribute(some_signal):
    some_signal.add_attribute("attr1", "val1")
    some_signal.del_attribute("attr1")
    assert some_signal.attributes == {}


def test_signal_delete_wrong_attribute_doesnt_raise(some_signal):
    some_signal.del_attribute("wrong")


def test_signal_spn(some_signal):
    assert some_signal.spn is None
    some_signal.add_attribute("SPN", 10)
    assert some_signal.spn == 10


def test_signal_set_startbit():
    signal = canmatrix.canmatrix.Signal(size=16)
    signal.set_startbit(2)
    assert signal.start_bit == 2


def test_signal_set_startbit_conversion():
    signal = canmatrix.canmatrix.Signal(size=16, is_little_endian=False)
    signal.set_startbit(20, startLittle=True)
    assert signal.start_bit == 5  # lsb on 20, msb is 20-15 = 5
    # TODO add test for reversed endianning


def test_signal_set_startbit_raise():
    signal = canmatrix.canmatrix.Signal(size=16, is_little_endian=False)
    with pytest.raises(Exception):
        signal.set_startbit(5, startLittle=True)  # lsb would be on -10


def test_signal_get_startbit():
    signal_big = canmatrix.canmatrix.Signal(start_bit=2, size=16, is_little_endian=True)
    assert signal_big.get_startbit() == 2


def test_signal_get_startbit_conversion():
    signal_big = canmatrix.canmatrix.Signal(start_bit=2, size=16, is_little_endian=False)
    assert signal_big.get_startbit(start_little=True) == 17  # looking for "end" of the signal: 2 + (16 - 1)
    # TODO add test for reversed endianning


def test_signal_range():
    unsigned = canmatrix.canmatrix.Signal(size=8, is_signed=False)
    assert unsigned.calculate_raw_range() == (decimal.Decimal(0), decimal.Decimal(255))
    signed = canmatrix.canmatrix.Signal(size=8)
    assert signed.calculate_raw_range() == (decimal.Decimal(-128), decimal.Decimal(127))


def test_signal_set_min_max():
    signal = canmatrix.canmatrix.Signal(size=8, offset=100)
    signal.set_min(-5)
    signal.set_max(30)
    assert signal.min == -5
    assert signal.max == 30


def test_signal_set_default_min_max():
    signal = canmatrix.canmatrix.Signal(size=8, offset=100, min=-5, max=10)
    signal.set_min(None)
    signal.set_max(None)
    assert signal.min == -128 + 100
    assert signal.max == 127 + 100


def test_signal_decode_named_value(some_signal):
    some_signal.add_values(255, "Init")
    some_signal.add_values(254, "Error")
    assert some_signal.raw2phys(254, decode_to_str=True) == "Error"
    assert some_signal.raw2phys(200, decode_to_str=True) == 200


def test_signal_encode_named_value(some_signal):
    some_signal.add_values(255, "Init")
    some_signal.add_values(254, "Error")
    assert some_signal.phys2raw("Error") == 254


def test_signal_encode_invalid_named_value(some_signal):
    with pytest.raises(ValueError):
        some_signal.phys2raw("wrong")


def test_signal_min_unspecified_respects_calc_for_min_none_false():
    signal = canmatrix.Signal(calc_min_for_none=False)
    assert signal.min is None


def test_signal_min_unspecified_respects_calc_for_min_none_true():
    signal = canmatrix.Signal(size=8, is_signed=True, calc_min_for_none=True)
    assert signal.min == -128


def test_signal_min_specified_respects_calc_for_min_none_false():
    signal = canmatrix.Signal(min=42, calc_min_for_none=False)
    assert signal.min == 42


def test_signal_min_specified_respects_calc_for_min_none_true():
    signal = canmatrix.Signal(min=42, calc_min_for_none=True)
    assert signal.min == 42


def test_signal_max_unspecified_respects_calc_for_max_none_false():
    signal = canmatrix.Signal(calc_max_for_none=False)
    assert signal.max is None


def test_signal_max_unspecified_respects_calc_for_max_none_true():
    signal = canmatrix.Signal(size=8, is_signed=True, calc_max_for_none=True)
    assert signal.max == 127


def test_signal_max_specified_respects_calc_for_max_none_false():
    signal = canmatrix.Signal(max=42, calc_max_for_none=False)
    assert signal.max == 42


def test_signal_max_specified_respects_calc_for_max_none_true():
    signal = canmatrix.Signal(max=42, calc_max_for_none=True)
    assert signal.max == 42


def test_signal_range_type_int():
    signal = canmatrix.Signal(is_float=False)
    signal_min, signal_max = signal.calculate_raw_range()

    min_is = isinstance(signal_min, int)
    max_is = isinstance(signal_max, int)

    assert (min_is, max_is) == (True, True), str((type(signal_min), type(signal_max)))


def test_signal_range_type_float():
    signal = canmatrix.Signal(is_float=True)
    signal_min, signal_max = signal.calculate_raw_range()

    factory_type = type(signal.float_factory())

    min_is = isinstance(signal_min, factory_type)
    max_is = isinstance(signal_max, factory_type)

    assert (min_is, max_is) == (True, True), str((type(signal_min), type(signal_max)))

def test_signal_multiplexer_value_in_range():
    # test multiplexer ranges (complex multiplex)
    signal = canmatrix.Signal()
    signal.mux_val_grp.append([1, 2])
    signal.mux_val_grp.append([4, 5])
    assert signal.multiplexer_value_in_range(0) == False
    assert signal.multiplexer_value_in_range(1) == True
    assert signal.multiplexer_value_in_range(2) == True
    assert signal.multiplexer_value_in_range(3) == False
    assert signal.multiplexer_value_in_range(4) == True
    assert signal.multiplexer_value_in_range(5) == True
    assert signal.multiplexer_value_in_range(6) == False

    # test standard multiplexer
    signal2 = canmatrix.Signal()
    signal2.multiplex_setter(1)
    assert signal2.multiplexer_value_in_range(1) == True
    assert signal2.multiplexer_value_in_range(0) == False

    signal3 = canmatrix.Signal()
    signal3.multiplex_setter("Multiplexor")
    assert signal3.multiplexer_value_in_range(1) == False
    assert signal3.multiplexer_value_in_range(0) == False

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
    the_group.add_signal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_can_remove(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.del_signal(some_signal)
    assert len(the_group.signals) == 0


def test_signalgroup_no_duplicates(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.add_signal(some_signal)
    assert len(the_group.signals) == 1


def test_signalgroup_is_iterable(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert [some_signal] == [s for s in the_group]


def test_signalgroup_find_something(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert some_signal == the_group.by_name("speed")
    assert some_signal == the_group["speed"]


def test_signalgroup_find_nothing(the_group, some_signal):
    the_group.add_signal(some_signal)
    assert the_group.by_name("wrong") is None
    with pytest.raises(KeyError):
        _ = the_group["wrong"]


def test_signalgroup_delete_nothing(the_group, some_signal):
    the_group.add_signal(some_signal)
    the_group.del_signal(canmatrix.canmatrix.Signal())
    assert len(the_group.signals) == 1


def test_encode_decode_frame():
    input_data = {'signal': decimal.Decimal('3.5')}

    s1 = canmatrix.canmatrix.Signal('signal', size=32, is_float=True)
    f1 = canmatrix.canmatrix.Frame('frame', arbitration_id=1, size=4)
    f1.add_signal(s1)

    raw_bytes = f1.encode(input_data)
    decoded_data = f1.decode(raw_bytes)

    assert decoded_data['signal'].raw_value == float(input_data['signal'])


# Frame tests
@pytest.fixture
def empty_frame():
    return canmatrix.canmatrix.Frame(name="test_frame")


def test_frame_has_comment(empty_frame):
    empty_frame.add_comment("comm")
    assert empty_frame.comment == "comm"


def test_frame_compute_dlc():
    frame = canmatrix.canmatrix.Frame()
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=0, size=2))
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=8, size=1))
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=2, size=2))
    frame.calc_dlc()
    assert frame.size == 2


def test_frame_find_unused_bits():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.add_signal(canmatrix.canmatrix.Signal(name="sig1", start_bit=0, size=3))
    frame.add_signal(canmatrix.canmatrix.Signal(name="sig2", start_bit=4, size=2))
    bit_usage = frame.get_frame_layout()
    assert bit_usage.count([]) == frame.size*8 - 3 - 2
    sig1 = frame.signal_by_name("sig1")
    sig2 = frame.signal_by_name("sig2")
    assert bit_usage == [[], [], [sig2], [sig2], [], [sig1], [sig1], [sig1]]


def test_frame_create_dummy_signals_covers_all_bits():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=0, size=3))
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=4, size=2))
    frame.create_dummy_signals()
    assert len(frame.signals) == 2 + 2
    assert frame.get_frame_layout().count([]) == 0


def test_frame_update_receivers():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=0, size=3, receivers=["GW", "Keyboard"]))
    frame.add_signal(canmatrix.canmatrix.Signal(start_bit=4, size=2, receivers=["GW", "Display"]))
    frame.update_receiver()
    assert frame.receivers == ["GW", "Keyboard", "Display"]


def test_frame_to_str():
    frame = canmatrix.canmatrix.Frame(size=1, name="tank_level")
    assert str(frame) == "tank_level"


def test_frame_is_multiplexed():
    frame = canmatrix.canmatrix.Frame(name="multiplexed_frame")
    signal = canmatrix.canmatrix.Signal(name="mx")
    signal.multiplex_setter("Multiplexor")
    frame.add_signal(signal)
    assert frame.is_multiplexed

def test_get_multiplexer():
    frame = canmatrix.canmatrix.Frame(name="multiplexed_frame")
    signal = canmatrix.canmatrix.Signal(name="mx")
    signal.multiplex_setter("Multiplexor")
    frame.add_signal(signal)
    assert frame.get_multiplexer == signal

def test_get_multiplexer_values():
    frame = canmatrix.canmatrix.Frame(name="multiplexed_frame")
    signal = canmatrix.canmatrix.Signal(name="mx")
    signal.multiplex_setter("Multiplexor")

    signal2 = canmatrix.canmatrix.Signal(name="s2")
    signal2.multiplex_setter(2)
    frame.add_signal(signal2)

    signal3 = canmatrix.canmatrix.Signal(name="s3")
    signal3.multiplex_setter(3)
    frame.add_signal(signal3)

    signal4 = canmatrix.canmatrix.Signal(name="s4")
    signal4.multiplex_setter(None)
    frame.add_signal(signal4)

    assert frame.get_signals_for_multiplexer_value(2)[0] == signal2
    assert frame.get_signals_for_multiplexer_value(2)[1] == signal4
    assert frame.get_signals_for_multiplexer_value(3)[0] == signal3
    assert frame.get_signals_for_multiplexer_value(3)[1] == signal4
    assert frame.get_signals_for_multiplexer_value(1)[0] == signal4

def test_get_multiplexer_values():
    frame = canmatrix.canmatrix.Frame(name="multiplexed_frame")
    signal = canmatrix.canmatrix.Signal(name="mx")
    signal.multiplex_setter("Multiplexor")

    signal2 = canmatrix.canmatrix.Signal(name="s2")
    signal2.multiplex_setter(2)
    frame.add_signal(signal2)

    signal3 = canmatrix.canmatrix.Signal(name="s3")
    signal3.multiplex_setter(3)
    frame.add_signal(signal3)

    signal4 = canmatrix.canmatrix.Signal(name="s4")
    signal4.multiplex_setter(None)
    frame.add_signal(signal4)

    assert frame.get_multiplexer_values == [2,3]


def test_frame_not_multiplexed():
    frame = canmatrix.canmatrix.Frame(name="not_multiplexed_frame")
    assert not frame.is_multiplexed
    frame.add_signal(canmatrix.canmatrix.Signal(name="some"))
    assert not frame.is_multiplexed


def test_frame_calc_j1939_id():
    # we have to set all j1939 properties in the __init__ otherwise the setters crash
    frame = canmatrix.canmatrix.Frame(j1939_source=0x11, j1939_pgn=0xFFFF, j1939_prio=0)
    frame.source = 0x22
    frame.pgn = 0xAAAA
    frame.priority = 3
    assert hex(frame.arbitration_id.id) == hex(0x0CAAAA22)


def test_frame_get_j1939_properties():
    frame = canmatrix.canmatrix.Frame(j1939_source=0x11, j1939_pgn=0xFFFF, j1939_prio=1)
    frame.recalc_J1939_id()  # pgn property is computed from id!
    assert frame.pgn == frame.j1939_pgn
    assert frame.source == frame.j1939_source
    assert frame.priority == frame.j1939_prio


def test_frame_add_transmitter(empty_frame):
    empty_frame.add_transmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_add_transmitter_no_duplicities(empty_frame):
    empty_frame.add_transmitter("BCM")
    empty_frame.add_transmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_transmitter(empty_frame):
    empty_frame.add_transmitter("MFL")
    empty_frame.add_transmitter("BCM")
    empty_frame.del_transmitter("MFL")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_wrong_transmitter_doesnt_raise(empty_frame):
    empty_frame.del_transmitter("wrong")


def test_frame_find_signal(empty_frame):
    empty_frame.add_signal(canmatrix.canmatrix.Signal("first"))
    second_signal = canmatrix.canmatrix.Signal("second")
    empty_frame.add_signal(second_signal)
    empty_frame.add_signal(canmatrix.canmatrix.Signal("third"))
    assert empty_frame.signal_by_name("second") == second_signal


def test_frame_find_missing_signal(empty_frame):
    assert empty_frame.signal_by_name("wrong") is None


def test_frame_glob_signals(empty_frame):
    audio_signal = canmatrix.canmatrix.Signal(name="front_audio_volume")
    empty_frame.add_signal(audio_signal)
    empty_frame.add_signal(canmatrix.canmatrix.Signal(name="display_dimming"))
    assert empty_frame.glob_signals("*audio*") == [audio_signal]


def test_frame_add_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "value1")
    assert empty_frame.attributes == {"attr1": "value1"}


def test_frame_del_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "value1")
    empty_frame.del_attribute("attr1")
    assert "attr1" not in empty_frame.attributes


def test_frame_del_missing_attribute_doesnt_raise(empty_frame):
    empty_frame.del_attribute("wrong")


def test_frame_is_iterable(empty_frame, some_signal):
    empty_frame.add_signal(some_signal)
    assert [s for s in empty_frame] == [some_signal]


def test_frame_find_mandatory_attribute(empty_frame):
    assert empty_frame.attribute("arbitration_id") == empty_frame.arbitration_id


def test_frame_find_optional_attribute(empty_frame):
    empty_frame.add_attribute("attr1", "str1")
    assert empty_frame.attribute("attr1") == "str1"


def test_frame_no_attribute(empty_frame):
    assert empty_frame.attribute("wrong") is None


def test_frame_no_attribute_with_default(empty_frame):
    assert empty_frame.attribute("wrong", default=0) == 0


def test_frame_default_attr_from_db(empty_frame):
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(frame_defines={"from_db": define})
    assert empty_frame.attribute("from_db", db=matrix, default=2) == 33
    assert empty_frame.attribute("wrong", db=matrix, default=2) == 2


def test_frame_add_signal_group(empty_frame):
    signal_a = canmatrix.canmatrix.Signal(name="A")
    signal_b = canmatrix.canmatrix.Signal(name="B")
    signal_c = canmatrix.canmatrix.Signal(name="C")
    empty_frame.signals = [signal_a, signal_b, signal_c]
    empty_frame.add_signal_group("AB", 0, ["A", "B"])
    assert empty_frame.signalGroups[0].signals == [signal_a, signal_b]


def test_frame_add_signal_group_wrong_signal(empty_frame):
    signal_a = canmatrix.canmatrix.Signal(name="A")
    empty_frame.signals = [signal_a]
    empty_frame.add_signal_group("Aw", 0, ["A", "wrong", "\t"])
    assert empty_frame.signalGroups[0].signals == [signal_a]


def test_frame_find_signal_group(empty_frame):
    empty_frame.add_signal_group("G1", 1, [])
    assert empty_frame.signal_group_by_name("G1") is not None


def test_frame_find_wrong_signal_group(empty_frame):
    empty_frame.add_signal_group("G1", 1, [])
    assert empty_frame.signal_group_by_name("wrong") is None


# Define tests
def test_define_set_default():
    define = canmatrix.canmatrix.Define("")
    define.set_default("string")
    assert define.defaultValue == "string"
    define.set_default('"quoted_string"')
    assert define.defaultValue == "quoted_string"


def test_define_update_enum_definition():
    define = canmatrix.canmatrix.Define("")
    define.type = "ENUM"
    define.values = ["ready", "off"]
    define.update()
    assert define.definition == 'ENUM "ready","off"'


def test_define_update_ingored_non_enum():
    def_str = "INT 0 100"
    define = canmatrix.canmatrix.Define(def_str)
    define.update()
    assert define.definition == def_str


def test_define_for_int():
    define = canmatrix.canmatrix.Define("INT -5 10")
    assert define.type == "INT"
    assert define.min == -5
    assert define.max == 10


def test_define_for_hex():
    define = canmatrix.canmatrix.Define("HEX 0 255")
    assert define.type == "HEX"
    assert define.min == 0
    assert define.max == 255


def test_define_for_string():
    define = canmatrix.canmatrix.Define("STRING")
    assert define.type == "STRING"
    assert define.min is None
    assert define.max is None


def test_define_for_enum():
    define = canmatrix.canmatrix.Define('ENUM red, green')
    assert define.type == "ENUM"
    assert define.values == ["red", "green"]


def test_define_for_enum_strip_quotes():
    define = canmatrix.canmatrix.Define('ENUM "red", "green"')
    assert define.type == "ENUM"
    assert define.values == ["red", "green"]


def test_define_for_float():
    define = canmatrix.canmatrix.Define("FLOAT -2.2 111.11")
    assert define.type == "FLOAT"
    assert define.min == decimal.Decimal('-2.2')
    assert define.max == decimal.Decimal('111.11')


# J1939CanId tests
def test_canid_parse_values():
    can_id = canmatrix.ArbitrationId(id=0x01ABCD02, extended=True)
    assert can_id.j1939_source == 0x02
    assert can_id.j1939_destination == 0xcd
    assert can_id.j1939_pgn == 0xAB00
    assert can_id.j1939_destination == 0xCD
    assert can_id.j1939_priority == 0
    assert can_id.j1939_tuple == (0xCD, 0xAB00, 2)

    test_data = {0xc00000b : 0,  0xcef27fd : 61184,  0xcffcafd : 65482, 0xc000003 : 0, 0xcf00203 : 61442, 0x18fe4a03 : 65098, 0xc010305 : 256}
    for canId, pgn in test_data.items():
        assert canmatrix.ArbitrationId(id=canId, extended=True).pgn == pgn

def test_canid_repr():
    can_id = canmatrix.ArbitrationId(id=0x01ABCD02, extended=True)
    assert can_id.j1939_str == "DA:0xCD PGN:0xAB00 SA:0x02"


# DecodedSignal tests
def test_decoded_signal_phys_value(some_signal):
    signal = canmatrix.canmatrix.Signal(factor="0.1", values={10: "Init"})
    decoded = canmatrix.canmatrix.DecodedSignal(100, signal)
    assert decoded.phys_value == decimal.Decimal("10")


def test_decoded_signal_named_value():
    signal = canmatrix.canmatrix.Signal(factor="0.1", values={10: "Init"})
    decoded = canmatrix.canmatrix.DecodedSignal(100, signal)
    assert decoded.named_value == "Init"


def test_Arbitration_id():
    id_standard = canmatrix.ArbitrationId(id=0x1, extended=False)
    id_extended = canmatrix.ArbitrationId(id=0x1, extended=True)
    id_unknown = canmatrix.ArbitrationId(id=0x1, extended=None)

    id_from_int_standard = canmatrix.ArbitrationId.from_compound_integer(1)
    id_from_int_extended = canmatrix.ArbitrationId.from_compound_integer(1 | 1 << 31)

    assert id_standard.to_compound_integer() == 1
    assert id_extended.to_compound_integer() == (1 | 1 << 31)

    assert id_standard.id == 1
    assert id_extended.id == 1
    assert id_unknown.id == 1
    assert id_standard != id_extended
    assert id_standard == id_unknown
    assert id_extended == id_unknown
    assert id_from_int_standard == id_standard
    assert id_from_int_standard != id_extended
    assert id_from_int_extended == id_extended
    assert id_from_int_extended != id_standard


@pytest.fixture
def empty_matrix():
    return canmatrix.CanMatrix()


def test_canmatrix_add_attribure(empty_matrix):
    empty_matrix.add_attribute("name1", "value1")
    assert empty_matrix.attributes == {"name1": "value1"}


def test_canmatrix_get_frame_by_glob(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    f2 = canmatrix.Frame(name="nm_osek_esp")
    empty_matrix.add_frame(f2)
    assert empty_matrix.glob_frames("*osek*") == [f2]


def test_canmatrix_get_frame_by_name(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_name(empty_frame.name) == empty_frame


def test_canmatrix_get_frame_by_wrong_name(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_name("wrong") is None

def test_canmatrix_get_frame_by_pgn(empty_matrix, empty_frame):
    empty_frame.arbitration_id.id = 0xA123456
    empty_frame.arbitration_id.extended = True
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_pgn(0x1234) == empty_frame

def test_canmatrix_get_frame_by_wrong_pgn(empty_matrix, empty_frame):
    empty_frame.arbitration_id.id = 0xAB123456
    empty_frame.arbitration_id.extended = True
    empty_matrix.add_frame(empty_frame)
    assert empty_matrix.frame_by_pgn(0xAB34) == None


def test_canmatrix_iterate_over_frames(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    assert [f for f in empty_matrix] == [empty_frame]


def test_canmatrix_remove_frame(empty_matrix, empty_frame):
    empty_matrix.add_frame(empty_frame)
    empty_matrix.add_frame(canmatrix.Frame())
    empty_matrix.remove_frame(empty_frame)
    assert len(empty_matrix.frames) == 1


def test_canmatrix_rename_ecu_by_name(empty_matrix):
    ecu = canmatrix.Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu("old_name", "new name")
    assert ecu.name == "new name"


def test_canmatrix_rename_ecu_by_wrong_name(empty_matrix):
    ecu = canmatrix.Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu("wrong", "new name")
    assert ecu.name == "old_name"


def test_canmatrix_rename_ecu_by_instance(empty_matrix):
    ecu = canmatrix.Ecu(name="old_name")
    empty_matrix.add_ecu(ecu)
    empty_matrix.rename_ecu(ecu, "new name")
    assert ecu.name == "new name"


def test_canmatrix_del_ecu_by_glob(empty_matrix):
    ecu1 = canmatrix.Ecu(name="ecu1")
    ecu2 = canmatrix.Ecu(name="ecu2")
    frame = canmatrix.Frame(transmitters=["ecu2", "ecu3"])
    empty_matrix.add_ecu(ecu1)
    empty_matrix.add_ecu(ecu2)
    frame.add_signal(canmatrix.Signal(receivers=["ecu1", "ecu2"]))
    empty_matrix.add_frame(frame)
    empty_matrix.del_ecu("*2")
    assert empty_matrix.ecus == [ecu1]
    assert frame.receivers == ["ecu1"]
    assert frame.transmitters == ["ecu3"]


def test_canmatrix_del_ecu_by_instance(empty_matrix):
    ecu1 = canmatrix.Ecu(name="ecu1")
    ecu2 = canmatrix.Ecu(name="ecu2")
    empty_matrix.add_ecu(ecu1)
    empty_matrix.add_ecu(ecu2)
    empty_matrix.del_ecu(ecu1)
    assert empty_matrix.ecus == [ecu2]


def test_canmatrix_rename_frame_by_name(empty_matrix):
    f = canmatrix.Frame(name="F1")
    empty_matrix.add_frame(f)
    empty_matrix.rename_frame("F1", "F2")
    assert f.name == "F2"
    empty_matrix.rename_frame("X*", "G")
    assert f.name == "F2"
    empty_matrix.rename_frame("F*", "G")
    assert f.name == "G2"
    empty_matrix.rename_frame("*0", "9")
    assert f.name == "G2"
    empty_matrix.rename_frame("*2", "9")
    assert f.name == "G9"


def test_canmatrix_rename_frame_by_instance(empty_matrix):
    f = canmatrix.Frame(name="F1")
    empty_matrix.add_frame(f)
    empty_matrix.rename_frame(f, "F2")
    assert f.name == "F2"


def test_canmatrix_del_frame_by_name(empty_matrix):
    f1 = canmatrix.Frame(name="F1")
    f2 = canmatrix.Frame(name="F2")
    empty_matrix.add_frame(f1)
    empty_matrix.add_frame(f2)
    empty_matrix.del_frame("F1")
    empty_matrix.del_frame("bad_one")
    assert empty_matrix.frames == [f2]


def test_canmatrix_del_frame_by_instance(empty_matrix):
    f1 = canmatrix.Frame(name="F1")
    f2 = canmatrix.Frame(name="F2")
    empty_matrix.add_frame(f1)
    empty_matrix.add_frame(f2)
    empty_matrix.del_frame(f1)
    assert empty_matrix.frames == [f2]

