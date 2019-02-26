#!/usr/bin/env python

# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,   PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR  OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# TODO: Definitions should be disassembled

from __future__ import division, absolute_import
import math
import attr
if attr.__version__ < '17.4.0':
    raise "need attrs >= 17.4.0"

import logging
import fnmatch
import decimal

try:
    from itertools import zip_longest as zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from itertools import chain
import struct

from past.builtins import basestring
import canmatrix.copy
import canmatrix.utils
logger = logging.getLogger(__name__)
defaultFloatFactory = decimal.Decimal

class ExceptionTemplate(Exception):
    def __call__(self, *args):
        return self.__class__(*(self.args + args))

class StartbitLowerZero(ExceptionTemplate): pass
class EncodingComplexMultiplexed(ExceptionTemplate): pass
class MissingMuxSignal(ExceptionTemplate): pass
class DecodingComplexMultiplexed(ExceptionTemplate): pass
class DecodingFrameLength(ExceptionTemplate): pass

@attr.s
class Ecu(object):
    """
    Contains one Boardunit/ECU
    """

    name = attr.ib(type=str)
    comment = attr.ib(default=None)
    attributes = attr.ib(type=dict, factory=dict, repr=False)

    def attribute(self, attributeName, db=None, default=None):
        """Get Board unit attribute by its name.

        :param str attributeName: attribute name.
        :param CanMatrix db: Optional database parameter to get global default attribute value.
        :param default: Default value if attribute doesn't exist.
        :return: Return the attribute value if found, else `default` or None
        """
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        elif db is not None:
            if attributeName in db.ecu_defines:
                define = db.ecu_defines[attributeName]
                return define.defaultValue
        return default

    def add_attribute(self, attribute, value):
        """
        Add the Attribute to current Boardunit/ECU. If the attribute already exists, update the value.

        :param str attribute: Attribute name
        :param any value: Attribute value
        """
        self.attributes[attribute] = value

    def del_attribute(self, attribute):
        if attribute in self.attributes:
            del self.attributes[attribute]

    def add_comment(self, comment):
        """
        Set Board unit comment.

        :param str comment: BU comment/description.
        """
        self.comment = comment


def normalize_value_table(table):
    return {int(k): v for k, v in table.items()}


@attr.s(cmp=False)
class Signal(object):
    """
    Represents a Signal in CAN Matrix.

    Signal has following attributes:

    * name
    * start_bit, size (in Bits)
    * is_little_endian (1: Intel, 0: Motorola)
    * is_signed (bool)
    * factor, offset, min, max
    * receiver  (Boarunit/ECU-Name)
    * attributes, _values, unit, comment
    * _multiplex ('Multiplexor' or Number of Multiplex)
    """

    name = attr.ib(default="")
    # float_factory = attr.ib(default=defaultFloatFactory)
    float_factory = defaultFloatFactory
    start_bit = attr.ib(type=int, default=0)
    size = attr.ib(type=int, default=0)
    is_little_endian = attr.ib(type=bool, default=True)
    is_signed = attr.ib(type=bool, default=True)
    offset = attr.ib(converter=float_factory, default=float_factory(0.0))
    factor = attr.ib(converter=float_factory, default=float_factory(1.0))

    unit = attr.ib(type=str, default="")
    receivers = attr.ib(type=list, factory=list)
    comment = attr.ib(default=None)
    multiplex = attr.ib(default=None)

    mux_value = attr.ib(default=None)
    is_float = attr.ib(type=bool, default=False)
    enumeration = attr.ib(type=str, default=None)
    comments = attr.ib(type=dict, factory=dict)
    attributes = attr.ib(type=dict, factory=dict)
    values = attr.ib(type=dict, converter=normalize_value_table, factory=dict)
    mux_val_max = attr.ib(default=0)
    mux_val_min = attr.ib(default=0)
    muxer_for_signal = attr.ib(type=str, default=None)

    # offset = attr.ib(converter=float_factory, default=0.0)
    calc_min_for_none = attr.ib(type=bool, default=True)
    calc_max_for_none = attr.ib(type=bool, default=True)

    min = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if value is not None
            else value
        )
    )
    @min.default
    def set_default_min(self):
        return self.set_min()

    max = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if value is not None
            else value
        )
    )
    @max.default
    def set_default_max(self):
        return self.set_max()

    def __attrs_post_init__(self):
        self.multiplex = self.multiplex_setter(self.multiplex)


    @property
    def spn(self):
        """Get signal J1939 SPN or None if not defined."""
        return self.attributes.get("SPN", None)

    def multiplex_setter(self, value):
        self.mux_val = None
        self.is_multiplexer = False
        ret_multiplex = None
        if value is not None and value != 'Multiplexor':
            ret_multiplex = int(value)
            self.mux_val = int(value)
        elif value == 'Multiplexor':
            self.is_multiplexer = True
            ret_multiplex = value
        return ret_multiplex

    def attribute(self, attributeName, db=None, default=None):
        """Get any Signal attribute by its name.

        :param str attributeName: attribute name, can be mandatory (ex: start_bit, size) or optional (customer) attribute.
        :param CanMatrix db: Optional database parameter to get global default attribute value.
        :param default: Default value if attribute doesn't exist.
        :return: Return the attribute value if found, else `default` or None
        """
        if attributeName in attr.fields_dict(type(self)):
            return getattr(self, attributeName)
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        if db is not None:
            if attributeName in db.signal_defines:
                define = db.signal_defines[attributeName]
                return define.defaultValue
        return default

    def add_comment(self, comment):
        """
        Set signal description.

        :param str comment: description
        """
        self.comment = comment

    def add_receiver(self, receiver):
        """Add signal receiver (ECU).

        :param str receiver: ECU name.
        """
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def del_receiver(self, receiver):
        """
        Remove receiver (ECU) from signal

        :param str receiver: ECU name.
        """
        if receiver in self.receivers:
            self.receivers.remove(receiver)

    def add_attribute(self, attribute, value):
        """
        Add user defined attribute to the Signal. Update the value if the attribute already exists.

        :param str attribute: attribute name
        :param value: attribute value
        """
        self.attributes[attribute] = value

    def del_attribute(self, attribute):
        """
        Remove user defined attribute from Signal.

        :param str attribute: attribute name
        """
        if attribute in self.attributes:
            del self.attributes[attribute]

    def add_values(self, value, valueName):
        """
        Add named Value Description to the Signal.

        :param int value: signal value (0xFF)
        :param str valueName: Human readable value description ("Init")
        """
        self.values[int(value)] = valueName

    def set_startbit(self, start_bit, bitNumbering=None, startLittle=None):
        """
        Set start_bit.

        bitNumbering is 1 for LSB0/LSBFirst, 0 for MSB0/MSBFirst.
        If bit numbering is consistent with byte order (little=LSB0, big=MSB0)
        (KCD, SYM), start bit unmodified.
        Otherwise reverse bit numbering. For DBC, ArXML (OSEK),
        both little endian and big endian use LSB0.
        If bitNumbering is None, assume consistent with byte order.
        If startLittle is set, given start_bit is assumed start from lsb bit
        rather than the start of the signal data in the message data.
        """
        # bit numbering not consistent with byte order. reverse
        if bitNumbering is not None and bitNumbering != self.is_little_endian:
            start_bit = start_bit - (start_bit % 8) + 7 - (start_bit % 8)
        # if given start_bit is for the end of signal data (lsbit),
        # convert to start of signal data (msbit)
        if startLittle is True and self.is_little_endian is False:
            start_bit = start_bit + 1 - self.size
        if start_bit < 0:
            print("wrong start_bit found Signal: %s Startbit: %d" %
                  (self.name, start_bit))
            raise StartbitLowerZero
        self.start_bit = start_bit

    def get_startbit(self, bit_numbering=None, start_little=None):
        """Get signal start bit. Handle byte and bit order."""
        startBitInternal = self.start_bit
        # convert from big endian start bit at
        # start bit(msbit) to end bit(lsbit)
        if start_little is True and self.is_little_endian is False:
            startBitInternal = startBitInternal + self.size - 1
        # bit numbering not consistent with byte order. reverse
        if bit_numbering is not None and bit_numbering != self.is_little_endian:
            startBitInternal = startBitInternal - (startBitInternal % 8) + 7 - (startBitInternal % 8)
        return int(startBitInternal)

    def calculate_raw_range(self):
        """Compute raw signal range based on Signal bit width and whether the Signal is signed or not.

        :return: Signal range, i.e. (0, 15) for unsigned 4 bit Signal or (-8, 7) for signed one.
        :rtype: tuple
        """
        factory = (
            self.float_factory
            if self.is_float
            else int
        )
        rawRange = 2 ** (self.size - (1 if self.is_signed else 0))
        return (
            factory(-rawRange if self.is_signed else 0),
            factory(rawRange - 1),
        )

    def set_min(self, min=None):
        """Set minimal physical Signal value.

        :param float or None min: minimal physical value. If None, compute using `calc_min`
        """
        self.min = min
        if self.calc_min_for_none and self.min is None:
            self.min = self.calc_min()

        return self.min

    def calc_min(self):
        """Compute minimal physical Signal value based on offset and factor and `calculate_raw_range`."""
        rawMin = self.calculate_raw_range()[0]

        return self.offset + (self.float_factory(rawMin) * self.factor)

    def set_max(self, max=None):
        """Set maximal signal value.

        :param float or None max: minimal physical value. If None, compute using `calc_max`
        """
        self.max = max

        if self.calc_max_for_none and self.max is None:
            self.max = self.calc_max()

        return self.max

    def calc_max(self):
        """Compute maximal physical Signal value based on offset, factor and `calculate_raw_range`."""
        rawMax = self.calculate_raw_range()[1]

        return self.offset + (self.float_factory(rawMax) * self.factor)


    def phys2raw(self, value=None):
        """Return the raw value (= as is on CAN).

        :param value: (scaled) value compatible with `decimal` or value choice to encode
        :return: raw unscaled value as it appears on the bus
        :rtype: int or decimal.Decimal
        """
        if value is None:
            return int(self.attributes.get('GenSigStartValue', 0))

        if isinstance(value, basestring):
            for value_key, value_string in self.values.items():
                if value_string == value:
                    value = value_key
                    break
            else:
                raise ValueError(
                        "{} is invalid value choice for {}".format(value, self)
                )

        if not (self.min <= value <= self.max):
            logger.info(
                "Value {} is not valid for {}. Min={} and Max={}".format(
                    value, self, self.min, self.max)
                )
        raw_value = (value - self.offset) / self.factor

        if not self.is_float:
            raw_value = int(raw_value)
        return raw_value

    def raw2phys(self, value, decodeToStr=False):
        """Decode the given raw value (= as is on CAN).

        :param value: raw value compatible with `decimal`.
        :param bool decodeToStr: If True, try to get value representation as *string* ('Init' etc.)
        :return: physical value (scaled)
        """

        if self.is_float:
            value = self.float_factory(value)
        value = value * self.factor + self.offset
        if decodeToStr:
            for value_key, value_string in self.values.items():
                if value_key == value:
                    value = value_string
                    break

        return value

    def __str__(self):
        return self.name


@attr.s(cmp=False)
class SignalGroup(object):
    """
    Represents signal-group, containing multiple Signals.
    """
    name = attr.ib(type=str)
    id = attr.ib(type=int)
    signals = attr.ib(type=list, factory=list, repr=False)

    def add_signal(self, signal):
        """Add a Signal to SignalGroup.

        :param Signal signal: signal to add
        """
        if signal not in self.signals:
            self.signals.append(signal)

    def del_signal(self, signal):
        """Remove Signal from SignalGroup.

        :param Signal signal: signal to remove
        """
        if signal in self.signals:
            self.signals.remove(signal)

    def by_name(self, name):
        """
        Find a Signal in the group by Signal name.

        :param str name: Signal name to find
        :return: signal contained in the group identified by name
        :rtype: Signal
        """
        for test in self.signals:
            if test.name == name:
                return test
        return None

    def __iter__(self):
        """Iterate over all contained signals."""
        return iter(self.signals)

    def __getitem__(self, name):
        signal = self.by_name(name)
        if signal:
            return signal
        raise KeyError("Signal '{}' doesn't exist".format(name))


@attr.s
class DecodedSignal(object):
    """
    Contains a decoded signal (frame decoding)

    * rawValue : rawValue (value on the bus)
    * physValue: physical Value (the scaled value)
    * namedValue: value of Valuetable
    * signal: pointer signal (object) which was decoded
    """
    raw_value = attr.ib()
    signal = attr.ib()

    @property
    def phys_value(self):
        """
        :return: physical Value (the scaled value)
        """
        return self.signal.raw2phys(self.raw_value)

    @property
    def named_value(self):
        """
        :return: value of Valuetable
        """
        return self.signal.raw2phys(self.raw_value, decodeToStr=True)


# https://docs.python.org/3/library/itertools.html
def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks."""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def unpack_bitstring(length, is_float, is_signed, bits):
    """
    returns a value calculated from bits
    :param length: length of signal in bits
    :param is_float: value is float
    :param bits: value as bits (array/iterable)
    :param is_signed: value is signed
    :return:
    """

    if is_float:
        types = {
            32: '>f',
            64: '>d'
        }

        float_type = types[length]
        value, = struct.unpack(float_type, bytearray(int(''.join(b), 2)  for b in grouper(bits, 8)))
    else:
        value = int(bits, 2)

        if is_signed and bits[0] == '1':
            value -= (1 << len(bits))

    return value

def pack_bitstring(length, is_float, value, signed):
    """
    returns a value in bits
    :param length: length of signal in bits
    :param is_float: value is float
    :param value: value to encode
    :param signed: value is signed
    :return:
    """
    if is_float:
        types = {
            32: '>f',
            64: '>d'
        }

        float_type = types[length]
        x = bytearray(struct.pack(float_type, value))
        bitstring = ''.join('{:08b}'.format(b) for b in x)
    else:
        b = '{:0{}b}'.format((2<<length )+ value, length)
        bitstring = b[-length:]

    return bitstring

@attr.s(cmp=False)
class Frame(object):
    """
    Contains one CAN Frame.

    The Frame has  following mandatory attributes

    * id,
    * name,
    * transmitters (list of boardunits/ECU-names),
    * size (= DLC),
    * signals (list of signal-objects),
    * attributes (list of attributes),
    * receivers (list of boardunits/ECU-names),
    * extended (Extended Frame = 1),
    * comment

    and any *custom* attributes in `attributes` dict.

    Frame signals can be accessed using the iterator.
    """

    name = attr.ib(default="")
    id = attr.ib(type=int, default=0)
    size = attr.ib(default=0)
    transmitters = attr.ib(type=list, factory=list)
    extended = attr.ib(type=bool, default=False)
    is_complex_multiplexed = attr.ib(type=bool, default=False)
    is_fd = attr.ib(type=bool, default=False)
    comment = attr.ib(default="")
    signals = attr.ib(type=list, factory=list)
    mux_names = attr.ib(type=dict, factory=dict)
    attributes = attr.ib(type=dict, factory=dict)
    receivers = attr.ib(type=list, factory=list)
    signalGroups = attr.ib(type=list, factory=list)

    j1939_pgn = attr.ib(default=None)
    j1939_source = attr.ib(default=0)
    j1939_prio = attr.ib(default=0)
    is_j1939 = attr.ib(type=bool, default=False)
    # ('cycleTime', '_cycleTime', int, None),
    # ('sendType', '_sendType', str, None),

    @property
    def is_multiplexed(self):
        """Frame is multiplexed if at least one of its signals is a multiplexer."""
        for sig in self.signals:
            if sig.is_multiplexer:
                return True
        return False

    @property
    def pgn(self):
        return CanId(self.id).pgn

    @pgn.setter
    def pgn(self, value):
        self.j1939_pgn = value
        self.recalc_J1939_id()

    @property
    def priority(self):
        """Get J1939 priority."""
        return self.j1939_prio

    @priority.setter
    def priority(self, value):
        """Set J1939 priority."""
        self.j1939_prio = value
        self.recalc_J1939_id()

    @property
    def source(self):
        """Get J1939 source."""
        return self.j1939_source

    @source.setter
    def source(self, value):
        """Set J1939 source."""
        self.j1939_source = value
        self.recalc_J1939_id()

    def recalc_J1939_id(self):
        """Recompute J1939 ID"""
        self.id = (self.j1939_source & 0xff) + ((self.j1939_pgn & 0xffff) << 8) + ((self.j1939_prio & 0x7) << 26)
        self.extended = True
        self.is_j1939 = True

    # @property
    # def cycleTime(self):
    #    if self._cycleTime is None:
    #        self._cycleTime = self.attribute("GenMsgCycleTime")
    #    return self._cycleTime
    #
    # @property
    # def sendType(self, db = None):
    #    if self._sendType is None:
    #        self._sendType = self.attribute("GenMsgSendType")
    #    return self._sendType
    #
    # @cycleTime.setter
    # def cycleTime(self, value):
    #    self._cycleTime = value
    #    self.attributes["GenMsgCycleTime"] = value
    #
    # @sendType.setter
    # def sendType(self, value):
    #    self._sendType = value
    #    self.attributes["GenMsgCycleTime"] = value



    def attribute(self, attributeName, db=None, default=None):
        """Get any Frame attribute by its name.

        :param str attributeName: attribute name, can be mandatory (ex: id) or optional (customer) attribute.
        :param CanMatrix db: Optional database parameter to get global default attribute value.
        :param default: Default value if attribute doesn't exist.
        :return: Return the attribute value if found, else `default` or None
        """
        if attributeName in attr.fields_dict(type(self)):
            return getattr(self, attributeName)
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        elif db is not None and attributeName in db.frame_defines:
            define = db.frame_defines[attributeName]
            return define.defaultValue
        return default

    def __iter__(self):
        """Iterator over all signals."""
        return iter(self.signals)

    def add_signal_group(self, Name, Id, signalNames):
        """Add new SignalGroup to the Frame. Add given signals to the group.

        :param str Name: Group name
        :param int Id: Group id
        :param list of str signalNames: list of Signal names to add. Non existing names are ignored.
        """
        newGroup = SignalGroup(Name, Id)
        self.signalGroups.append(newGroup)
        for signal in signalNames:
            signal = signal.strip()
            if signal.__len__() == 0:
                continue
            signalId = self.signal_by_name(signal)
            if signalId is not None:
                newGroup.add_signal(signalId)

    def signal_group_by_name(self, name):
        """Get signal group.

        :param str name: group name
        :return: SignalGroup by name or None if not found.
        :rtype: SignalGroup
        """
        for signalGroup in self.signalGroups:
            if signalGroup.name == name:
                return signalGroup
        return None

    def add_signal(self, signal):
        """
        Add Signal to Frame.

        :param Signal signal: Signal to be added.
        :return: the signal added.
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def add_transmitter(self, transmitter):
        """Add transmitter ECU Name to Frame.

        :param str transmitter: transmitter name
        """
        if transmitter not in self.transmitters:
            self.transmitters.append(transmitter)

    def del_transmitter(self, transmitter):
        """Delete transmitter ECU Name from Frame.

        :param str transmitter: transmitter name
        """
        if transmitter in self.transmitters:
            self.transmitters.remove(transmitter)

    def add_receiver(self, receiver):
        """Add receiver ECU Name to Frame.

        :param str receiver: receiver name
        """
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def signal_by_name(self, name):
        """
        Get signal by name.

        :param str name: signal name to be found.
        :return: signal with given name or None if not found
        """
        for signal in self.signals:
            if signal.name == name:
                return signal
        return None

    def glob_signals(self, globStr):
        """Find Frame Signals by given glob pattern.

        :param str globStr: glob pattern for signal name. See `fnmatch.fnmatchcase`
        :return: list of Signals by glob pattern.
        :rtype: list of Signal
        """
        returnArray = []
        for signal in self.signals:
            if fnmatch.fnmatchcase(signal.name, globStr):
                returnArray.append(signal)
        return returnArray

    def add_attribute(self, attribute, value):
        """
        Add the attribute with value to customer Frame attribute-list. If Attribute already exits, modify its value.
        :param str attribute: Attribute name
        :param any value: attribute value
        """
        try:
            self.attributes[attribute] = str(value)
        except UnicodeDecodeError:
            self.attributes[attribute] = value

    def del_attribute(self, attribute):
        """
        Remove attribute from customer Frame attribute-list.

        :param str attribute: Attribute name
        """
        if attribute in self.attributes:
            del self.attributes[attribute]

    def add_comment(self, comment):
        """
        Set Frame comment.

        :param str comment: Frame comment
        """
        self.comment = comment

    def calc_dlc(self):
        """
        Compute minimal Frame DLC (length) based on its Signals

        :return: Message DLC
        """
        maxBit = 0
        for sig in self.signals:
            if sig.get_startbit() + int(sig.size) > maxBit:
                maxBit = sig.get_startbit() + int(sig.size)
        self.size = max(self.size, int(math.ceil(maxBit / 8)))

    def get_frame_layout(self):
        """
        get layout of frame.

        Represents the bit usage in the frame by means of a list with n items (n bits of frame length).
        Every item represents one bit and contains a list of signals (object refs) with each signal, occupying that bit.
        Bits with empty list are unused.

        Example: [[], [], [], [sig1], [sig1], [sig1, sig5], [sig2, sig5], [sig2], []]
        :return: list of lists with signalnames
        :rtype: list of lists
        """
        little_bits = [[] for _dummy in range((self.size * 8))]
        big_bits = [[] for _dummy in range((self.size * 8))]
        for signal in self.signals:
            if signal.is_little_endian:
                least = len(little_bits) - signal.start_bit
                most = least - signal.size
                for little_bit_signals in little_bits[most:least]:
                    little_bit_signals.append(signal)

            else:
                most = signal.start_bit
                least = most + signal.size
                for big_bit_signals in big_bits[most:least]:
                    big_bit_signals.append(signal)

        little_bits = reversed(tuple(grouper(little_bits, 8)))
        little_bits = tuple(chain(*little_bits))

        returnList = [
            little + big
            for little, big in zip(little_bits, big_bits)
        ]

        return returnList

    def create_dummy_signals(self):
        """Create big-endian dummy signals for unused bits.

        Names of dummy signals are *_Dummy_<frame.name>_<index>*
        """
        bitfield = self.get_frame_layout()
        startBit = -1
        sigCount = 0
        for index, bit_signals in enumerate(bitfield):
            if bit_signals == [] and startBit == -1:
                startBit = index
            if (index == (len(bitfield)-1) or bit_signals != []) and startBit != -1:
                if index == (len(bitfield)-1):
                    index = len(bitfield)
                self.add_signal(Signal("_Dummy_%s_%d" % (self.name, sigCount), size=index - startBit, start_bit=startBit, is_little_endian = False))
                startBit = -1
                sigCount += 1



    def update_receiver(self):
        """
        Collect Frame receivers out of receiver given in each signal. Add them to `self.receiver` list.
        """
        for sig in self.signals:
            for receiver in sig.receivers:
                self.add_receiver(receiver)


    def signals_to_bytes(self, data):
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param data: data dictionary of signal : rawValue
        :return: A byte string of the packed values.
        """

        little_bits = [None] * (self.size * 8)
        big_bits = list(little_bits)
        for signal in self.signals:
            if signal.name in data:
                value = data.get(signal.name)
                bits = pack_bitstring(signal.size, signal.is_float, value, signal.is_signed)

                if signal.is_little_endian:
                    least = self.size * 8 - signal.start_bit
                    most = least - signal.size

                    little_bits[most:least] = bits
                else:
                    most = signal.start_bit
                    least = most + signal.size

                    big_bits[most:least] = bits
        little_bits = reversed(tuple(grouper(little_bits, 8)))
        little_bits = tuple(chain(*little_bits))
        bitstring = ''.join(
            next(x for x in (l, b, '0') if x is not None)
            # l if l != ' ' else (b if b != ' ' else '0')
            for l, b in zip(little_bits, big_bits)
        )
        return bytearray(
            int(''.join(b), 2)
            for b in grouper(bitstring, 8)
        )


    def encode(self, data=None):
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param dict data: data dictionary
        :return: A byte string of the packed values.
        """

        data = dict() if data is None else data

        if self.is_complex_multiplexed:
            raise EncodingComplexMultiplexed
        elif self.is_multiplexed:
            # search for mulitplexer-signal
            for signal in self.signals:
                if signal.is_multiplexer:
                    muxSignal = signal
                    muxVal = data.get(signal.name)
                    break
            else:
                raise MissingMuxSignal
            # create list of signals which belong to muxgroup
            encodeSignals = [muxSignal.name]
            for signal in self.signals:
                if signal.mux_val == muxVal or signal.mux_val is None:
                    encodeSignals.append(signal.name)
            newData = dict()
            # kick out signals, which do not belong to this mux-id
            for signalName in data:
                if signalName in encodeSignals:
                    newData[signalName] = data[signalName]
            data = newData
        return self.signals_to_bytes(data)

    def bytes_to_bitstrings(self, data):
        """Return two arrays big and little containing bits of given data (bytearray)

        :param data: bytearray of bits (little endian).
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :return: bit arrays in big and little byteorder
        """
        b = tuple('{:08b}'.format(b) for b in data)
        little = ''.join(reversed(b))
        big = ''.join(b)

        return little, big

    def bitstring_to_signal_list(self, signals, big, little):
        """Return OrderedDictionary with Signal Name: object decodedSignal (flat / without support for multiplexed frames)

        :param signals: Iterable of signals (class signal) to decode from frame.
        :param big: bytearray of bits (big endian).
        :param little: bytearray of bits (little endian).
        :return: array with raw values (same order like signals)
        """
        unpacked = []
        for signal in signals:
            if signal.is_little_endian:
                least = self.size * 8 - signal.start_bit
                most = least - signal.size

                bits = little[most:least]
            else:
                most = signal.start_bit
                least = most + signal.size

                bits = big[most:least]

            unpacked.append(unpack_bitstring(signal.size, signal.is_float, signal.is_signed, bits))

        return unpacked

    def unpack(self, data, report_error=True):
        """Return OrderedDictionary with Signal Name: object decodedSignal (flat / without support for multiplexed frames)
        decodes every signal in signal-list.

        :param data: bytearray
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :return: OrderedDictionary
        """

        rx_length = len(data)
        if rx_length != self.size and report_error:
            print(
                'Received message 0x{self.id:08X} with length {rx_length}, expected {self.size}'.format(**locals()))
            raise DecodingFrameLength
        else:
            little, big = self.bytes_to_bitstrings(data)

            unpacked = self.bitstring_to_signal_list(self.signals, big, little)

            returnDict= dict()

            for s, v in zip(self.signals, unpacked):
                returnDict[s.name] = DecodedSignal(v, s)

            return returnDict

    def decode(self, data):
        """Return OrderedDictionary with Signal Name: object decodedSignal (support for multiplexed frames)
        decodes only signals matching to muxgroup

        :param data: bytearray .
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :return: OrderedDictionary
        """
        decoded = self.unpack(data)

        if self.is_complex_multiplexed:
            # TODO
            raise DecodingComplexMultiplexed
        elif self.is_multiplexed:
            returnDict = dict()
            # find multiplexer and decode only its value:

            for signal in self.signals:
                if signal.is_multiplexer:
                    muxVal = decoded[signal.name].raw_value

            # find all signals with the identified multiplexer-value
            for signal in self.signals:
                if signal.mux_val == muxVal or signal.mux_val is None:
                    returnDict[signal.name] = decoded[signal.name]
            return returnDict
        else:
            return decoded


    def __str__(self):
        """Represent the frame by its name only."""
        return self.name  # add more details than the name only?

class Define(object):
    """
    Hold the defines and default-values.
    """

    def __init__(self, definition):
        """Initialize Define object.

        :param str definition: definition string. Ex: "INT -5 10"
        """
        definition = definition.strip()
        self.definition = definition
        self.type = None
        self.defaultValue = None

        def safe_convert_str_to_int(inStr):
            """Convert string to int safely. Check that it isn't float.

            :param str inStr: integer represented as string.
            :rtype: int
            """
            out = int(defaultFloatFactory(inStr))
            if out != defaultFloatFactory(inStr):
                logger.warning("Warning, integer was expected but got float: got: {0} using {1}\n".format(inStr, str(out)))
            return out

        # for any known type:
        if definition[0:3] == 'INT':
            self.type = 'INT'
            min, max = definition[4:].split(' ', 2)
            self.min = safe_convert_str_to_int(min)
            self.max = safe_convert_str_to_int(max)

        elif definition[0:6] == 'STRING':
            self.type = 'STRING'
            self.min = None
            self.max = None

        elif definition[0:4] == 'ENUM':
            self.type = 'ENUM'
            tempValues = canmatrix.utils.quote_aware_comma_split(definition[5:])
            self.values = []
            for value in tempValues:
                value = value.replace("vector_leerstring", "")
                self.values.append(value)

        elif definition[0:3] == 'HEX':  # differently rendered in DBC editor, but values are saved like for an INT
            self.type = 'HEX'
            min, max = definition[4:].split(' ', 2)
            self.min = safe_convert_str_to_int(min)
            self.max = safe_convert_str_to_int(max)

        elif definition[0:5] == 'FLOAT':
            self.type = 'FLOAT'
            min, max = definition[6:].split(' ', 2)
            self.min = defaultFloatFactory(min)
            self.max = defaultFloatFactory(max)


    def set_default(self, default):
        """Set Definition default value.

        :param default: default value; number, str or quoted str ("value")
        """
        if default is not None and len(default) > 1 and default[0] == '"' and default[-1] == '"':
            default = default[1:-1]
        self.defaultValue = default

    def update(self):
        """Update definition string for type ENUM.

        For type ENUM rebuild the definition string from current values. Otherwise do nothing.
        """
        if self.type != 'ENUM':
            return
        self.definition = 'ENUM "' + '","' .join(self.values) +'"'


@attr.s(cmp=False)
class CanMatrix(object):
    """
    The Can-Matrix-Object
    attributes (global canmatrix-attributes),
    boardUnits (list of boardunits/ECUs),
    frames (list of Frames)
    signalDefines (list of signal-attribute types)
    frameDefines (list of frame-attribute types)
    buDefines (list of BoardUnit-attribute types)
    globalDefines (list of global attribute types)
    valueTables (global defined values)
    """

    attributes = attr.ib(type=dict, factory=dict)
    ecus = attr.ib(type=list, factory=list)
    frames = attr.ib(type=list, factory=list)

    signal_defines = attr.ib(type=dict, factory=dict)
    frame_defines = attr.ib(type=dict, factory=dict)
    global_defines = attr.ib(type=dict, factory=dict)
    env_defines = attr.ib(type=dict, factory=dict)
    ecu_defines = attr.ib(type=dict, factory=dict)
    value_tables = attr.ib(type=dict, factory=dict)
    env_vars = attr.ib(type=dict, factory=dict)
    signals = attr.ib(type=list, factory=list)

    load_errors = attr.ib(type=list, factory=list)

    def __iter__(self):
        """Matrix iterates over Frames (Messages)."""
        return iter(self.frames)

    def add_env_var(self, name, envVarDict):
        self.env_vars[name] = envVarDict

    def add_env_attribute(self, env_name, attribute_name, attribute_value):
        if env_name in self.env_vars:
            if not "attributes" in self.env_vars[env_name]:
                self.env_vars[env_name]["attributes"] = dict()
            self.env_vars[env_name]["attributes"][attribute_name] = attribute_value

    @property
    def contains_fd(self):
        for frame in self.frames:
            if frame.is_fd:
                return True
        return False

    @property
    def contains_j1939(self):
        """Check whether the Matrix contains any J1939 Frame."""
        for frame in self.frames:
            if frame.is_j1939:
                return True
        return False


    def attribute(self, attributeName, default=None):
        """Return custom Matrix attribute by name.

        :param str attributeName: attribute name
        :param default: default value if given attribute doesn't exist
        :return: attribute value or default or None if no such attribute found.
        """
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        else:
            if attributeName in self.global_defines:
                define = self.global_defines[attributeName]
                return define.defaultValue

    def add_value_table(self, name, valueTable):
        """Add named value table.

        :param str name: value table name
        :param valueTable: value table itself
        """
        self.value_tables[name] = normalize_value_table(valueTable)

    def add_attribute(self, attribute, value):
        """
        Add attribute to Matrix attribute-list.

        :param str attribute: attribute name
        :param value: attribute value
        """
        self.attributes[attribute] = value

    def add_signal_defines(self, type, definition):
        """
        Add signal-attribute definition to canmatrix.

        :param str type: signal type
        :param str definition: signal-attribute string definition, see class Define
        """
        if type not in self.signal_defines:
            self.signal_defines[type] = Define(definition)

    def add_frame_defines(self, type, definition):
        """
        Add frame-attribute definition to canmatrix.

        :param str type: frame type
        :param str definition: frame definition as string
        """
        if type not in self.frame_defines:
            self.frame_defines[type] = Define(definition)

    def add_ecu_defines(self, type, definition):
        """
        Add Boardunit-attribute definition to canmatrix.

        :param str type: Boardunit type
        :param str definition: BU definition as string
        """
        if type not in self.ecu_defines:
            self.ecu_defines[type] = Define(definition)

    def add_env_defines(self, type, definition):
        """
        Add enviroment variable-attribute definition to canmatrix.

        :param str type: enviroment variable type
        :param str definition: enviroment variable definition as string
        """
        if type not in self.env_defines:
            self.env_defines[type] = Define(definition)

    def add_global_defines(self, type, definition):
        """
        Add global-attribute definition to canmatrix.

        :param str type: attribute type
        :param str definition: attribute definition as string
        """
        if type not in self.global_defines:
            self.global_defines[type] = Define(definition)

    def add_define_default(self, name, value):
        if name in self.signal_defines:
            self.signal_defines[name].set_default(value)
        if name in self.frame_defines:
            self.frame_defines[name].set_default(value)
        if name in self.ecu_defines:
            self.ecu_defines[name].set_default(value)
        if name in self.global_defines:
            self.global_defines[name].set_default(value)

    def delete_obsolete_defines(self):
        """Delete all unused Defines.

        Delete them from frameDefines, buDefines and signalDefines.
        """
        toBeDeleted = []
        for frameDef in self.frame_defines:
            found = False
            for frame in self.frames:
                if frameDef in frame.attributes:
                    found = True
                    break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(frameDef)
        for element in toBeDeleted:
            del self.frame_defines[element]
        toBeDeleted = []
        for buDef in self.ecu_defines:
            found = False
            for ecu in self.ecus:
                if buDef in ecu.attributes:
                    found = True
                    break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(buDef)
        for element in toBeDeleted:
            del self.ecu_defines[element]

        toBeDeleted = []
        for signalDef in self.signal_defines:
            found = False
            for frame in self.frames:
                for signal in frame.signals:
                    if signalDef in signal.attributes:
                        found = True
                        break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(signalDef)
        for element in toBeDeleted:
            del self.signal_defines[element]

    def frame_by_id(self, Id, extended=None):
        """Get Frame by its arbitration id.

        :param Id: Frame id as str or int
        :param extended: is it an extended id? None means "doesn't matter"
        :rtype: Frame or None
        """
        Id = int(Id)
        extendedMarker = 0x80000000
        for test in self.frames:
            if test.id == Id:
                if extended is None:
                    # found ID while ignoring extended or standard
                    return test
                elif test.extended == extended:
                    # found ID while checking extended or standard
                    return test
            else:
                if extended is not None:
                    # what to do if Id is not equal and extended is also provided ???
                    pass
                else:
                    if test.extended and Id & extendedMarker:
                        # check regarding common used extended Bit 31
                        if test.id == Id - extendedMarker:
                            return test
        return None

    def frame_by_name(self, name):
        """Get Frame by name.

        :param str name: Frame name to search for
        :rtype: Frame or None
        """
        for test in self.frames:
            if test.name == name:
                return test
        return None

    def glob_frames(self, globStr):
        """Find Frames by given glob pattern.

        :param str globStr: glob pattern to filter Frames. See `fnmatch.fnmatchcase`.
        :rtype: list of Frame
        """
        returnArray = []
        for test in self.frames:
            if fnmatch.fnmatchcase(test.name, globStr):
                returnArray.append(test)
        return returnArray

    def ecu_by_name(self, name):
        """
        Returns Boardunit by Name.

        :param str name: BoardUnit name
        :rtype: Ecu or None
        """
        for test in self.ecus:
            if test.name == name:
                return test
        return None

    def glob_ecus(self, globStr):
        """
        Find ECUs by given glob pattern.

        :param globStr: glob pattern to filter BoardUnits. See `fnmatch.fnmatchcase`.
        :rtype: list of Ecu
        """
        returnArray = []
        for test in self.ecus:
            if fnmatch.fnmatchcase(test.name, globStr):
                returnArray.append(test)
        return returnArray

    def add_frame(self, frame):
        """Add the Frame to the Matrix.

        :param Frame frame: Frame to add
        :return: the inserted Frame
        """
        self.frames.append(frame)
        return self.frames[len(self.frames) - 1]

    def remove_frame(self, frame):
        """Remove the Frame from Matrix.

        :param Frame frame: frame to remove from CAN Matrix
        """
        self.frames.remove(frame)

    def add_signal(self, signal):
        """
        Add Signal to Frame.

        :param Signal signal: Signal to be added.
        :return: the signal added.
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def remove_signal(self, signal):
        """Remove the Frame from Matrix.

        :param Frame frame: frame to remove from CAN Matrix
        """
        self.signals.remove(signal)

    def delete_zero_signals(self):
        """Delete all signals with zero bit width from all Frames."""
        for frame in self.frames:
            for signal in frame.signals:
                if 0 == signal.size:
                    frame.signals.remove(signal)

    def del_signal_attributes(self, unwantedAttributes):
        """Delete Signal attributes from all Signals of all Frames.

        :param list of str unwantedAttributes: List of attributes to remove
        """
        for frame in self.frames:
            for signal in frame.signals:
                for attrib in unwantedAttributes:
                    signal.del_attribute(attrib)

    def del_frame_attributes(self, unwantedAttributes):
        """Delete Frame attributes from all Frames.

        :param list of str unwantedAttributes: List of attributes to remove
        """
        for frame in self.frames:
            for attrib in unwantedAttributes:
                frame.del_attribute(attrib)

    def recalc_dlc(self, strategy):
        """Recompute DLC of all Frames.

        :param str strategy: selected strategy, "max" or "force".
        """
        for frame in self.frames:
            originalDlc = frame.size  # unused, remove?
            if "max" == strategy:
                frame.calc_dlc()
            if "force" == strategy:
                maxBit = 0
                for sig in frame.signals:
                    if sig.get_startbit() + int(sig.size) > maxBit:
                        maxBit = sig.get_startbit() + int(sig.size)
                frame.size = math.ceil(maxBit / 8)

    def rename_ecu(self, old, newName):
        """Rename ECU in the Matrix. Update references in all Frames.

        :param str or Ecu old: old name or ECU instance
        :param str newName: new name
        """
        if type(old).__name__ == 'instance':
            pass
        else:
            old = self.ecu_by_name(old)
        if old is None:
            return
        oldName = old.name
        old.name = newName
        for frame in self.frames:
            if oldName in frame.transmitters:
                frame.transmitters.remove(oldName)
                frame.add_transmitter(newName)
            for signal in frame.signals:
                if oldName in signal.receiver:
                    signal.receiver.remove(oldName)
                    signal.add_receiver(newName)
            frame.update_receiver()

    def add_ecu(self, ecu):
        """Add new ECU to the Matrix. Do nothing if ecu with the same name already exists.

        :param Ecu ecu: ECU name to add
        """
        for bu in self.ecus:
            if bu.name.strip() == ecu.name:
                return
        self.ecus.append(ecu)

    def del_ecu(self, ecu):
        """Remove ECU from Matrix and all Frames.

        :param str or Ecu ecu: ECU instance or glob pattern to remove from list
        """
        if type(ecu).__name__ == 'instance':
            ecuList = [ecu]
        else:
            ecuList = self.glob_ecus(ecu)

        for ecu in ecuList:
            if ecu in self.ecus:
                self.ecus.remove(ecu)
                for frame in self.frames:
                    if ecu.name in frame.transmitters:
                        frame.transmitters.remove(ecu.name)
                    for signal in frame.signals:
                        if ecu.name in signal.receiver:
                            signal.receiver.remove(ecu.name)
                    frame.update_receiver()

    def update_ecu_list(self):
        """Check all Frames and add unknown ECUs to the Matrix ECU list."""
        for frame in self.frames:
            for transmit_ecu in frame.transmitters:
                self.add_ecu(canmatrix.Ecu(transmit_ecu))
            frame.update_receiver()
            for signal in frame.signals:
                for receive_ecu in signal.receivers:
                    self.add_ecu(canmatrix.Ecu(receive_ecu))

    def rename_frame(self, old, newName):
        """Rename Frame.

        :param Frame or str old: Old Frame instance or name or part of the name with '*' at the beginning or the end.
        :param str newName: new Frame name, suffix or prefix
        """
        if type(old).__name__ == 'instance':
            old = old.name
        for frame in self.frames:
            if old[-1] == '*':
                oldPrefixLen = len(old)-1
                if frame.name[:oldPrefixLen] == old[:-1]:
                    frame.name = newName + frame.name[oldPrefixLen:]
            if old[0] == '*':
                oldSuffixLen = len(old)-1
                if frame.name[-oldSuffixLen:] == old[1:]:
                    frame.name = frame.name[:-oldSuffixLen] + newName
            elif frame.name == old:
                frame.name = newName

    def del_frame(self, frame):
        """Delete Frame from Matrix.

        :param Frame or str frame: Frame or name to delete"""
        if type(frame).__name__ == 'instance' or type(frame).__name__ == 'Frame':
            pass
        else:
            frame = self.frame_by_name(frame)
        self.frames.remove(frame)

    def rename_signal(self, old, newName):
        """Rename Signal.

        :param Signal or str old: Old Signal instance or name or part of the name with '*' at the beginning or the end.
        :param str newName: new Signal name, suffix or prefix
        """
        if type(old).__name__ == 'instance' or type(old).__name__ == 'Signal':
            old.name = newName
        else:
            for frame in self.frames:
                if old[-1] == '*':
                    oldPrefixLen = len(old) - 1
                    for signal in frame.signals:
                        if signal.name[:oldPrefixLen] == old[:-1]:
                            signal.name = newName + signal.name[oldPrefixLen:]
                if old[0] == '*':
                    oldSuffixLen = len(old) - 1
                    for signal in frame.signals:
                        if signal.name[-oldSuffixLen:] == old[1:]:
                            signal.name = signal.name[:-oldSuffixLen] + newName

                else:
                    signal = frame.signal_by_name(old)
                    if signal is not None:
                        signal.name = newName

    def del_signal(self, signal):
        """Delete Signal from Matrix and all Frames.

        :param Signal or str signal: Signal instance or glob pattern to be deleted"""
        if type(signal).__name__ == 'instance' or type(signal).__name__ == 'Signal':
            for frame in self.frames:
                if signal in frame.signals:
                    frame.signals.remove(signal)
        else:
            for frame in self.frames:
                signalList = frame.glob_signals(signal)
                for sig in signalList:
                    frame.signals.remove(sig)

    def add_signal_receiver(self, globFrame, globSignal, ecu):
        """Add Receiver to all Frames and Signals by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str globSignal: glob pattern for Signal name. Only signals under globFrame are filtered.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            for signal in frame.glob_signals(globSignal):
                signal.add_receiver(ecu)
            frame.update_receiver()

    def del_signal_receiver(self, globFrame, globSignal, ecu):
        """Delete Receiver from all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str globSignal: glob pattern for Signal name. Only signals under globFrame are filtered.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            for signal in frame.glob_signals(globSignal):
                signal.del_receiver(ecu)
            frame.update_receiver()

    def add_frame_transmitter(self, globFrame, ecu):
        """Add Transmitter to all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            frame.add_transmitter(ecu)

    def add_frame_receiver(self, globFrame, ecu):
        """Add Receiver to all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            for signal in frame.signals:
                signal.add_receiver(ecu)

    def del_frame_transmitter(self, globFrame, ecu):
        """Delete Transmitter from all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            frame.del_transmitter(ecu)

    def merge(self, mergeArray):
        """Merge multiple Matrices to this Matrix.

        Try to copy all Frames and all environment variables from source Matrices. Don't make duplicates.
        Log collisions.

        :param list of Matrix mergeArray: list of source CAN Matrices to be merged to to self.
        """
        for dbTemp in mergeArray:
            for frame in dbTemp.frames:
                copyResult = canmatrix.copy.copy_frame(frame.id, dbTemp, self)
                if copyResult == False:
                    logger.error(
                        "ID Conflict, could not copy/merge frame " + frame.name + "  %xh " % frame.id + self.frame_by_id(frame.id).name)
            for envVar in dbTemp.env_vars:
                if envVar not in self.env_vars:
                    self.add_env_var(envVar, dbTemp.envVars[envVar])
                else:
                    logger.error(
                        "Name Conflict, could not copy/merge EnvVar " + envVar)

    def set_fd_type(self):
        """Try to guess and set the CAN type for every frame.

        If a Frame is longer than 8 bytes, it must be Flexible Data Rate frame (CAN-FD).
        If not, the Frame type stays unchanged.
        """
        for frame in self.frames:
            if frame.size > 8:
                frame.is_fd = True

    def encode(self, frame_id, data):
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param frame_id: frame id
        :param data: data dictionary
        :return: A byte string of the packed values.
        """
        return self.frame_by_id(frame_id).encode(data)

    def decode(self, frame_id, data):
        """Return OrderedDictionary with Signal Name: object decodedSignal

        :param frame_id: frame id
        :param data: Iterable or bytes.
            i.e. (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8)
        :return: OrderedDictionary
        """
        return self.frame_by_id(frame_id).decode(data)

    def enum_attribs_to_values(self):
        for define in self.ecu_defines:
            if self.ecu_defines[define].type == "ENUM":
                for bu in self.ecus:
                    if define in bu.attributes:
                        bu.attributes[define] = self.ecu_defines[define].values[int(bu.attributes[define])]

        for define in self.frame_defines:
            if self.frame_defines[define].type == "ENUM":
                for frame in self.frames:
                    if define in frame.attributes:
                        frame.attributes[define] = self.frame_defines[define].values[int(frame.attributes[define])]

        for define in self.signal_defines:
            if self.signal_defines[define].type == "ENUM":
                for frame in self.frames:
                    for signal in frame.signals:
                        if define in signal.attributes:
                            signal.attributes[define] = self.signal_defines[define].values[int(signal.attributes[define])]

    def enum_attribs_to_keys(self):
        for define in self.ecu_defines:
            if self.ecu_defines[define].type == "ENUM":
                for bu in self.ecus:
                    if define in bu.attributes:
                        if len(bu.attributes[define]) > 0:
                            bu.attributes[define] = self.ecu_defines[define].values.index(bu.attributes[define])
                            bu.attributes[define] = str(bu.attributes[define])
        for define in self.frame_defines:
            if self.frame_defines[define].type == "ENUM":
                for frame in self.frames:
                    if define in frame.attributes:
                        if len(frame.attributes[define]) > 0:
                            frame.attributes[define] = self.frame_defines[define].values.index(frame.attributes[define])
                            frame.attributes[define] = str(frame.attributes[define])
        for define in self.signal_defines:
            if self.signal_defines[define].type == "ENUM":
                for frame in self.frames:
                    for signal in frame.signals:
                        if define in signal.attributes:
                            signal.attributes[define] = self.signal_defines[define].values.index(signal.attributes[define])
                            signal.attributes[define] = str(signal.attributes[define])


class CanId(object):
    """
    Split Id into Global source addresses (source, destination) off ECU and PGN (SAE J1939).
    """
    # TODO link to BoardUnit/ECU
    source = None  # Source Address
    destination = None  # Destination Address
    pgn = None  # PGN

    def __init__(self, id, extended=True):
        if extended:
            self.source = id & int('0xFF', 16)
            self.pgn = (id >> 8) & int('0xFFFF', 16)
            self.destination = id >> 8 * 3 & int('0xFF', 16)
        else:
            # TODO implement for standard Id
            pass

    def tuples(self):
        """Get tuple (destination, PGN, source)

        :rtype: tuple"""
        return self.destination, self.pgn, self.source

    def __str__(self):
        return "DA:0x{da:02X} PGN:0x{pgn:04X} SA:0x{sa:02X}".format(
            da=self.destination, pgn=self.pgn, sa=self.source)
