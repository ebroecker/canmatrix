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
# this script exports arxml-files from a canmatrix-object
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


# for typing only
_Element = etree._Element
_DocRoot = typing.Union[_Element, ArTree]
_MultiplexId = typing.Union[str, int, None]
_FloatFactory = typing.Callable[[typing.Any], typing.Any]


def create_sub_element(parent, element_name, text=None):
    # type: (_Element, str, typing.Optional[str]) -> _Element
    sn = etree.SubElement(parent, element_name)
    if text is not None:
        sn.text = str(text)
    return sn


def get_base_type_of_signal(signal):
    # type: (canmatrix.Signal) -> typing.Tuple[str, int]
    """Get signal arxml-type and size based on the Signal properties."""
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

def fill_tree_from_xml(tag, ar_tree, namespace):
    # type: (_Element, ArTree, str) -> None
    """Parse the xml tree into ArTree objects."""
    for child in tag:  # type: _Element
        name_elem = child.find('./' + namespace + 'SHORT-NAME')
        # long_name = child.find('./' + namespace + 'LONG-NAME')
        if name_elem is not None and child is not None:
            fill_tree_from_xml(child, ar_tree.append_child(name_elem.text, child), namespace)
        if name_elem is None and child is not None:
            fill_tree_from_xml(child, ar_tree, namespace)


def find_children_by_path(from_element, path, root_or_cache, namespace):
    # type: (_Element, str, _DocRoot, str) -> typing.Sequence[_Element]
    path_elements = path.split('/')
    element = from_element
    for element_name in path_elements[:-1]:
        element = get_child(element, element_name, root_or_cache, namespace)
    children = get_children(element, path_elements[-1], root_or_cache, namespace)
    return children


def ar_path_to_x_path(ar_path, dest_element=None):
    # type: (str, typing.Optional[str]) -> str
    """Get path in translation-dictionary."""
    ar_path_elements = ar_path.strip('/').split('/')
    xpath = "."

    for element in ar_path_elements[:-1]:
        xpath += "//A:SHORT-NAME[text()='" + element + "']/.."
    if dest_element:
        xpath += "//A:" + dest_element + "/A:SHORT-NAME[text()='" + ar_path_elements[-1] + "']/.."
    else:
        xpath += "//A:SHORT-NAME[text()='" + ar_path_elements[-1] + "']/.."

    return xpath


xml_element_cache = dict()  # type: typing.Dict[str, _Element]


def get_element_by_path(tree, path_and_name, namespace):
    # type: (_Element, str, str) -> typing.Union[_Element, None]
    """Find sub-element of given path with given short name."""
    global xml_element_cache
    namespace_map = {'A': namespace[1:-1]}
    base_path, element_name = path_and_name.rsplit('/', 1)
    if base_path in xml_element_cache:
        base_element = xml_element_cache[base_path]
    else:
        base_xpath = ar_path_to_x_path(base_path)
        elems = tree.xpath(base_xpath, namespaces=namespace_map)
        base_element = elems[0] if elems else None
        xml_element_cache[base_path] = base_element

    element_found = None
    if base_element is not None:
        element_found = base_element.xpath(
            ".//A:SHORT-NAME[text()='{name}']/..".format(name=element_name),
            namespaces=namespace_map)[0]
    return element_found


def get_cached_element_by_path(data_tree, path):
    # type: (ArTree, str) -> typing.Optional[_Element]
    """Get element from ArTree by path."""
    if not isinstance(data_tree, ArTree):
        logger.warning("%s not called with ArTree, return None", get_cached_element_by_path.__name__)
        return None
    ptr = data_tree
    for name in path.split('/'):
        if ptr is None:
            return None
        if name.strip():
            ptr = ptr.get_child_by_name(name)
    return ptr.ref if ptr else None


def get_child(parent, tag_name, root_or_cache, namespace):
    # type: (_Element, str, _DocRoot, str) -> typing.Optional[_Element]
    """Get first sub-child or referenced sub-child with given name."""
    # logger.debug("get_child: " + tag_name)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tag_name)
    if ret is None:  # no direct element - try reference
        reference = parent.find('.//' + namespace + tag_name + '-REF')
        if reference is not None:
            if isinstance(root_or_cache, ArTree):
                ret = get_cached_element_by_path(root_or_cache, reference.text)
            else:
                ret = get_element_by_path(root_or_cache, reference.text, namespace)
    return ret


def get_children(parent, tag_name, root_or_cache, namespace):
    # type: (_Element, str, _DocRoot, str) -> typing.Sequence[_Element]
    if parent is None:
        return []
    ret = parent.findall('.//' + namespace + tag_name)
    if not ret:  # no direct element - get references
        ret_list = parent.findall('.//' + namespace + tag_name + '-REF')
        if isinstance(root_or_cache, ArTree):
            ret = [get_cached_element_by_path(root_or_cache, item.text) for item in ret_list]
        else:
            ret = [get_element_by_path(root_or_cache, item.text, namespace) for item in ret_list]
    return ret


def get_element_name(parent, ns):
    # type: (_Element, str) -> str
    """Get element short name."""
    name = parent.find('./' + ns + 'SHORT-NAME')
    if name is not None and name.text is not None:
        return name.text
    return ""


pdu_frame_mapping = {}  # type: typing.Dict[_Element, str]
signal_rxs = {}  # type: typing.Dict[_Element, canmatrix.Signal]


def get_sys_signals(sys_signal, sys_signal_array, frame, group_id, ns):
    # type: (_Element, typing.Sequence[_Element], canmatrix.Frame, int, str) -> None
    members = [get_element_name(signal, ns) for signal in sys_signal_array]
    frame.add_signal_group(get_element_name(sys_signal, ns), 1, members)  # todo use group_id instead of 1?


def decode_compu_method(compu_method, root_or_cache, ns, float_factory):
    # type: (_Element, _DocRoot, str, _FloatFactory) -> typing.Tuple
    values = {}
    factor = float_factory(1.0)
    offset = float_factory(0)
    unit = get_child(compu_method, "UNIT", root_or_cache, ns)
    const = None
    compu_scales = find_children_by_path(compu_method, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE", root_or_cache, ns)
    for compu_scale in compu_scales:
        ll = get_child(compu_scale, "LOWER-LIMIT", root_or_cache, ns)
        ul = get_child(compu_scale, "UPPER-LIMIT", root_or_cache, ns)
        sl = get_child(compu_scale, "SHORT-LABEL", root_or_cache, ns)
        if sl is None:
            desc = get_element_desc(compu_scale, root_or_cache, ns)
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

        scale_desc = get_element_desc(compu_scale, root_or_cache, ns)
        rational = get_child(compu_scale, "COMPU-RATIONAL-COEFFS", root_or_cache, ns)
        if rational is not None:
            numerator_parent = get_child(rational, "COMPU-NUMERATOR", root_or_cache, ns)
            numerator = get_children(numerator_parent, "V", root_or_cache, ns)
            denominator_parent = get_child(rational, "COMPU-DENOMINATOR", root_or_cache, ns)
            denominator = get_children(denominator_parent, "V", root_or_cache, ns)

            factor = float_factory(numerator[1].text) / float_factory(denominator[0].text)
            offset = float_factory(numerator[0].text) / float_factory(denominator[0].text)
        else:
            const = get_child(compu_scale, "COMPU-CONST", root_or_cache, ns)
            # add value
            if const is None:
                logger.warning("Unknown Compu-Method: at sourceline %d ", compu_method.sourceline)
    return values, factor, offset, unit, const


def get_signals(signal_array, frame, root_or_cache, ns, multiplex_id, float_factory):
    # type: (typing.Sequence[_Element], canmatrix.Frame, _DocRoot, str, _MultiplexId, typing.Callable) -> None
    """Add signals from xml to the Frame."""
    global signal_rxs
    group_id = 1
    if signal_array is None:  # Empty signalarray - nothing to do
        return
    for signal in signal_array:
        compu_method = None
        motorola = get_child(signal, "PACKING-BYTE-ORDER", root_or_cache, ns)
        start_bit = get_child(signal, "START-POSITION", root_or_cache, ns)

        isignal = get_child(signal, "SIGNAL", root_or_cache, ns)
        if isignal is None:
            isignal = get_child(signal, "I-SIGNAL", root_or_cache, ns)
        if isignal is None:
            isignal = get_child(signal, "I-SIGNAL-GROUP", root_or_cache, ns)
            if isignal is not None:
                logger.debug("get_signals: found I-SIGNAL-GROUP ")

                isignal_array = find_children_by_path(isignal, "I-SIGNAL", root_or_cache, ns)
                get_sys_signals(isignal, isignal_array, frame, group_id, ns)
                group_id = group_id + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                frame.name, get_child(signal, "SHORT-NAME", root_or_cache, ns).text)

        base_type = get_child(isignal, "BASE-TYPE", root_or_cache, ns)
        signal_name = None  # type: typing.Optional[str]
        signal_name_elem = get_child(isignal, "LONG-NAME", root_or_cache, ns)
        if signal_name_elem is not None:
            signal_name_elem = get_child(signal_name_elem, "L-4", root_or_cache, ns)
            if signal_name_elem is not None:
                signal_name = signal_name_elem.text
        system_signal = get_child(isignal, "SYSTEM-SIGNAL", root_or_cache, ns)
        if system_signal is None:
            logger.debug('Frame %s, signal %s has no system-signal', frame.name, isignal.tag)

        if "SYSTEM-SIGNAL-GROUP" in system_signal.tag:
            system_signals = find_children_by_path(system_signal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", root_or_cache, ns)
            get_sys_signals(system_signal, system_signals, frame, group_id, ns)
            group_id = group_id + 1
            continue

        length = get_child(isignal, "LENGTH", root_or_cache, ns)
        if length is None:
            length = get_child(system_signal, "LENGTH", root_or_cache, ns)

        name = get_child(system_signal, "SHORT-NAME", root_or_cache, ns)
        unit_element = get_child(isignal, "UNIT", root_or_cache, ns)
        display_name = get_child(unit_element, "DISPLAY-NAME", root_or_cache, ns)
        if display_name is not None:
            signal_unit = display_name.text
        else:
            signal_unit = ""

        signal_min = None  # type: canmatrix.types.OptionalPhysicalValue
        signal_max = None  # type: canmatrix.types.OptionalPhysicalValue
        receiver = []  # type: typing.List[str]

        signal_description = get_element_desc(system_signal, root_or_cache, ns)

        datatype = get_child(system_signal, "DATA-TYPE", root_or_cache, ns)
        if datatype is None:  # AR4?
            data_constr = None
            compu_method = None
            base_type = None
            for test_signal in [isignal, system_signal]:
                if data_constr is None:
                    data_constr = get_child(test_signal, "DATA-CONSTR", root_or_cache, ns)
                if compu_method is None:
                    compu_method = get_child(test_signal, "COMPU-METHOD", root_or_cache, ns)
                if base_type is None:
                    base_type = get_child(test_signal, "BASE-TYPE", root_or_cache, ns)



            lower = get_child(data_constr, "LOWER-LIMIT", root_or_cache, ns)
            upper = get_child(data_constr, "UPPER-LIMIT", root_or_cache, ns)
            encoding = None  # TODO - find encoding in AR4
        else:
            lower = get_child(datatype, "LOWER-LIMIT", root_or_cache, ns)
            upper = get_child(datatype, "UPPER-LIMIT", root_or_cache, ns)
            encoding = get_child(datatype, "ENCODING", root_or_cache, ns)

        if encoding is not None and (encoding.text == "SINGLE" or encoding.text == "DOUBLE"):
            is_float = True
        else:
            is_float = False
        
        if lower is not None and upper is not None:
            signal_min = float_factory(lower.text)
            signal_max = float_factory(upper.text)

        datdefprops = get_child(datatype, "SW-DATA-DEF-PROPS", root_or_cache, ns)

        if compu_method is None:
            compu_method = get_child(datdefprops, "COMPU-METHOD", root_or_cache, ns)
        if compu_method is None:  # AR4
            compu_method = get_child(isignal, "COMPU-METHOD", root_or_cache, ns)
            base_type = get_child(isignal, "BASE-TYPE", root_or_cache, ns)
            encoding = get_child(base_type, "BASE-TYPE-ENCODING", root_or_cache, ns)
            if encoding is not None and encoding.text == "IEEE754":
                is_float = True
        if compu_method is None:
            logger.debug('No Compmethod found!! - try alternate scheme 1.')
            networkrep = get_child(isignal, "NETWORK-REPRESENTATION-PROPS", root_or_cache, ns)
            data_def_props_var = get_child(networkrep, "SW-DATA-DEF-PROPS-VARIANTS", root_or_cache, ns)
            data_def_props_cond = get_child(data_def_props_var, "SW-DATA-DEF-PROPS-CONDITIONAL", root_or_cache, ns)
            if data_def_props_cond is not None:
                try:
                    compu_method = get_child(data_def_props_cond, "COMPU-METHOD", root_or_cache, ns)
                except:
                    logger.debug('No valid compu method found for this - check ARXML file!!')
                    compu_method = None
        #####################################################################################################
        # no found compu-method fuzzy search in systemsignal:
        #####################################################################################################
        if compu_method is None:
            logger.debug('No Compmethod found!! - fuzzy search in syssignal.')
            compu_method = get_child(system_signal, "COMPU-METHOD", root_or_cache, ns)

        # decode compuMethod:
        (values, factor, offset, unit_elem, const) = decode_compu_method(compu_method, root_or_cache, ns, float_factory)

        if signal_min is not None:
            signal_min *= factor
            signal_min += offset
        if signal_max is not None:
            signal_max *= factor
            signal_max += offset

        if base_type is None:
            base_type = get_child(datdefprops, "BASE-TYPE", root_or_cache, ns)
        if base_type is not None:
            type_name = get_element_name(base_type, ns)
            if type_name[0] == 'u':
                is_signed = False  # unsigned
            else:
                is_signed = True  # signed
        else:
            is_signed = True  # signed

        if unit_elem is not None:
            longname = get_child(unit_elem, "LONG-NAME", root_or_cache, ns)
        #####################################################################################################
        # Modification to support obtaining the Signals Unit by DISPLAY-NAME. 07June16
        #####################################################################################################
            display_name = None
            try:
                display_name = get_child(unit_elem, "DISPLAY-NAME", root_or_cache, ns)
            except:
                logger.debug('No Unit Display name found!! - using long name')
            if display_name is not None:
                signal_unit = display_name.text
            else:
                l4 = get_child(longname, "L-4", root_or_cache, ns)
                if l4 is not None:
                    signal_unit = l4.text

        init_list = find_children_by_path(system_signal, "INIT-VALUE/VALUE", root_or_cache, ns)

        if not init_list:
            init_list = find_children_by_path(isignal, "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE", root_or_cache, ns)  # #AR4.2
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
            signal_rxs[system_signal] = new_signal

            if base_type is not None:
                temp = get_child(base_type, "SHORT-NAME", root_or_cache, ns)
                if temp is not None and "boolean" == temp.text:
                    new_signal.add_values(1, "TRUE")
                    new_signal.add_values(0, "FALSE")

            if initvalue is not None and initvalue.text is not None:
                initvalue.text = canmatrix.utils.guess_value(initvalue.text)
                new_signal._initValue = float_factory(initvalue.text)
                new_signal.add_attribute("GenSigStartValue", str(new_signal._initValue))
            else:
                new_signal._initValue = 0

            for key, value in list(values.items()):
                new_signal.add_values(key, value)
            if signal_name is not None:
                new_signal.add_attribute("LongName", signal_name)
            frame.add_signal(new_signal)


def get_frame(frame_triggering, root_or_cache, multiplex_translation, ns, float_factory):
    # type: (_Element, _DocRoot, dict, str, typing.Callable) -> typing.Union[canmatrix.Frame, None]
    global pdu_frame_mapping
    address_mode = get_child(frame_triggering, "CAN-ADDRESSING-MODE", root_or_cache, ns)
    arb_id = get_child(frame_triggering, "IDENTIFIER", root_or_cache, ns)
    frame_elem = get_child(frame_triggering, "FRAME", root_or_cache, ns)

    frame_name_elem = get_child(frame_triggering, "SHORT-NAME", root_or_cache, ns)
    logger.debug("processing Frame: %s", frame_name_elem.text)
    if arb_id is None:
        logger.info("found Frame %s without arbitration id", frame_name_elem.text)
        return None
    arbitration_id = int(arb_id.text)

    if frame_elem is not None:
        dlc_elem = get_child(frame_elem, "FRAME-LENGTH", root_or_cache, ns)
        pdu_mappings = get_child(frame_elem, "PDU-TO-FRAME-MAPPINGS", root_or_cache, ns)
        pdu_mapping = get_child(pdu_mappings, "PDU-TO-FRAME-MAPPING", root_or_cache, ns)
        pdu = get_child(pdu_mapping, "PDU", root_or_cache, ns)  # SIGNAL-I-PDU

        if pdu is not None and 'SECURED-I-PDU' in pdu.tag:
            logger.info("found secured pdu - no signal extraction possible: %s", get_element_name(pdu, ns))

        pdu_frame_mapping[pdu] = get_element_name(frame_elem, ns)

        new_frame = canmatrix.Frame(get_element_name(frame_elem, ns), size=int(dlc_elem.text))
        comment = get_element_desc(frame_elem, root_or_cache, ns)
        if comment is not None:
            new_frame.add_comment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF", frame_name_elem.text)
        ipdu_triggering_refs = get_child(frame_triggering, "I-PDU-TRIGGERING-REFS", root_or_cache, ns)
        ipdu_triggering = get_child(ipdu_triggering_refs, "I-PDU-TRIGGERING", root_or_cache, ns)
        pdu = get_child(ipdu_triggering, "I-PDU", root_or_cache, ns)
        if pdu is None:
            pdu = get_child(ipdu_triggering, "I-SIGNAL-I-PDU", root_or_cache, ns)  # AR4.2
        dlc_elem = get_child(pdu, "LENGTH", root_or_cache, ns)
        new_frame = canmatrix.Frame(frame_name_elem.text, arbitration_id=arbitration_id, size=int(int(dlc_elem.text) / 8))

    if pdu is None:
        logger.error("pdu is None")
    else:
        logger.debug(get_element_name(pdu, ns))

    if pdu is not None and "MULTIPLEXED-I-PDU" in pdu.tag:
        selector_byte_order = get_child(pdu, "SELECTOR-FIELD-BYTE-ORDER", root_or_cache, ns)
        selector_len = get_child(pdu, "SELECTOR-FIELD-LENGTH", root_or_cache, ns)
        selector_start = get_child(pdu, "SELECTOR-FIELD-START-POSITION", root_or_cache, ns)
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
        static_part = get_child(pdu, "STATIC-PART", root_or_cache, ns)
        ipdu = get_child(static_part, "I-PDU", root_or_cache, ns)
        if ipdu is not None:
            pdu_sig_mappings = get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS", root_or_cache, ns)
            pdu_sig_mapping = get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING", root_or_cache, ns)
            get_signals(pdu_sig_mapping, new_frame, root_or_cache, ns, None, float_factory)
            multiplex_translation[get_element_name(ipdu, ns)] = get_element_name(pdu, ns)

        dynamic_part = get_child(pdu, "DYNAMIC-PART", root_or_cache, ns)
#               segmentPositions = arGetChild(dynamic_part, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamic_part_alternatives = get_child(dynamic_part, "DYNAMIC-PART-ALTERNATIVES", root_or_cache, ns)
        dynamic_part_alternative_list = get_children(dynamic_part_alternatives, "DYNAMIC-PART-ALTERNATIVE", root_or_cache, ns)
        for alternative in dynamic_part_alternative_list:
            selector_id = get_child(alternative, "SELECTOR-FIELD-CODE", root_or_cache, ns)
            ipdu = get_child(alternative, "I-PDU", root_or_cache, ns)
            multiplex_translation[get_element_name(ipdu, ns)] = get_element_name(pdu, ns)
            if ipdu is not None:
                pdu_sig_mappings = get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS", root_or_cache, ns)
                pdu_sig_mapping = get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING", root_or_cache, ns)
                get_signals(pdu_sig_mapping, new_frame, root_or_cache, ns, selector_id.text, float_factory)

    if new_frame.comment is None:
        new_frame.add_comment(get_element_desc(pdu, root_or_cache, ns))

    if address_mode is not None and address_mode.text == 'EXTENDED':
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=True)
    else:
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=False)

    timing_spec = get_child(pdu, "I-PDU-TIMING-SPECIFICATION", root_or_cache, ns)
    if timing_spec is None:
        timing_spec = get_child(pdu, "I-PDU-TIMING-SPECIFICATIONS", root_or_cache, ns)
    cyclic_timing = get_child(timing_spec, "CYCLIC-TIMING", root_or_cache, ns)
    repeating_time = get_child(cyclic_timing, "REPEATING-TIME", root_or_cache, ns)

    event_timing = get_child(timing_spec, "EVENT-CONTROLLED-TIMING", root_or_cache, ns)
    repeats = get_child(event_timing, "NUMBER-OF-REPEATS", root_or_cache, ns)
    minimum_delay = get_child(timing_spec, "MINIMUM-DELAY", root_or_cache, ns)
    starting_time = get_child(timing_spec, "STARTING-TIME", root_or_cache, ns)

    time_offset = get_child(cyclic_timing, "TIME-OFFSET", root_or_cache, ns)
    time_period = get_child(cyclic_timing, "TIME-PERIOD", root_or_cache, ns)

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
        value = get_child(starting_time, "VALUE", root_or_cache, ns)
        new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))
    elif cyclic_timing is not None:
        value = get_child(time_offset, "VALUE", root_or_cache, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))

    value = get_child(repeating_time, "VALUE", root_or_cache, ns)
    if value is not None:
        new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))
    elif cyclic_timing is not None:
        value = get_child(time_period, "VALUE", root_or_cache, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))


#    pdu_sig_mappings = get_child(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if not pdu_sig_mappings:
#        logger.debug("Frame %s no SIGNAL-TO-PDU-MAPPINGS found", new_frame.name)
    pdu_sig_mapping = get_children(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", root_or_cache, ns)
    if pdu_sig_mapping:
        get_signals(pdu_sig_mapping, new_frame, root_or_cache, ns, None, float_factory)

    # Seen some pdu_sig_mapping being [] and not None with some arxml 4.2
    else:  # AR 4.2
        pdu_trigs = get_children(frame_triggering, "PDU-TRIGGERINGS", root_or_cache, ns)
        if pdu_trigs is not None:
            for pdu_trig in pdu_trigs:
                trig_ref_cond = get_child(pdu_trig, "PDU-TRIGGERING-REF-CONDITIONAL", root_or_cache, ns)
                trigs = get_child(trig_ref_cond, "PDU-TRIGGERING", root_or_cache, ns)
                ipdus = get_child(trigs, "I-PDU", root_or_cache, ns)

                signal_to_pdu_maps = get_child(ipdus, "I-SIGNAL-TO-PDU-MAPPINGS", root_or_cache, ns)
                if signal_to_pdu_maps is None:
                    signal_to_pdu_maps = get_child(ipdus, "I-SIGNAL-TO-I-PDU-MAPPINGS", root_or_cache, ns)

                if signal_to_pdu_maps is None:
                    logger.debug("AR4.x PDU %s no SIGNAL-TO-PDU-MAPPINGS found - no signal extraction!",
                                 get_element_name(ipdus, ns))
                # signal_to_pdu_map = get_children(signal_to_pdu_maps, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                get_signals(signal_to_pdu_maps, new_frame, root_or_cache, ns, None, float_factory)  # todo BUG expects list, not item
        else:
            logger.debug("Frame %s (assuming AR4.2) no PDU-TRIGGERINGS found", new_frame.name)
    return new_frame


def get_element_desc(element, ar_tree, ns):
    # type: (_Element, _DocRoot, str) -> str
    """Get element description from XML."""
    desc = get_child(element, "DESC", ar_tree, ns)
    txt = get_child(desc, 'L-2[@L="DE"]', ar_tree, ns)
    if txt is None:
        txt = get_child(desc, 'L-2[@L="EN"]', ar_tree, ns)
    if txt is None:
        txt = get_child(desc, 'L-2', ar_tree, ns)
    if txt is not None:
        return txt.text
    else:
        return ""


def process_ecu(ecu_elem, db, ar_dict, multiplex_translation, ns):
    # type: (_Element, canmatrix.CanMatrix, _DocRoot, typing.Mapping[str, str], str) -> canmatrix.Ecu
    global pdu_frame_mapping
    connectors = get_child(ecu_elem, "CONNECTORS", ar_dict, ns)
    diag_address = get_child(ecu_elem, "DIAGNOSTIC-ADDRESS", ar_dict, ns)
    diag_response = get_child(ecu_elem, "RESPONSE-ADDRESSS", ar_dict, ns)
    # TODO: use diag_address for frame-classification
    comm_connector = get_child(connectors, "COMMUNICATION-CONNECTOR", ar_dict, ns)
    if comm_connector is None:
        comm_connector = get_child(connectors, "CAN-COMMUNICATION-CONNECTOR", ar_dict, ns)
    frames = find_children_by_path(comm_connector, "ECU-COMM-PORT-INSTANCES/FRAME-PORT", ar_dict, ns)
    nm_address = get_child(comm_connector, "NM-ADDRESS", ar_dict, ns)
    assoc_refs = get_child(ecu_elem, "ASSOCIATED-I-PDU-GROUP-REFS", ar_dict, ns)

    if assoc_refs is not None:
        assoc = get_children(assoc_refs, "ASSOCIATED-I-PDU-GROUP", ar_dict, ns)
    else:  # AR4
        assoc_refs = get_child(ecu_elem, "ASSOCIATED-COM-I-PDU-GROUP-REFS", ar_dict, ns)
        assoc = get_children(assoc_refs, "ASSOCIATED-COM-I-PDU-GROUP", ar_dict, ns)

    in_frame = []
    out_frame = []

    # get direction of frames (is current ECU sender/receiver/...?)
    for ref in assoc:
        direction = get_child(ref, "COMMUNICATION-DIRECTION", ar_dict, ns)
        group_refs = get_child(ref, "CONTAINED-I-PDU-GROUPS-REFS", ar_dict, ns)
        pdu_refs = get_child(ref, "I-PDU-REFS", ar_dict, ns)
        if pdu_refs is not None:  # AR3
            # local defined pdus
            pdus = get_children(pdu_refs, "I-PDU", ar_dict, ns)
            for pdu in pdus:
                if pdu in pdu_frame_mapping:
                    if direction.text == "IN":
                        in_frame.append(pdu_frame_mapping[pdu])
                    else:
                        out_frame.append(pdu_frame_mapping[pdu])
        else:  # AR4
            isigpdus = get_child(ref, "I-SIGNAL-I-PDUS", ar_dict, ns)
            isigconds = get_children(
                isigpdus, "I-SIGNAL-I-PDU-REF-CONDITIONAL", ar_dict, ns)
            for isigcond in isigconds:
                pdus = get_children(isigcond, "I-SIGNAL-I-PDU", ar_dict, ns)
                for pdu in pdus:
                    if pdu in pdu_frame_mapping:
                        if direction.text == "IN":
                            in_frame.append(pdu_frame_mapping[pdu])
                        else:
                            out_frame.append(pdu_frame_mapping[pdu])

        # grouped pdus
        group = get_children(group_refs, "CONTAINED-I-PDU-GROUPS", ar_dict, ns)
        for t in group:
            if direction is None:
                direction = get_child(
                    t, "COMMUNICATION-DIRECTION", ar_dict, ns)
            pdu_refs = get_child(t, "I-PDU-REFS", ar_dict, ns)
            pdus = get_children(pdu_refs, "I-PDU", ar_dict, ns)
            for pdu in pdus:
                if direction.text == "IN":
                    in_frame.append(get_element_name(pdu, ns))
                else:
                    out_frame.append(get_element_name(pdu, ns))

        for out in out_frame:
            if out in multiplex_translation:
                out = multiplex_translation[out]
            frame = db.frame_by_name(out)
            if frame is not None:
                frame.add_transmitter(get_element_name(ecu_elem, ns))
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
    new_ecu = canmatrix.Ecu(get_element_name(ecu_elem, ns))
    if nm_address is not None:
        new_ecu.add_attribute("NWM-Stationsadresse", nm_address.text)
        new_ecu.add_attribute("NWM-Knoten", "ja")
    else:
        new_ecu.add_attribute("NWM-Stationsadresse", "0")
        new_ecu.add_attribute("NWM-Knoten", "nein")
    return new_ecu


def ecuc_extract_signal(signal_node, ns):
    # type: (_Element, str) -> canmatrix.Signal
    """Extract signal from ECUc file."""
    attributes = signal_node.findall(".//" + ns + "DEFINITION-REF")  # type: typing.Sequence[_Element]
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
    return canmatrix.Signal(get_element_name(signal_node, ns), start_bit=start_bit, size=size, is_little_endian=is_little)


def extract_cm_from_ecuc(com_module, root_or_cache, ns):
    # type: (_Element, _DocRoot, str) -> typing.Dict[str, canmatrix.CanMatrix]
    db = canmatrix.CanMatrix()
    definitions = com_module.findall('.//' + ns + "DEFINITION-REF")
    for definition in definitions:
        if definition.text.endswith("ComIPdu"):
            container = definition.getparent()
            frame = canmatrix.Frame(get_element_name(container, ns))
            db.add_frame(frame)
            all_references = get_children(container, "ECUC-REFERENCE-VALUE", root_or_cache, ns)
            for reference in all_references:
                value = get_child(reference, "VALUE", root_or_cache, ns)
                if value is not None:
                    signal_definition = value.find('./' + ns + "DEFINITION-REF")
                    if signal_definition.text.endswith("ComSignal"):
                        signal = ecuc_extract_signal(value, ns)
                        frame.add_signal(signal)
    db.recalc_dlc(strategy="max")
    return {"": db}


def load(file, **options):
    # type: (typing.IO, **typing.Any) -> typing.Dict[str, canmatrix.CanMatrix]

    global xml_element_cache
    xml_element_cache = dict()
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

    root = tree.getroot()  # type: _Element
    logger.debug(" Done\n")

    ns = "{" + tree.xpath('namespace-uri(.)') + "}"  # type: str
    nsp = tree.xpath('namespace-uri(.)')

    top_level_packages = root.find('./' + ns + 'TOP-LEVEL-PACKAGES')

    if top_level_packages is None:
        # no "TOP-LEVEL-PACKAGES found, try root
        top_level_packages = root

    logger.debug("Build arTree ...")

    if use_ar_xpath:
        search_point = top_level_packages  # type: typing.Union[_Element, ArTree]
    else:
        ar_tree = ArTree()
        fill_tree_from_xml(top_level_packages, ar_tree, ns)
        search_point = ar_tree

    logger.debug(" Done\n")

    if isinstance(search_point, ArTree):
        com_module = get_cached_element_by_path(search_point, "ActiveEcuC/Com")
    else:
        com_module = get_element_by_path(search_point, "ActiveEcuC/Com", ns)
    if com_module is not None:
        logger.info("seems to be a ECUC arxml. Very limited support for extracting canmatrix.")
        return extract_cm_from_ecuc(com_module, search_point, ns)

    frames = root.findall('.//' + ns + 'CAN-FRAME')  # AR4.2
    if frames is None:
        frames = root.findall('.//' + ns + 'FRAME')  # AR3.2-4.1?
    
    logger.debug("%d frames in arxml...", len(frames))
    can_triggers = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
    logger.debug("%d can-frame-triggering in arxml...", len(can_triggers))

    sig_pdu_map = root.findall('.//' + ns + 'SIGNAL-TO-PDU-MAPPINGS')
    logger.debug("%d SIGNAL-TO-PDU-MAPPINGS in arxml...", len(sig_pdu_map))

    sig_ipdu = root.findall('.//' + ns + 'I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug("%d I-SIGNAL-TO-I-PDU-MAPPING in arxml...", len(sig_ipdu))

    if ignore_cluster_info is True:
        ccs = [etree.Element("ignoreClusterInfo")]  # type: typing.Sequence[_Element]
    else:
        ccs = root.findall('.//' + ns + 'CAN-CLUSTER')
    for cc in ccs:  # type: _Element
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
            speed = get_child(cc, "SPEED", search_point, ns)
            logger.debug("Busname: " + get_element_name(cc, ns))

            bus_name = get_element_name(cc, ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            physical_channels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")  # type: _Element
            if physical_channels is None:
                logger.error("PHYSICAL-CHANNELS not found")

            nm_lower_id = get_child(cc, "NM-LOWER-CAN-ID", search_point, ns)

            physical_channel = get_child(physical_channels, "PHYSICAL-CHANNEL", search_point, ns)
            if physical_channel is None:
                physical_channel = get_child(physical_channels, "CAN-PHYSICAL-CHANNEL", search_point, ns)
            if physical_channel is None:
                logger.error("PHYSICAL-CHANNEL not found")
            can_frame_trig = get_children(physical_channel, "CAN-FRAME-TRIGGERING", search_point, ns)
            if can_frame_trig is None:
                logger.error("CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug("%d frames found in arxml", len(can_frame_trig))

        multiplex_translation = {}  # type: typing.Dict[str, str]
        for frameTrig in can_frame_trig:  # type: _Element
            frame = get_frame(frameTrig, search_point, multiplex_translation, ns, float_factory)
            if frame is not None:
                db.add_frame(frame)
                
        if ignore_cluster_info is True:
            pass
            # no support for signal direction
        else:
            isignal_triggerings = find_children_by_path(physical_channel, "I-SIGNAL-TRIGGERING", search_point, ns)
            for sig_trig in isignal_triggerings:
                isignal = get_child(sig_trig, 'SIGNAL', search_point, ns)
                if isignal is None:
                    isignal = get_child(sig_trig, 'I-SIGNAL', search_point, ns)
                if isignal is None:
                    sig_trig_text = get_element_name(sig_trig, ns) if sig_trig is not None else "None"
                    logger.debug("load: no isignal for %s", sig_trig_text)
                    continue

                port_ref = get_children(sig_trig, "I-SIGNAL-PORT", search_point, ns)

                for port in port_ref:
                    comm_direction = get_child(port, "COMMUNICATION-DIRECTION", search_point, ns)
                    if comm_direction is not None and comm_direction.text == "IN":
                        sys_signal = get_child(isignal, "SYSTEM-SIGNAL", search_point, ns)
                        ecu_name = get_element_name(port.getparent().getparent().getparent().getparent(), ns)
                        # port points in ECU; probably more stable to go up
                        # from each ECU than to go down in XML...
                        if sys_signal in signal_rxs:
                            signal_rxs[sys_signal].add_receiver(ecu_name)
    # find ECUs:
        nodes = root.findall('.//' + ns + 'ECU-INSTANCE')
        for node in nodes:  # type: _Element
            ecu = process_ecu(node, db, search_point, multiplex_translation, ns)
            desc = get_child(node, "DESC", search_point, ns)
            l2 = get_child(desc, "L-2", search_point, ns)
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
