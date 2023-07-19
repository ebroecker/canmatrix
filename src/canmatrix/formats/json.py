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
# this script exports json-files from a canmatrix-object
# json-files are the can-matrix-definitions of the CANard-project
# (https://github.com/ericevenchick/CANard)

from __future__ import absolute_import, division, print_function

import json
import sys
import typing
from builtins import *
import decimal
import canmatrix


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.BinaryIO, **str) -> None

    export_canard = options.get('jsonExportCanard', False)
    motorola_bit_format = options.get('jsonMotorolaBitFormat', "lsb")
    export_all = options.get('jsonExportAll', False)
    native_types = options.get('jsonNativeTypes', False)
    number_converter = float if native_types else str
    additional_frame_columns = [x for x in options.get("additionalFrameAttributes", "").split(",") if x]


    export_dict = {}
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
                if not signal.is_little_endian:
                    if motorola_bit_format == "msb":
                        start_bit = signal.get_startbit(bit_numbering=1)
                    elif motorola_bit_format == "msbreverse":
                        start_bit = signal.get_startbit()
                    else:  # motorola_bit_format == "lsb"
                        start_bit = signal.get_startbit(bit_numbering=1, start_little=True)
                else:
                    start_bit = signal.get_startbit(bit_numbering=1, start_little=True)

                symbolic_signals.append({
                    "name": signal.name,
                    "start_bit": start_bit,
                    "bit_length": signal.size,
                    "factor": number_converter(signal.factor),
                    "offset": number_converter(signal.offset),
                    "is_big_endian": signal.is_little_endian is False,
                    "is_signed": signal.is_signed,
                    "is_float": signal.is_float,
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
                if not signal.is_little_endian:
                    if motorola_bit_format == "msb":
                        start_bit = signal.get_startbit(bit_numbering=1)
                    elif motorola_bit_format == "msbreverse":
                        start_bit = signal.get_startbit()
                    else:  # motorola_bit_format == "lsb"
                        start_bit = signal.get_startbit(bit_numbering=1, start_little=True)
                else:  # motorola_bit_format == "lsb"
                    start_bit = signal.get_startbit(bit_numbering=1, start_little=True)

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
    if sys.version_info > (3, 0):
        import io
        temp = io.TextIOWrapper(f, encoding='UTF-8')
    else:
        temp = f

    try:
        json.dump(export_dict, temp, sort_keys=True,
                  indent=4, separators=(',', ': '))
    finally:
        if sys.version_info > (3, 0):
            # When TextIOWrapper is garbage collected, it closes the raw stream
            # unless the raw stream is detached first
            temp.detach()


def load(f, **_options):
    # type: (typing.BinaryIO, **str) -> canmatrix.CanMatrix

    db = canmatrix.CanMatrix()

    if sys.version_info > (3, 0):
        import io
        json_data = json.load(io.TextIOWrapper(f, encoding='UTF-8'))
    else:

        json_data = json.load(f)

    if "enumerations" in json_data:
        for val_tab_name, val_tab_dict in json_data['enumerations'].items():
            for key, val in val_tab_dict.items():
                if key.isdigit():
                    key = int(key)
                db.value_tables.setdefault(val_tab_name, {})[key] = val

    if "ecus" in json_data:
        for ecu in json_data["ecus"]:
            new_ecu = canmatrix.Ecu(name=ecu, comment=json_data["ecus"][ecu])
            db.add_ecu(new_ecu)
    if "messages" in json_data:
        for frame in json_data["messages"]:
            # new_frame = Frame(frame["id"],frame["name"],8,None)
            arb_id = canmatrix.canmatrix.ArbitrationId(id=frame["id"], extended=frame.get("is_extended_frame", "False"))
            new_frame = canmatrix.Frame(frame["name"], arbitration_id=arb_id, size=8)
            if "length" in frame:
                new_frame.size = frame["length"]
            simple_mapping = ["is_complex_multiplexed", "mux_names", "cycle_time", "is_j1939", "header_id", "pdu_name"]
            for key in simple_mapping:
                if key in frame:
                    if key == "is_complex_multiplexed":
                        new_frame.is_complex_multiplexed = frame[key]
                    elif key == "mux_names":
                        new_frame.mux_names = frame[key]
                    elif key == "cycle_time":
                        new_frame.cycle_time = frame[key]
                    elif key == "is_j1939":
                        new_frame.is_j1939 = frame[key]
                    elif key == "header_id":
                        new_frame.header_id = frame[key]
                    elif key == "pdu_name":
                        new_frame.pdu_name = frame[key]

            new_frame.arbitration_id.extended = frame.get("is_extended_frame", False)
            if "transmitters" in frame:
                new_frame.transmitters = frame["transmitters"]
            for signal in frame["signals"]:
                is_little_endian = not signal.get("is_big_endian", False)
                is_float = signal.get("is_float", False)
                is_signed = signal.get("is_signed", False)

                new_signal = canmatrix.Signal(
                    signal["name"],
                    start_bit=signal["start_bit"],
                    size=signal["bit_length"],
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    is_float=is_float,
                    factor=signal.get("factor", 1),
                    offset=signal.get("offset", 0)
                )

                if signal.get("min") is not None:
                    new_signal.min = new_signal.float_factory(signal["min"])

                if signal.get("max", False):
                    new_signal.max = new_signal.float_factory(signal["max"])

                if signal.get("unit", False):
                    new_signal.unit = signal["unit"]

                if signal.get("multiplex", False):
                    new_signal.multiplex = signal["multiplex"]

                if signal.get("values", False):
                    for key in signal["values"]:
                        new_signal.add_values(key, signal["values"][key])

                if signal.get("attributes", False):
                    for key in signal["attributes"]:
                        new_signal.add_attribute(key, signal["attributes"][key])

                if "comment" in signal:
                    new_signal.comment = signal["comment"]

                if "comments" in signal:
                    new_signal.comments = signal["comments"]

                if "initial_value" in signal:
                    new_signal.initial_value = decimal.Decimal(signal["initial_value"])

                if signal.get("receivers", False):
                    for ecu in signal["receivers"]:
                        new_signal.add_receiver(ecu)
                if new_signal.is_little_endian is False:
                    new_signal.set_startbit(
                        new_signal.start_bit, bitNumbering=1, startLittle=True)
                new_frame.add_signal(new_signal)
            db.add_frame(new_frame)

    _define_list = {"signal_defines": db.add_signal_defines, "frame_defines": db.add_frame_defines,
                    "global_defines": db.add_global_defines, "env_defines": db.add_env_defines,
                    "ecu_defines": db.add_ecu_defines}
    for define_type, fptr in _define_list.items():
        if define_type in json_data:
            for define in json_data[define_type]:
                fptr(define['name'], define['define'])

    cm_import_list_dict = {'attributes': db.attributes, 'value_tables': db.value_tables, 'env_vars': db.env_vars}

    cm_import_list_val = ['baudrate', 'fd_baudrate']

    for key in cm_import_list_dict:
        if key in json_data:
            cm_import_list_dict[key].update(json_data[key])

    for key in cm_import_list_val:
        if key in json_data:
            if key == 'baudrate':
                db.baudrate = json_data[key]
            elif key == 'fd_baudrate':
                db.fd_baudrate = json_data[key]

    f.close()
    db.update_ecu_list()
    return db
