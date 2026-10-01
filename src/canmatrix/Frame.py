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
import typing
import fnmatch

import logging

import itertools

from canmatrix.utils import arbitration_id_converter, grouper, pack_bitstring, unpack_bitstring, get_gcd
from canmatrix.AutosarE2EProperties import AutosarE2EProperties
from canmatrix.AutosarSecOCProperties import AutosarSecOCProperties
from canmatrix.DecodedSignal import DecodedSignal
from canmatrix.SignalGroup import SignalGroup
from canmatrix.Signal import Signal
from canmatrix.exceptions import EncodingContainerPdu, DecodingContainerPdu, DecodingFrameLength
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.Pdu import Pdu
from canmatrix.exceptions import EncodingComplexMultiplexed, MissingMuxSignal, DecodingContainerPdu
from canmatrix.types import RawValue

@attr.s(eq=False)
class Frame(object):
    """
    Represents CAN Frame.

    The Frame has following mandatory attributes

    * arbitration_id,
    * name,
    * transmitters (list of ECU names),
    * size (DLC),
    * signals (list of signal-objects),
    * attributes (list of attributes),
    * receivers (list of ECU names),
    * comment

    and any *custom* attributes in `attributes` dict.

    Frame signals can be accessed using the iterator.
    """

    name = attr.ib(default="")  # type: str
    # mypy Unsupported converter:
    arbitration_id = attr.ib(converter=arbitration_id_converter, default=0)  # type: ArbitrationId
    size = attr.ib(default=0)  # type: int
    transmitters = attr.ib(factory=list)  # type: typing.MutableSequence[str]
    # extended = attr.ib(default=False)  # type: bool
    is_complex_multiplexed = attr.ib(default=False)  # type: bool
    is_fd = attr.ib(default=False)  # type: bool
    comment = attr.ib(default="")  # type: str
    signals = attr.ib(factory=list)  # type: typing.MutableSequence[Signal]
    mux_names = attr.ib(factory=dict)  # type: typing.MutableMapping[int, str]
    attributes = attr.ib(factory=dict)  # type: typing.MutableMapping[str, typing.Any]
    receivers = attr.ib(factory=list)  # type: typing.MutableSequence[str]
    signalGroups = attr.ib(factory=list)  # type: typing.MutableSequence[SignalGroup]

    cycle_time = attr.ib(default=0)  # type: int
    event_controlled_time = attr.ib(default=0)  # type: int
    debounce_time_range = attr.ib(default=0)  # type: int
    final_repetitions = attr.ib(default=0)  # type: int
    repeating_time_range = attr.ib(default=0)  # type: int

    is_j1939 = attr.ib(default=False)  # type: bool
    # ('cycleTime', '_cycleTime', int, None),
    # ('sendType', '_sendType', str, None),

    pdus = attr.ib(factory=list)  # type: typing.MutableSequence[CanMatrix.Pdu]
    pdu_name = attr.ib(default="")  # type: str

    header_id = attr.ib(default=None)  # type: int
    endpoints = attr.ib(default=None)  # type: typing.MutableSequence[Endpoint]

    secOC_properties = attr.ib(default=None)  # type:  Optional[AutosarSecOCProperties]

    @property
    def is_multiplexed(self):  # type: () -> bool
        """Frame is multiplexed if at least one of its signals is a multiplexer."""
        for sig in self.signals:
            if sig.is_multiplexer:
                return True
        return False

    @property
    def get_multiplexer(self):  # type: () -> typing.Union[Signal, None]
        """get multiplexer signal if any in frame."""
        for sig in self.signals:
            if sig.is_multiplexer:
                return sig
        return None

    @property
    def get_multiplexer_values(self):  # type: () -> typing.Sequence[int]
        """get possible multiplexer values."""
        multiplexer_values = {
            sig.mux_val
            for sig in self.signals
            if sig.mux_val is not None
        }
        return list(multiplexer_values)

    def get_signals_for_multiplexer_value(self, mux_value):
        # type: (int) -> typing.Sequence[Signal]
        """Find Frame Signals by given muxer value.
        :param int mux_value: muxer value
        :return: list of signals relevant for given muxer value.
        :rtype: list of signals
        """
        muxed_signals = []
        for sig in self.signals:
            if (sig.mux_val is None and not sig.is_multiplexer) or sig.mux_val == mux_value:
                muxed_signals.append(sig)
        return muxed_signals

    @property
    def is_pdu_container(self):  # type: () -> bool
        return len(self.pdus) > 0

    @property
    def get_pdu_id_values(self):  # type: () -> typing.Sequence[int]
        return list({pdu.id for pdu in self.pdus})

    @property
    def pgn(self):  # type: () -> int
        return self.arbitration_id.pgn

    @pgn.setter
    def pgn(self, value):  # type: (int) -> None
        self.arbitration_id.pgn = value

    @property
    def priority(self):  # type: () -> int
        """Get J1939 priority."""
        return self.arbitration_id.j1939_priority

    @priority.setter
    def priority(self, value):  # type: (int) -> None
        """Set J1939 priority."""
        self.arbitration_id.j1939_priority = value

    @property
    def source(self):  # type: () -> int
        """Get J1939 source."""
        return  self.arbitration_id.j1939_source

    @source.setter
    def source(self, value):  # type: (int) -> None
        """Set J1939 source."""
        self.arbitration_id.j1939_source = value

    @property
    def effective_cycle_time(self):
        """Calculate effective cycle time for frame, depending on signal cycle times"""
        min_cycle_time_list = [y for y in [x.cycle_time for x in self.signals] + [self.cycle_time] if y != 0]
        if len(min_cycle_time_list) == 0:
            return 0
        elif len(min_cycle_time_list) == 1:
            return min_cycle_time_list[0]
        else:
            gcd = get_gcd(min_cycle_time_list[0], min_cycle_time_list[1])
            for i in range(2, len(min_cycle_time_list)):
                gcd = get_gcd(gcd, min_cycle_time_list[i])
            return gcd
        #    return min(min_cycle_time_list)

    # @property
    # def sendType(self, db = None):
    #    if self._sendType is None:
    #        self._sendType = self.attribute("GenMsgSendType")
    #    return self._sendType
    #
    # @sendType.setter
    # def sendType(self, value):
    #    self._sendType = value

    def attribute(self, attribute_name, db=None, default=None):
        # type: (str, typing.Optional[CanMatrix], typing.Any) -> typing.Any
        """Get any Frame attribute by its name.

        :param str attribute_name: attribute name, can be mandatory (ex: id) or optional (customer) attribute.
        :param CanMatrix db: Optional database parameter to get global default attribute value.
        :param default: Default value if attribute doesn't exist.
        :return: Return the attribute value if found, else `default` or None
        """
        if attribute_name in attr.fields_dict(type(self)):
            return getattr(self, attribute_name)
        if attribute_name in self.attributes:
            return self.attributes[attribute_name]
        elif db is not None and attribute_name in db.frame_defines:
            define = db.frame_defines[attribute_name]
            return define.defaultValue
        return default

    def __iter__(self):  # type: () -> typing.Iterator[Signal]
        """Iterator over all signals."""

        return iter(self.signals)

    def add_signal_group(self,
                         Name: str, 
                         Id: int, 
                         signalNames: typing.Sequence[str], 
                         e2e_properties: typing.Optional[AutosarE2EProperties] = None) -> None:
        """Add new SignalGroup to the Frame. Add given signals to the group.

        :param str Name: Group name
        :param int Id: Group id
        :param list of str signalNames: list of Signal names to add. Non existing names are ignored.
        """
        newGroup = SignalGroup(Name, Id, e2e_properties=e2e_properties)
        self.signalGroups.append(newGroup)
        for signal in signalNames:
            signal = signal.strip()
            if signal.__len__() == 0:
                continue
            signalId = self.signal_by_name(signal)
            if signalId is not None:
                newGroup.add_signal(signalId)

    def signal_group_by_name(self, name):
        # type: (str) -> typing.Union[SignalGroup, None]
        """Get signal group.

        :param str name: group name
        :return: SignalGroup by name or None if not found.
        :rtype: SignalGroup
        """
        for signalGroup in self.signalGroups:
            if signalGroup.name == name:
                return signalGroup
        return None

    def add_pdu(self, pdu):
        # type: (Pdu.Pdu) -> Pdu.Pdu
        """
        Add Pdu to Frame.

        :param Pdu pdu: Pdu to be added.
        :return: the pdu added.
        """
        self.pdus.append(pdu)
        return self.pdus[len(self.pdus) - 1]

    def pdu_by_name(self, name):
        # type: (str) -> typing.Union[Pdu.Pdu, None]
        """Get PDU.

        :param str name: PDU name
        :return: PDU by name or None if not found.
        :rtype: Pdu
        """
        for pdu in self.pdus:
            if pdu.name == name:
                return pdu
        return None

    def pdu_by_id(self, pdu_id):
        # type: (int) -> typing.Union[Pdu, None]
        """Get PDU.

        :param int pdu_id: PDU id
        :return: PDU by id or None if not found.
        :rtype: Pdu
        """
        for pdu in self.pdus:
            if pdu.id == pdu_id:
                return pdu
        return None

    def add_signal(self, signal):
        # type: (Signal) -> Signal
        """
        Add Signal to Frame.

        :param Signal signal: Signal to be added.
        :return: the signal added.
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def add_transmitter(self, transmitter):
        # type: (str) -> None
        """Add transmitter ECU Name to Frame.

        :param str transmitter: transmitter name
        """
        if transmitter not in self.transmitters:
            self.transmitters.append(transmitter)

    def del_transmitter(self, transmitter):
        # type: (str) -> None
        """Delete transmitter ECU Name from Frame.

        :param str transmitter: transmitter name
        """
        if transmitter in self.transmitters:
            self.transmitters.remove(transmitter)

    def add_receiver(self, receiver):
        # type: (str) -> None
        """Add receiver ECU Name to Frame.

        :param str receiver: receiver name
        """
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def signal_by_name(self, name):
        # type: (str) -> typing.Union[Signal, None]
        """
        Get signal by name.

        :param str name: signal name to be found.
        :return: signal with given name or None if not found
        """
        for signal in self.signals:
            if signal.name == name:
                return signal
        return None

    def glob_signals(self, glob_str):
        # type: (str) -> typing.Sequence[Signal]
        """Find Frame Signals by given glob pattern.

        :param str glob_str: glob pattern for signal name. See `fnmatch.fnmatchcase`
        :return: list of Signals by glob pattern.
        :rtype: list of Signal
        """
        return_array = []
        for signal in self.signals:
            if fnmatch.fnmatchcase(signal.name, glob_str):
                return_array.append(signal)
        return return_array

    def add_attribute(self, attribute, value):
        # type: (str, typing.Any) -> None
        """
        Add the attribute with value to customer Frame attribute-list. If Attribute already exits, modify its value.
        :param str attribute: Attribute name
        :param any value: attribute value
        """
        try:
            self.attributes[attribute] = str(value)
        except UnicodeDecodeError:
            self.attributes[attribute] = value
        if type(self.attributes[attribute]) == str:
            self.attributes[attribute] = self.attributes[attribute].strip()

    def del_attribute(self, attribute):
        # type: (str) -> typing.Any
        """
        Remove attribute from customer Frame attribute-list.

        :param str attribute: Attribute name
        """
        if attribute in self.attributes:
            del self.attributes[attribute]

    def add_comment(self, comment):
        # type: (str) -> None
        """
        Set Frame comment.

        :param str comment: Frame comment
        """
        self.comment = comment

    def calc_dlc(self):
        # type: () -> None
        """
        Compute minimal Frame DLC (length) based on its Signals

        :return: Message DLC
        """
        max_bit = 0
        for sig in self.signals:
            if sig.get_startbit() + int(sig.size) > max_bit:
                max_bit = sig.get_startbit() + int(sig.size)
        max_byte = (max_bit + 7) // 8
        if self.is_pdu_container:
            max_byte *= len(self.pdus)
            for pdu in self.pdus:
                max_byte += pdu.size
        self.size = max(self.size, max_byte)

    def fit_dlc(self):
        """
            Compute next allowed DLC (length) for current Frame
        """
        max_byte = self.size
        last_size = 8
        for max_size in [12, 16, 20, 24, 32, 48, 64]:
            if max_byte > last_size and max_byte < max_size:
                self.size = max_size
                break
            last_size = max_size

    def get_frame_layout(self):
        # type: () -> typing.Sequence[typing.Sequence[str]]
        """
        get layout of frame.

        Represents the bit usage in the frame by means of a list with n items (n bits of frame length).
        Every item represents one bit and contains a list of signals (object refs) with each signal, occupying that bit.
        Bits with empty list are unused.

        Example: [[], [], [], [sig1], [sig1], [sig1, sig5], [sig2, sig5], [sig2], []]
        :return: list of lists with signalnames
        :rtype: list of lists
        """
        little_bits = [[] for _dummy in range((self.size * 8))]  # type: typing.List[typing.List]
        big_bits = [[] for _dummy in range((self.size * 8))]  # type: typing.List[typing.List]
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

        little_bits_iter = reversed(tuple(grouper(little_bits, 8)))
        little_bits = list(itertools.chain(*little_bits_iter))

        return_list = [
            little + big
            for little, big in zip(little_bits, big_bits)
        ]

        return return_list

    def create_dummy_signals(self):  # type: () -> None
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

    def update_receiver(self):  # type: () -> None
        """
        Collect Frame receivers out of receiver given in each signal. Add them to `self.receiver` list.
        """
        self.receivers = []
        for sig in self.signals:
            for receiver in sig.receivers:
                self.add_receiver(receiver)

    def signals_to_bytes(self, data):
        # type: (typing.Mapping[str, RawValue]) -> bytes
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param data: data dictionary of signal : rawValue
        :return: A byte string of the packed values.
        """

        little_bits = [None] * (self.size * 8)  # type: typing.List[typing.Optional[str]]
        big_bits = list(little_bits)
        for signal in self.signals:
            if signal.name in data:
                value = data.get(signal.name)
                if isinstance(value, str):
                    value = signal.phys2raw(value)
                    if value is None:
                        # TODO Error Handling
                        value = 0
                bits = pack_bitstring(signal.size, signal.is_float, value, signal.is_signed)

                if signal.is_little_endian:
                    least = self.size * 8 - signal.start_bit
                    most = least - signal.size

                    little_bits[most:least] = bits
                else:
                    most = signal.start_bit
                    least = most + signal.size

                    big_bits[most:least] = bits
        little_bits_iter = reversed(tuple(grouper(little_bits, 8)))
        little_bits = list(itertools.chain(*little_bits_iter))
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
        # type: (typing.Optional[typing.Mapping[str, typing.Any]]) -> bytes
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param dict data: data dictionary
        :return: A byte string of the packed values.
        """

        data = dict() if data is None else data
        if self.is_complex_multiplexed:
            raise EncodingComplexMultiplexed
        elif self.is_pdu_container:
            raise EncodingContainerPdu  # TODO add encoding
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

    @staticmethod
    def bytes_to_bitstrings(data):
        # type: (bytes) -> typing.Tuple[str, str]
        """Return two arrays big and little containing bits of given data (bytearray)

        :param data: bytearray of bits (little endian).
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :return: bit arrays in big and little byteorder
        """
        b = tuple('{:08b}'.format(b) for b in data)
        little = ''.join(reversed(b))
        big = ''.join(b)

        return little, big

    @staticmethod
    def bitstring_to_signal_list(signals, big, little, size):
        # type: (typing.Sequence[Signal.Signal], str, str, int) -> typing.Sequence[RawValue.RawValue]
        """Return OrderedDictionary with Signal Name: object decodedSignal (flat / without support for multiplexed frames)

        :param signals: Iterable of signals (class signal) to decode from frame.
        :param big: bytearray of bits (big endian).
        :param little: bytearray of bits (little endian).
        :param size: number of bits.
        :return: array with raw values (same order like signals)
        """
        unpacked = []
        for signal in signals:
            if signal.is_little_endian:
                least = size - signal.start_bit
                most = least - signal.size

                bits = little[most:least]
            else:
                most = signal.start_bit
                least = most + signal.size

                bits = big[most:least]

            unpacked.append(unpack_bitstring(signal.size, signal.is_float, signal.is_signed, bits))

        return unpacked

    def unpack(self, data: bytes,
               allow_truncated: bool = False,
               allow_exceeded: bool = False,
               ) -> typing.Mapping[str, DecodedSignal]:
        """Return OrderedDictionary with Signal Name: object decodedSignal (flat / without support for multiplexed frames)
        decodes every signal in signal-list.

        :param data: bytearray
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :param report_error: set to False to silence error output
        :return: OrderedDictionary
        """

        rx_length = len(data)
        if rx_length != self.size:
            msg_id = self.arbitration_id.id if self.arbitration_id.id != 0 else self.header_id
            if msg_id is None:
                msg_description = "nothing"
            else:
                msg_description = f"message 0x{msg_id:08X} with length {rx_length}"
            msg = f"Received {msg_description}, expected {self.size}"
            logging.warning(msg)

            if allow_truncated:
                # pad the data with 0xff to prevent the codec from
                # raising an exception.
                data = data.ljust(self.size, b"\xFF")

            if allow_exceeded:
                # trim the payload data to match the expected size
                data = data[:self.size]

            if len(data) != self.size:
                # return None
                raise DecodingFrameLength(f"{msg} (wrong data size)")

        if self.is_pdu_container:
            # note: PDU-Container without header is possible for ARXML-Container-PDUs with NO-HEADER
            #       that mean this are not dynamic Container-PDUs rather than static ones. (each sub-pdu has
            #       a fixed offset in the container)
            header_signals = []
            header_id_signal = self.signal_by_name("Header_ID")
            header_dlc_signal = self.signal_by_name("Header_DLC")

            if header_id_signal is not None:
                header_signals.append(header_id_signal)
                _header_id_signal_size = header_id_signal.size
            else:
                _header_id_signal_size = 0
            if header_dlc_signal is not None:
                header_signals.append(header_dlc_signal)
                _header_dlc_signal_size = header_dlc_signal.size
            else:
                _header_dlc_signal_size = 0
            # TODO: may be we need to check that ID/DLC signals are contiguous
            if len(header_signals) > 0 and len(header_signals) != 2:
                raise DecodingContainerPdu(
                        'Received message 0x{:08X} with incorrect Header-Defintiion. '
                        'Header_ID signal or Header_DLC is missing'.format(self.arbitration_id.id)
                    )
            header_size = _header_id_signal_size + _header_dlc_signal_size
            little, big = self.bytes_to_bitstrings(data)
            size = self.size * 8
            return_dict = dict({"pdus": []})
            # decode signal which are not in PDUs
            signals = [s for s in self.signals if s not in header_signals]
            if signals:
                unpacked = self.bitstring_to_signal_list(signals, big, little, size)
                for s, v in zip(signals, unpacked):
                    return_dict[s.name] = DecodedSignal(v, s)
            # decode PDUs
            offset = header_id_signal.start_bit if header_id_signal is not None else 0
            no_header_next_pdu_idx = 0
            # decode as long as there is data left to decode (if there is a header), or as long as there are sub-pdus
            # left to decode (in case of static-container without pdu-headers)
            while (offset + header_size) < size and no_header_next_pdu_idx < len(self.pdus):
                if len(header_signals) > 0:
                    unpacked = self.bitstring_to_signal_list(
                        header_signals,
                        big[offset:offset + header_size],
                        little[size - offset - header_size:size - offset],
                        header_size
                    )
                    offset += header_size
                    pdu_id = unpacked[0]
                    pdu_dlc = unpacked[1]
                    for s, v in zip(header_signals, unpacked):
                        if s.name not in return_dict:
                            return_dict[s.name] = []
                        return_dict[s.name].append(DecodedSignal(v, s))
                    pdu = self.pdu_by_id(pdu_id)
                else:
                    # if there is no pdu-header, then we have a static container-pdu
                    # we have to loop all sub-pdus and set the offset to the offset of the PDU
                    # note: order of processing sub-PDUs is not important, even if the sub-PDUs are not ordered
                    #       by the pdu-offset (we just set the offset correct to the actual processed sub-PDU)
                    pdu = self.pdus[no_header_next_pdu_idx]
                    no_header_next_pdu_idx += 1
                    pdu_dlc = pdu.size
                    offset = pdu.offset_bytes * 8
                decode_size_bits = pdu_dlc * 8
                if pdu is None:
                    return_dict['pdus'].append(None)
                else:
                    unpacked = self.bitstring_to_signal_list(
                        pdu.signals,
                        big[offset:offset + decode_size_bits],
                        little[size - offset - decode_size_bits:size - offset],
                        decode_size_bits
                    )
                    pdu_dict = dict()
                    for s, v in zip(pdu.signals, unpacked):
                        pdu_dict[s.name] = DecodedSignal(v, s)
                    return_dict["pdus"].append({pdu.name: pdu_dict})
                if len(header_signals) > 0:
                    # if there is a pdu-header, we have to set the offset to the start of the next pdu
                    offset += decode_size_bits
            return return_dict
        else:
            little, big = self.bytes_to_bitstrings(data)

            unpacked = self.bitstring_to_signal_list(self.signals, big, little, self.size * 8)

            return_dict = dict()

            for s, v in zip(self.signals, unpacked):
                return_dict[s.name] = DecodedSignal(v, s)

            return return_dict

    def _get_sub_multiplexer(self, parent_multiplexer_name, parent_multiplexer_value):
        """
        get any sub-multiplexer in frame used
        for complex-multiplexed frame decoding

        :param parent_multiplexer_name: string with name of parent multiplexer
        :param parent_multiplexer_value: raw_value (int) of parent multiplexer
        :return: muxer signal or None
        """
        for signal in self.signals:
            if signal.is_multiplexer and signal.muxer_for_signal == parent_multiplexer_name and signal.multiplexer_value_in_range(parent_multiplexer_value):
                return signal

    def _filter_signals_for_multiplexer(self, multiplexer_name, multiplexer_value):
        """
        filter a list of signals with given multiplexer (name and value)
        used for complex-multiplexed frame decoding


        :param multiplexer_name: string with name of parent multiplexer
        :param multiplexer_value: raw_value (int) of parent multiplexer
        :return: filtered array of canmatrix.Signal
        """
        filtered_signals = []
        for signal in self.signals:
            if signal.multiplexer_value_in_range(multiplexer_value) and signal.muxer_for_signal == multiplexer_name and not signal.is_multiplexer:
                filtered_signals.append(signal)
            elif signal.name == multiplexer_name:
                filtered_signals.append(signal)
        return filtered_signals

    def decode(self, data):
        # type: (bytes) -> typing.Mapping[str, typing.Any]
        """Return OrderedDictionary with Signal Name: object decodedSignal (support for multiplexed frames)
        decodes only signals matching to muxgroup

        :param data: bytearray .
            i.e. bytearray([0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8])
        :return: OrderedDictionary
        """
        decoded = self.unpack(data)

        if self.is_complex_multiplexed:
            decoded_values = dict()
            filtered_signals = self._filter_signals_for_multiplexer(None, None)

            multiplex_name = None
            multiplex_value = None

            sub_multiplexer = self._get_sub_multiplexer(multiplex_name, multiplex_value)
            while sub_multiplexer is not None:
                multiplex_name = sub_multiplexer.name
                multiplex_signal = decoded_values[multiplex_name] = decoded[multiplex_name]
                multiplex_value = multiplex_signal.raw_value
                filtered_signals += self._filter_signals_for_multiplexer(multiplex_name, multiplex_value)

                sub_multiplexer = self._get_sub_multiplexer(multiplex_name, multiplex_value)

            for signal in filtered_signals:
                decoded_values[signal.name] = decoded[signal.name]
            return decoded_values

        elif self.is_multiplexed and not self.is_pdu_container:
            decoded_values = dict()
            # find multiplexer and decode only its value:

            for signal in self.signals:
                if signal.is_multiplexer:
                    muxVal = decoded[signal.name].raw_value

            # find all signals with the identified multiplexer-value
            for signal in self.signals:
                if signal.mux_val == muxVal or signal.mux_val is None:
                    decoded_values[signal.name] = decoded[signal.name]
            return decoded_values

        else:
            return decoded

    def _compress_little(self):
        for signal in self.signals:
            if not signal.is_little_endian:
                return
        gap_found = True
        while gap_found:
            gap_found = False
            layout = self.get_frame_layout()
            gap_len = None
            for byte in range(len(layout)//8):
                for bit in range(7,-1,-1):
                    bit_nr = byte*8+bit
                    signal_list = layout[bit_nr]
                    if signal_list == []:
                        if gap_len is None:
                            gap_len = 1
                        else:
                            gap_len += 1
                    else:
                        if gap_len is not None:
                            signal = layout[bit_nr][0]
                            signal.start_bit -= gap_len
                            gap_found = True
                            break
                if gap_found:
                    break

    def compress(self):
        for signal in self.signals:
            if signal.is_little_endian:
                return self._compress_little()
        gap_found = True
        while gap_found:
            gap_found = False
            layout = self.get_frame_layout()
            free_start = None
            for bit_nr, signal_list in enumerate(layout):
                if signal_list == []:
                    if free_start is None:
                        free_start = bit_nr
                else:
                    if free_start is not None:
                        signal = layout[bit_nr][0]
                        signal.start_bit = free_start
                        gap_found = True
                        break

    def multiplex_signals(self):
        """Assign multiplexer to signals. When a multiplexor is in the frame."""
        multiplexor = self.get_multiplexer
        if multiplexor is None:
            return

        for signal in self.signals:
            if signal.is_multiplexer or (signal.muxer_for_signal is not None):
                continue
            signal.mux_val = signal.multiplex
            if signal.multiplex is not None:
                signal.muxer_for_signal = multiplexor.name

    def __str__(self):  # type: () -> str
        """Represent the frame by its name only."""
        return self.name  # add more details than the name only?
