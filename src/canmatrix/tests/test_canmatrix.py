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
    min, max = signal.calculateRawRange()

    min_is = isinstance(min, int)
    max_is = isinstance(max, int)

    assert (min_is, max_is) == (True, True), str((type(min), type(max)))


def test_signal_range_type_float():
    signal = canmatrix.Signal(is_float=True)
    min, max = signal.calculateRawRange()

    factory_type = type(signal.float_factory())

    min_is = isinstance(min, factory_type)
    max_is = isinstance(max, factory_type)

    assert (min_is, max_is) == (True, True), str((type(min), type(max)))


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

    assert decoded_data['signal'].raw_value == float(input_data['signal'])


# Frame tests
@pytest.fixture
def empty_frame():
    return canmatrix.canmatrix.Frame(name="test_frame")


def test_frame_has_comment(empty_frame):
    empty_frame.addComment("comm")
    assert empty_frame.comment == "comm"


def test_frame_compute_dlc():
    frame = canmatrix.canmatrix.Frame()
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=0, size=2))
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=8, size=1))
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=2, size=2))
    frame.calcDLC()
    assert frame.size == 2


def test_frame_find_unused_bits():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.addSignal(canmatrix.canmatrix.Signal(name="sig1",startBit=0, size=3))
    frame.addSignal(canmatrix.canmatrix.Signal(name="sig2",startBit=4, size=2))
    bit_usage = frame.get_frame_layout()
    assert bit_usage.count([]) == frame.size*8 - 3 - 2
    sig1 = frame.signalByName("sig1")
    sig2 = frame.signalByName("sig2")
    assert bit_usage == [[], [], [sig2], [sig2], [], [sig1], [sig1], [sig1]]


def test_frame_create_dummy_signals_covers_all_bits():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=0, size=3))
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=4, size=2))
    frame.create_dummy_signals()
    assert len(frame.signals) == 2 + 2
    assert frame.get_frame_layout().count([]) == 0


def test_frame_update_receivers():
    frame = canmatrix.canmatrix.Frame(size=1)
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=0, size=3, receiver=["GW", "Keyboard"]))
    frame.addSignal(canmatrix.canmatrix.Signal(startBit=4, size=2, receiver=["GW", "Display"]))
    frame.updateReceiver()
    assert frame.receiver == ["GW", "Keyboard", "Display"]


def test_frame_to_str():
    frame = canmatrix.canmatrix.Frame(size=1, name="tank_level")
    assert str(frame) == "tank_level"


def test_frame_is_multiplexed():
    frame = canmatrix.canmatrix.Frame(name="multiplexed_frame")
    signal = canmatrix.canmatrix.Signal(name="mx")
    signal.multiplexSetter("Multiplexor")
    frame.addSignal(signal)
    assert frame.is_multiplexed


def test_frame_not_multiplexed():
    frame = canmatrix.canmatrix.Frame(name="not_multiplexed_frame")
    assert not frame.is_multiplexed
    frame.addSignal(canmatrix.canmatrix.Signal(name="some"))
    assert not frame.is_multiplexed


def test_frame_calc_j1939_id():
    # we have to set all j1939 properties in the __init__ otherwise the setters crash
    frame = canmatrix.canmatrix.Frame(j1939_source=0x11, j1939_pgn=0xFFFF, j1939_prio=0)
    frame.source = 0x22
    frame.pgn = 0xAAAA
    frame.priority = 3
    assert hex(frame.id) == hex(0x0CAAAA22)


def test_frame_get_j1939_properties():
    frame = canmatrix.canmatrix.Frame(j1939_source=0x11, j1939_pgn=0xFFFF, j1939_prio=1)
    frame.recalcJ1939Id()  # pgn property is computed from id!
    assert frame.pgn == frame.j1939_pgn
    assert frame.source == frame.j1939_source
    assert frame.priority == frame.j1939_prio


def test_frame_add_transmitter(empty_frame):
    empty_frame.addTransmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_add_transmitter_no_duplicities(empty_frame):
    empty_frame.addTransmitter("BCM")
    empty_frame.addTransmitter("BCM")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_transmitter(empty_frame):
    empty_frame.addTransmitter("MFL")
    empty_frame.addTransmitter("BCM")
    empty_frame.delTransmitter("MFL")
    assert empty_frame.transmitters == ["BCM"]


def test_frame_delete_wrong_transmitter_doesnt_raise(empty_frame):
    empty_frame.delTransmitter("wrong")


def test_frame_find_signal(empty_frame):
    empty_frame.addSignal(canmatrix.canmatrix.Signal("first"))
    second_signal = canmatrix.canmatrix.Signal("second")
    empty_frame.addSignal(second_signal)
    empty_frame.addSignal(canmatrix.canmatrix.Signal("third"))
    assert empty_frame.signalByName("second") == second_signal


def test_frame_find_missing_signal(empty_frame):
    assert empty_frame.signalByName("wrong") is None


def test_frame_glob_signals(empty_frame):
    audio_signal = canmatrix.canmatrix.Signal(name="front_audio_volume")
    empty_frame.addSignal(audio_signal)
    empty_frame.addSignal(canmatrix.canmatrix.Signal(name="display_dimming"))
    assert empty_frame.globSignals("*audio*") == [audio_signal]


def test_frame_add_attribute(empty_frame):
    empty_frame.addAttribute("attr1", "value1")
    assert empty_frame.attributes == {"attr1": "value1"}


def test_frame_del_attribute(empty_frame):
    empty_frame.addAttribute("attr1", "value1")
    empty_frame.delAttribute("attr1")
    assert "attr1" not in empty_frame.attributes


def test_frame_del_missing_attribute_doesnt_raise(empty_frame):
    empty_frame.delAttribute("wrong")


def test_frame_is_iterable(empty_frame, some_signal):
    empty_frame.addSignal(some_signal)
    assert [s for s in empty_frame] == [some_signal]


def test_frame_find_mandatory_attribute(empty_frame):
    assert empty_frame.attribute("id") == empty_frame.id


def test_frame_find_optional_attribute(empty_frame):
    empty_frame.addAttribute("attr1", "str1")
    assert empty_frame.attribute("attr1") == "str1"


def test_frame_no_attribute(empty_frame):
    assert empty_frame.attribute("wrong") is None


def test_frame_no_attribute_with_default(empty_frame):
    assert empty_frame.attribute("wrong", default=0) == 0


def test_frame_default_attr_from_db(empty_frame):
    define = canmatrix.canmatrix.Define("INT 0 255")
    define.defaultValue = 33
    matrix = canmatrix.canmatrix.CanMatrix(frameDefines={"from_db": define})
    assert empty_frame.attribute("from_db", db=matrix, default=2) == 33
    assert empty_frame.attribute("wrong", db=matrix, default=2) == 2


def test_frame_add_signal_group(empty_frame):
    signal_a = canmatrix.canmatrix.Signal(name="A")
    signal_b = canmatrix.canmatrix.Signal(name="B")
    signal_c = canmatrix.canmatrix.Signal(name="C")
    empty_frame.signals = [signal_a, signal_b, signal_c]
    empty_frame.addSignalGroup("AB", 0, ["A", "B"])
    assert empty_frame.signalGroups[0].signals == [signal_a, signal_b]


def test_frame_add_signal_group_wrong_signal(empty_frame):
    signal_a = canmatrix.canmatrix.Signal(name="A")
    empty_frame.signals = [signal_a]
    empty_frame.addSignalGroup("Aw", 0, ["A", "wrong", "\t"])
    assert empty_frame.signalGroups[0].signals == [signal_a]


def test_frame_find_signal_group(empty_frame):
    empty_frame.addSignalGroup("G1", 1, [])
    assert empty_frame.signalGroupByName("G1") is not None


def test_frame_find_wrong_signal_group(empty_frame):
    empty_frame.addSignalGroup("G1", 1, [])
    assert empty_frame.signalGroupByName("wrong") is None


# Define tests
def test_define_set_default():
    define = canmatrix.canmatrix.Define("")
    define.setDefault("string")
    assert define.defaultValue == "string"
    define.setDefault('"quoted_string"')
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


# CanId tests
def test_canid_parse_values():
    can_id = canmatrix.canmatrix.CanId(0x01ABCD02)
    assert can_id.source == 0x02
    assert can_id.destination == 0x01
    assert can_id.pgn == 0xABCD
    assert can_id.tuples() == (1, 0xABCD, 2)


def test_canid_repr():
    can_id = canmatrix.canmatrix.CanId(0x01ABCD02)
    assert str(can_id) == "DA:0x01 PGN:0xABCD SA:0x02"


# DecodedSignal tests
def test_decoded_signal_phys_value(some_signal):
    signal = canmatrix.canmatrix.Signal(factor="0.1", values={10: "Init"})
    decoded = canmatrix.canmatrix.DecodedSignal(100, signal)
    assert decoded.phys_value == decimal.Decimal("10")


def test_decoded_signal_named_value():
    signal = canmatrix.canmatrix.Signal(factor="0.1", values={10: "Init"})
    decoded = canmatrix.canmatrix.DecodedSignal(100, signal)
    assert decoded.named_value == "Init"
