#!/usr/bin/env python

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
# this script imports dbf-files in a canmatrix-object
# dbf-files are the can-matrix-definitions of the busmaster-project (http://rbei-etas.github.io/busmaster/)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import decimal
import logging
import math
import re
import typing

import canmatrix

logger = logging.getLogger(__name__)


def default_float_factory(value):  # type: (typing.Any) -> decimal.Decimal
    return decimal.Decimal(value)


# TODO support for [START_PARAM_NODE_RX_SIG]
# TODO support for [START_PARAM_NODE_TX_MSG]


def decode_define(line):  # type: (str) -> typing.Tuple[str, str, str]
    (define, value_type, value) = line.split(',', 2)
    value_type = value_type.strip()
    if value_type == "INT" or value_type == "HEX":
        (Min, Max, default) = value.split(',', 2)
        my_def = value_type + ' ' + Min.strip() + ' ' + Max.strip()
        default = default.strip()
    elif value_type == "ENUM":
        (enums, default) = value.rsplit(',', 1)
        my_def = value_type + "  " + enums[1:]
    elif value_type == "STRING":
        my_def = value_type
        default = value
    else:
        logger.debug(line)

    return define[1:-1], my_def, default


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    dbf_import_encoding = options.get("dbfImportEncoding", 'iso-8859-1')
    float_factory = options.get('float_factory', default_float_factory)

    db = canmatrix.CanMatrix()

    mode = ''
    for line in f:
        line = line.decode(dbf_import_encoding).strip()

        if mode == 'SignalDescription':
            if line.startswith(
                    "[END_DESC_SIG]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (bo_id, tem_s, signal_name, comment) = line.split(' ', 3)
                comment = comment.replace('"', '').replace(';', '')
                db.frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(bo_id))).signal_by_name(
                    signal_name).add_comment(comment)

        if mode == 'BUDescription':
            if line.startswith(
                    "[END_DESC_NODE]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (bu_name, comment) = line.split(' ', 1)
                comment = comment.replace('"', '').replace(';', '')
                db.ecu_by_name(bu_name).add_comment(comment)

        if mode == 'FrameDescription':
            if line.startswith(
                    "[END_DESC_MSG]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (bo_id, tem_s, comment) = line.split(' ', 2)
                comment = comment.replace('"', '').replace(';', '')
                frame = db.frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(bo_id)))
                if frame:
                    frame.add_comment(comment)

        elif mode == 'ParamMsgVal':
            if line.startswith("[END_PARAM_MSG_VAL]"):
                mode = ''
            else:
                (bo_id, tem_s, attrib, value) = line.split(',', 3)
                db.frame_by_id(canmatrix.ArbitrationId.from_compound_integer(
                    int(bo_id))).add_attribute(
                    attrib.replace('"', ''),
                    value.replace('"', ''))

        elif mode == 'ParamNodeVal':
            if line.startswith("[END_PARAM_NODE_VAL]"):
                mode = ''
            else:
                (bu, attrib, value) = line.split(',', 2)
                db.ecu_by_name(bu).add_attribute(
                    attrib.replace('"', ''), value[1:-1])

        elif mode == 'ParamNetVal':
            if line.startswith("[END_PARAM_NET_VAL]"):
                mode = ''
            else:
                (attrib, value) = line.split(',', 1)
                db.add_attribute(attrib.replace('"', ''), value[1:-1])

        elif mode == 'ParamSigVal':
            if line.startswith("[END_PARAM_SIG_VAL]"):
                mode = ''
            else:
                (bo_id, tem_s, signal_name, attrib, value) = line.split(',', 4)
                db.frame_by_id(canmatrix.ArbitrationId.from_compound_integer(int(bo_id)))\
                    .signal_by_name(signal_name)\
                    .add_attribute(attrib.replace('"', ''), value[1:-1])

        elif mode == 'ParamSig':
            if line.startswith("[END_PARAM_SIG]"):
                mode = ''
            else:
                (name, define, default) = decode_define(line)
                db.add_signal_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamMsg':
            if line.startswith("[END_PARAM_MSG]"):
                mode = ''
            else:
                (name, define, default) = decode_define(line)
                db.add_frame_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamNode':
            if line.startswith("[END_PARAM_NODE]"):
                mode = ''
            else:
                (name, define, default) = decode_define(line)
                db.add_ecu_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamNet':
            if line.startswith("[END_PARAM_NET]"):
                mode = ''
            else:
                (name, define, default) = decode_define(line)
                db.add_global_defines(name, define)
                db.add_define_default(name, default)

        else:
            if line.startswith("[START_DESC_SIG]"):
                mode = 'SignalDescription'

            if line.startswith("[START_DESC_MSG]"):
                mode = 'FrameDescription'

            if line.startswith("[START_DESC_NODE]"):
                mode = 'BUDescription'

            if line.startswith("[START_PARAM_NODE_VAL]"):
                mode = 'ParamNodeVal'

            if line.startswith("[START_PARAM_NET_VAL]"):
                mode = 'ParamNetVal'

            if line.startswith("[START_PARAM_MSG_VAL]"):
                mode = 'ParamMsgVal'

            if line.startswith("[START_PARAM_SIG_VAL]"):
                mode = 'ParamSigVal'

            if line.startswith("[START_PARAM_SIG]"):
                mode = 'ParamSig'
            if line.startswith("[START_PARAM_MSG]"):
                mode = 'ParamMsg'
            if line.startswith("[START_PARAM_NODE]"):
                mode = 'ParamNode'
            if line.startswith("[START_PARAM_NET]"):
                mode = 'ParamNet'

            if line.startswith("[START_MSG]"):
                temp_str = line.strip()[11:].strip()
                temp_array = temp_str.split(',')
                (name, arb_id, size, n_signals, dummy) = temp_array[0:5]
                if len(temp_array) > 5:
                    extended = temp_array[5]
                else:
                    extended = None
                if len(temp_array) > 6:
                    transmitters = temp_array[6].split()
                else:
                    transmitters = list()
                new_frame = db.add_frame(
                    canmatrix.Frame(
                        name,
                        size=int(size),
                        transmitters=transmitters))
                new_frame.arbitration_id = canmatrix.ArbitrationId.from_compound_integer(int(arb_id))
                #   Frame(int(Id), name, size, transmitter))
                if extended == 'X':
                    logger.debug("Extended")
                    new_frame.arbitration_id.extended = True

            if line.startswith("[NODE]"):
                temp_str = line.strip()[6:].strip()
                bo_list = temp_str.split(',')
                for bo in bo_list:
                    db.add_ecu(canmatrix.Ecu(bo))

            if line.startswith("[START_SIGNALS]"):
                temp_str = line.strip()[15:].strip()
                temp_array = temp_str.split(',')
                (name, size, start_byte, start_bit, sign, max_val, min_val, byteorder,
                 offset, factor, unit, multiplex) = temp_array[0:12]
                min_val = float_factory(min_val)
                max_val = float_factory(max_val)
                factor = float_factory(factor)
                offset = float_factory(offset)

                if len(temp_array) > 12:
                    receiver = temp_array[12].split(',')
                else:
                    receiver = []

                if multiplex == 'M':
                    multiplex = 'Multiplexor'
                elif len(multiplex.strip()) > 0:
                    multiplex = int(multiplex[1:])
                else:
                    multiplex = None

                is_float = False
                is_signed = False
                
                if sign == "U":
                    is_signed = False
                elif sign == "F" or sign == "D":
                    is_float = True
                else:
                    is_signed = True
                start_bit = int(start_bit)
                start_bit += (int(start_byte) - 1) * 8

                new_signal = new_frame.add_signal(
                    canmatrix.Signal(
                        name,
                        start_bit=int(start_bit),
                        size=int(size),
                        is_little_endian=(int(byteorder) == 1),
                        is_signed=is_signed,
                        factor=factor,
                        offset=offset,
                        min=min_val * factor,
                        max=max_val * factor,
                        unit=unit,
                        receivers=receiver,
                        is_float=is_float,
                        multiplex=multiplex))

                if int(byteorder) == 0:
                    # this is dummy here, because internal lsb is default - for now
                    new_signal.set_startbit(
                        start_bit, bitNumbering=1, startLittle=True)

            if line.startswith("[VALUE_DESCRIPTION]"):
                temp_str = line.strip()[19:].strip()
                regexp = re.compile("\"(.+)\" *, *(.+)")
                temp = regexp.match(temp_str)

                if temp:
                    new_signal.add_values(value=temp.group(2), valueName=temp.group(1))

        for frame in db.frames:
            # receiver is only given in the signals, so do propagate the receiver to the frame:
            frame.update_receiver()
    db.enum_attribs_to_values()
    free_signals_dummy_frame = db.frame_by_name("VECTOR__INDEPENDENT_SIG_MSG")
    if free_signals_dummy_frame is not None and free_signals_dummy_frame.arbitration_id == 0x40000000:
        db.signals = free_signals_dummy_frame.signals
        db.del_frame(free_signals_dummy_frame)
    return db


def dump(mydb, f, **options):
    # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    # create copy because export changes database
    db = copy.deepcopy(mydb)
    dbf_export_encoding = options.get("dbfExportEncoding", 'iso-8859-1')
    db.enum_attribs_to_keys()
    if len(db.signals) > 0:
        free_signals_dummy_frame = canmatrix.Frame("VECTOR__INDEPENDENT_SIG_MSG")
        free_signals_dummy_frame.arbitration_id = canmatrix.ArbitrationId(id=0x40000000, extended=True)
        free_signals_dummy_frame.signals = db.signals
        db.add_frame(free_signals_dummy_frame)

    out_str = """//******************************BUSMASTER Messages and signals Database ******************************//

[DATABASE_VERSION] 1.3

[PROTOCOL] CAN

[BUSMASTER_VERSION] [1.7.2]
[NUMBER_OF_MESSAGES] """

    out_str += str(len(db.frames)) + "\n"

    # Frames
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
            continue

        # Name unMsgId m_ucLength m_ucNumOfSignals m_cDataFormat m_cFrameFormat? m_txNode
        # m_cDataFormat Data format: 1-Intel, 0-Motorola -- always 1 original converter decides based on signal count.
        # cFrameFormat Standard 'S' Extended 'X'
        extended = 'x' if frame.arbitration_id.extended == 1 else 'S'
        out_str += "[START_MSG] " + frame.name + \
            ",%d,%d,%d,1,%c," % (frame.arbitration_id.id, frame.size, len(frame.signals), extended)
        if not frame.transmitters:
            frame.add_transmitter("Vector__XXX")
# DBF does not support multiple Transmitters
        out_str += frame.transmitters[0] + "\n"

        for signal in frame.signals:
            # m_acName ucLength m_ucWhichByte m_ucStartBit
            # m_ucDataFormat m_fOffset m_fScaleFactor m_acUnit m_acMultiplex m_rxNode
            # m_ucDataFormat
            which_byte = int(
                math.floor(
                    signal.get_startbit(
                        bit_numbering=1,
                        start_little=True) /
                    8) +
                1)
            sign = 'I'

            if not signal.is_signed:
                sign = 'U'
            
            if signal.is_float:
                if signal.size > 32:
                    sign = 'D'
                else:
                    sign = 'F'

            if signal.factor == 0:
                signal.factor = 1

            out_str += "[START_SIGNALS] " + signal.name \
                       + ",%d,%d,%d,%c," % (signal.size,
                                            which_byte,
                                            int(signal.get_startbit(bit_numbering=1,
                                                                    start_little=True)) % 8,
                                            sign) + '{},{}'.format(float(signal.max) / float(signal.factor),
                                                                   float(signal.min) / float(signal.factor))

            out_str += ",%d,%s,%s" % (signal.is_little_endian, signal.offset, signal.factor)
            multiplex = ""
            if signal.multiplex is not None:
                if signal.multiplex == 'Multiplexor':
                    multiplex = 'M'
                else:
                    multiplex = 'm' + str(signal.multiplex)

            out_str += "," + signal.unit + ",%s," % multiplex + \
                ','.join(signal.receivers) + "\n"

            if len(signal.values) > 0:
                for value, name in sorted(list(signal.values.items())):
                    out_str += '[VALUE_DESCRIPTION] "' + \
                        name + '",' + str(value) + '\n'

        out_str += "[END_MSG]\n\n"

    # Board units
    out_str += "[NODE] "
    count = 1
    for ecu in db.ecus:
        out_str += ecu.name
        if count < len(db.ecus):
            out_str += ","
        count += 1
    out_str += "\n"

    out_str += "[START_DESC]\n\n"

    # BU-descriptions
    out_str += "[START_DESC_MSG]\n"
    for frame in db.frames:
        if frame.comment is not None:
            comment = frame.comment.replace("\n", " ")
            out_str += str(frame.arbitration_id.id) + ' S "' + comment + '";\n'

    out_str += "[END_DESC_MSG]\n"

    # Frame descriptions
    out_str += "[START_DESC_NODE]\n"
    for ecu in db.ecus:
        if ecu.comment is not None:
            comment = ecu.comment.replace("\n", " ")
            out_str += ecu.name + ' "' + comment + '";\n'

    out_str += "[END_DESC_NODE]\n"

    # signal descriptions
    out_str += "[START_DESC_SIG]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for signal in frame.signals:
            if signal.comment is not None:
                comment = signal.comment.replace("\n", " ")
                out_str += "%d S " % frame.arbitration_id.id + signal.name + ' "' + comment + '";\n'

    out_str += "[END_DESC_SIG]\n"
    out_str += "[END_DESC]\n\n"

    out_str += "[START_PARAM]\n"

    # db-parameter
    out_str += "[START_PARAM_NET]\n"
    for (data_type, define) in sorted(list(db.global_defines.items())):
        default_val = define.defaultValue
        if default_val is None:
            default_val = "0"
        out_str += '"' + data_type + '",' + define.definition.replace(' ', ',') + ',' + default_val + '\n'
    out_str += "[END_PARAM_NET]\n"

    # bu-parameter
    out_str += "[START_PARAM_NODE]\n"
    for (data_type, define) in sorted(list(db.ecu_defines.items())):
        default_val = define.defaultValue
        if default_val is None:
            default_val = "0"
        out_str += '"' + data_type + '",' + define.definition.replace(' ', ',') + ',' + default_val + '\n'
    out_str += "[END_PARAM_NODE]\n"

    # frame-parameter
    out_str += "[START_PARAM_MSG]\n"
    for (data_type, define) in sorted(list(db.frame_defines.items())):
        default_val = define.defaultValue
        if default_val is None:
            default_val = "0"
        out_str += '"' + data_type + '",' + define.definition.replace(' ', ',') + ',' + default_val + '\n'

    out_str += "[END_PARAM_MSG]\n"

    # signal-parameter
    out_str += "[START_PARAM_SIG]\n"
    for (data_type, define) in list(db.signal_defines.items()):
        default_val = define.defaultValue
        if default_val is None:
            default_val = "0"
        out_str += '"' + data_type + '",' + define.definition.replace(' ', ',') + ',' + default_val + '\n'
    out_str += "[END_PARAM_SIG]\n"

    out_str += "[START_PARAM_VAL]\n"
    # board unit attributes:
    out_str += "[START_PARAM_NODE_VAL]\n"
    for ecu in db.ecus:
        for attrib, val in sorted(list(ecu.attributes.items())):
            out_str += ecu.name + ',"' + attrib + '","' + val + '"\n'
    out_str += "[END_PARAM_NODE_VAL]\n"

    # messages-attributes:
    out_str += "[START_PARAM_MSG_VAL]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for attrib, val in sorted(list(frame.attributes.items())):
            out_str += str(frame.arbitration_id.id) + ',S,"' + attrib + '","' + val + '"\n'
    out_str += "[END_PARAM_MSG_VAL]\n"

    # signal-attributes:
    out_str += "[START_PARAM_SIG_VAL]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for signal in frame.signals:
            for attrib, val in sorted(list(signal.attributes.items())):
                out_str += str(frame.arbitration_id.id) + ',S,' + signal.name + \
                    ',"' + attrib + '","' + val + '"\n'
    out_str += "[END_PARAM_SIG_VAL]\n"
    out_str += "[END_PARAM_VAL]\n"
    f.write(out_str.encode(dbf_export_encoding))
