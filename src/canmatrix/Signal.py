# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# With contributions 2025, Gabriele Omodeo Vanone
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

import attr
from decimal import Decimal as DefaultFloatFactory
import typing
import logging

import canmatrix.types
import canmatrix.exceptions
from canmatrix.utils import normalize_value_table
from canmatrix.FloatFactory import FloatFactory


logger = logging.getLogger(__name__)

@attr.s(eq=False)
class Signal(object):
    """
    Represents a Signal in CAN Matrix.

    Signal has following attributes:

    * name
    * start_bit (internal start_bit, see get/set_startbit also)
    * size (in Bits)
    * is_little_endian (1: Intel, 0: Motorola)
    * is_signed (bool)
    * factor, offset, min, max
    * receivers  (ECU Name)
    * attributes, _values, unit, comment
    * multiplex ('Multiplexor' or Number of Multiplex)
    * short_name (if name exceeds normal length)
    """

    name = attr.ib(default="")  # type: str
    # float_factory = attr.ib(default=defaultFloatFactory)
    float_factory = FloatFactory.get_float  # type: typing.Callable[[typing.Any], canmatrix.types.PhysicalValue]
    start_bit = attr.ib(default=0)  # type: int
    size = attr.ib(default=0)  # type: int
    is_little_endian = attr.ib(default=True)  # type: bool
    is_signed = attr.ib(default=True)  # type: bool
    offset = attr.ib(converter=float_factory)  # type: canmatrix.types.PhysicalValue
    factor = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if float_factory(value) != 0
            else float_factory(1.0)
        )
    )  # type: canmatrix.types.PhysicalValue

    unit = attr.ib(default="")  # type: str
    receivers = attr.ib(factory=list)  # type: typing.MutableSequence[str]
    comment = attr.ib(default=None)  # type: typing.Optional[str]
    multiplex = attr.ib(default=None)  # type: typing.Union[str, int]

    mux_value = attr.ib(default=None)
    is_float = attr.ib(default=False)  # type: bool
    is_ascii = attr.ib(default=False)  # type: bool
    type_label = attr.ib(default="")
    enumeration = attr.ib(default=None)  # type: typing.Optional[str]
    comments = attr.ib(factory=dict)  # type: typing.MutableMapping[int, str]
    attributes = attr.ib(factory=dict)  # type: typing.MutableMapping[str, typing.Any]
    values = attr.ib(converter=normalize_value_table, factory=dict)  # type: typing.MutableMapping[int, str]
    mux_val_grp = attr.ib(factory=list)  # type: typing.MutableSequence[list]
    muxer_for_signal = attr.ib(default=None)  # type: typing.Optional[str]

    # offset = attr.ib(converter=float_factory, default=0.0)  # type: float # ??
    calc_min_for_none = attr.ib(default=True)  # type: bool
    calc_max_for_none = attr.ib(default=True)  # type: bool

    cycle_time = attr.ib(default=0)  # type: int
    initial_value = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if value is not None
            else 0.0
        )
    )  # type: canmatrix.types.PhysicalValue
    scale_ranges = attr.ib(factory=list)
    min = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if value is not None
            else value
        )
    )  # type: typing.Union[int, decimal.Decimal, None]

    short_name = attr.ib(default="")  # type: str

    @offset.default
    def set_default_offset(self):
        # default-factory can be changed by option, so we need to initialize it during object-creation
        # to use the correct float-factory itstead of class-initialisation above
        return FloatFactory.get_float(0.0)

    @factor.default
    def set_default_factor(self):
        # default-factory can be changed by option, so we need to initialize it during object-creation
        # to use the correct float-factory itstead of class-initialisation above
        return FloatFactory.get_float(1.0)

    @initial_value.default
    def set_default_initial_value(self):
        # default-factory can be changed by option, so we need to initialize it during object-creation
        # to use the correct float-factory itstead of class-initialisation above
        FloatFactory.get_float(0.0)

    @min.default
    def set_default_min(self):  # type: () -> canmatrix.types.OptionalPhysicalValue
        return self.set_min()

    max = attr.ib(
        converter=lambda value, float_factory=float_factory: (
            float_factory(value)
            if value is not None
            else value
        )
    )  # type: canmatrix.types.OptionalPhysicalValue
    @max.default
    def set_default_max(self):
        return self.set_max()

    def __attrs_post_init__(self):
        self.multiplex = self.multiplex_setter(self.multiplex)


    @property
    def spn(self):  # type: () -> typing.Optional[int]
        """Get signal J1939 SPN or None if not defined.

        :rtype: typing.Optional[int]"""
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
            self.multiplex = 'Multiplexor'
            ret_multiplex = value
        return ret_multiplex

    def multiplexer_value_in_range(self, mux_value):
        if len(self.mux_val_grp) > 0 and mux_value is not None:
            for mux_min, mux_max in self.mux_val_grp:
                if mux_value >= mux_min and mux_value <= mux_max:
                    return True
            else:
                return False
        else:
            return mux_value == self.mux_val

    def attribute(self, attributeName, db=None, default=None):
        # type: (str, CanMatrix, typing.Any) -> typing.Any
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
        try:
            self.attributes[attribute] = str(value)
        except UnicodeDecodeError:
            self.attributes[attribute] = value
        if type(self.attributes[attribute]) == str:
            self.attributes[attribute] = self.attributes[attribute].strip()

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

        :param int or str value: signal value (0xFF)
        :param str valueName: Human readable value description ("Init")
        """
        if isinstance(value, FloatFactory.get_float_factory()):
            self.values[value.to_integral()] = valueName
        else:
            self.values[int(str(value), 0)] = valueName

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
            raise StartbitLowerZero(
                "wrong start_bit found Signal: %s Startbit: %d" % (self.name, start_bit)
            )
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
        size_to_calc = self.size if self.size <= 128 else 128
        if size_to_calc != self.size:
            logger.info("max calculation for {} not possible using 128 as base for max value".format(self.size))
        rawRange = 2 ** (size_to_calc - (1 if self.is_signed else 0))

        return (
            factory(-rawRange if self.is_signed else 0),
            factory(rawRange - 1),
        )

    def set_min(self, min=None):
        # type: (canmatrix.types.OptionalPhysicalValue) -> canmatrix.types.OptionalPhysicalValue
        """Set minimal physical Signal value.

        :param min: minimal physical value. If None and enabled (`calc_min_for_none`), compute using `calc_min`
        """
        self.min = min
        if self.calc_min_for_none and self.min is None:
            self.min = self.calc_min()

        return self.min

    def calc_min(self):  # type: () -> canmatrix.types.PhysicalValue
        """Compute minimal physical Signal value based on offset and factor and `calculate_raw_range`."""
        rawMin = self.calculate_raw_range()[0]

        return self.offset + (self.float_factory(rawMin) * self.factor)

    def set_max(self, max=None):
        # type: (canmatrix.types.OptionalPhysicalValue) -> canmatrix.types.OptionalPhysicalValue
        """Set maximal signal value.

        :param max: minimal physical value. If None and enabled (`calc_max_for_none`), compute using `calc_max`
        """
        self.max = max

        if self.calc_max_for_none and self.max is None:
            self.max = self.calc_max()

        return self.max

    def calc_max(self):  # type: () -> canmatrix.types.PhysicalValue
        """Compute maximal physical Signal value based on offset, factor and `calculate_raw_range`."""
        rawMax = self.calculate_raw_range()[1]

        return self.offset + (self.float_factory(rawMax) * self.factor)

    def phys2raw(self, value=None):
        # type: (canmatrix.types.OptionalPhysicalValue) -> canmatrix.types.RawValue
        """Return the raw value (= as is on CAN).

        :param value: (scaled) value compatible with `decimal` or value choice to encode
        :return: raw unscaled value as it appears on the bus
        :rtype: int or decimal.Decimal
        """
        if value is None:
            value = self.initial_value
            if not (self.min <= value <= self.max):
                value = self.min

        if isinstance(value, str) and self.values:
            for value_key, value_string in self.values.items():
                if value_string == value:
                    value = value_key
                    return value

        try:
            value = FloatFactory.get_float(value)
        except Exception as e:
            raise e

        # if not (0 <= value <= 10):
        if not (self.min <= value <= self.max):
            logger.warning(
                "Signal {}: Value {} is not valid for {}. Min={} and Max={}".format(
                    self.name, value, self, self.min, self.max)
                )
        raw_value = (self.float_factory(value) - self.float_factory(self.offset)) / self.float_factory(self.factor)

        if not self.is_float:
            raw_value = int(round(raw_value))

        return raw_value

    def raw2phys(self, value, decode_to_str=False):
        # type: (canmatrix.types.RawValue, bool) -> typing.Union[canmatrix.types.PhysicalValue, str]
        """Decode the given raw value (= as is on CAN).

        :param value: raw value compatible with `decimal`.
        :param bool decode_to_str: If True, try to get value representation as *string* ('Init' etc.)
        :return: physical value (scaled)
        """
        if self.is_float:
            value = self.float_factory(value)

        if decode_to_str:
            try:
                return self.values[value]
            except KeyError:
                pass

        result = value * self.factor + self.offset  # type: typing.Union[canmatrix.types.PhysicalValue, str]

        return result

    def __str__(self):  # type: () -> str
        return self.name
