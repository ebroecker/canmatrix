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
# this script axports arxml-files from a canmatrix-object
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
# currently Support for Autosar 3.2 and 4.0-4.3 is planned

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import decimal
import logging
import typing
from builtins import *

from lxml import etree

import canmatrix
import canmatrix.types
import canmatrix.utils

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal

clusterExporter = 1
clusterImporter = 1


def create_sub_element(parent, element_name, text=None):
    # type: (etree._Element, str, str) -> etree._Element
    sn = etree.SubElement(parent, element_name)
    if text is not None:
        sn.text = str(text)
    return sn


def get_base_type_of_signal(signal):
    # type: (canmatrix.Signal) -> typing.Tuple[str, int]
    if signal.is_float:
        if signal.size > 32:
            create_type = "double"
            size = 64
        else:
            create_type = "single"
            size = 32
    else:
        if signal.size > 32:
            if signal.is_signed:
                create_type = "sint64"
            else:
                create_type = "uint64"
            size = 64                            
        elif signal.size > 16:
            if signal.is_signed:
                create_type = "sint32"
            else:
                create_type = "uint32"
            size = 32                            
        elif signal.size > 8:
            if signal.is_signed:
                create_type = "sint16"
            else:
                create_type = "uint16"
            size = 16
        else:
            if signal.is_signed:
                create_type = "sint8"
            else:
                create_type = "uint8"
            size = 8
    return create_type, size


def dump(dbs, f, **options):
    # type: (canmatrix.cancluster.CanCluster, typing.IO, **str) -> None
    ar_version = options.get("arVersion", "3.2.3")

    for name in dbs:
        db = dbs[name]  # type: canmatrix.CanMatrix
        for frame in db.frames:
            for signal in frame.signals:
                for rec in signal.receivers:
                    frame.add_receiver(rec.strip())

    if ar_version[0] == "3":
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: 'http://autosar.org/' + ar_version,
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/' + ar_version + ' AUTOSAR_' + ar_version.replace('.', '') + '.xsd'
        top_level_packages = create_sub_element(root, 'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: "http://autosar.org/schema/r4.0",
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/schema/r4.0 AUTOSAR_' + ar_version.replace('.', '-') + '.xsd'
        top_level_packages = create_sub_element(root, 'AR-PACKAGES')

    #
    # AR-PACKAGE Cluster
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Cluster')
    elements = create_sub_element(ar_package, 'ELEMENTS')

    for name in dbs:
        db = dbs[name]
        # if len(name) == 0:
        #    (path, ext) = os.path.splitext(filename)
        #    bus_name = path
        # else:
        if len(name) > 0:
            bus_name = name
        else:
            bus_name = "CAN"

        can_cluster = create_sub_element(elements, 'CAN-CLUSTER')
        create_sub_element(can_cluster, 'SHORT-NAME', bus_name)
        if ar_version[0] == "3":
            # createSubElement(can_cluster, 'SPEED', '50000')
            physical_channels = create_sub_element(can_cluster, 'PHYSICAL-CHANNELS')
            physical_channel = create_sub_element(physical_channels, 'PHYSICAL-CHANNEL')
            create_sub_element(physical_channel, 'SHORT-NAME', 'CAN')
            frame_triggering = create_sub_element(physical_channel, 'FRAME-TRIGGERINGSS')
        else:
            can_cluster_variants = create_sub_element(can_cluster, 'CAN-CLUSTER-VARIANTS')
            can_cluster_conditional = create_sub_element(can_cluster_variants, 'CAN-CLUSTER-CONDITIONAL')
            physical_channels = create_sub_element(can_cluster_conditional, 'PHYSICAL-CHANNELS')
            physical_channel = create_sub_element(physical_channels, 'CAN-PHYSICAL-CHANNEL')
            create_sub_element(physical_channel, 'SHORT-NAME', 'CAN')
            frame_triggering = create_sub_element(physical_channel, 'FRAME-TRIGGERINGS')
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                logger.error("Export complex multiplexers is not supported - ignoring frame %s", frame.name)
                continue
            can_frame_triggering = create_sub_element(frame_triggering, 'CAN-FRAME-TRIGGERING')
            create_sub_element(can_frame_triggering, 'SHORT-NAME', frame.name)
            frame_port_refs = create_sub_element(can_frame_triggering, 'FRAME-PORT-REFS')
            for transmitter in frame.transmitters:
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF')
                frame_port_ref.set('DEST', 'FRAME-PORT')
                frame_port_ref.text = "/ECU/{0}/CN_{0}/{1}".format(transmitter, frame.name)
            for rec in frame.receivers:
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF')
                frame_port_ref.set('DEST', 'FRAME-PORT')
                frame_port_ref.text = "/ECU/{0}/CN_{0}/{1}".format(rec, frame.name)
            frame_ref = create_sub_element(can_frame_triggering, 'FRAME-REF')
            if ar_version[0] == "3":
                frame_ref.set('DEST', 'FRAME')
                frame_ref.text = "/Frame/FRAME_{0}".format(frame.name)
                pdu_triggering_refs = create_sub_element(can_frame_triggering, 'I-PDU-TRIGGERING-REFS')
                pdu_triggering_ref = create_sub_element(pdu_triggering_refs, 'I-PDU-TRIGGERING-REF')
                pdu_triggering_ref.set('DEST', 'I-PDU-TRIGGERING')
            else:
                frame_ref.set('DEST', 'CAN-FRAME')
                frame_ref.text = "/CanFrame/FRAME_{0}".format(frame.name)
                pdu_triggering = create_sub_element(can_frame_triggering, 'PDU-TRIGGERINGS')
                pdu_triggering_ref_conditional = create_sub_element(pdu_triggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
                pdu_triggering_ref = create_sub_element(pdu_triggering_ref_conditional, 'PDU-TRIGGERING-REF')
                pdu_triggering_ref.set('DEST', 'PDU-TRIGGERING')

            if frame.arbitration_id.extended is False:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
            else:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')
            create_sub_element(can_frame_triggering, 'IDENTIFIER', str(frame.arbitration_id.id))

            pdu_triggering_ref.text = "/Cluster/CAN/IPDUTRIGG_{0}".format(frame.name)

        if ar_version[0] == "3":
            ipdu_triggerings = create_sub_element(physical_channel, 'I-PDU-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                ipdu_triggering = create_sub_element(ipdu_triggerings, 'I-PDU-TRIGGERING')
                create_sub_element(ipdu_triggering, 'SHORT-NAME', "IPDUTRIGG_{0}".format(frame.name))
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF')
                ipdu_ref.set('DEST', 'SIGNAL-I-PDU')
                ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
            isignal_triggerings = create_sub_element(physical_channel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue
                for signal in frame.signals:
                    isignal_triggering = create_sub_element(isignal_triggerings, 'I-SIGNAL-TRIGGERING')
                    create_sub_element(isignal_triggering, 'SHORT-NAME', signal.name)
                    isignal_port_refs = create_sub_element(isignal_triggering, 'I-SIGNAL-PORT-REFS')

                    for receiver in signal.receivers:
                        isignal_port_ref = create_sub_element(
                            isignal_port_refs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name))
                        isignal_port_ref.set('DEST', 'SIGNAL-PORT')

                    isignal_ref = create_sub_element(
                        isignal_triggering, 'SIGNAL-REF')
                    isignal_ref.set('DEST', 'I-SIGNAL')
                    isignal_ref.text = "/ISignal/{}".format(signal.name)
        else:
            isignal_triggerings = create_sub_element(physical_channel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    isignal_triggering = create_sub_element(isignal_triggerings, 'I-SIGNAL-TRIGGERING')
                    create_sub_element(isignal_triggering, 'SHORT-NAME', signal.name)
                    isignal_port_refs = create_sub_element(isignal_triggering, 'I-SIGNAL-PORT-REFS')
                    for receiver in signal.receivers:
                        isignal_port_ref = create_sub_element(
                            isignal_port_refs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name))
                        isignal_port_ref.set('DEST', 'I-SIGNAL-PORT')

                    isignal_ref = create_sub_element(isignal_triggering, 'I-SIGNAL-REF')
                    isignal_ref.set('DEST', 'I-SIGNAL')
                    isignal_ref.text = "/ISignal/{0}".format(signal.name)
            ipdu_triggerings = create_sub_element(physical_channel, 'PDU-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                ipdu_triggering = create_sub_element(ipdu_triggerings, 'PDU-TRIGGERING')
                create_sub_element(
                    ipdu_triggering,
                    'SHORT-NAME',
                    "IPDUTRIGG_{0}".format(frame.name))
                # missing: I-PDU-PORT-REFS
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF')
                ipdu_ref.set('DEST', 'I-SIGNAL-I-PDU')
                ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
                # missing: I-SIGNAL-TRIGGERINGS

# TODO
#        ipdu_triggerings = createSubElement(physical_channel, 'PDU-TRIGGERINGS')
#        for frame in db.frames:
#            ipdu_triggering = createSubElement(ipdu_triggerings, 'PDU-TRIGGERING')
#            createSubElement(ipdu_triggering, 'SHORT-NAME', "PDUTRIGG_{0}".format(frame.name))
#            ipdu_ref = createSubElement(ipdu_triggering, 'I-PDU-REF')
#            ipdu_ref.set('DEST','SIGNAL-I-PDU')
#            ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)

    #
    # AR-PACKAGE FRAME
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    if ar_version[0] == "3":
        create_sub_element(ar_package, 'SHORT-NAME', 'Frame')
    else:
        create_sub_element(ar_package, 'SHORT-NAME', 'CanFrame')

    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        # TODO: reused frames will be paced multiple times in file
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            if ar_version[0] == "3":
                frame_ele = create_sub_element(elements, 'FRAME')
            else:
                frame_ele = create_sub_element(elements, 'CAN-FRAME')
            create_sub_element(frame_ele, 'SHORT-NAME', "FRAME_{0}".format(frame.name))
            if frame.comment:
                desc = create_sub_element(frame_ele, 'DESC')
                l2 = create_sub_element(desc, 'L-2')
                l2.set("L", "FOR-ALL")
                l2.text = frame.comment
            create_sub_element(frame_ele, 'FRAME-LENGTH', "%d" % frame.size)
            pdu_mappings = create_sub_element(frame_ele, 'PDU-TO-FRAME-MAPPINGS')
            pdu_mapping = create_sub_element(pdu_mappings, 'PDU-TO-FRAME-MAPPING')
            create_sub_element(pdu_mapping, 'SHORT-NAME', frame.name)
            create_sub_element(pdu_mapping, 'PACKING-BYTE-ORDER', "MOST-SIGNIFICANT-BYTE-LAST")
            pdu_ref = create_sub_element(pdu_mapping, 'PDU-REF')
            create_sub_element(pdu_mapping, 'START-POSITION', '0')
            pdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
            if ar_version[0] == "3":
                pdu_ref.set('DEST', 'SIGNAL-I-PDU')
            else:
                pdu_ref.set('DEST', 'I-SIGNAL-I-PDU')

    #
    # AR-PACKAGE PDU
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'PDU')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            if ar_version[0] == "3":
                signal_ipdu = create_sub_element(elements, 'SIGNAL-I-PDU')
                create_sub_element(signal_ipdu, 'SHORT-NAME', "PDU_{}".format(frame.name))
                create_sub_element(signal_ipdu, 'LENGTH', str(frame.size * 8))
            else:
                signal_ipdu = create_sub_element(elements, 'I-SIGNAL-I-PDU')
                create_sub_element(signal_ipdu, 'SHORT-NAME', "PDU_{}".format(frame.name))
                create_sub_element(signal_ipdu, 'LENGTH', str(frame.size))

            # I-PDU-TIMING-SPECIFICATION
            if ar_version[0] == "3":
                signal_to_pdu_mappings = create_sub_element(signal_ipdu, 'SIGNAL-TO-PDU-MAPPINGS')
            else:
                signal_to_pdu_mappings = create_sub_element(signal_ipdu, 'I-SIGNAL-TO-PDU-MAPPINGS')

            for signal in frame.signals:
                signal_to_pdu_mapping = create_sub_element(signal_to_pdu_mappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                create_sub_element(signal_to_pdu_mapping, 'SHORT-NAME', signal.name)

                if ar_version[0] == "3":
                    if signal.is_little_endian:  # Intel
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                    signal_ref = create_sub_element(signal_to_pdu_mapping, 'SIGNAL-REF')
                else:
                    signal_ref = create_sub_element(signal_to_pdu_mapping, 'I-SIGNAL-REF')
                    if signal.is_little_endian:  # Intel
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                signal_ref.text = "/ISignal/{0}".format(signal.name)
                signal_ref.set('DEST', 'I-SIGNAL')

                create_sub_element(signal_to_pdu_mapping, 'START-POSITION',
                                   str(signal.get_startbit(bit_numbering=1)))
                # missing: TRANSFER-PROPERTY: PENDING/...

            for group in frame.signalGroups:
                signal_to_pdu_mapping = create_sub_element(signal_to_pdu_mappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                create_sub_element(signal_to_pdu_mapping, 'SHORT-NAME', group.name)
                signal_ref = create_sub_element(signal_to_pdu_mapping, 'SIGNAL-REF')
                signal_ref.text = "/ISignal/{}".format(group.name)
                signal_ref.set('DEST', 'I-SIGNAL')
                # TODO: TRANSFER-PROPERTY: PENDING???

    #
    # AR-PACKAGE ISignal
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'ISignal')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                signal_ele = create_sub_element(elements, 'I-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', signal.name)
                if ar_version[0] == "4":
                    create_sub_element(signal_ele, 'LENGTH', str(signal.size))

                    network_represent_props = create_sub_element(
                        signal_ele, 'NETWORK-REPRESENTATION-PROPS')
                    sw_data_def_props_variants = create_sub_element(
                        network_represent_props, 'SW-DATA-DEF-PROPS-VARIANTS')
                    sw_data_def_props_conditional = create_sub_element(
                        sw_data_def_props_variants, 'SW-DATA-DEF-PROPS-CONDITIONAL')
                    
                    base_type_ref = create_sub_element(sw_data_def_props_conditional, 'BASE-TYPE-REF')
                    base_type_ref.set('DEST', 'SW-BASE-TYPE')
                    create_type, size = get_base_type_of_signal(signal)
                    base_type_ref.text = "/DataType/{}".format(create_type)
                    compu_method_ref = create_sub_element(
                        sw_data_def_props_conditional,
                        'COMPU-METHOD-REF',
                        '/DataType/Semantics/{}'.format(signal.name))
                    compu_method_ref.set('DEST', 'COMPU-METHOD')
                    unit_ref = create_sub_element(
                        sw_data_def_props_conditional,
                        'UNIT-REF',
                        '/DataType/Unit/{}'.format(signal.name))
                    unit_ref.set('DEST', 'UNIT')

                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF')
                sys_sig_ref.text = "/Signal/{}".format(signal.name)

                sys_sig_ref.set('DEST', 'SYSTEM-SIGNAL')
            for group in frame.signalGroups:
                signal_ele = create_sub_element(elements, 'I-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', group.name)
                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF')
                sys_sig_ref.text = "/Signal/{}".format(group.name)
                sys_sig_ref.set('DEST', 'SYSTEM-SIGNAL-GROUP')

    #
    # AR-PACKAGE Signal
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Signal')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                signal_ele = create_sub_element(elements, 'SYSTEM-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', signal.name)
                if signal.comment:
                    desc = create_sub_element(signal_ele, 'DESC')
                    l2 = create_sub_element(desc, 'L-2')
                    l2.set("L", "FOR-ALL")
                    l2.text = signal.comment
                if ar_version[0] == "3":
                    data_type_ref = create_sub_element(signal_ele, 'DATA-TYPE-REF')
                    if signal.is_float:
                        data_type_ref.set('DEST', 'REAL-TYPE')
                    else:
                        data_type_ref.set('DEST', 'INTEGER-TYPE')
                    data_type_ref.text = "/DataType/{}".format(signal.name)
                    create_sub_element(signal_ele, 'LENGTH', str(signal.size))
                # init_value_ref = create_sub_element(signal_ele, 'INIT-VALUE-REF')
                # init_value_ref.set('DEST', 'INTEGER-LITERAL')
                # init_value_ref.text = "/CONSTANTS/{}".format(signal.name)
            for group in frame.signalGroups:
                group_ele = create_sub_element(elements, 'SYSTEM-SIGNAL-GROUP')
                create_sub_element(group_ele, 'SHORT-NAME', group.name)
                if ar_version[0] == "3":
                    data_type_ref.set('DEST', 'INTEGER-TYPE')  # todo check this
                sys_signal_refs = create_sub_element(
                    group_ele, 'SYSTEM-SIGNAL-REFS')
                for member in group.signals:
                    member_ele = create_sub_element(
                        sys_signal_refs, 'SYSTEM-SIGNAL-REF')
                    member_ele.set('DEST', 'SYSTEM-SIGNAL')
                    member_ele.text = "/Signal/{}".format(member.name)

    #
    # AR-PACKAGE Datatype
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'DataType')
    elements = create_sub_element(ar_package, 'ELEMENTS')

    if ar_version[0] == "3":
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    if signal.is_float:
                        type_ele = create_sub_element(elements, 'REAL-TYPE')
                    else:
                        type_ele = create_sub_element(elements, 'INTEGER-TYPE')
                    create_sub_element(type_ele, 'SHORT-NAME', signal.name)
                    sw_data_def_props = create_sub_element(
                        type_ele, 'SW-DATA-DEF-PROPS')
                    if signal.is_float:
                        encoding = create_sub_element(type_ele, 'ENCODING')
                        if signal.size > 32:
                            encoding.text = "DOUBLE"
                        else:
                            encoding.text = "SINGLE"
                    compu_method_ref = create_sub_element(sw_data_def_props, 'COMPU-METHOD-REF')
                    compu_method_ref.set('DEST', 'COMPU-METHOD')
                    compu_method_ref.text = "/DataType/Semantics/{}".format(signal.name)
    else:
        created_types = []  # type: typing.List[str]
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    create_type, size = get_base_type_of_signal(signal)
                    if create_type not in created_types:
                        created_types.append(create_type)
                        sw_base_type = create_sub_element(elements, 'SW-BASE-TYPE')
                        create_sub_element(sw_base_type, 'SHORT-NAME', create_type)
                        create_sub_element(sw_base_type, 'CATEGORY', 'FIXED_LENGTH')
                        create_sub_element(sw_base_type, 'BASE-TYPE-SIZE', str(size))
                        if signal.is_float:
                            create_sub_element(sw_base_type, 'BASE-TYPE-ENCODING', 'IEEE754')

    if ar_version[0] == "3":
        subpackages = create_sub_element(ar_package, 'SUB-PACKAGES')
    else:
        subpackages = create_sub_element(ar_package, 'AR-PACKAGES')
    ar_package = create_sub_element(subpackages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Semantics')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                compu_method = create_sub_element(elements, 'COMPU-METHOD')
                create_sub_element(compu_method, 'SHORT-NAME', signal.name)
                # missing: UNIT-REF
                compu_int_to_phys = create_sub_element(
                    compu_method, 'COMPU-INTERNAL-TO-PHYS')
                compu_scales = create_sub_element(compu_int_to_phys, 'COMPU-SCALES')
                for value in sorted(signal.values, key=lambda x: int(x)):
                    compu_scale = create_sub_element(compu_scales, 'COMPU-SCALE')
                    desc = create_sub_element(compu_scale, 'DESC')
                    l2 = create_sub_element(desc, 'L-2')
                    l2.set('L', 'FOR-ALL')
                    l2.text = signal.values[value]
                    create_sub_element(compu_scale, 'LOWER-LIMIT', str(value))
                    create_sub_element(compu_scale, 'UPPER-LIMIT', str(value))
                    compu_const = create_sub_element(compu_scale, 'COMPU-CONST')
                    create_sub_element(compu_const, 'VT', signal.values[value])
                else:
                    compu_scale = create_sub_element(compu_scales, 'COMPU-SCALE')
                    # createSubElement(compuScale, 'LOWER-LIMIT', str(#TODO))
                    # createSubElement(compuScale, 'UPPER-LIMIT', str(#TODO))
                    compu_rationsl_coeff = create_sub_element(compu_scale, 'COMPU-RATIONAL-COEFFS')
                    compu_numerator = create_sub_element(compu_rationsl_coeff, 'COMPU-NUMERATOR')
                    create_sub_element(compu_numerator, 'V', "%g" % signal.offset)
                    create_sub_element(compu_numerator, 'V', "%g" % signal.factor)
                    compu_denomiator = create_sub_element(compu_rationsl_coeff, 'COMPU-DENOMINATOR')
                    create_sub_element(compu_denomiator, 'V', "1")

    ar_package = create_sub_element(subpackages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Unit')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                unit = create_sub_element(elements, 'UNIT')
                create_sub_element(unit, 'SHORT-NAME', signal.name)
                create_sub_element(unit, 'DISPLAY-NAME', signal.unit)

    tx_ipdu_groups = {}  # type: typing.Dict[str, typing.List[str]]
    rx_ipdu_groups = {}  # type: typing.Dict[str, typing.List[str]]

    #
    # AR-PACKAGE ECU
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'ECU')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for ecu in db.ecus:
            ecu_instance = create_sub_element(elements, 'ECU-INSTANCE')
            create_sub_element(ecu_instance, 'SHORT-NAME', ecu.name)
            if ecu.comment:
                desc = create_sub_element(ecu_instance, 'DESC')
                l2 = create_sub_element(desc, 'L-2')
                l2.set('L', 'FOR-ALL')
                l2.text = ecu.comment

            if ar_version[0] == "3":
                asso_ipdu_group_refs = create_sub_element(
                    ecu_instance, 'ASSOCIATED-I-PDU-GROUP-REFS')
                connectors = create_sub_element(ecu_instance, 'CONNECTORS')
                comm_connector = create_sub_element(connectors, 'COMMUNICATION-CONNECTOR')
            else:
                asso_ipdu_group_refs = create_sub_element(ecu_instance, 'ASSOCIATED-COM-I-PDU-GROUP-REFS')
                connectors = create_sub_element(ecu_instance, 'CONNECTORS')
                comm_connector = create_sub_element(connectors, 'CAN-COMMUNICATION-CONNECTOR')

            create_sub_element(comm_connector, 'SHORT-NAME', 'CN_' + ecu.name)
            ecu_comm_port_instances = create_sub_element(comm_connector, 'ECU-COMM-PORT-INSTANCES')

            rec_temp = None
            send_temp = None

            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                if ecu.name in frame.transmitters:
                    frame_port = create_sub_element(ecu_comm_port_instances, 'FRAME-PORT')
                    create_sub_element(frame_port, 'SHORT-NAME', frame.name)
                    create_sub_element(frame_port, 'COMMUNICATION-DIRECTION', 'OUT')
                    send_temp = 1
                    if ecu.name + "_Tx" not in tx_ipdu_groups:
                        tx_ipdu_groups[ecu.name + "_Tx"] = []
                    tx_ipdu_groups[ecu.name + "_Tx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if ar_version[0] == "3":
                            signal_port = create_sub_element(ecu_comm_port_instances, 'SIGNAL-PORT')
                        else:
                            signal_port = create_sub_element(ecu_comm_port_instances, 'I-SIGNAL-PORT')

                        create_sub_element(signal_port, 'SHORT-NAME', signal.name)
                        create_sub_element(signal_port, 'COMMUNICATION-DIRECTION', 'OUT')
                if ecu.name in frame.receivers:
                    frame_port = create_sub_element(ecu_comm_port_instances, 'FRAME-PORT')
                    create_sub_element(frame_port, 'SHORT-NAME', frame.name)
                    create_sub_element(frame_port, 'COMMUNICATION-DIRECTION', 'IN')
                    rec_temp = 1
                    if ecu.name + "_Tx" not in rx_ipdu_groups:
                        rx_ipdu_groups[ecu.name + "_Rx"] = []
                    rx_ipdu_groups[ecu.name + "_Rx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if ecu.name in signal.receivers:
                            if ar_version[0] == "3":
                                signal_port = create_sub_element(ecu_comm_port_instances, 'SIGNAL-PORT')
                            else:
                                signal_port = create_sub_element(ecu_comm_port_instances, 'I-SIGNAL-PORT')

                            create_sub_element(signal_port, 'SHORT-NAME', signal.name)
                            create_sub_element(signal_port, 'COMMUNICATION-DIRECTION', 'IN')

            if rec_temp is not None:
                if ar_version[0] == "3":
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-SIGNAL-I-PDU-GROUP")

                asso_ipdu_group_ref.text = "/IPDUGroup/{0}_Rx".format(ecu.name)

            if send_temp is not None:
                if ar_version[0] == "3":
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-SIGNAL-I-PDU-GROUP")
                asso_ipdu_group_ref.text = "/IPDUGroup/{}_Tx".format(ecu.name)

    #
    # AR-PACKAGE IPDUGroup
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'IPDUGroup')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for pdu_group in tx_ipdu_groups:
        if ar_version[0] == "3":
            ipdu_grp = create_sub_element(elements, 'I-PDU-GROUP')
        else:
            ipdu_grp = create_sub_element(elements, 'I-SIGNAL-I-PDU-GROUP')

        create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
        create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "OUT")

        if ar_version[0] == "3":
            ipdu_refs = create_sub_element(ipdu_grp, 'I-PDU-REFS')
            for frame_name in tx_ipdu_groups[pdu_group]:
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF')
                ipdu_ref.set('DEST', "SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)
        else:
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in tx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF')
                ipdu_ref.set('DEST', "I-SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)

    if ar_version[0] == "3":
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")

            ipdu_refs = create_sub_element(ipdu_grp, 'I-PDU-REFS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF')
                ipdu_ref.set('DEST', "SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)
    else:
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-SIGNAL-I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF')
                ipdu_ref.set('DEST', "I-SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_" + frame_name

    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True))

###################################
# read ARXML
###################################


class ArTree(object):
    def __init__(self, name="", ref=None):  # type: (str, etree._Element) -> None
        self._name = name
        self._ref = ref
        self._array = []  # type: typing.List[ArTree]

    def append_child(self, name, child):  # type: (str, typing.Any) -> ArTree
        """Append new child and return it."""
        temp = ArTree(name, child)
        self._array.append(temp)
        return temp

    def get_child_by_name(self, name):  # type: (str) -> typing.Union[ArTree, None]
        for child in self._array:
            if child._name == name:
                return child
        return None

    @property
    def ref(self):  # type: () -> etree._Element
        return self._ref


def ar_parse_tree(tag, ar_tree, namespace):
    # type: (etree._Element, ArTree, str) -> None
    for child in tag:
        name_elem = child.find('./' + namespace + 'SHORT-NAME')
        # long_name = child.find('./' + namespace + 'LONG-NAME')
        if name_elem is not None and child is not None:
            ar_parse_tree(child, ar_tree.append_child(name_elem.text, child), namespace)
        if name_elem is None and child is not None:
            ar_parse_tree(child, ar_tree, namespace)


def ar_get_xchildren(root, path, ar_tree, ns):
    # type: (etree._Element, str, ArTree, str) -> typing.Sequence[etree._Element]
    path_elements = path.split('/')
    element = root
    for element_name in path_elements[:-1]:
        element = ar_get_child(element, element_name, ar_tree, ns)
    children = ar_get_children(element, path_elements[-1], ar_tree, ns)
    return children


#
# get path in tranlation-dictionary
#
def ar_path_to_x_path(ar_path, dest_element=None):
    # type: (str, typing.Optional[str]) -> str
    ar_path_elements = ar_path.strip('/').split('/')
    xpath = "."

    for element in ar_path_elements[:-1]:
        xpath += "//A:SHORT-NAME[text()='" + element + "']/.."
    if dest_element:
        xpath += "//A:" + dest_element + "/A:SHORT-NAME[text()='" + ar_path_elements[-1] + "']/.."
    else:
        xpath += "//A:SHORT-NAME[text()='" + ar_path_elements[-1] + "']/.."

    return xpath


ArCache = dict()  # type: typing.Dict[str, etree._Element]


def get_ar_path(tree, ar_path, namespaces):
    global ArCache
    namespace_map = {'A': namespaces[1:-1]}
    base_ar_path = ar_path[:ar_path.rfind('/')]
    if base_ar_path in ArCache:
        base_element = ArCache[base_ar_path]
    else:
        xbase_path = ar_path_to_x_path(base_ar_path)
        base_element = tree.xpath(xbase_path, namespaces=namespace_map)[0]
        ArCache[base_ar_path] = base_element
    found = base_element.xpath(
        ".//A:SHORT-NAME[text()='" + ar_path[ar_path.rfind('/') + 1:] + "']/..",
        namespaces=namespace_map)[0]
    return found


def ar_get_path(ar_tree, path):
    # type: (ArTree, str) -> typing.Optional[etree._Element]
    ptr = ar_tree
    for p in path.split('/'):
        if p.strip():
            if ptr is not None:
                try:  # any reason to raise?
                    ptr = ptr.get_child_by_name(p)
                except:
                    return None
            else:
                return None
    if ptr is not None:
        return ptr.ref
    else:
        return None


def ar_get_child(parent, tag_name, xml_root, namespace):
    # type: (etree._Element, str, typing.Union[etree._Element, ArTree], str) -> typing.Optional[etree._Element]
    # logger.debug("ar_get_child: " + tag_name)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tag_name)
    if ret is None:
        ret = parent.find('.//' + namespace + tag_name + '-REF')
        if ret is not None:
            if isinstance(xml_root, ArTree):
                ret = ar_get_path(xml_root, ret.text)
            else:
                ret = get_ar_path(xml_root, ret.text, namespace)
    return ret


def ar_get_children(parent, tag_name, ar_translation_table, namespace):
    # type: (etree._Element, str, ArTree, str) -> typing.List[etree._Element]
    if parent is None:
        return []
    ret = parent.findall('.//' + namespace + tag_name)
    if not ret:
        ret_list = parent.findall('.//' + namespace + tag_name + '-REF')
        ret = [ar_get_path(ar_translation_table, item.text) for item in ret_list]
    return ret


def ar_get_name(parent, ns):
    # type: (etree._Element, str) -> str
    name = parent.find('./' + ns + 'SHORT-NAME')
    if name is not None and name.text is not None:
        return name.text
    return ""


pdu_frame_mapping = {}  # type: typing.Dict[etree._Element, str]
signal_rxs = {}  # type: typing.Dict[etree._Element, canmatrix.Signal]


def get_sys_signals(sys_signal, sys_signal_array, frame, group_id, ns):
    # type: (etree._Element, typing.Sequence[etree._Element], canmatrix.Frame, int, str) -> None
    members = [ar_get_name(signal, ns) for signal in sys_signal_array]
    frame.add_signal_group(ar_get_name(sys_signal, ns), 1, members)  # todo use group_id instead of 1?


def decode_compu_method(compu_method, ar_cache, ns, float_factory):
    # type: (etree._Element, ArTree, str, typing.Callable[[typing.Any], typing.Any]) -> typing.Tuple
    values = {}
    factor = float_factory(1.0)
    offset = float_factory(0)
    unit = ar_get_child(compu_method, "UNIT", ar_cache, ns)
    const = None
    compu_scales = ar_get_xchildren(compu_method, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE", ar_cache, ns)
    for compu_scale in compu_scales:
        ll = ar_get_child(compu_scale, "LOWER-LIMIT", ar_cache, ns)
        ul = ar_get_child(compu_scale, "UPPER-LIMIT", ar_cache, ns)
        sl = ar_get_child(compu_scale, "SHORT-LABEL", ar_cache, ns)
        if sl is None:
            desc = get_desc(compu_scale, ar_cache, ns)
        else:
            desc = sl.text
        #####################################################################################################
        # Modification to support sourcing the COMPU_METHOD info from the Vector NETWORK-REPRESENTATION-PROPS
        # keyword definition. 06Jun16
        #####################################################################################################
        if ll is not None and desc is not None and int(float_factory(ul.text)) == int(float_factory(ll.text)):
            #####################################################################################################
            #####################################################################################################
            values[ll.text] = desc

        scale_desc = get_desc(compu_scale, ar_cache, ns)
        rational = ar_get_child(compu_scale, "COMPU-RATIONAL-COEFFS", ar_cache, ns)
        if rational is not None:
            numerator_parent = ar_get_child(rational, "COMPU-NUMERATOR", ar_cache, ns)
            numerator = ar_get_children(numerator_parent, "V", ar_cache, ns)
            denominator_parent = ar_get_child(rational, "COMPU-DENOMINATOR", ar_cache, ns)
            denominator = ar_get_children(denominator_parent, "V", ar_cache, ns)

            factor = float_factory(numerator[1].text) / float_factory(denominator[0].text)
            offset = float_factory(numerator[0].text) / float_factory(denominator[0].text)
        else:
            const = ar_get_child(compu_scale, "COMPU-CONST", ar_cache, ns)
            # add value
            if const is None:
                logger.warning("Unknown Compu-Method: at sourceline %d ", compu_method.sourceline)
    return values, factor, offset, unit, const


def get_signals(signal_array, frame, xml_root, ns, multiplex_id, float_factory):
    # type: (typing.Sequence[etree._Element], canmatrix.Frame, ArTree, str, typing.Optional[int], typing.Callable) -> None
    """Add signals from xml to the Frame."""
    global signal_rxs
    group_id = 1
    if signal_array is None:  # Empty signalarray - nothing to do
        return
    for signal in signal_array:
        compu_method = None
        motorola = ar_get_child(signal, "PACKING-BYTE-ORDER", xml_root, ns)
        start_bit = ar_get_child(signal, "START-POSITION", xml_root, ns)

        isignal = ar_get_child(signal, "SIGNAL", xml_root, ns)
        if isignal is None:
            isignal = ar_get_child(signal, "I-SIGNAL", xml_root, ns)
        if isignal is None:
            isignal = ar_get_child(signal, "I-SIGNAL-GROUP", xml_root, ns)
            if isignal is not None:
                logger.debug("get_signals: found I-SIGNAL-GROUP ")

                isignalarray = ar_get_xchildren(isignal, "I-SIGNAL", xml_root, ns)
                get_sys_signals(isignal, isignalarray, frame, group_id, ns)
                group_id = group_id + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                frame.name, ar_get_child(signal, "SHORT-NAME", xml_root, ns).text)

        base_type = ar_get_child(isignal, "BASE-TYPE", xml_root, ns)
        sig_long_name = ar_get_child(isignal, "LONG-NAME", xml_root, ns)
        if sig_long_name is not None:
            sig_long_name = ar_get_child(sig_long_name, "L-4", xml_root, ns)
            if sig_long_name is not None:
                sig_long_name = sig_long_name.text
        syssignal = ar_get_child(isignal, "SYSTEM-SIGNAL", xml_root, ns)
        if syssignal is None:
            logger.debug('Frame %s, signal %s has no systemsignal', isignal.tag, frame.name)

        if "SYSTEM-SIGNAL-GROUP" in syssignal.tag:
            syssignalarray = ar_get_xchildren(syssignal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", xml_root, ns)
            get_sys_signals(syssignal, syssignalarray, frame, group_id, ns)
            group_id = group_id + 1
            continue

        length = ar_get_child(isignal, "LENGTH", xml_root, ns)
        if length is None:
            length = ar_get_child(syssignal, "LENGTH", xml_root, ns)

        name = ar_get_child(syssignal, "SHORT-NAME", xml_root, ns)
        unit_element = ar_get_child(isignal, "UNIT", xml_root, ns)
        display_name = ar_get_child(unit_element, "DISPLAY-NAME", xml_root, ns)
        if display_name is not None:
            signal_unit = display_name.text
        else:
            signal_unit = ""

        signal_min = None  # type: canmatrix.types.OptionalPhysicalValue
        signal_max = None  # type: canmatrix.types.OptionalPhysicalValue
        receiver = []  # type: typing.List[str]

        signal_description = get_desc(syssignal, xml_root, ns)

        datatype = ar_get_child(syssignal, "DATA-TYPE", xml_root, ns)
        if datatype is None:  # AR4?
            data_constr = ar_get_child(isignal, "DATA-CONSTR", xml_root, ns)
            compu_method = ar_get_child(isignal, "COMPU-METHOD", xml_root, ns)
            base_type = ar_get_child(isignal, "BASE-TYPE", xml_root, ns)
            lower = ar_get_child(data_constr, "LOWER-LIMIT", xml_root, ns)
            upper = ar_get_child(data_constr, "UPPER-LIMIT", xml_root, ns)
            encoding = None  # TODO - find encoding in AR4
        else:
            lower = ar_get_child(datatype, "LOWER-LIMIT", xml_root, ns)
            upper = ar_get_child(datatype, "UPPER-LIMIT", xml_root, ns)
            encoding = ar_get_child(datatype, "ENCODING", xml_root, ns)

        if encoding is not None and (encoding.text == "SINGLE" or encoding.text == "DOUBLE"):
            is_float = True
        else:
            is_float = False
        
        if lower is not None and upper is not None:
            signal_min = float_factory(lower.text)
            signal_max = float_factory(upper.text)

        datdefprops = ar_get_child(datatype, "SW-DATA-DEF-PROPS", xml_root, ns)

        if compu_method is None:
            compu_method = ar_get_child(datdefprops, "COMPU-METHOD", xml_root, ns)
        if compu_method is None:  # AR4
            compu_method = ar_get_child(isignal, "COMPU-METHOD", xml_root, ns)
            base_type = ar_get_child(isignal, "BASE-TYPE", xml_root, ns)
            encoding = ar_get_child(base_type, "BASE-TYPE-ENCODING", xml_root, ns)
            if encoding is not None and encoding.text == "IEEE754":
                is_float = True
        if compu_method is None:
            logger.debug('No Compmethod found!! - try alternate scheme 1.')
            networkrep = ar_get_child(isignal, "NETWORK-REPRESENTATION-PROPS", xml_root, ns)
            data_def_props_var = ar_get_child(networkrep, "SW-DATA-DEF-PROPS-VARIANTS", xml_root, ns)
            data_def_props_cond = ar_get_child(data_def_props_var, "SW-DATA-DEF-PROPS-CONDITIONAL", xml_root, ns)
            if data_def_props_cond is not None:
                try:
                    compu_method = ar_get_child(data_def_props_cond, "COMPU-METHOD", xml_root, ns)
                except:
                    logger.debug('No valid compu method found for this - check ARXML file!!')
                    compu_method = None
        #####################################################################################################
        # no found compu-method fuzzy search in systemsignal:
        #####################################################################################################
        if compu_method is None:
            logger.debug('No Compmethod found!! - fuzzy search in syssignal.')
            compu_method = ar_get_child(syssignal, "COMPU-METHOD", xml_root, ns)

        # decode compuMethod:
        (values, factor, offset, unit_elem, const) = decode_compu_method(compu_method, xml_root, ns, float_factory)

        if signal_min is not None:
            signal_min *= factor
            signal_min += offset
        if signal_max is not None:
            signal_max *= factor
            signal_max += offset

        if base_type is None:
            base_type = ar_get_child(datdefprops, "BASE-TYPE", xml_root, ns)
        if base_type is not None:
            type_name = ar_get_name(base_type, ns)
            if type_name[0] == 'u':
                is_signed = False  # unsigned
            else:
                is_signed = True  # signed
        else:
            is_signed = True  # signed

        if unit_elem is not None:
            longname = ar_get_child(unit_elem, "LONG-NAME", xml_root, ns)
        #####################################################################################################
        # Modification to support obtaining the Signals Unit by DISPLAY-NAME. 07June16
        #####################################################################################################
            display_name = None
            try:
                display_name = ar_get_child(unit_elem, "DISPLAY-NAME", xml_root, ns)
            except:
                logger.debug('No Unit Display name found!! - using long name')
            if display_name is not None:
                signal_unit = display_name.text
            else:
                l4 = ar_get_child(longname, "L-4", xml_root, ns)
                if l4 is not None:
                    signal_unit = l4.text

        init_list = ar_get_xchildren(syssignal, "INIT-VALUE/VALUE", xml_root, ns)

        if not init_list:
            init_list = ar_get_xchildren(isignal, "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE", xml_root, ns)  # #AR4.2
        if init_list:
            initvalue = init_list[0]
        else:
            initvalue = None

        is_little_endian = False
        if motorola is not None:
            if motorola.text == 'MOST-SIGNIFICANT-BYTE-LAST':
                is_little_endian = True
        else:
            logger.debug('no name byte order for signal' + name.text)

        if name is None:
            logger.debug('no name for signal given')
        if start_bit is None:
            logger.debug('no startBit for signal given')
        if length is None:
            logger.debug('no length for signal given')

        if start_bit is not None:
            new_signal = canmatrix.Signal(
                name.text,
                start_bit=int(start_bit.text),
                size=int(length.text),
                is_little_endian=is_little_endian,
                is_signed=is_signed,
                factor=factor,
                offset=offset,
                unit=signal_unit,
                receivers=receiver,
                multiplex=multiplex_id,
                comment=signal_description,
                is_float=is_float)

            if signal_min is not None:
                new_signal.min = signal_min
            if signal_max is not None:
                new_signal.max = signal_max

            if new_signal.is_little_endian == 0:
                # startbit of motorola coded signals are MSB in arxml
                new_signal.set_startbit(int(start_bit.text), bitNumbering=1)

            # save signal, to determin receiver-ECUs for this signal later
            signal_rxs[syssignal] = new_signal

            if base_type is not None:
                temp = ar_get_child(base_type, "SHORT-NAME", xml_root, ns)
                if temp is not None and "boolean" == temp.text:
                    new_signal.add_values(1, "TRUE")
                    new_signal.add_values(0, "FALSE")

            if initvalue is not None and initvalue.text is not None:
                initvalue.text = canmatrix.utils.guess_value(initvalue.text)
                new_signal._initValue = int(initvalue.text)
                new_signal.add_attribute("GenSigStartValue", str(new_signal._initValue))
            else:
                new_signal._initValue = 0

            for key, value in list(values.items()):
                new_signal.add_values(key, value)
            if sig_long_name is not None:
                new_signal.add_attribute("LongName", sig_long_name)
            frame.add_signal(new_signal)


def get_frame(frame_triggering, xml_root, multiplex_translation, ns, float_factory):
    # type: (etree._Element, ArTree, dict, str, typing.Callable) -> typing.Union[canmatrix.Frame, None]
    global pdu_frame_mapping
    address_mode = ar_get_child(frame_triggering, "CAN-ADDRESSING-MODE", xml_root, ns)
    arb_id = ar_get_child(frame_triggering, "IDENTIFIER", xml_root, ns)
    frame_elem = ar_get_child(frame_triggering, "FRAME", xml_root, ns)

    frame_name_elem = ar_get_child(frame_triggering, "SHORT-NAME", xml_root, ns)
    logger.debug("processing Frame: %s", frame_name_elem.text)
    if arb_id is None:
        logger.info("found Frame %s without arbitration id", frame_name_elem.text)
        return None
    arbitration_id = int(arb_id.text)

    if frame_elem is not None:
        dlc = ar_get_child(frame_elem, "FRAME-LENGTH", xml_root, ns)
        pdumappings = ar_get_child(frame_elem, "PDU-TO-FRAME-MAPPINGS", xml_root, ns)
        pdumapping = ar_get_child(pdumappings, "PDU-TO-FRAME-MAPPING", xml_root, ns)
        pdu = ar_get_child(pdumapping, "PDU", xml_root, ns)  # SIGNAL-I-PDU

        if pdu is not None and 'SECURED-I-PDU' in pdu.tag:
            logger.info("found secured pdu - no signal extraction possible: %s", ar_get_name(pdu, ns))

        pdu_frame_mapping[pdu] = ar_get_name(frame_elem, ns)

        new_frame = canmatrix.Frame(ar_get_name(frame_elem, ns), size=int(dlc.text))
        comment = get_desc(frame_elem, xml_root, ns)
        if comment is not None:
            new_frame.add_comment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF", frame_name_elem.text)
        ipdu_triggering_refs = ar_get_child(frame_triggering, "I-PDU-TRIGGERING-REFS", xml_root, ns)
        ipdu_triggering = ar_get_child(ipdu_triggering_refs, "I-PDU-TRIGGERING", xml_root, ns)
        pdu = ar_get_child(ipdu_triggering, "I-PDU", xml_root, ns)
        if pdu is None:
            pdu = ar_get_child(ipdu_triggering, "I-SIGNAL-I-PDU", xml_root, ns)  # AR4.2
        dlc = ar_get_child(pdu, "LENGTH", xml_root, ns)
        new_frame = canmatrix.Frame(frame_name_elem.text, arbitration_id=arbitration_id, size=int(int(dlc.text) / 8))

    if pdu is None:
        logger.error("ERROR: pdu")
    else:
        logger.debug(ar_get_name(pdu, ns))

    if pdu is not None and "MULTIPLEXED-I-PDU" in pdu.tag:
        selector_byte_order = ar_get_child(pdu, "SELECTOR-FIELD-BYTE-ORDER", xml_root, ns)
        selector_len = ar_get_child(pdu, "SELECTOR-FIELD-LENGTH", xml_root, ns)
        selector_start = ar_get_child(pdu, "SELECTOR-FIELD-START-POSITION", xml_root, ns)
        is_little_endian = False
        if selector_byte_order.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False  # unsigned
        multiplexor = canmatrix.Signal(
            "Multiplexor",
            start_bit=int(selector_start.text),
            size=int(selector_len.text),
            is_little_endian=is_little_endian,
            multiplex="Multiplexor")

        multiplexor._initValue = 0
        new_frame.add_signal(multiplexor)
        static_part = ar_get_child(pdu, "STATIC-PART", xml_root, ns)
        ipdu = ar_get_child(static_part, "I-PDU", xml_root, ns)
        if ipdu is not None:
            pdu_sig_mappings = ar_get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xml_root, ns)
            pdu_sig_mapping = ar_get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING", xml_root, ns)
            get_signals(pdu_sig_mapping, new_frame, xml_root, ns, None, float_factory)
            multiplex_translation[ar_get_name(ipdu, ns)] = ar_get_name(pdu, ns)

        dynamic_part = ar_get_child(pdu, "DYNAMIC-PART", xml_root, ns)
#               segmentPositions = arGetChild(dynamic_part, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamic_part_alternatives = ar_get_child(dynamic_part, "DYNAMIC-PART-ALTERNATIVES", xml_root, ns)
        dynamic_part_alternative_list = ar_get_children(dynamic_part_alternatives, "DYNAMIC-PART-ALTERNATIVE", xml_root, ns)
        for alternative in dynamic_part_alternative_list:
            selector_id = ar_get_child(alternative, "SELECTOR-FIELD-CODE", xml_root, ns)
            ipdu = ar_get_child(alternative, "I-PDU", xml_root, ns)
            multiplex_translation[ar_get_name(ipdu, ns)] = ar_get_name(pdu, ns)
            if ipdu is not None:
                pdu_sig_mappings = ar_get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xml_root, ns)
                pdu_sig_mapping = ar_get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING", xml_root, ns)
                get_signals(pdu_sig_mapping, new_frame, xml_root, ns, selector_id.text, float_factory)

    if new_frame.comment is None:
        new_frame.add_comment(get_desc(pdu, xml_root, ns))

    if address_mode is not None and address_mode.text == 'EXTENDED':
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=True)
    else:
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=False)

    timing_spec = ar_get_child(pdu, "I-PDU-TIMING-SPECIFICATION", xml_root, ns)
    if timing_spec is None:
        timing_spec = ar_get_child(pdu, "I-PDU-TIMING-SPECIFICATIONS", xml_root, ns)
    cyclic_timing = ar_get_child(timing_spec, "CYCLIC-TIMING", xml_root, ns)
    repeating_time = ar_get_child(cyclic_timing, "REPEATING-TIME", xml_root, ns)

    event_timing = ar_get_child(timing_spec, "EVENT-CONTROLLED-TIMING", xml_root, ns)
    repeats = ar_get_child(event_timing, "NUMBER-OF-REPEATS", xml_root, ns)
    minimum_delay = ar_get_child(timing_spec, "MINIMUM-DELAY", xml_root, ns)
    starting_time = ar_get_child(timing_spec, "STARTING-TIME", xml_root, ns)

    time_offset = ar_get_child(cyclic_timing, "TIME-OFFSET", xml_root, ns)
    time_period = ar_get_child(cyclic_timing, "TIME-PERIOD", xml_root, ns)

    if cyclic_timing is not None and event_timing is not None:
        new_frame.add_attribute("GenMsgSendType", "cyclicAndSpontanX")        # CycleAndSpontan
        if minimum_delay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclic_timing is not None:
        new_frame.add_attribute("GenMsgSendType", "cyclicX")  # CycleX
        if minimum_delay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        new_frame.add_attribute("GenMsgSendType", "spontanX")  # Spontan
        if minimum_delay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)

    if starting_time is not None:
        value = ar_get_child(starting_time, "VALUE", xml_root, ns)
        new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))
    elif cyclic_timing is not None:
        value = ar_get_child(time_offset, "VALUE", xml_root, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))

    value = ar_get_child(repeating_time, "VALUE", xml_root, ns)
    if value is not None:
        new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))
    elif cyclic_timing is not None:
        value = ar_get_child(time_period, "VALUE", xml_root, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))


#    pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if pdusigmappings is None or pdusigmappings.__len__() == 0:
#        logger.debug("DEBUG: Frame %s no SIGNAL-TO-PDU-MAPPINGS found" % (new_frame.name))
    pdu_sig_mapping = ar_get_children(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", xml_root, ns)

    if pdu_sig_mapping is not None and pdu_sig_mapping.__len__() > 0:
        get_signals(pdu_sig_mapping, new_frame, xml_root, ns, None, float_factory)

    # Seen some pdusigmapping being [] and not None with some arxml 4.2
    else:  # AR 4.2
        pdu_trigs = ar_get_children(frame_triggering, "PDU-TRIGGERINGS", xml_root, ns)
        if pdu_trigs is not None:
            for pdu_trig in pdu_trigs:
                trig_ref_cond = ar_get_child(pdu_trig, "PDU-TRIGGERING-REF-CONDITIONAL", xml_root, ns)
                trigs = ar_get_child(trig_ref_cond, "PDU-TRIGGERING", xml_root, ns)
                ipdus = ar_get_child(trigs, "I-PDU", xml_root, ns)

                signal_to_pdu_maps = ar_get_child(ipdus, "I-SIGNAL-TO-PDU-MAPPINGS", xml_root, ns)
                if signal_to_pdu_maps is None:
                    signal_to_pdu_maps = ar_get_child(ipdus, "I-SIGNAL-TO-I-PDU-MAPPINGS", xml_root, ns)

                if signal_to_pdu_maps is None:
                    logger.debug("DEBUG: AR4.x PDU %s no SIGNAL-TO-PDU-MAPPINGS found - no signal extraction!" % (ar_get_name(ipdus, ns)))
#                signaltopdumap = arGetChild(signaltopdumaps, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                get_signals(signal_to_pdu_maps, new_frame, xml_root, ns, None, float_factory)
        else:
            logger.debug("DEBUG: Frame %s (assuming AR4.2) no PDU-TRIGGERINGS found", new_frame.name)
    return new_frame


def get_desc(element, ar_tree, ns):
    # type: (etree._Element, ArTree, str) -> str
    desc = ar_get_child(element, "DESC", ar_tree, ns)
    txt = ar_get_child(desc, 'L-2[@L="DE"]', ar_tree, ns)
    if txt is None:
        txt = ar_get_child(desc, 'L-2[@L="EN"]', ar_tree, ns)
    if txt is None:
        txt = ar_get_child(desc, 'L-2', ar_tree, ns)
    if txt is not None:
        return txt.text
    else:
        return ""


def process_ecu(ecu, db, ar_dict, multiplex_translation, ns):
    global pdu_frame_mapping
    connectors = ar_get_child(ecu, "CONNECTORS", ar_dict, ns)
    diag_address = ar_get_child(ecu, "DIAGNOSTIC-ADDRESS", ar_dict, ns)
    diag_response = ar_get_child(ecu, "RESPONSE-ADDRESSS", ar_dict, ns)
    # TODO: use diag_address for frame-classification
    comm_connector = ar_get_child(connectors, "COMMUNICATION-CONNECTOR", ar_dict, ns)
    if comm_connector is None:
        comm_connector = ar_get_child(connectors, "CAN-COMMUNICATION-CONNECTOR", ar_dict, ns)
    frames = ar_get_xchildren(comm_connector, "ECU-COMM-PORT-INSTANCES/FRAME-PORT", ar_dict, ns)
    nm_address = ar_get_child(comm_connector, "NM-ADDRESS", ar_dict, ns)
    assoc_refs = ar_get_child(ecu, "ASSOCIATED-I-PDU-GROUP-REFS", ar_dict, ns)

    if assoc_refs is not None:
        assoc = ar_get_children(assoc_refs, "ASSOCIATED-I-PDU-GROUP", ar_dict, ns)
    else:  # AR4
        assoc_refs = ar_get_child(ecu, "ASSOCIATED-COM-I-PDU-GROUP-REFS", ar_dict, ns)
        assoc = ar_get_children(assoc_refs, "ASSOCIATED-COM-I-PDU-GROUP", ar_dict, ns)

    in_frame = []
    out_frame = []

    # get direction of frames (is current ECU sender/receiver/...?)
    for ref in assoc:
        direction = ar_get_child(ref, "COMMUNICATION-DIRECTION", ar_dict, ns)
        group_refs = ar_get_child(ref, "CONTAINED-I-PDU-GROUPS-REFS", ar_dict, ns)
        pdu_refs = ar_get_child(ref, "I-PDU-REFS", ar_dict, ns)
        if pdu_refs is not None:  # AR3
            # local defined pdus
            pdus = ar_get_children(pdu_refs, "I-PDU", ar_dict, ns)
            for pdu in pdus:
                if pdu in pdu_frame_mapping:
                    if direction.text == "IN":
                        in_frame.append(pdu_frame_mapping[pdu])
                    else:
                        out_frame.append(pdu_frame_mapping[pdu])
        else:  # AR4
            isigpdus = ar_get_child(ref, "I-SIGNAL-I-PDUS", ar_dict, ns)
            isigconds = ar_get_children(
                isigpdus, "I-SIGNAL-I-PDU-REF-CONDITIONAL", ar_dict, ns)
            for isigcond in isigconds:
                pdus = ar_get_children(isigcond, "I-SIGNAL-I-PDU", ar_dict, ns)
                for pdu in pdus:
                    if pdu in pdu_frame_mapping:
                        if direction.text == "IN":
                            in_frame.append(pdu_frame_mapping[pdu])
                        else:
                            out_frame.append(pdu_frame_mapping[pdu])

        # grouped pdus
        group = ar_get_children(group_refs, "CONTAINED-I-PDU-GROUPS", ar_dict, ns)
        for t in group:
            if direction is None:
                direction = ar_get_child(
                    t, "COMMUNICATION-DIRECTION", ar_dict, ns)
            pdu_refs = ar_get_child(t, "I-PDU-REFS", ar_dict, ns)
            pdus = ar_get_children(pdu_refs, "I-PDU", ar_dict, ns)
            for pdu in pdus:
                if direction.text == "IN":
                    in_frame.append(ar_get_name(pdu, ns))
                else:
                    out_frame.append(ar_get_name(pdu, ns))

        for out in out_frame:
            if out in multiplex_translation:
                out = multiplex_translation[out]
            frame = db.frame_by_name(out)
            if frame is not None:
                frame.add_transmitter(ar_get_name(ecu, ns))
            else:
                pass

#               for inf in inFrame:
#                       if inf in multiplexTranslation:
#                               inf = multiplexTranslation[inf]
#                       frame = db.frameByName(inf)
#                       if frame is not None:
#                               for signal in frame.signals:
#                                       recname = arGetName(ecu, ns)
#                                       if recname not in  signal.receiver:
#                                               signal.receiver.append(recname)
#                       else:
#                               print "in not found: " + inf
    bu = ecu(ar_get_name(ecu, ns))
    if nm_address is not None:
        bu.add_attribute("NWM-Stationsadresse", nm_address.text)
        bu.add_attribute("NWM-Knoten", "ja")
    else:
        bu.add_attribute("NWM-Stationsadresse", "0")
        bu.add_attribute("NWM-Knoten", "nein")
    return bu


def ecuc_extract_signal(signal_node, ns):
    # type: (etree._Element, str) -> canmatrix.Signal
    """Extract signal from ECUc file."""
    attributes = signal_node.findall(".//" + ns + "DEFINITION-REF")  # type: typing.Sequence[etree._Element]
    start_bit = None
    size = 0
    is_little = False
    # endianness = None
    # init_value = 0
    # signal_type = None
    # timeout = 0
    for attribute in attributes:
        if attribute.text.endswith("ComBitPosition"):
            start_bit = int(attribute.getparent().find(".//" + ns + "VALUE").text)
        if attribute.text.endswith("ComBitSize"):
            size = int(attribute.getparent().find(".//" + ns + "VALUE").text)
        if attribute.text.endswith("ComSignalEndianness"):
            endianness = attribute.getparent().find(".//" + ns + "VALUE").text
            is_little = "LITTLE_ENDIAN" in endianness
        if attribute.text.endswith("ComSignalInitValue"):
            init_value = int(attribute.getparent().find(".//" + ns + "VALUE").text)
        if attribute.text.endswith("ComSignalType"):
            signal_type = attribute.getparent().find(".//" + ns + "VALUE").text
        if attribute.text.endswith("ComTimeout"):
            timeout = int(attribute.getparent().find(".//" + ns + "VALUE").text)
    return canmatrix.Signal(ar_get_name(signal_node, ns), start_bit=start_bit, size=size, is_little_endian=is_little)


def extract_cm_from_ecuc(com_module, search_point, ns):
    db = canmatrix.CanMatrix()
    definitions = com_module.findall('.//' + ns + "DEFINITION-REF")
    for definition in definitions:
        if definition.text.endswith("ComIPdu"):
            container = definition.getparent()
            frame = canmatrix.Frame(ar_get_name(container, ns))
            db.add_frame(frame)
            all_references = ar_get_children(container, "ECUC-REFERENCE-VALUE", search_point, ns)
            for reference in all_references:
                value = ar_get_child(reference, "VALUE", search_point, ns)
                if value is not None:
                    signal_definition = value.find('./' + ns + "DEFINITION-REF")
                    if signal_definition.text.endswith("ComSignal"):
                        signal = ecuc_extract_signal(value, ns)
                        frame.add_signal(signal)
    db.recalc_dlc(strategy="max")
    return {"": db}


def load(file, **options):
    # type: (typing.IO, **typing.Any) -> typing.Dict[str, canmatrix.CanMatrix]

    global ArCache
    ArCache = dict()
    global pdu_frame_mapping
    pdu_frame_mapping = {}
    global signal_rxs
    signal_rxs = {}

    float_factory = options.get("float_factory", default_float_factory)  # type: typing.Callable
    ignore_cluster_info = options.get("arxmlIgnoreClusterInfo", False)
    use_ar_xpath = options.get("arxmlUseXpath", False)

    result = {}
    logger.debug("Read arxml ...")
    tree = etree.parse(file)

    root = tree.getroot()  # type: etree._Element
    logger.debug(" Done\n")

    ns = "{" + tree.xpath('namespace-uri(.)') + "}"
    nsp = tree.xpath('namespace-uri(.)')

    top_level_packages = root.find('./' + ns + 'TOP-LEVEL-PACKAGES')

    if top_level_packages is None:
        # no "TOP-LEVEL-PACKAGES found, try root
        top_level_packages = root

    logger.debug("Build arTree ...")

    if use_ar_xpath:
        search_point = top_level_packages  # type: typing.Union[etree._Element, ArTree]
    else:
        ar_tree = ArTree()
        ar_parse_tree(top_level_packages, ar_tree, ns)
        search_point = ar_tree

    logger.debug(" Done\n")

    com_module = ar_get_path(search_point, "ActiveEcuC/Com")
    if com_module is not None:
        logger.info("seems to be a ECUC arxml. Very limited support for extracting canmatrix.")
        return extract_cm_from_ecuc(com_module, search_point, ns)

    frames = root.findall('.//' + ns + 'CAN-FRAME')  # AR4.2
    if frames is None:
        frames = root.findall('.//' + ns + 'FRAME')  # AR3.2-4.1?
    
    logger.debug("DEBUG %d frames in arxml...", len(frames))
    can_triggers = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
    logger.debug("DEBUG %d can-frame-triggering in arxml...", len(can_triggers))

    sig_pdu_map = root.findall('.//' + ns + 'SIGNAL-TO-PDU-MAPPINGS')
    logger.debug("DEBUG %d SIGNAL-TO-PDU-MAPPINGS in arxml...", len(sig_pdu_map))

    sig_ipdu = root.findall('.//' + ns + 'I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug("DEBUG %d I-SIGNAL-TO-I-PDU-MAPPING in arxml...", len(sig_ipdu))

    if ignore_cluster_info is True:
        ccs = [etree.Element("ignoreClusterInfo")]  # type: typing.Sequence[etree._Element]
    else:
        ccs = root.findall('.//' + ns + 'CAN-CLUSTER')
    for cc in ccs:  # type: etree._Element
        db = canmatrix.CanMatrix()
# Defines not jet imported...
        db.add_ecu_defines("NWM-Stationsadresse", 'HEX 0 63')
        db.add_ecu_defines("NWM-Knoten", 'ENUM  "nein","ja"')
        db.add_signal_defines("LongName", 'STRING')
        db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
        db.add_frame_defines("GenMsgDelayTime", 'INT 0 65535')
        db.add_frame_defines("GenMsgNrOfRepetitions", 'INT 0 65535')
        db.add_frame_defines("GenMsgStartValue", 'STRING')
        db.add_frame_defines("GenMsgStartDelayTime", 'INT 0 65535')
        db.add_frame_defines(
            "GenMsgSendType",
            'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
        db.add_signal_defines("GenSigStartValue", 'HEX 0 4294967295')

        if ignore_cluster_info is True:
            can_frame_trig = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
            bus_name = ""
        else:
            speed = ar_get_child(cc, "SPEED", search_point, ns)
            logger.debug("Busname: " + ar_get_name(cc, ns))

            bus_name = ar_get_name(cc, ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            physical_channels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")  # type: etree._Element
            if physical_channels is None:
                logger.error("Error - PHYSICAL-CHANNELS not found")

            nm_lower_id = ar_get_child(cc, "NM-LOWER-CAN-ID", search_point, ns)

            physical_channel = ar_get_child(physical_channels, "PHYSICAL-CHANNEL", search_point, ns)
            if physical_channel is None:
                physical_channel = ar_get_child(physical_channels, "CAN-PHYSICAL-CHANNEL", search_point, ns)
            if physical_channel is None:
                logger.error("Error - PHYSICAL-CHANNEL not found")
            can_frame_trig = ar_get_children(physical_channel, "CAN-FRAME-TRIGGERING", search_point, ns)
            if can_frame_trig is None:
                logger.error("Error - CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug("%d frames found in arxml", len(can_frame_trig))

        multiplex_translation = {}  # type: typing.Dict[str, str]
        for frameTrig in can_frame_trig:  # type: etree._Element
            frame = get_frame(frameTrig, search_point, multiplex_translation, ns, float_factory)
            if frame is not None:
                db.add_frame(frame)
                
        if ignore_cluster_info is True:
            pass
            # no support for signal direction
        else:
            isignal_triggerings = ar_get_xchildren(physical_channel, "I-SIGNAL-TRIGGERING", search_point, ns)
            for sig_trig in isignal_triggerings:
                isignal = ar_get_child(sig_trig, 'SIGNAL', search_point, ns)
                if isignal is None:
                    isignal = ar_get_child(sig_trig, 'I-SIGNAL', search_point, ns)
                if isignal is None:
                    sig_trig_text = ar_get_name(sig_trig, ns) if sig_trig is not None else "None"
                    logger.debug("load: no isignal for %s", sig_trig_text)
                    continue

                port_ref = ar_get_children(sig_trig, "I-SIGNAL-PORT", search_point, ns)

                for port in port_ref:
                    comm_direction = ar_get_child(port, "COMMUNICATION-DIRECTION", search_point, ns)
                    if comm_direction is not None and comm_direction.text == "IN":
                        sys_signal = ar_get_child(isignal, "SYSTEM-SIGNAL", search_point, ns)
                        ecu_name = ar_get_name(port.getparent().getparent().getparent().getparent(), ns)
                        # port points in ECU; probably more stable to go up
                        # from each ECU than to go down in XML...
                        if sys_signal in signal_rxs:
                            signal_rxs[sys_signal].add_receiver(ecu_name)
    # find ECUs:
        nodes = root.findall('.//' + ns + 'ECU-INSTANCE')
        for node in nodes:  # type: etree._Element
            ecu = process_ecu(node, db, search_point, multiplex_translation, ns)
            desc = ar_get_child(node, "DESC", search_point, ns)
            l2 = ar_get_child(desc, "L-2", search_point, ns)
            if l2 is not None:
                ecu.add_comment(l2.text)

            db.add_ecu(ecu)

        for frame in db.frames:
            sig_value_hash = dict()
            for sig in frame.signals:
                sig_value_hash[sig.name] = sig._initValue
            frame_data = frame.encode(sig_value_hash)
            frame.add_attribute("GenMsgStartValue", "".join(["%02x" % x for x in frame_data]))
        result[bus_name] = db
    return result
