# -*- coding: utf-8 -*-
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

import decimal
import fnmatch
import itertools
import logging
import math
import struct
import sys
import typing
import warnings
from builtins import *
from typing import Optional

import attr
from itertools import zip_longest

import canmatrix.copy
import canmatrix.types
import canmatrix.utils
import canmatrix.exceptions

import canmatrix.Ecu as Ecu
import canmatrix.Signal as Signal
import canmatrix.SignalGroup as SignalGroup
import canmatrix.DecodedSignal as DecodedSignal
import canmatrix.ArbitrationId as ArbitrationId
import canmatrix.Frame as Frame
from canmatrix.Define import Define

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

if version("attrs") < '17.4.0':
    raise RuntimeError("need attrs >= 17.4.0")

logger = logging.getLogger(__name__)

import enum


class matrix_class(enum.Enum):
    CAN = 1
    FLEXRAY = 2
    SOMEIP = 3

@attr.s(eq=False)
class CanMatrix(object):
    """
    The Can-Matrix-Object
    attributes (global canmatrix-attributes),
    ecus (list of ECUs),
    frames (list of Frames)
    signal_defines (list of signal-attribute types)
    frame_defines (list of frame-attribute types)
    ecu_defines (list of ECU-attribute types)
    global_defines (list of global attribute types)
    value_tables (global defined values)
    """

    type = attr.ib(default=matrix_class.CAN)  #type: matrix_class
    attributes = attr.ib(factory=dict)  # type: typing.MutableMapping[str, typing.Any]
    ecus = attr.ib(factory=list)  # type: typing.MutableSequence[Ecu]
    frames = attr.ib(factory=list)  # type: typing.MutableSequence[Frame]

    frames_dict_name = attr.ib(factory=dict)  # type: typing.MutableSequence[Frame]
    frames_dict_id = attr.ib(factory=dict)  # type: typing.MutableSequence[Frame]
    _frames_dict_id_extend = {}
    signal_defines = attr.ib(factory=dict)  # type: typing.MutableMapping[str, Define]
    frame_defines = attr.ib(factory=dict)  # type: typing.MutableMapping[str, Define]
    global_defines = attr.ib(factory=dict)  # type: typing.MutableMapping[str, Define]
    env_defines = attr.ib(factory=dict)  # type: typing.MutableMapping[str, Define]
    ecu_defines = attr.ib(factory=dict)  # type: typing.MutableMapping[str, Define]
    value_tables = attr.ib(factory=dict)  # type: typing.MutableMapping[str, typing.MutableMapping]
    env_vars = attr.ib(factory=dict)  # type: typing.MutableMapping[str, typing.MutableMapping]
    signals = attr.ib(factory=list)  # type: typing.MutableSequence[Signal]
    baudrate = attr.ib(default=0)  # type:int
    fd_baudrate = attr.ib(default=0)  # type:int
    vlan = attr.ib(default=None)  # type:int
    load_errors = attr.ib(factory=list)  # type: typing.MutableSequence[Exception]

    def __iter__(self):  # type: () -> typing.Iterator[Frame]
        """Matrix iterates over Frames (Messages)."""
        return iter(self.frames)

    def add_env_var(self, name, envVarDict):  # type: (str, typing.MutableMapping) -> None
        self.env_vars[name] = envVarDict

    def add_env_attribute(self, env_name, attribute_name, attribute_value):
        # type: (str, str, typing.Any) -> None
        if env_name in self.env_vars:
            if not "attributes" in self.env_vars[env_name]:
                self.env_vars[env_name]["attributes"] = dict()
            self.env_vars[env_name]["attributes"][attribute_name] = attribute_value

    @property
    def contains_fd(self):  # type: () -> bool
        for frame in self.frames:
            if frame.is_fd:
                return True
        return False

    @property
    def contains_j1939(self):  # type: () -> bool
        """Check whether the Matrix contains any J1939 Frame."""
        for frame in self.frames:
            if frame.is_j1939:
                return True
        return False

    def attribute(self, attributeName, default=None):  # type(str, typing.Any) -> typing.Any
        """Return custom Matrix attribute by name.

        :param str attributeName: attribute name
        :param default: default value if given attribute doesn't exist
        :return: attribute value or default or None if no such attribute found.
        """
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        elif attributeName in self.global_defines:
                define = self.global_defines[attributeName]
                return define.defaultValue
        else:
            return default

    def add_value_table(self, name, valueTable):  # type: (str, typing.Mapping) -> None
        """Add named value table.

        :param str name: value table name
        :param valueTable: value table itself
        """
        self.value_tables[name] = canmatrix.utils.normalize_value_table(valueTable)

    def add_attribute(self, attribute, value):  # type: (str, typing.Any) -> None
        """
        Add attribute to Matrix attribute-list.

        :param str attribute: attribute name
        :param value: attribute value
        """
        try:
            self.attributes[attribute] = str(value)
        except UnicodeDecodeError:
            self.attributes[attribute] = value
        if type(self.attributes[attribute]) == str:
            self.attributes[attribute] = self.attributes[attribute].strip()

    def add_signal_defines(self, type, definition):
        """
        Add signal-attribute definition to canmatrix.

        :param str type: signal type
        :param str definition: signal-attribute string definition, see class Define
        """
        if type not in self.signal_defines:
            self.signal_defines[type] = Define(definition)

    def add_frame_defines(self, name, definition):  # type: (str, str) -> None
        """
        Add frame-attribute definition to canmatrix.

        :param str name: frame type
        :param str definition: frame definition as string
        """
        if name not in self.frame_defines:
            self.frame_defines[name] = Define(definition)

    def add_ecu_defines(self, name, definition):  # type: (str, str) -> None
        """
        Add Boardunit-attribute definition to canmatrix.

        :param str name: Boardunit type
        :param str definition: BU definition as string
        """
        if name not in self.ecu_defines:
            self.ecu_defines[name] = Define(definition)

    def add_env_defines(self, name, definition):  # type: (str, str) -> None
        """
        Add enviroment variable-attribute definition to canmatrix.

        :param str name: enviroment variable type
        :param str definition: enviroment variable definition as string
        """
        if name not in self.env_defines:
            self.env_defines[name] = Define(definition)

    def add_global_defines(self, name, definition):  # type: (str, str) -> None
        """
        Add global-attribute definition to canmatrix.

        :param str name: attribute type
        :param str definition: attribute definition as string
        """
        if name not in self.global_defines:
            self.global_defines[name] = Define(definition)

    def add_define_default(self, name, value):  # type: (str, typing.Any) -> None
        if name in self.signal_defines:
            self.signal_defines[name].set_default(value)
        if name in self.frame_defines:
            self.frame_defines[name].set_default(value)
        if name in self.ecu_defines:
            self.ecu_defines[name].set_default(value)
        if name in self.global_defines:
            self.global_defines[name].set_default(value)

    def delete_obsolete_ecus(self):  # type: () -> None
        """Delete all unused ECUs
        """
        used_ecus = [ecu for f in self.frames for ecu in f.transmitters]
        used_ecus += [ecu for f in self.frames for ecu in f.receivers]
        used_ecus += [ecu for f in self.frames for s in f.signals for ecu in s.receivers]
        used_ecus += [ecu for s in self.signals for ecu in s.receivers]
        ecus_to_delete = [ecu.name for ecu in self.ecus if ecu.name not in used_ecus]
        for ecu in ecus_to_delete:
            self.del_ecu(ecu)

    def delete_obsolete_defines(self):  # type: () -> None
        """Delete all unused Defines.

        Delete them from frame_defines, ecu_defines and signal_defines.
        """
        defines_to_delete = set()  # type: typing.Set[str]
        for frameDef in self.frame_defines:
            for frame in self.frames:
                if frameDef in frame.attributes:
                    break
            else:
                defines_to_delete.add(frameDef)
        for element in defines_to_delete:
            del self.frame_defines[element]
        defines_to_delete = set()
        for ecu_define in self.ecu_defines:
            for ecu in self.ecus:
                if ecu_define in ecu.attributes:
                    break
            else:
                defines_to_delete.add(ecu_define)
        for element in defines_to_delete:
            del self.ecu_defines[element]

        defines_to_delete = set()
        for signal_define in self.signal_defines:
            for frame in self.frames:
                for signal in frame.signals:
                    if signal_define in signal.attributes:
                        break
                else:
                    defines_to_delete.add(signal_define)
        for element in defines_to_delete:
            del self.signal_defines[element]

    def get_frame_by_id(self, arbitration_id):  # type: (ArbitrationId) -> typing.Union[Frame, None]
        """Get Frame by its arbitration id.

        :param ArbitrationId arbitration_id: Frame id as canmatrix.ArbitrationId
        :rtype: Frame or None
        """
        hash_name = f"{arbitration_id.id}_{arbitration_id.extended}"
        
        frame = self._frames_dict_id_extend.get(hash_name, None)
        if frame is not None:
            return frame
        for frame in self.frames:
            if frame.arbitration_id == arbitration_id:
                # found ID while ignoring extended or standard
                self._frames_dict_id_extend[hash_name] = frame
                return frame
        return None
    
    def frame_by_id(self, arbitration_id):  # type: (ArbitrationId) -> typing.Union[Frame, None]
        """Get Frame by its arbitration id.
        :param ArbitrationId arbitration_id: Frame id as canmatrix.ArbitrationId
        :rtype: Frame or None
        """
        for test in self.frames:
            if test.arbitration_id == arbitration_id:
                # found ID while ignoring extended or standard
                return test
        return None

    def frame_by_header_id(self, header_id):  # type: (HeaderId) -> typing.Union[Frame, None]
        """Get Frame by its Header id.

        :param HeaderId header_id: Header id as canmatrix.header_id
        :rtype: Frame or None
        """
        for test in self.frames:
            if test.header_id == header_id:
                return test
        return None

    def get_frame_by_id(self, id: int
                        ) -> typing.Union[Frame.Frame, None]:
        """Get Frame by id.

        :param str name: Frame id to search for
        :rtype: Frame or None
        """

        return self.frames_dict_id[id]

    def frame_by_pgn(self, pgn):  # type: (int) -> typing.Union[Frame, None]
        """Get Frame by pgn (j1939).

        :param int pgn: pgn to search for
        :rtype: Frame or None
        """

        for test in self.frames:
            if test.arbitration_id.pgn == ArbitrationId.ArbitrationId.from_pgn(pgn).pgn:
                # canmatrix.ArbitrationId.from_pgn(pgn).pgn instead
                # of just pgn is needed to do the pf >= 240 check
                return test
        return None

    def frame_by_name(self, name):  # type: (str) -> typing.Union[Frame, None]
        """Get Frame by name.

        :param str name: Frame name to search for
        :rtype: Frame or None
        """
        for test in self.frames:
            if test.name == name:
                return test
        return None

    def get_frame_by_name(self, name):  # type: (str) -> typing.Union[Frame, None]
        """Get Frame by name.

        :param str name: Frame name to search for
        :rtype: Frame or None
        """

        return self.frames_dict_name[name]

    def glob_frames(self, globStr):  # type: (str) -> typing.List[Frame]
        """Find Frames by given glob pattern.

        :param str globStr: glob pattern to filter Frames. See `fnmatch.fnmatchcase`.
        :rtype: list of Frame
        """
        return_array = []
        for test in self.frames:
            if fnmatch.fnmatchcase(test.name, globStr):
                return_array.append(test)
        return return_array

    def ecu_by_name(self, name):  # type: (str) -> typing.Union[Ecu, None]
        """
        Returns Boardunit by Name.

        :param str name: BoardUnit name
        :rtype: Ecu or None
        """
        for test in self.ecus:
            if test.name == name:
                return test
        return None

    def glob_ecus(self, globStr):  # type: (str) -> typing.List[Ecu]
        """
        Find ECUs by given glob pattern.

        :param globStr: glob pattern to filter BoardUnits. See `fnmatch.fnmatchcase`.
        :rtype: list of Ecu
        """
        return_array = []
        for test in self.ecus:
            if fnmatch.fnmatchcase(test.name, globStr):
                return_array.append(test)
        return return_array

    def add_frame(self, frame):  # type: (Frame) -> Frame
        """Add the Frame to the Matrix.

        :param Frame frame: Frame to add
        :return: the inserted Frame
        """
        self.frames.append(frame)
        self._frames_dict_id_extend = {}
        self.frames_dict_name[frame.name] = frame
        if frame.header_id:
            self.frames_dict_id[frame.header_id] = frame
        elif frame.arbitration_id.id:
            self.frames_dict_id[frame.arbitration_id.id] = frame

        return self.frames[len(self.frames) - 1]

    def remove_frame(self, frame):  # type: (Frame) -> None
        """Remove the Frame from Matrix.

        :param Frame frame: frame to remove from CAN Matrix
        """
        self.frames.remove(frame)
        self._frames_dict_id_extend = {}

    def add_signal(self, signal):  # type: (Signal) -> Signal
        """
        Add Signal to Frame.

        :param Signal signal: Signal to be added.
        :return: the signal added.
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def remove_signal(self, signal):  # type: (Signal) -> None
        """Remove the Frame from Matrix.

        :param Signal signal: frame to remove from CAN Matrix
        """
        self.signals.remove(signal)

    def delete_zero_signals(self):  # type: () -> None
        """Delete all signals with zero bit width from all Frames."""
        for frame in self.frames:
            for signal in frame.signals:
                if 0 == signal.size:
                    frame.signals.remove(signal)

    def del_signal_attributes(self, unwanted_attributes):  # type: (typing.Sequence[str]) -> None
        """Delete Signal attributes from all Signals of all Frames.

        :param list of str unwanted_attributes: List of attributes to remove
        """
        for frame in self.frames:
            for signal in frame.signals:
                for attrib in unwanted_attributes:
                    signal.del_attribute(attrib)

    def del_frame_attributes(self, unwanted_attributes):  # type: (typing.Sequence[str]) -> None
        """Delete Frame attributes from all Frames.

        :param list of str unwanted_attributes: List of attributes to remove
        """
        for frame in self.frames:
            for attrib in unwanted_attributes:
                frame.del_attribute(attrib)

    def recalc_dlc(self, strategy):  # type: (str) -> None
        """Recompute DLC of all Frames.

        :param str strategy: selected strategy, "max" or "force".
        """
        for frame in self.frames:
            if "max" == strategy:
                frame.calc_dlc()
            if "force" == strategy:
                maxBit = 0
                for sig in frame.signals:
                    if sig.get_startbit() + int(sig.size) > maxBit:
                        maxBit = sig.get_startbit() + int(sig.size)
                max_byte = (maxBit + 7) // 8
                if frame.is_pdu_container:
                    max_byte *= len(frame.pdus)
                    for pdu in self.pdus:
                        max_byte += pdu.size
                frame.size = max_byte

    def rename_ecu(self, ecu_or_name, new_name):  # type: (typing.Union[Ecu, str], str) -> None
        """Rename ECU in the Matrix. Update references in all Frames.

        :param str or Ecu ecu_or_name: old name or ECU instance
        :param str new_name: new name
        """
        ecu = ecu_or_name if isinstance(ecu_or_name, Ecu.Ecu) else self.ecu_by_name(ecu_or_name)
        if ecu is None:
            return
        old_name = ecu.name
        ecu.name = new_name
        for frame in self.frames:
            if old_name in frame.transmitters:
                frame.transmitters.remove(old_name)
                frame.add_transmitter(new_name)
            for signal in frame.signals:
                if old_name in signal.receivers:
                    signal.receivers.remove(old_name)
                    signal.add_receiver(new_name)
            frame.update_receiver()

    def add_ecu(self, ecu):  # type(Ecu) -> None  # todo return Ecu?
        """Add new ECU to the Matrix. Do nothing if ecu with the same name already exists.

        :param Ecu ecu: ECU name to add
        """
        for bu in self.ecus:
            if bu.name.strip() == ecu.name:
                return
        self.ecus.append(ecu)
        self._frames_dict_id_extend = {}


    def del_ecu(self, ecu_or_glob):  # type: (typing.Union[Ecu, str]) -> None
        """Remove ECU from Matrix and all Frames.

        :param str or Ecu ecu_or_glob: ECU instance or glob pattern to remove from list
        """
        ecu_list = [ecu_or_glob] if isinstance(ecu_or_glob, Ecu.Ecu) else self.glob_ecus(ecu_or_glob)

        for ecu in ecu_list:
            if ecu in self.ecus:
                self.ecus.remove(ecu)
                for frame in self.frames:
                    frame.del_transmitter(ecu.name)
                    for signal in frame.signals:
                        signal.del_receiver(ecu.name)

                    frame.update_receiver()

    def update_ecu_list(self):  # type: () -> None
        """Check all Frames and add unknown ECUs to the Matrix ECU list."""
        for frame in self.frames:
            for transmit_ecu in frame.transmitters:
                self.add_ecu(Ecu.Ecu(transmit_ecu))
            frame.update_receiver()
            for signal in frame.signals:
                for receive_ecu in signal.receivers:
                    self.add_ecu(Ecu.Ecu(receive_ecu))

    def rename_frame(self, frame_or_name, new_name):  # type: (typing.Union[Frame,str], str) -> None
        """Rename Frame.

        :param Frame or str frame_or_name: Old Frame instance or name or part of the name with '*' at the beginning or the end.
        :param str new_name: new Frame name, suffix or prefix
        """
        old_name = frame_or_name.name if isinstance(frame_or_name, Frame.Frame) else frame_or_name
        for frame in self.frames:
            if old_name[-1] == '*':
                old_prefix_len = len(old_name)-1
                if frame.name[:old_prefix_len] == old_name[:-1]:
                    frame.name = new_name + frame.name[old_prefix_len:]
            if old_name[0] == '*':
                old_suffix_len = len(old_name)-1
                if frame.name[-old_suffix_len:] == old_name[1:]:
                    frame.name = frame.name[:-old_suffix_len] + new_name
            elif frame.name == old_name:
                frame.name = new_name

    def del_frame(self, frame_or_name):  # type: (typing.Union[Frame, str]) -> None
        """Delete Frame from Matrix.

        :param Frame or str frame_or_name: Frame or name to delete"""
        frame = frame_or_name if isinstance(frame_or_name, Frame.Frame) else self.frame_by_name(frame_or_name)
        if frame:
            self.frames.remove(frame)

    def rename_signal(self, signal_or_name, new_name):  # type: (typing.Union[Signal, str], str) -> None
        """Rename Signal.

        :param Signal or str signal_or_name: Old Signal instance or name or part of the name with '*' at the beginning or the end.
        :param str new_name: new Signal name, suffix or prefix
        """
        old_name = signal_or_name.name if isinstance(signal_or_name, Signal.Signal) else signal_or_name
        for frame in self.frames:
            if old_name[-1] == '*':
                old_prefix_len = len(old_name) - 1
                for signal in frame.signals:
                    if signal.name[:old_prefix_len] == old_name[:-1]:
                        signal.name = new_name + signal.name[old_prefix_len:]
            elif old_name[0] == '*':
                old_suffix_len = len(old_name) - 1
                for signal in frame.signals:
                    if signal.name[-old_suffix_len:] == old_name[1:]:
                        signal.name = signal.name[:-old_suffix_len] + new_name
            else:
                signal_found = frame.signal_by_name(old_name)
                if signal_found:
                    signal_found.name = new_name

    def del_signal(self, signal):  # type: (typing.Union[Signal, str]) -> None
        """Delete Signal from Matrix and all Frames.

        :param Signal or str signal: Signal instance or glob pattern to be deleted"""
        if isinstance(signal, Signal.Signal):
            for frame in self.frames:
                if signal in frame.signals:
                    frame.signals.remove(signal)
        else:
            for frame in self.frames:
                signal_list = frame.glob_signals(signal)
                for sig in signal_list:
                    frame.signals.remove(sig)

    def add_signal_receiver(self, globFrame, globSignal, ecu):  # type: (str, str, str) -> None
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

    def del_signal_receiver(self, globFrame, globSignal, ecu):  # type: (str, str, str) -> None
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

    def add_frame_transmitter(self, globFrame, ecu):  # type: (str, str) -> None
        """Add Transmitter to all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            frame.add_transmitter(ecu)

    def add_frame_receiver(self, globFrame, ecu):  # type: (str, str) -> None
        """Add Receiver to all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            for signal in frame.signals:
                signal.add_receiver(ecu)

    def del_frame_transmitter(self, globFrame, ecu):  # type: (str, str) -> None
        """Delete Transmitter from all Frames by glob pattern.

        :param str globFrame: glob pattern for Frame name.
        :param str ecu: Receiver ECU name
        """
        frames = self.glob_frames(globFrame)
        for frame in frames:
            frame.del_transmitter(ecu)

    def merge(self, mergeArray):  # type: (typing.Sequence[CanMatrix]) -> None
        """Merge multiple Matrices to this Matrix.

        Try to copy all Frames and all environment variables from source Matrices. Don't make duplicates.
        Log collisions.

        :param list of Matrix mergeArray: list of source CAN Matrices to be merged to to self.
        """
        for dbTemp in mergeArray:  # type: CanMatrix
            for frame in dbTemp.frames:
                copyResult = canmatrix.copy.copy_frame(frame.arbitration_id, dbTemp, self)
                if copyResult is False:
                    logger.error(
                        "ID Conflict, could not copy/merge frame " + frame.name + "  %xh " % frame.arbitration_id.id + self.frame_by_id(frame.arbitration_id).name
                    )
            for envVar in dbTemp.env_vars:
                if envVar not in self.env_vars:
                    self.add_env_var(envVar, dbTemp.env_vars[envVar])
                else:
                    logger.error(
                        "Name Conflict, could not copy/merge EnvVar " + envVar)
        self._frames_dict_id_extend = {}

    def set_fd_type(self) -> None:
        """Try to guess and set the CAN type for every frame.

        If a Frame is longer than 8 bytes, it must be Flexible Data Rate frame (CAN-FD).
        If not, the Frame type stays unchanged.
        """
        for frame in self.frames:
            if frame.size > 8:
                frame.is_fd = True

    def encode(self,
               frame_id: ArbitrationId,
               data: typing.Mapping[str, typing.Any]
               ) -> bytes:
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param frame_id: frame id
        :param data: data dictionary
        :return: A byte string of the packed values.
        """
        return self.frame_by_id(frame_id).encode(data)

    def decode_pycan(self, pycan_msg):
        """Return OrderedDictionary with Signal Name: object decodedSignal

        :param pycan_msg: python-can message
        :return: OrderedDictionary
        """
        canmatrix_arbitration_id = ArbitrationId.ArbitrationId(pycan_msg.arbitration_id, extended=pycan_msg.is_extended_id)
        return self.decode(canmatrix_arbitration_id, pycan_msg.data)

    def decode(self, frame_id, data):  # type: (ArbitrationId, bytes) -> typing.Mapping[str, typing.Any]
        """Return OrderedDictionary with Signal Name: object decodedSignal

        :param frame_id: frame id
        :param data: Iterable or bytes.
            i.e. (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8)
        :return: OrderedDictionary
        """
        if not self.contains_j1939:
            return self.frame_by_id(frame_id).decode(data)
        elif frame_id.extended:
            frame = self.frame_by_id(frame_id)
            if frame is None:
                frame = self.frame_by_pgn(frame_id.pgn)
            if frame:
                return frame.decode(data)
            else:
                return {}
        else:
            return {}

    def enum_attribs_to_values(self):  # type: () -> None
        for define in self.ecu_defines:
            if self.ecu_defines[define].type == "ENUM":
                for bu in self.ecus:
                    if define in bu.attributes:
                        bu.attributes[define] = self.ecu_defines[define].values[int(float(bu.attributes[define]))]

        for define in self.frame_defines:
            if self.frame_defines[define].type == "ENUM":
                for frame in self.frames:
                    if define in frame.attributes:
                        frame.attributes[define] = self.frame_defines[define].values[int(float(frame.attributes[define]))]

        for define in self.signal_defines:
            if self.signal_defines[define].type == "ENUM":
                for frame in self.frames:
                    for signal in frame.signals:
                        if define in signal.attributes:
                            signal.attributes[define] = self.signal_defines[define].values[int(float(signal.attributes[define]))]

    def enum_attribs_to_keys(self):  # type: () -> None
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
