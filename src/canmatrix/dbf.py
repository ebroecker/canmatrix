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
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from copy import deepcopy

import logging

from .canmatrix import *
import re
import decimal

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal


# TODO support for [START_PARAM_NODE_RX_SIG]
# TODO support for [START_PARAM_NODE_TX_MSG]


def decodeDefine(line):
    (define, valueType, value) = line.split(',', 2)
    valueType = valueType.strip()
    if valueType == "INT" or valueType == "HEX":
        (Min, Max, default) = value.split(',', 2)
        myDef = valueType + ' ' + Min.strip() + ' ' + Max.strip()
        default = default.strip()
    elif valueType == "ENUM":
        (enums, default) = value.rsplit(',', 1)
        myDef = valueType + "  " + enums[1:]
    elif valueType == "STRING":
        myDef = valueType
        default = value
    else:
        logger.debug(line)

    return define[1:-1], myDef, default


def load(f, **options):
    dbfImportEncoding = options.get("dbfImportEncoding",'iso-8859-1')
    float_factory = options.get('float_factory', default_float_factory)

    db = CanMatrix()

    mode = ''
    for line in f:
        line = line.decode(dbfImportEncoding).strip()

        if mode == 'SignalDescription':
            if line.startswith(
                    "[END_DESC_SIG]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (boId, temS, SignalName, comment) = line.split(' ', 3)
                comment = comment.replace('"', '').replace(';', '')
                db.frame_by_id(int(boId)).signal_by_name(
                    SignalName).add_comment(comment)

        if mode == 'BUDescription':
            if line.startswith(
                    "[END_DESC_NODE]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (BUName, comment) = line.split(' ', 1)
                comment = comment.replace('"', '').replace(';', '')
                db.ecu_by_name(BUName).add_comment(comment)

        if mode == 'FrameDescription':
            if line.startswith(
                    "[END_DESC_MSG]") or line.startswith("[END_DESC]"):
                mode = ''
            else:
                (boId, temS, comment) = line.split(' ', 2)
                comment = comment.replace('"', '').replace(';', '')
                frame = db.frame_by_id(int(boId))
                if frame:
                    frame.add_comment(comment)

        elif mode == 'ParamMsgVal':
            if line.startswith("[END_PARAM_MSG_VAL]"):
                mode = ''
            else:
                (boId, temS, attrib, value) = line.split(',', 3)
                db.frame_by_id(
                    int(boId)).add_attribute(
                    attrib.replace(
                        '"',
                        ''),
                    value.replace(
                        '"',
                        ''))

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
                (boId, temS, SignalName, attrib, value) = line.split(',', 4)
                db.frame_by_id(
                    int(boId)).signal_by_name(SignalName).add_attribute(
                    attrib.replace(
                        '"', ''), value[
                        1:-1])

        elif mode == 'ParamSig':
            if line.startswith("[END_PARAM_SIG]"):
                mode = ''
            else:
                (name, define, default) = decodeDefine(line)
                db.add_signal_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamMsg':
            if line.startswith("[END_PARAM_MSG]"):
                mode = ''
            else:
                (name, define, default) = decodeDefine(line)
                db.add_frame_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamNode':
            if line.startswith("[END_PARAM_NODE]"):
                mode = ''
            else:
                (name, define, default) = decodeDefine(line)
                db.add_ecu_defines(name, define)
                db.add_define_default(name, default)

        elif mode == 'ParamNet':
            if line.startswith("[END_PARAM_NET]"):
                mode = ''
            else:
                (name, define, default) = decodeDefine(line)
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
                temstr = line.strip()[11:].strip()
                temparray = temstr.split(',')
                (name, Id, size, nSignals, dummy) = temparray[0:5]
                if len(temparray) > 5:
                    extended = temparray[5]
                else:
                    extended = None
                if len(temparray) > 6:
                    transmitters = temparray[6].split()
                else:
                    transmitters = list()
                newBo = db.add_frame(
                    Frame(name,
                          id=int(Id),
                          size=int(size),
                          transmitters=transmitters))
                #   Frame(int(Id), name, size, transmitter))
                if extended == 'X':
                    logger.debug("Extended")
                    newBo.extended = 1

            if line.startswith("[NODE]"):
                temstr = line.strip()[6:].strip()
                boList = temstr.split(',')
                for bo in boList:
                    db.add_ecu(ecu(bo))

            if line.startswith("[START_SIGNALS]"):
                temstr = line.strip()[15:].strip()
                temparray = temstr.split(',')
                (name, size, startbyte, startbit, sign, Max, Min, byteorder,
                 offset, factor, unit, multiplex) = temparray[0:12]
                Min = float_factory(Min)
                Max = float_factory(Max)
                factor = float_factory(factor)
                ofset = float_factory(offset)

                if len(temparray) > 12:
                    receiver = temparray[12].split(',')
                else:
                    receiver = []

                if multiplex == 'M':
                    multiplex = 'Multiplexor'
                elif multiplex.strip().__len__() > 0:
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
                startbit = int(startbit)
                startbit += (int(startbyte) - 1) * 8

                newSig = newBo.add_signal(Signal(name,
                                                 start_bit=int(startbit),
                                                 size=int(size),
                                                 is_little_endian=(
                                                    int(byteorder) == 1),
                                                 is_signed=is_signed,
                                                 factor=factor,
                                                 offset=offset,
                                                 min=Min * factor,
                                                 max=Max * factor,
                                                 unit=unit,
                                                 receiver=receiver,
                                                 is_float=is_float,
                                                 multiplex=multiplex))

                if int(byteorder) == 0:
                    # this is dummy here, because internal lsb is default - for
                    # now
                    newSig.set_startbit(
                        startbit, bitNumbering=1, startLittle=True)

            if line.startswith("[VALUE_DESCRIPTION]"):
                temstr = line.strip()[19:].strip()
                regexp = re.compile("\"(.+)\" *, *(.+)")
                temp = regexp.match(temstr)

                if temp:
                    name = temp.group(1)
                    value = temp.group(2)
                    newSig.add_values(value, name)

        for frame in db.frames:
            # receiver is only given in the signals, so do propagate the
            # receiver to the frame:
            frame.update_receiver()
    db.enum_attribs_to_values()
    free_signals_dummy_frame = db.frame_by_name("VECTOR__INDEPENDENT_SIG_MSG")
    if free_signals_dummy_frame is not None and free_signals_dummy_frame.id == 0x40000000:
        db.signals = free_signals_dummy_frame.signals
        db.delFrame(free_signals_dummy_frame)
    return db


def dump(mydb, f, **options):
    # create copy because export changes database
    db = deepcopy(mydb)
    dbfExportEncoding = options.get("dbfExportEncoding", 'iso-8859-1')
    db.enum_attribs_to_keys()
    if len(db.signals) > 0:
        free_signals_dummy_frame = canmatrix.Frame("VECTOR__INDEPENDENT_SIG_MSG",  id = 0x40000000, extended=True)
        free_signals_dummy_frame.signals = db.signals
        db.addFrame(free_signals_dummy_frame)

    outstr =  """//******************************BUSMASTER Messages and signals Database ******************************//

[DATABASE_VERSION] 1.3

[PROTOCOL] CAN

[BUSMASTER_VERSION] [1.7.2]
[NUMBER_OF_MESSAGES] """

    outstr += str(len(db.frames)) + "\n"

    # Frames
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
            continue

        # Name unMsgId m_ucLength m_ucNumOfSignals m_cDataFormat m_cFrameFormat? m_txNode
        # m_cDataFormat If 1 dataformat Intel, 0- Motorola -- immer 1 original Converter macht das nach anzahl entsprechender Signale
        # cFrameFormat Standard 'S' Extended 'X'
        extended = 'S'
        if frame.extended == 1:
            extended = 'X'
        outstr += "[START_MSG] " + frame.name + \
            ",%d,%d,%d,1,%c," % (frame.id, frame.size,
                                 len(frame.signals), extended)
        if frame.transmitters.__len__() == 0:
            frame.add_transmitter("Vector__XXX")
# DBF does not support multiple Transmitters
        outstr += frame.transmitters[0] + "\n"

        for signal in frame.signals:
            # m_acName ucLength m_ucWhichByte m_ucStartBit
            # m_ucDataFormat m_fOffset m_fScaleFactor m_acUnit m_acMultiplex m_rxNode
            # m_ucDataFormat
            whichbyte = int(
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
                if signal.signalsize > 32:
                    sign = 'D'
                else:
                    sign = 'F'

            if signal.factor == 0:
                signal.factor = 1

            outstr += "[START_SIGNALS] " + signal.name + ",%d,%d,%d,%c," % (signal.size,
                                                                            whichbyte,
                                                                            int(signal.get_startbit(bit_numbering=1,
                                                                                                    start_little=True)) % 8,
                                                                            sign) + '{},{}'.format(float(signal.max) / float(signal.factor),
                                                                                                   float(signal.min) / float(signal.factor))

            outstr += ",%d,%s,%s" % (signal.is_little_endian,
                                     signal.offset, signal.factor)
            multiplex = ""
            if signal.multiplex is not None:
                if signal.multiplex == 'Multiplexor':
                    multiplex = 'M'
                else:
                    multiplex = 'm' + str(signal.multiplex)

            outstr += "," + signal.unit + ",%s," % multiplex + \
                ','.join(signal.receiver) + "\n"

            if len(signal.values) > 0:
                for attrib, val in sorted(list(signal.values.items())):
                    outstr += '[VALUE_DESCRIPTION] "' + \
                        val + '",' + str(attrib) + '\n'

        outstr += "[END_MSG]\n\n"

    # Boardunits
    outstr += "[NODE] "
    count = 1
    for bu in db.ecus:
        outstr += bu.name
        if count < len(db.ecus):
            outstr += ","
        count += 1
    outstr += "\n"

    outstr += "[START_DESC]\n\n"

    # BU-descriptions
    outstr += "[START_DESC_MSG]\n"
    for frame in db.frames:
        if frame.comment is not None:
            comment = frame.comment.replace("\n", " ")
            outstr += str(frame.id) + ' S "' + comment + '";\n'

    outstr += "[END_DESC_MSG]\n"

    # Frame descriptions
    outstr += "[START_DESC_NODE]\n"
    for bu in db.ecus:
        if bu.comment is not None:
            comment = bu.comment.replace("\n", " ")
            outstr += bu.name + ' "' + comment + '";\n'

    outstr += "[END_DESC_NODE]\n"

    # signal descriptions
    outstr += "[START_DESC_SIG]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for signal in frame.signals:
            if signal.comment is not None:
                comment = signal.comment.replace("\n", " ")
                outstr += "%d S " % frame.id + signal.name + ' "' + comment + '";\n'

    outstr += "[END_DESC_SIG]\n"
    outstr += "[END_DESC]\n\n"

    outstr += "[START_PARAM]\n"

    # db-parameter
    outstr += "[START_PARAM_NET]\n"
    for (type, define) in sorted(list(db.global_defines.items())):
        defaultVal = define.defaultValue
        if defaultVal is None:
            defaultVal = "0"
        outstr += '"' + type + '",' + define.definition.replace(' ', ',') + ',' + defaultVal + '\n'
    outstr += "[END_PARAM_NET]\n"

    # bu-parameter
    outstr += "[START_PARAM_NODE]\n"
    for (type, define) in sorted(list(db.ecu_defines.items())):
        defaultVal = define.defaultValue
        if defaultVal is None:
            defaultVal = "0"
        outstr += '"' + type + '",' + define.definition.replace(' ', ',') + ',' + defaultVal + '\n'
    outstr += "[END_PARAM_NODE]\n"

    # frame-parameter
    outstr += "[START_PARAM_MSG]\n"
    for (type, define) in sorted(list(db.frame_defines.items())):
        defaultVal = define.defaultValue
        if defaultVal is None:
            defaultVal = "0"
        outstr += '"' + type + '",' + define.definition.replace(' ', ',') + ',' + defaultVal + '\n'

    outstr += "[END_PARAM_MSG]\n"

    # signal-parameter
    outstr += "[START_PARAM_SIG]\n"
    for (type, define) in list(db.signal_defines.items()):
        defaultVal = define.defaultValue
        if defaultVal is None:
            defaultVal = "0"
        outstr += '"' + type + '",' + define.definition.replace(' ', ',') + ',' + defaultVal + '\n'
    outstr += "[END_PARAM_SIG]\n"

    outstr += "[START_PARAM_VAL]\n"
    # boardunit-attributes:
    outstr += "[START_PARAM_NODE_VAL]\n"
    for bu in db.ecus:
        for attrib, val in sorted(list(bu.attributes.items())):
            outstr += bu.name + ',"' + attrib + '","' + val + '"\n'
    outstr += "[END_PARAM_NODE_VAL]\n"

    # messages-attributes:
    outstr += "[START_PARAM_MSG_VAL]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for attrib, val in sorted(list(frame.attributes.items())):
            outstr += str(frame.id) + ',S,"' + attrib + '","' + val + '"\n'
    outstr += "[END_PARAM_MSG_VAL]\n"

    # signal-attributes:
    outstr += "[START_PARAM_SIG_VAL]\n"
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            continue

        for signal in frame.signals:
            for attrib, val in sorted(list(signal.attributes.items())):
                outstr += str(frame.id) + ',S,' + signal.name + \
                    ',"' + attrib + '","' + val + '"\n'
    outstr += "[END_PARAM_SIG_VAL]\n"
    outstr += "[END_PARAM_VAL]\n"
    f.write(outstr.encode(dbfExportEncoding))
