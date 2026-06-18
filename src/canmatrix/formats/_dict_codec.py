# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

#
# Shared structured representation: convert a CanMatrix to/from a plain Python dict.
# The json and yaml formats both serialize this dict, so they describe the same
# logical model and differ only in syntax.

import decimal
import typing

import canmatrix
from canmatrix.ArbitrationId import ArbitrationId
from canmatrix.CanMatrix import CanMatrix, matrix_class
from canmatrix.Ecu import Ecu
from canmatrix.Frame import Frame
from canmatrix.Signal import Signal


def _start_bit(signal, motorola_bit_format):
    # type: (Signal, str) -> int
    if not signal.is_little_endian:
        if motorola_bit_format == "msb":
            return signal.get_startbit(bit_numbering=1)
        elif motorola_bit_format == "msbreverse":
            return signal.get_startbit()
        else:  # motorola_bit_format == "lsb"
            return signal.get_startbit(bit_numbering=1, start_little=True)
    else:
        return signal.get_startbit(bit_numbering=1, start_little=True)


def to_dict(db, export_all=False, native_types=False, motorola_bit_format="lsb",
            export_canard=False, additional_frame_columns=None):
    # type: (canmatrix.CanMatrix, bool, bool, str, bool, typing.Optional[typing.Sequence[str]]) -> dict
    number_converter = float if native_types else str
    additional_frame_columns = list(additional_frame_columns or [])

    export_dict = {}  # type: typing.Dict[str, typing.Any]
    if export_all:
        export_dict['enumerations'] = db.value_tables

    export_dict['messages'] = []

    if export_canard:
        for frame in db.frames:
            signals = {}
            for signal in frame.signals:
                signals[
                    signal.get_startbit(
                        bit_numbering=1,
                        start_little=True)] = {
                    "name": signal.name,
                    "bit_length": signal.size,
                    "factor": signal.factor,
                    "offset": signal.offset}
            export_dict['messages'].append(
                {"name": frame.name, "id": hex(frame.arbitration_id.id), "signals": signals})

    elif export_all is False:
        for frame in db.frames:
            symbolic_signals = []
            for signal in frame.signals:
                start_bit = _start_bit(signal, motorola_bit_format)
                symbolic_signals.append({
                    "name": signal.name,
                    "start_bit": start_bit,
                    "bit_length": signal.size,
                    "factor": number_converter(signal.factor),
                    "offset": number_converter(signal.offset),
                    "is_big_endian": signal.is_little_endian is False,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float,
                    "is_ascii": signal.is_ascii,
                })
            symbolic_frame = {"name": frame.name,
                              "id": int(frame.arbitration_id.id),
                              "is_extended_frame": frame.arbitration_id.extended,
                              "is_fd": frame.is_fd,
                              "signals": symbolic_signals}
            frame_attributes = {
                attr: frame.attribute(attr)
                for attr in additional_frame_columns
                if frame.attribute(attr) is not None  # don't export None parameters
            }
            if frame_attributes:  # only add attributes if there are any
                symbolic_frame["attributes"] = frame_attributes
            export_dict['messages'].append(symbolic_frame)
    else:  # export_all
        _define_mapping = {"signal_defines": db.signal_defines, "frame_defines": db.frame_defines,
                           "global_defines": db.global_defines, "env_defines": db.env_defines, "ecu_defines": db.ecu_defines}
        for define_type in _define_mapping:
            export_dict[define_type] = [{"name": a,
                                         "define": _define_mapping[define_type][a].definition,
                                         "default": _define_mapping[define_type][a].defaultValue,
                                         "type": _define_mapping[define_type][a].type} for a in _define_mapping[define_type]]
        export_dict['ecus'] = {ecu.name: ecu.comment for ecu in db.ecus}
        export_dict['attributes'] = db.attributes
        export_dict['value_tables'] = db.value_tables
        export_dict['env_vars'] = db.env_vars
        export_dict['baudrate'] = db.baudrate
        export_dict['fd_baudrate'] = db.fd_baudrate

        for frame in db.frames:
            frame_attributes = {attribute: frame.attribute(attribute, db=db) for attribute in db.frame_defines}
            symbolic_signals = []
            for signal in frame.signals:
                attributes = {attribute: signal.attribute(attribute, db=db) for attribute in db.signal_defines}
                values = {key: signal.values[key] for key in signal.values}
                start_bit = _start_bit(signal, motorola_bit_format)

                symbolic_signal = {
                    "name": signal.name,
                    "start_bit": start_bit,
                    "bit_length": signal.size,
                    "factor": number_converter(signal.factor),
                    "offset": number_converter(signal.offset),
                    "min": number_converter(signal.min),
                    "max": number_converter(signal.max),
                    "is_big_endian": signal.is_little_endian is False,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float,
                    "is_ascii": signal.is_ascii,
                    "comment": signal.comment,
                    "comments": signal.comments,
                    "attributes": attributes,
                    "initial_value": number_converter(signal.initial_value),
                    "values": values,
                    "is_multiplexer": signal.is_multiplexer,
                    "mux_value": signal.mux_val,
                    "receivers": signal.receivers,
                }
                if signal.multiplex is not None:
                    symbolic_signal["multiplex"] = signal.multiplex
                if signal.unit:
                    symbolic_signal["unit"] = signal.unit
                if signal.muxer_for_signal is not None:
                    symbolic_signal["muxer_for_signal"] = signal.muxer_for_signal
                if signal.mux_val_grp:
                    symbolic_signal["mux_val_grp"] = signal.mux_val_grp

                symbolic_signals.append(symbolic_signal)

            export_dict['messages'].append(
                {"name": frame.name,
                 "id": int(frame.arbitration_id.id),
                 "is_extended_frame": frame.arbitration_id.extended,
                 "is_fd": frame.is_fd,
                 "signals": symbolic_signals,
                 "attributes": frame_attributes,
                 "comment": frame.comment,
                 "length": frame.size,
                 "is_complex_multiplexed": frame.is_complex_multiplexed,
                 "mux_names": frame.mux_names,
                 "cycle_time": frame.cycle_time,
                 "is_j1939": frame.is_j1939,
                 "header_id": frame.header_id,
                 "pdu_name": frame.pdu_name,
                 "transmitters": frame.transmitters})

    return export_dict
