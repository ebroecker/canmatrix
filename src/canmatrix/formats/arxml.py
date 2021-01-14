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
# this script exports arxml-files from a canmatrix-object
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
# currently Support for Autosar 3.2 and 4.0-4.3 is planned

from __future__ import absolute_import, division, print_function

import decimal
import logging
import typing
from builtins import *

import lxml.etree

import canmatrix
import canmatrix.types
import canmatrix.utils

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal

clusterExporter = 1
clusterImporter = 1


class ArTree(object):
    def __init__(self, name="", ref=None):  # type: (str, lxml.etree._Element) -> None
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
    def ref(self):  # type: () -> lxml.etree._Element
        return self._ref


# for typing only
_Element = lxml.etree._Element
_DocRoot = typing.Union[_Element, ArTree]
_MultiplexId = typing.Union[str, int, None]
_FloatFactory = typing.Callable[[typing.Any], typing.Any]


class Earxml:
    def __init__(self, use_ar_xpath):
        self.xml_element_cache = dict()  # type: typing.Dict[str, _Element]
        self.use_ar_xpath = use_ar_xpath
        self.xml_element_cache = {}


    def open(self, filename):
        self.tree = lxml.etree.parse(filename)

        self.root = self.tree.getroot()  # type: _Element

        self.ns = "{" + self.tree.xpath('namespace-uri(.)') + "}"  # type: str
        self.nsp = self.tree.xpath('namespace-uri(.)')

    def findall(self, xpath, start_element=None):
        if start_element is None:
            start_element = self.root
        return start_element.findall('.//' + self.ns + xpath)

    def find(self, xpath, start_element=None):
        if start_element is None:
            start_element = self.root
        return start_element.find('.//' + self.ns + xpath)

    def ar_path_to_x_path(self, ar_path, dest_element=None):
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

    def get_short_name_path(self, shortname_path):
        if shortname_path in self.xml_element_cache:
            return self.xml_element_cache[shortname_path]

        if self.use_ar_xpath:
            namespace_map = {'A': self.ns[1:-1]}
            base_xpath = self.ar_path_to_x_path(shortname_path)
            temp = self.tree.xpath(base_xpath, namespaces=namespace_map)
            if len(temp) > 0:
                self.xml_element_cache[shortname_path] = temp[0]
                return temp[0]
            self.xml_element_cache[shortname_path] = temp[0]
            return temp
        else:
            return self.get_shortname_path_from_artree(shortname_path)
        return elems

    def get_short_name(self, element):
        # type: (_Element, str) -> str
        """Get element short name."""
        name = self.find('SHORT-NAME', element)
        if name is not None and name.text is not None:
            return name.text
        return ""

    def follow_ref(self, start_element, element_name):
        ref_element = self.find(element_name, start_element)
        if ref_element is None:
            return None
        target_element = self.get_short_name_path(ref_element.text)
        return target_element

    def follow_all_ref(self, start_element, element_name):
        if start_element is None:
            return []
        ref_elements = self.findall(element_name, start_element)
        if ref_elements is None:
            return None
        target_elements = [self.get_short_name_path(item.text) for item in ref_elements]
        return target_elements


    def get_all_sub_by_name(self, start_element, name):
        return self.findall(name, start_element)

    def get_sub_by_name(self, start_element, name):
        return self.find(name, start_element)

    def fill_tree_from_xml(self, tag, tree_point):
        # type: (_Element, ArTree, str) -> None
        """Parse the xml tree into ArTree objects."""
        for child in tag:  # type: _Element
            name_elem = child.find('./' + self.ns + 'SHORT-NAME')
            # long_name = child.find('./' + namespace + 'LONG-NAME')
            if name_elem is not None and child is not None:
                self.fill_tree_from_xml(child, tree_point.append_child(name_elem.text, child))
            if name_elem is None and child is not None:
                self.fill_tree_from_xml(child, tree_point)

    def find_children_by_path(self, from_element, path):
        # type: (_Element, str, _DocRoot, str) -> typing.Sequence[_Element]
        path_elements = path.split('/')
        element = from_element
        for element_name in path_elements[:-1]:
            element = self.get_child(element, element_name)
        children = self.get_children(element, path_elements[-1])
        return children

    def get_element_name(self, parent):
        # type: (_Element, str) -> str
        """Get element short name."""
        name = self.find('SHORT-NAME', parent)
        if name is not None and name.text is not None:
            return name.text
        return ""

    def get_shortname_path_from_artree(self, path):
        # type: (ArTree, str) -> typing.Optional[_Element]
        """Get element from ArTree by path."""
        ptr = self.ar_tree
        for name in path.split('/'):
            if ptr is None:
                return None
            if name.strip():
                ptr = ptr.get_child_by_name(name)
        return ptr.ref if ptr else None

    def get_child(self, parent, tag_name):
        # type: (_Element, str, _DocRoot, str) -> typing.Optional[_Element]
        """Get first sub-child or referenced sub-child with given name."""
        # logger.debug("get_child: " + tag_name)
        if parent is None:
            return None
        ret = self.find(tag_name, parent)
        if ret is None:  # no direct element - try reference
            reference = self.find(tag_name + '-REF', parent)
            if reference is not None:
                ret = self.get_short_name_path(reference.text)
                raise "use follow_ref!"
        return ret

    def get_children(self, parent, tag_name):
        # type: (_Element, str, _DocRoot, str) -> typing.Sequence[_Element]
        if parent is None:
            return []
        ret = self.findall(tag_name, parent)
        if not ret:  # no direct element - get references
            ret_list = self.findall(tag_name + '-REF', parent)
            ret = [self.get_short_name_path(item.text) for item in ret_list]
            if len(ret) > 0:
                raise "use follow_all_ref!"
        return ret

    def build_ar_tree(self):
        top_level_packages = self.find('TOP-LEVEL-PACKAGES')

        if top_level_packages is None:
            # no "TOP-LEVEL-PACKAGES found, try root
            top_level_packages = self.root

        if self.use_ar_xpath:
            search_point = top_level_packages  # type: typing.Union[_Element, ArTree]
        else:
            self.ar_tree = ArTree()
            self.fill_tree_from_xml(top_level_packages, self.ar_tree)

    def get_element_desc(self, element):
        # type: (_Element, _DocRoot, str) -> str
        """Get element description from XML."""
        desc = self.get_child(element, "DESC")
        txt = self.get_child(desc, 'L-2[@L="DE"]')
        if txt is None:
            txt = self.get_child(desc, 'L-2[@L="EN"]')
        if txt is None:
            txt = self.get_child(desc, 'L-2')
        if txt is not None:
            return txt.text
        else:
            return ""


def create_sub_element(parent, element_name, text=None, dest=None):
    # type: (_Element, str, typing.Optional[str]) -> _Element
    sn = lxml.etree.SubElement(parent, element_name)
    if text is not None:
        sn.text = str(text)
    if dest is not None:
        sn.set("DEST", dest)
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
    # type: (typing.Mapping[str, canmatrix.CanMatrix], typing.IO, **str) -> None
    ar_version = options.get("arVersion", "3.2.3")

    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                for rec in signal.receivers:
                    frame.add_receiver(rec.strip())

    if ar_version[0] == "3":
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = lxml.etree.Element(
            'AUTOSAR',
            nsmap={
                None: 'http://autosar.org/' + ar_version,
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/' + ar_version + ' AUTOSAR_' + ar_version.replace('.', '') + '.xsd'
        top_level_packages = create_sub_element(root, 'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = lxml.etree.Element(
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
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF', dest='FRAME-PORT', text="/ECU/{0}/CN_{0}/{1}".format(transmitter, frame.name))
            for rec in frame.receivers:
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF', dest='FRAME-PORT', text="/ECU/{0}/CN_{0}/{1}".format(rec, frame.name))
            frame_ref = create_sub_element(can_frame_triggering, 'FRAME-REF')
            if ar_version[0] == "3":
                frame_ref.set('DEST', 'FRAME')
                frame_ref.text = "/Frame/FRAME_{0}".format(frame.name)
                pdu_triggering_refs = create_sub_element(can_frame_triggering, 'I-PDU-TRIGGERING-REFS')
                pdu_triggering_ref = create_sub_element(pdu_triggering_refs, 'I-PDU-TRIGGERING-REF', dest='I-PDU-TRIGGERING')
            else:
                frame_ref.set('DEST', 'CAN-FRAME')
                frame_ref.text = "/CanFrame/FRAME_{0}".format(frame.name)
                pdu_triggering = create_sub_element(can_frame_triggering, 'PDU-TRIGGERINGS')
                pdu_triggering_ref_conditional = create_sub_element(pdu_triggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
                pdu_triggering_ref = create_sub_element(pdu_triggering_ref_conditional, 'PDU-TRIGGERING-REF', dest='PDU-TRIGGERING')

            if frame.arbitration_id.extended is False:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
            else:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')

            if frame.is_fd:
                create_sub_element(can_frame_triggering, 'CAN-FRAME-RX-BEHAVIOR', "CAN-FD")
                create_sub_element(can_frame_triggering, 'CAN-FRAME-RX-BEHAVIOR', "CAN-FD")
            create_sub_element(can_frame_triggering, 'IDENTIFIER', str(frame.arbitration_id.id))

            pdu_triggering_ref.text = "/Cluster/CAN/IPDUTRIGG_{0}".format(frame.name)

        if ar_version[0] == "3":
            ipdu_triggerings = create_sub_element(physical_channel, 'I-PDU-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                ipdu_triggering = create_sub_element(ipdu_triggerings, 'I-PDU-TRIGGERING')
                create_sub_element(ipdu_triggering, 'SHORT-NAME', "IPDUTRIGG_{0}".format(frame.name))
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF', dest='SIGNAL-I-PDU', text="/PDU/PDU_{0}".format(frame.name))
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
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name), dest='SIGNAL-PORT')

                    isignal_ref = create_sub_element(
                        isignal_triggering, 'SIGNAL-REF', dest='I-SIGNAL', text="/ISignal/{}".format(signal.name))
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
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name), dest='I-SIGNAL-PORT')

                    isignal_ref = create_sub_element(isignal_triggering, 'I-SIGNAL-REF', dest='I-SIGNAL', text="/ISignal/{0}".format(signal.name))
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
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF', dest='I-SIGNAL-I-PDU', text="/PDU/PDU_{0}".format(frame.name))
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
            pdu_ref = create_sub_element(pdu_mapping, 'PDU-REF', text="/PDU/PDU_{0}".format(frame.name))
            create_sub_element(pdu_mapping, 'START-POSITION', '0')

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
                signal_ref.text = "/ISignal/{0}".format(signal.name, dest='I-SIGNAL')

                create_sub_element(signal_to_pdu_mapping, 'START-POSITION',
                                   str(signal.get_startbit(bit_numbering=1)))
                # missing: TRANSFER-PROPERTY: PENDING/...

            for group in frame.signalGroups:
                signal_to_pdu_mapping = create_sub_element(signal_to_pdu_mappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                create_sub_element(signal_to_pdu_mapping, 'SHORT-NAME', group.name)
                signal_ref = create_sub_element(signal_to_pdu_mapping, 'SIGNAL-REF', text="/ISignal/{}".format(group.name), dest='I-SIGNAL')
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
                        '/DataType/Unit/{}'.format(signal.name), dest='UNIT')

                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF')
                sys_sig_ref.text = "/Signal/{}".format(signal.name)

                sys_sig_ref.set('DEST', 'SYSTEM-SIGNAL')
            for group in frame.signalGroups:
                signal_ele = create_sub_element(elements, 'I-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', group.name)
                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF', text="/Signal/{}".format(group.name), dest='SYSTEM-SIGNAL-GROUP')

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
                    data_type_ref = create_sub_element(signal_ele, 'DATA-TYPE-REF', text="/DataType/{}".format(signal.name))
                    if signal.is_float:
                        data_type_ref.set('DEST', 'REAL-TYPE')
                    else:
                        data_type_ref.set('DEST', 'INTEGER-TYPE')
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
                        sys_signal_refs, 'SYSTEM-SIGNAL-REF', dest='SYSTEM-SIGNAL', text="/Signal/{}".format(member.name))

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
                    compu_method_ref = create_sub_element(sw_data_def_props, 'COMPU-METHOD-REF', dest='COMPU-METHOD', text="/DataType/Semantics/{}".format(signal.name))
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
                    if ecu.name + "_Rx" not in rx_ipdu_groups:
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
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF', dest="I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF', dest="I-SIGNAL-I-PDU-GROUP")

                asso_ipdu_group_ref.text = "/IPDUGroup/{0}_Rx".format(ecu.name)

            if send_temp is not None:
                if ar_version[0] == "3":
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF', dest="I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF', dest="I-SIGNAL-I-PDU-GROUP")
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
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF', dest="SIGNAL-I-PDU", text="/PDU/PDU_{}".format(frame_name))
        else:
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in tx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF', dest="I-SIGNAL-I-PDU", text="/PDU/PDU_{}".format(frame_name))

    if ar_version[0] == "3":
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")

            ipdu_refs = create_sub_element(ipdu_grp, 'I-PDU-REFS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF', dest="SIGNAL-I-PDU", text="/PDU/PDU_{}".format(frame_name))
    else:
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-SIGNAL-I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF', dest="I-SIGNAL-I-PDU", text="/PDU/PDU_" + frame_name)

    f.write(lxml.etree.tostring(root, pretty_print=True, xml_declaration=True))


###################################
# read ARXML
###################################



pdu_frame_mapping = {}  # type: typing.Dict[_Element, str]
signal_rxs = {}  # type: typing.Dict[_Element, canmatrix.Signal]


def get_sys_signals(sys_signal, sys_signal_array, frame, group_id, ea):
    # type: (_Element, typing.Sequence[_Element], canmatrix.Frame, int, str) -> None
    members = [ea.get_element_name(signal) for signal in sys_signal_array]
    frame.add_signal_group(ea.get_element_name(sys_signal), group_id, members)


def decode_compu_method(compu_method, ea, float_factory):
    # type: (_Element, _DocRoot, str, _FloatFactory) -> typing.Tuple
    values = {}
    factor = float_factory(1.0)
    offset = float_factory(0)

    if compu_method is None:
        return values, factor, offset, None, None


    unit = ea.follow_ref(compu_method, "UNIT-REF")
    const = None
    compu_scales = ea.find_children_by_path(compu_method, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
    for compu_scale in compu_scales:
        ll = ea.get_child(compu_scale, "LOWER-LIMIT")
        ul = ea.get_child(compu_scale, "UPPER-LIMIT")
        sl = ea.get_child(compu_scale, "SHORT-LABEL")
        if sl is None:
            desc = ea.get_element_desc(compu_scale)
        else:
            desc = sl.text
        #####################################################################################################
        # Modification to support sourcing the COMPU_METHOD info from the Vector NETWORK-REPRESENTATION-PROPS
        # keyword definition. 06Jun16
        #####################################################################################################

        if ll is not None and desc is not None and canmatrix.utils.decode_number(ul.text, float_factory) == canmatrix.utils.decode_number(ll.text, float_factory):
            #####################################################################################################
            #####################################################################################################
            values[ll.text] = desc

        scale_desc = ea.get_element_desc(compu_scale)
        rational = ea.get_child(compu_scale, "COMPU-RATIONAL-COEFFS")
        if rational is not None:
            numerator_parent = ea.get_child(rational, "COMPU-NUMERATOR")
            numerator = ea.get_children(numerator_parent, "V")
            denominator_parent = ea.get_child(rational, "COMPU-DENOMINATOR")
            denominator = ea.get_children(denominator_parent, "V")
            try:
                factor = float_factory(numerator[1].text) / float_factory(denominator[0].text)
                offset = float_factory(numerator[0].text) / float_factory(denominator[0].text)
            except decimal.DivisionByZero:
                if numerator[0].text != denominator[0].text or numerator[1].text != denominator[1].text:
                    logger.warning("ARXML signal scaling: polynom is not supported and it is replaced by factor=1 and offset =0.")
                factor = float_factory(1)
                offset = float_factory(0)
        else:
            const = ea.get_child(compu_scale, "COMPU-CONST")
            # add value
            if const is None:
                logger.warning("Unknown Compu-Method: at sourceline %d ", compu_method.sourceline)
    return values, factor, offset, unit, const


def eval_type_of_signal(type_encoding, base_type, ea):
    if type_encoding == "NONE":
        is_signed = False
        is_float = False
    elif type_encoding == "2C":
        is_signed = True
        is_float = False
    elif type_encoding == "IEEE754" or type_encoding == "SINGLE" or type_encoding == "DOUBLE":
        is_signed = True
        is_float = True
    elif type_encoding == "BOOLEAN":
        is_signed = False
        is_float = False
    elif base_type is not None:
        is_float = False
        type_name = ea.get_element_name(base_type)
        if type_name[0] == 'u':
            is_signed = False  # unsigned
        else:
            is_signed = True  # signed
    else:
        is_float = False
        is_signed = False  # signed
    return is_signed, is_float

def ar_byteorder_is_little(in_string):
    if in_string == 'MOST-SIGNIFICANT-BYTE-LAST' or in_string == 'OPAQUE':
        return True
    return False

def get_signals(signal_array, frame, ea, multiplex_id, float_factory, bit_offset=0):
    # type: (typing.Sequence[_Element], canmatrix.Frame, _DocRoot, str, _MultiplexId, typing.Callable, int) -> None
    """Add signals from xml to the Frame."""
    global signal_rxs
    group_id = 1
    if signal_array is None:  # Empty signalarray - nothing to do
        return
    for signal in signal_array:
        compu_method = None
        motorola = ea.get_child(signal, "PACKING-BYTE-ORDER")
        start_bit = ea.get_child(signal, "START-POSITION")

        isignal = ea.follow_ref(signal, "SIGNAL-REF")
        if isignal is None:
            isignal = ea.follow_ref(signal, "I-SIGNAL-REF")

        if isignal is None:
            isignal = ea.follow_ref(signal, "I-SIGNAL-GROUP-REF")
            if isignal is not None:
                logger.debug("get_signals: found I-SIGNAL-GROUP ")

                isignal_array = ea.follow_ref(isignal, "I-SIGNAL-REF")

                system_signal_array = [ea.follow_ref(isignal, "SYSTEM-SIGNAL-REF") for isignal in isignal_array]
                system_signal_group = ea.follow_ref(isignal, "SYSTEM-SIGNAL-GROUP-REF")
                get_sys_signals(system_signal_group, system_signal_array, frame, group_id, ea)
                group_id = group_id + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                frame.name, ea.get_child(signal, "SHORT-NAME").text)

        base_type = ea.follow_ref(isignal, "BASE-TYPE-REF")
        try:
            type_encoding = ea.get_child(base_type, "BASE-TYPE-ENCODING").text
        except AttributeError:
            type_encoding = "None"
        signal_name = None  # type: typing.Optional[str]
        signal_name_elem = ea.get_child(isignal, "LONG-NAME")
        if signal_name_elem is not None:
            signal_name_elem = ea.get_child(signal_name_elem, "L-4")
            if signal_name_elem is not None:
                signal_name = signal_name_elem.text

        system_signal = ea.follow_ref(isignal, "SYSTEM-SIGNAL-REF")

        if system_signal is None:
            logger.debug('Frame %s, signal %s has no system-signal', frame.name, isignal.tag)


        if system_signal is not None and "SYSTEM-SIGNAL-GROUP" in system_signal.tag:
            system_signals = ea.find_children_by_path(system_signal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL")
            get_sys_signals(system_signal, system_signals, frame, group_id, ns)

            group_id = group_id + 1
            continue

        length = ea.get_child(isignal, "LENGTH")
        if length is None:
            length = ea.get_child(system_signal, "LENGTH")

        name = ea.get_child(system_signal, "SHORT-NAME")
        unit_element = ea.get_child(isignal, "UNIT")
        display_name = ea.get_child(unit_element, "DISPLAY-NAME")
        if display_name is not None:
            signal_unit = display_name.text
        else:
            signal_unit = ""

        signal_min = None  # type: canmatrix.types.OptionalPhysicalValue
        signal_max = None  # type: canmatrix.types.OptionalPhysicalValue
        receiver = []  # type: typing.List[str]

        signal_description = ea.get_element_desc(system_signal)

        datatype = ea.follow_ref(system_signal, "DATA-TYPE-REF")
        if datatype is None:  # AR4?
            data_constr = None
            compu_method = None
            base_type = None
            for test_signal in [isignal, system_signal]:
                if data_constr is None:
                    data_constr = ea.follow_ref(test_signal, "DATA-CONSTR-REF")
                if compu_method is None:
                    compu_method = ea.follow_ref(test_signal, "COMPU-METHOD-REF")
                if base_type is None:
                    base_type = ea.follow_ref(test_signal, "BASE-TYPE-REF")

            lower = ea.get_child(data_constr, "LOWER-LIMIT")
            upper = ea.get_child(data_constr, "UPPER-LIMIT")
            encoding = None  # TODO - find encoding in AR4
        else:
            lower = ea.get_child(datatype, "LOWER-LIMIT")
            upper = ea.get_child(datatype, "UPPER-LIMIT")
            type_encoding = ea.get_child(datatype, "ENCODING")

        if lower is not None and upper is not None:
            signal_min = float_factory(lower.text)
            signal_max = float_factory(upper.text)

        datdefprops = ea.get_child(datatype, "SW-DATA-DEF-PROPS")


        if compu_method is None and datdefprops is not None:
            compu_method = ea.follow_ref(datdefprops, "COMPU-METHOD-REF")
        if compu_method is None:  # AR4
            compu_method = ea.follow_ref(isignal, "COMPU-METHOD-REF")

            base_type = ea.follow_ref(isignal, "BASE-TYPE-REF")
            encoding = ea.get_child(base_type, "BASE-TYPE-ENCODING")
            if encoding is not None and encoding.text == "IEEE754":
                is_float = True
        if compu_method is None:
            logger.debug('No Compmethod found!! - try alternate scheme 1.')
            networkrep = ea.get_child(isignal, "NETWORK-REPRESENTATION-PROPS")
            data_def_props_var = ea.get_child(networkrep, "SW-DATA-DEF-PROPS-VARIANTS")
            data_def_props_cond = ea.get_child(data_def_props_var, "SW-DATA-DEF-PROPS-CONDITIONAL")
            if data_def_props_cond is not None:
                try:
                    compu_method = ea.get_child(data_def_props_cond, "COMPU-METHOD")
                except:
                    logger.debug('No valid compu method found for this - check ARXML file!!')
                    compu_method = None
        #####################################################################################################
        # no found compu-method fuzzy search in systemsignal:
        #####################################################################################################
        if compu_method is None:
            logger.debug('No Compmethod found!! - fuzzy search in syssignal.')
            compu_method = ea.follow_ref(system_signal, "COMPU-METHOD-REF")


        # decode compuMethod:
        (values, factor, offset, unit_elem, const) = decode_compu_method(compu_method, ea, float_factory)

        if signal_min is not None:
            signal_min *= factor
            signal_min += offset
        if signal_max is not None:
            signal_max *= factor
            signal_max += offset

        if base_type is None:
            base_type = ea.get_child(datdefprops, "BASE-TYPE")

        (is_signed, is_float) = eval_type_of_signal(type_encoding, base_type, ea)

        if unit_elem is not None:
            longname = ea.get_child(unit_elem, "LONG-NAME")
        #####################################################################################################
        # Modification to support obtaining the Signals Unit by DISPLAY-NAME. 07June16
        #####################################################################################################
            display_name = None
            try:
                display_name = ea.get_child(unit_elem, "DISPLAY-NAME")
            except:
                logger.debug('No Unit Display name found!! - using long name')
            if display_name is not None:
                signal_unit = display_name.text
            else:
                l4 = ea.get_child(longname, "L-4")
                if l4 is not None:
                    signal_unit = l4.text

        init_list = ea.find_children_by_path(system_signal, "INIT-VALUE/VALUE")

        if not init_list:
            init_list = ea.find_children_by_path(isignal, "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE")  # #AR4.2
        if init_list:
            initvalue = init_list[0]
        else:
            initvalue = None

        is_little_endian = False
        if motorola is not None:
            is_little_endian = ar_byteorder_is_little(motorola.text)
        else:
            logger.debug('no name byte order for signal' + name.text)

        if name is None:
            logger.debug('no name for signal given')
            name = ea.get_child(isignal, "SHORT-NAME")
        if start_bit is None:
            logger.debug('no startBit for signal given')
        if length is None:
            logger.debug('no length for signal given')

        if start_bit is not None:
            new_signal = canmatrix.Signal(
                name.text,
                start_bit=int(start_bit.text) + bit_offset,
                size=int(length.text) if length is not None else 0,
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

            if not new_signal.is_little_endian:
                # startbit of motorola coded signals are MSB in arxml
                new_signal.set_startbit(int(start_bit.text) + bit_offset, bitNumbering=1)

            # save signal, to determin receiver-ECUs for this signal later
            signal_rxs[system_signal] = new_signal

            if base_type is not None:
                temp = ea.get_child(base_type, "SHORT-NAME")
                if temp is not None and "boolean" == temp.text:
                    new_signal.add_values(1, "TRUE")
                    new_signal.add_values(0, "FALSE")

            if initvalue is not None and initvalue.text is not None:
                initvalue.text = canmatrix.utils.guess_value(initvalue.text)
                new_signal.initial_value = float_factory(initvalue.text)

            for key, value in list(values.items()):
                new_signal.add_values(canmatrix.utils.decode_number(key, float_factory), value)
            if signal_name is not None:
                new_signal.add_attribute("LongName", signal_name)
            existing_signal = frame.signal_by_name(new_signal.name)
            if existing_signal is None:
                frame.add_signal(new_signal)


def get_frame_from_multiplexed_ipdu(pdu, target_frame, multiplex_translation, ea, float_factory):
    selector_byte_order = ea.get_child(pdu, "SELECTOR-FIELD-BYTE-ORDER")
    selector_len = ea.get_child(pdu, "SELECTOR-FIELD-LENGTH")
    selector_start = ea.get_child(pdu, "SELECTOR-FIELD-START-POSITION")

    is_little_endian = ar_byteorder_is_little(selector_byte_order.text)


    is_signed = False  # unsigned
    multiplexor = canmatrix.Signal(
        "Multiplexor",
        start_bit=int(selector_start.text),
        size=int(selector_len.text),
        is_little_endian=is_little_endian,
        multiplex="Multiplexor")

    multiplexor.initial_value = 0
    target_frame.add_signal(multiplexor)
    static_part = ea.get_child(pdu, "STATIC-PART")
    ipdu = ea.get_child(static_part, "I-PDU")
    if ipdu is not None:
        pdu_sig_mappings = ea.get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS")
        pdu_sig_mapping = ea.get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING")
        get_signals(pdu_sig_mapping, target_frame, ea, None, float_factory)
        multiplex_translation[ea.get_element_name(ipdu)] = ea.get_element_name(pdu)

    dynamic_part = ea.get_child(pdu, "DYNAMIC-PART")
    #               segmentPositions = arGetChild(dynamic_part, "SEGMENT-POSITIONS", arDict, ns)
    #               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
    #               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
    #               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
    #               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
    dynamic_part_alternatives = ea.get_child(dynamic_part, "DYNAMIC-PART-ALTERNATIVES")
    dynamic_part_alternative_list = ea.get_children(dynamic_part_alternatives, "DYNAMIC-PART-ALTERNATIVE")
    for alternative in dynamic_part_alternative_list:
        selector_id = ea.get_child(alternative, "SELECTOR-FIELD-CODE")
        ipdu = ea.follow_ref(alternative, "I-PDU-REF")
        multiplex_translation[ea.get_element_name(ipdu)] = ea.get_element_name(pdu)
        if ipdu is not None:
            pdu_sig_mappings = ea.get_child(ipdu, "SIGNAL-TO-PDU-MAPPINGS")
            pdu_sig_mapping = ea.get_children(pdu_sig_mappings, "I-SIGNAL-TO-I-PDU-MAPPING")

            get_signals(pdu_sig_mapping, target_frame, ea, selector_id.text, float_factory)

def containters_are_little_endian(ea):
    container_i_pdu_header_byte_orders = ea.findall("CONTAINER-I-PDU-HEADER-BYTE-ORDER")
    if len(container_i_pdu_header_byte_orders) > 0:
        return ar_byteorder_is_little(container_i_pdu_header_byte_orders[0].text)

def get_frame_from_container_ipdu(pdu, target_frame, ea, float_factory):
    headers_are_littleendian = containters_are_little_endian(ea)
    target_frame.is_fd = True
    #pdus = ea.get_children(pdu, "CONTAINED-PDU-TRIGGERING")
    pdus = ea.follow_all_ref(pdu, "CONTAINED-PDU-TRIGGERING-REF")
    signal_group_id = 1
    singnals_grouped = []  # type: typing.List[str]
    header_type = ea.get_child(pdu, "HEADER-TYPE").text

    if header_type == "SHORT-HEADER":
        if headers_are_littleendian:  # INTEL
            target_frame.add_signal(
                canmatrix.Signal(start_bit=0, size=24, name="Header_ID", multiplex="Multiplexor",
                                 is_little_endian=True))
            target_frame.add_signal(canmatrix.Signal(start_bit=24, size=8, name="Header_DLC", is_little_endian=True))
        else:  # Motorola
            header_id_signal= canmatrix.Signal(start_bit=0, size=24, name="Header_ID", multiplex="Multiplexor",
                                 is_little_endian=False)
            target_frame.add_signal(header_id_signal)
            header_dlc_signal = canmatrix.Signal(start_bit=24, size=8, name="Header_DLC", is_little_endian=False)
            target_frame.add_signal(header_dlc_signal)
        header_length = 32

    elif header_type == "LONG-HEADER":
        if headers_are_littleendian:
            target_frame.add_signal(canmatrix.Signal(start_bit=0, size=32, name="Header_ID", multiplex="Multiplexor", is_little_endian=True))
            target_frame.add_signal(canmatrix.Signal(start_bit=32, size=32, name="Header_DLC", is_little_endian=True))
        else:
            target_frame.add_signal(canmatrix.Signal(start_bit=0, size=32, name="Header_ID", multiplex="Multiplexor",
                                                     is_little_endian=False))
            target_frame.add_signal(canmatrix.Signal(start_bit=32, size=32, name="Header_DLC", is_little_endian=False))
        header_length = 64
    else:
        header_length = 0
       

    for cpdu in pdus:
        ipdu = ea.follow_ref(cpdu, "I-PDU-REF")
        try:
            if header_type == "SHORT-HEADER":
                header_id = ea.get_child(ipdu, "HEADER-ID-SHORT-HEADER").text
            elif header_type == "LONG-HEADER":
                header_id = ea.get_child(ipdu, "HEADER-ID-LONG-HEADER").text
            else:
                # none type
                header_id = None
                pass
        except AttributeError:
            header_id = None
        if header_id is not None:
            if header_id.startswith("0x"):
                header_id = int(header_id, 16)
            else:
                header_id = int(header_id)

        offset = 0
        if ipdu is not None and 'SECURED-I-PDU' in ipdu.tag:
            payload = ea.follow_ref(ipdu, "PAYLOAD-REF")
            ipdu = ea.follow_ref(payload, "I-PDU-REF")
#            length = ea.get_child(ipdu, "LENGTH").text
        try:
            offset = int(ea.get_child(ipdu, "OFFSET").text)*8
        except:
            offset = 0
        # pdu_sig_mapping = get_children(ipdu, "I-SIGNAL-IN-I-PDU", root_or_cache, ns)
        pdu_sig_mapping = ea.get_children(ipdu, "I-SIGNAL-TO-I-PDU-MAPPING")
        # TODO
        if pdu_sig_mapping:

            get_signals(pdu_sig_mapping, target_frame, ea, header_id, float_factory, bit_offset=header_length+offset)

            new_signals = []
            for signal in target_frame:
                if signal.name not in singnals_grouped and signal.name != "Header_ID" and signal.name != "Header_DLC":
                    new_signals.append(signal.name)
            if header_id is None:
                target_frame.add_signal_group(ea.get_short_name(ipdu), signal_group_id, new_signals)
            else:
                sg_group_name =  ea.get_short_name(ipdu)
                if len(sg_group_name) == 0:
                    sg_group_name = "HEARDER_ID_" + str(header_id)
                target_frame.add_signal_group(sg_group_name, signal_group_id, new_signals)
            singnals_grouped += new_signals
            signal_group_id += 1


def store_frame_timings(target_frame, cyclic_timing, event_timing, minimum_delay, repeats, starting_time, time_offset, repeating_time, ea, time_period, float_factory):
    if cyclic_timing is not None and event_timing is not None:
        target_frame.add_attribute("GenMsgSendType", "cyclicAndSpontanX")  # CycleAndSpontan
        if minimum_delay is not None:
            target_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            target_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclic_timing is not None:
        target_frame.add_attribute("GenMsgSendType", "cyclicX")  # CycleX
        if minimum_delay is not None:
            target_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            target_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        target_frame.add_attribute("GenMsgSendType", "spontanX")  # Spontan
        if minimum_delay is not None:
            target_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimum_delay.text) * 1000)))
        if repeats is not None:
            target_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)

    if starting_time is not None:
        value = ea.get_child(starting_time, "VALUE")
        target_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))
    elif cyclic_timing is not None:
        value = ea.get_child(time_offset, "VALUE")
        if value is not None:
            target_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))

    value = ea.get_child(repeating_time, "VALUE")
    if value is not None:
        target_frame.cycle_time = int(float_factory(value.text) * 1000)
    elif cyclic_timing is not None:
        value = ea.get_child(time_period, "VALUE")
        if value is not None:
            target_frame.cycle_time = int(float_factory(value.text) * 1000)


def get_frame(frame_triggering, ea, multiplex_translation, float_factory):
    # type: (_Element, _DocRoot, dict, str, typing.Callable) -> typing.Union[canmatrix.Frame, None]
    global pdu_frame_mapping
    address_mode = ea.get_child(frame_triggering, "CAN-ADDRESSING-MODE")
    frame_rx_behaviour_elem = ea.get_child(frame_triggering, "CAN-FRAME-RX-BEHAVIOR")
    frame_tx_behaviour_elem = ea.get_child(frame_triggering, "CAN-FRAME-TX-BEHAVIOR")
    is_fd_elem = ea.get_child(frame_triggering, "CAN-FD-FRAME-SUPPORT")

    arb_id = ea.get_child(frame_triggering, "IDENTIFIER")


    frame_elem = ea.follow_ref(frame_triggering, "FRAME-REF")


    frame_name_elem = ea.get_child(frame_triggering, "SHORT-NAME")
    logger.debug("processing Frame: %s", frame_name_elem.text)
    if arb_id is None:
        logger.info("found Frame %s without arbitration id", frame_name_elem.text)
        return None
    arbitration_id = int(arb_id.text)

    if frame_elem is not None:
        dlc_elem = ea.get_child(frame_elem, "FRAME-LENGTH")
       # pdu_mapping = ea.get_child(frame_elem, "PDU-TO-FRAME-MAPPING")
       # pdu = ea.follow_ref(pdu_mapping, "PDU-REF")  # SIGNAL-I-PDU
        pdu = ea.follow_ref(frame_elem, "PDU-REF")  # SIGNAL-I-PDU

        if pdu is not None and 'SECURED-I-PDU' in pdu.tag:
            payload = ea.follow_ref(pdu, "PAYLOAD-REF")
            pdu = ea.follow_ref(payload, "I-PDU-REF")
            # logger.info("found secured pdu - no signal extraction possible: %s", get_element_name(pdu, ns))

        pdu_frame_mapping[pdu] = ea.get_element_name(frame_elem)

        new_frame = canmatrix.Frame(ea.get_element_name(frame_elem), size=int(dlc_elem.text))
        comment = ea.get_element_desc(frame_elem)
        if comment is not None:
            new_frame.add_comment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF", frame_name_elem.text)
        ipdu_triggering = ea.follow_ref(frame_triggering, "I-PDU-TRIGGERING-REF")
        pdu = ea.follow_ref(ipdu_triggering, "I-PDU-REF")
        if pdu is None:
            pdu = ea.get_child(ipdu_triggering, "I-SIGNAL-I-PDU")  # AR4.2
        dlc_elem = ea.get_child(pdu, "LENGTH")

        new_frame = canmatrix.Frame(frame_name_elem.text, arbitration_id=arbitration_id, size=int(int(dlc_elem.text) / 8))

    if pdu is None:
        logger.error("pdu is None")
    else:
        logger.debug(ea.get_element_name(pdu))

    if pdu is not None and "MULTIPLEXED-I-PDU" in pdu.tag:
        get_frame_from_multiplexed_ipdu(pdu, new_frame, multiplex_translation, ea, float_factory)

    if new_frame.comment is None:
        new_frame.add_comment(ea.get_element_desc(pdu))

    if address_mode is not None and address_mode.text == 'EXTENDED':
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=True)
    else:
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=False)

    if (frame_rx_behaviour_elem is not None and frame_rx_behaviour_elem.text == 'CAN-FD') or \
        (frame_tx_behaviour_elem is not None and frame_tx_behaviour_elem.text == 'CAN-FD') or \
        (is_fd_elem is not None and is_fd_elem.text == 'TRUE'):
        new_frame.is_fd = True
    else:
        new_frame.is_fd = False

    timing_spec = ea.get_child(pdu, "I-PDU-TIMING-SPECIFICATION")
    if timing_spec is None:
        timing_spec = ea.get_child(pdu, "I-PDU-TIMING-SPECIFICATIONS")
    cyclic_timing = ea.get_child(timing_spec, "CYCLIC-TIMING")
    repeating_time = ea.get_child(cyclic_timing, "REPEATING-TIME")

    event_timing = ea.get_child(timing_spec, "EVENT-CONTROLLED-TIMING")
    repeats = ea.get_child(event_timing, "NUMBER-OF-REPEATS")
    minimum_delay = ea.get_child(timing_spec, "MINIMUM-DELAY")
    starting_time = ea.get_child(timing_spec, "STARTING-TIME")

    time_offset = ea.get_child(cyclic_timing, "TIME-OFFSET")
    time_period = ea.get_child(cyclic_timing, "TIME-PERIOD")

    store_frame_timings(new_frame, cyclic_timing, event_timing, minimum_delay, repeats, starting_time, time_offset, repeating_time, ea, time_period, float_factory)

    if pdu.tag == ea.ns + "CONTAINER-I-PDU":
        get_frame_from_container_ipdu(pdu, new_frame, ea, float_factory)

    else:
        pdu_sig_mapping = ea.follow_all_ref(pdu, "I-SIGNAL-TO-I-PDU-MAPPING-REF")
        if len(pdu_sig_mapping) == 0:
            pdu_sig_mapping = ea.get_children(pdu, "I-SIGNAL-TO-I-PDU-MAPPING")
        if pdu_sig_mapping:
            get_signals(pdu_sig_mapping, new_frame, ea, None, float_factory)
        # Seen some pdu_sig_mapping being [] and not None with some arxml 4.2
        else:  # AR 4.2
            pdu_trigs = ea.follow_all_ref(frame_triggering, "PDU-TRIGGERINGS-REF")
            if pdu_trigs is not None:
                for pdu_trig in pdu_trigs:
                    trig_ref_cond = ea.get_child(pdu_trig, "PDU-TRIGGERING-REF-CONDITIONAL")
                    trigs = ea.follow_ref(trig_ref_cond, "PDU-TRIGGERING-REF")
                    ipdus = ea.follow_ref(trigs, "I-PDU-REF")

                    signal_to_pdu_maps = ea.get_child(ipdus, "I-SIGNAL-TO-PDU-MAPPINGS")
                    if signal_to_pdu_maps is None:
                        signal_to_pdu_maps = ea.get_child(ipdus, "I-SIGNAL-TO-I-PDU-MAPPINGS")

                    if signal_to_pdu_maps is None:
                        logger.debug("AR4.x PDU %s no SIGNAL-TO-PDU-MAPPINGS found - no signal extraction!",
                                     ea.get_element_name(ipdus))
                    # signal_to_pdu_map = get_children(signal_to_pdu_maps, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                    get_signals(signal_to_pdu_maps, new_frame, ea, None, float_factory)  # todo BUG expects list, not item
            else:
                logger.debug("Frame %s (assuming AR4.2) no PDU-TRIGGERINGS found", new_frame.name)
    new_frame.fit_dlc()
    return new_frame





def process_ecu(ecu_elem, db, ea, multiplex_translation):
    # type: (_Element, canmatrix.CanMatrix, _DocRoot, typing.Mapping[str, str], str) -> canmatrix.Ecu
    global pdu_frame_mapping
    connectors = ea.get_child(ecu_elem, "CONNECTORS")
    diag_address = ea.get_child(ecu_elem, "DIAGNOSTIC-ADDRESS")
    diag_response = ea.get_child(ecu_elem, "RESPONSE-ADDRESSS")
    # TODO: use diag_address for frame-classification
    comm_connector = ea.get_child(connectors, "COMMUNICATION-CONNECTOR")
    if comm_connector is None:
        comm_connector = ea.get_child(connectors, "CAN-COMMUNICATION-CONNECTOR")
    frames = ea.find_children_by_path(comm_connector, "ECU-COMM-PORT-INSTANCES/FRAME-PORT")
    nm_address = ea.get_child(comm_connector, "NM-ADDRESS")
    assoc_refs = ea.get_child(ecu_elem, "ASSOCIATED-I-PDU-GROUP-REFS")

    if assoc_refs is not None:
        assoc = ea.follow_all_ref(assoc_refs, "ASSOCIATED-I-PDU-GROUP-REF")
    else:  # AR4
        assoc_refs = ea.get_child(ecu_elem, "ASSOCIATED-COM-I-PDU-GROUP-REFS")
        assoc = ea.follow_all_ref(assoc_refs, "ASSOCIATED-COM-I-PDU-GROUP-REF")

    in_frame = []
    out_frame = []

    # get direction of frames (is current ECU sender/receiver/...?)
    for ref in assoc:
        direction = ea.get_child(ref, "COMMUNICATION-DIRECTION")
        group_refs = ea.get_child(ref, "CONTAINED-I-PDU-GROUPS-REFS")
        pdu_refs = ea.get_child(ref, "I-PDU-REFS")
        if pdu_refs is not None:  # AR3
            # local defined pdus
            pdus = ea.follow_all_ref(pdu_refs, "I-PDU-REF")
            for pdu in pdus:
                if pdu in pdu_frame_mapping:
                    if direction.text == "IN":
                        in_frame.append(pdu_frame_mapping[pdu])
                    else:
                        out_frame.append(pdu_frame_mapping[pdu])
        else:  # AR4
            isigpdus = ea.get_child(ref, "I-SIGNAL-I-PDUS")
            isigconds = ea.get_children(
                isigpdus, "I-SIGNAL-I-PDU-REF-CONDITIONAL")
            for isigcond in isigconds:
                pdus = ea.follow_all_ref(isigcond, "I-SIGNAL-I-PDU-REF")
                for pdu in pdus:
                    if pdu in pdu_frame_mapping:
                        if direction.text == "IN":
                            in_frame.append(pdu_frame_mapping[pdu])
                        else:
                            out_frame.append(pdu_frame_mapping[pdu])

        # grouped pdus
        group = ea.get_children(group_refs, "CONTAINED-I-PDU-GROUPS")
        for t in group:
            if direction is None:
                direction = ea.get_child(
                    t, "COMMUNICATION-DIRECTION")
            pdu_refs = ea.get_child(t, "I-PDU-REFS")
            pdus = ea.get_children(pdu_refs, "I-PDU")
            for pdu in pdus:
                if direction.text == "IN":
                    in_frame.append(ea.get_element_name(pdu))
                else:
                    out_frame.append(ea.get_element_name(pdu))

        for out in out_frame:
            if out in multiplex_translation:
                out = multiplex_translation[out]
            frame = db.frame_by_name(out)
            if frame is not None:
                frame.add_transmitter(ea.get_element_name(ecu_elem))
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
    new_ecu = canmatrix.Ecu(ea.get_element_name(ecu_elem))
    if nm_address is not None:
        new_ecu.add_attribute("NWM-Stationsadresse", nm_address.text)
        new_ecu.add_attribute("NWM-Knoten", "ja")
    else:
        new_ecu.add_attribute("NWM-Stationsadresse", "0")
        new_ecu.add_attribute("NWM-Knoten", "nein")
    return new_ecu


def ecuc_extract_signal(signal_node, ea):
    # type: (_Element, str) -> canmatrix.Signal
    """Extract signal from ECUc file."""
    attributes = ea.findall("DEFINITION-REF", signal_node)  # type: typing.Sequence[_Element]
    start_bit = None
    size = 0
    is_little = False
    # endianness = None
    # init_value = 0
    # signal_type = None
    # timeout = 0
    for attribute in attributes:
        if attribute.text.endswith("ComBitPosition"):
            start_bit = int(attribute.getparent().find(".//" + ea.ns + "VALUE").text)
        if attribute.text.endswith("ComBitSize"):
            size = int(attribute.getparent().find(".//" + ea.ns + "VALUE").text)
        if attribute.text.endswith("ComSignalEndianness"):
            endianness = attribute.getparent().find(".//" + ea.ns + "VALUE").text
            is_little = "LITTLE_ENDIAN" in endianness
        if attribute.text.endswith("ComSignalInitValue"):
            init_value = int(attribute.getparent().find(".//" + ea.ns + "VALUE").text)
        if attribute.text.endswith("ComSignalType"):
            signal_type = attribute.getparent().find(".//" + ea.ns + "VALUE").text
        if attribute.text.endswith("ComTimeout"):
            timeout = int(attribute.getparent().find(".//" + ea.ns + "VALUE").text)
    return canmatrix.Signal(ea.get_element_name(signal_node), start_bit=start_bit, size=size, is_little_endian=is_little)


def extract_cm_from_ecuc(com_module, ea):
    # type: (_Element, Earxml -> typing.Dict[str, canmatrix.CanMatrix]
    db = canmatrix.CanMatrix()
    definitions = ea.findall("DEFINITION-REF", com_module)
    for definition in definitions:
        if definition.text.endswith("ComIPdu"):
            container = definition.getparent()
            frame = canmatrix.Frame(ea.get_element_name(container))
            db.add_frame(frame)
            all_references = ea.get_children(container, "ECUC-REFERENCE-VALUE")
            for reference in all_references:
                value = ea.follow_ref(reference, "VALUE-REF")
                if value is not None:
                    signal_definition = value.find('./' + ea.ns + "DEFINITION-REF")
                    if signal_definition.text.endswith("ComSignal"):
                        signal = ecuc_extract_signal(value, ea)
                        frame.add_signal(signal)
    db.recalc_dlc(strategy="max")
    return {"": db}

def decode_ethernet_helper(ea, float_factory):
    found_matrixes = {}


    socket_connetions = ea.findall("SOCKET-CONNECTION-IPDU-IDENTIFIER")
    pdu_triggering_header_id_map = {}
    # network_endpoints = pc.findall('.//' + ns + "NETWORK-ENDPOINT")
    for socket_connetion in socket_connetions:
        header_id = ea.get_child(socket_connetion, "HEADER-ID")
        ipdu_triggering = ea.follow_ref(socket_connetion, "PDU-TRIGGERING-REF")
        try:
            pdu_triggering_header_id_map[ipdu_triggering] = header_id.text
        except:
            pass


    ecs = ea.findall('ETHERNET-CLUSTER')
    for ec in ecs:
        baudrate_elem = ea.find("BAUDRATE", ec)
        physical_channels = ea.findall("ETHERNET-PHYSICAL-CHANNEL", ec)
        for pc in physical_channels:

            db = canmatrix.CanMatrix(type=canmatrix.matrix_class.SOMEIP)

            db.baudrate = baudrate_elem.text if baudrate_elem is not None else 0
            db.add_signal_defines("LongName", 'STRING')
            channel_name = ea.get_element_name(pc)
            found_matrixes[channel_name] = db

            for socket_connetion in ea.findall("SOCKET-CONNECTION-IPDU-IDENTIFIER", pc):
                header_id = ea.get_child(socket_connetion, "HEADER-ID")
                ipdu_triggering = ea.follow_ref(socket_connetion, "PDU-TRIGGERING-REF")
#            for ipdu_triggering in ea.findall("PDU-TRIGGERING", pc):
                ipdu = ea.follow_ref(ipdu_triggering, "I-PDU-REF")
                if ipdu is not None and 'SECURED-I-PDU' in ipdu.tag:
                    payload = ea.follow_ref(ipdu, "PAYLOAD-REF")
                    ipdu = ea.follow_ref(payload, "I-PDU-REF")

                ipdu_name = ea.get_element_name(ipdu)
                logger.info("ETH PDU " + ipdu_name + " found")
                target_frame = canmatrix.Frame(name = ipdu_name)
                try:
                    target_frame.header_id = int(header_id.text)
                except:
                    try:
                        target_frame.header_id = int(pdu_triggering_header_id_map[ipdu_triggering])
                    except:
                        target_frame.header_id = 0
#                    continue
                pdu_sig_mapping = ea.findall("I-SIGNAL-TO-I-PDU-MAPPING", ipdu)

                get_signals(pdu_sig_mapping, target_frame, ea, None, float_factory)
                target_frame.update_receiver()
                db.add_frame(target_frame)
    return found_matrixes

def decode_flexray_helper(ea, float_factory):
    found_matrixes = {}
    fcs = ea.findall('FLEXRAY-CLUSTER')
    frame_counter = 0

    for fc in fcs:
        physical_channels = ea.findall("FLEXRAY-PHYSICAL-CHANNEL", fc)
        for pc in physical_channels:
            db = canmatrix.CanMatrix()
            db.is_flexray = True
            db.add_signal_defines("LongName", 'STRING')
            channel_name = ea.get_element_name(pc)
            found_matrixes[channel_name] = db

            frames = ea.findall("FLEXRAY-FRAME-TRIGGERING", pc)
            for frame_element in frames:
                frame_counter += 1
                slot_id = int(ea.get_child(frame_element, "SLOT-ID").text)
                base_cycle = ea.get_child(frame_element, "BASE-CYCLE").text
                ipdu_triggerings = ea.get_children(frame_element, "I-PDU-TRIGGERING")
                frame_repetition_cycle = ea.find_children_by_path(frame_element, "CYCLE-REPETITION/CYCLE-REPETITION")[0].text
                network_endpoints = pc.findall('.//' + ea.ns + "NETWORK-ENDPOINT")
                frame_size = int(ea.find_children_by_path(frame_element, "FRAME/FRAME-LENGTH")[0].text)
                frame = canmatrix.Frame(size = frame_size, arbitration_id = frame_counter)
                frame.slot_id = slot_id
                frame.base_cycle = base_cycle
                frame.repitition_cycle = frame_repetition_cycle.replace("CYCLE-REPETITION-","")
                db.add_frame(frame)
                for ipdu_triggering in ipdu_triggerings:
                    ipdu_triggering_name = ea.get_element_name(ipdu_triggering)
                    ipdu = ea.get_child(ipdu_triggering, "I-PDU")
                    pdu_type = ea.get_child(ipdu_triggering, "I-PDU-REF").attrib["DEST"]
                    ipdu_length = int(ea.get_child(ipdu, "LENGTH").text)
                    pdu_port_type = ea.get_child(ipdu_triggering, "I-PDU-PORT-REF").attrib["DEST"]
                    ipdu_name = ea.get_element_name(ipdu)
                    target_pdu = canmatrix.Pdu(name = ipdu_name, size=ipdu_length,
                                               triggering_name = ipdu_triggering_name, pdu_type=pdu_type, port_type=pdu_port_type)
                    pdu_sig_mapping = ea.get_children(ipdu, "I-SIGNAL-TO-I-PDU-MAPPING")
                    get_signals(pdu_sig_mapping, target_pdu, ea, None, float_factory)
                    frame.add_pdu(target_pdu)
    return found_matrixes

def decode_can_helper(ea, float_factory, ignore_cluster_info):
    found_matrixes = {}
    if ignore_cluster_info is True:
        ccs = [lxml.etree.Element("ignoreClusterInfo")]  # type: typing.Sequence[_Element]
    else:
        ccs = ea.findall('CAN-CLUSTER')
    for cc in ccs:  # type: _Element
        db = canmatrix.CanMatrix()
        # Defines not jet imported...
        db.add_ecu_defines("NWM-Stationsadresse", 'HEX 0 63')
        db.add_ecu_defines("NWM-Knoten", 'ENUM  "nein","ja"')
        db.add_signal_defines("LongName", 'STRING')
        db.add_frame_defines("GenMsgDelayTime", 'INT 0 65535')
        db.add_frame_defines("GenMsgNrOfRepetitions", 'INT 0 65535')
        db.add_frame_defines("GenMsgStartValue", 'STRING')
        db.add_frame_defines("GenMsgStartDelayTime", 'INT 0 65535')
        db.add_frame_defines(
            "GenMsgSendType",
            'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')

        if ignore_cluster_info is True:
            can_frame_trig = ea.findall('CAN-FRAME-TRIGGERING')
            bus_name = ""
        else:
            speed = ea.get_child(cc, "SPEED")
            baudrate_elem = ea.find("BAUDRATE", cc)
            fd_baudrate_elem = ea.find("CAN-FD-BAUDRATE", cc)

            logger.debug("Busname: " + ea.get_element_name(cc))

            bus_name = ea.get_element_name(cc)
            if speed is not None:
                db.baudrate = int(speed.text)
            elif baudrate_elem is not None:
                db.baudrate = int(baudrate_elem.text)

            logger.debug("Baudrate: "+ str(db.baudrate))
            if fd_baudrate_elem is not None:
                db.fd_baudrate = fd_baudrate_elem.text

        

            physical_channels = ea.find("PHYSICAL-CHANNELS", cc)  # type: _Element
            if physical_channels is None:
                logger.error("PHYSICAL-CHANNELS not found")

            nm_lower_id = ea.get_child(cc, "NM-LOWER-CAN-ID")

            physical_channel = ea.get_child(physical_channels, "PHYSICAL-CHANNEL")
            if physical_channel is None:
                physical_channel = ea.get_child(physical_channels, "CAN-PHYSICAL-CHANNEL")
            if physical_channel is None:
                logger.error("PHYSICAL-CHANNEL not found")
            can_frame_trig = ea.get_children(physical_channel, "CAN-FRAME-TRIGGERING")
            if can_frame_trig is None:
                logger.error("CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug("%d frames found in arxml", len(can_frame_trig))

        multiplex_translation = {}  # type: typing.Dict[str, str]
        for frameTrig in can_frame_trig:  # type: _Element
            frame = get_frame(frameTrig, ea, multiplex_translation, float_factory)
            if frame is not None:
                db.add_frame(frame)

        if ignore_cluster_info is True:
            pass
            # no support for signal direction
        else:  # find signal senders/receivers...
            isignal_triggerings = ea.find_children_by_path(physical_channel, "I-SIGNAL-TRIGGERING")
            for sig_trig in isignal_triggerings:
                isignal = ea.follow_ref(sig_trig, 'SIGNAL-REF') # AR 3.2
                if isignal is None:
                    isignal = ea.follow_ref(sig_trig, 'I-SIGNAL-REF') # AR4
                if isignal is None:
                    sig_trig_text = ea.get_element_name(sig_trig) if sig_trig is not None else "None"
                    logger.debug("load: no isignal for %s", sig_trig_text)
                    continue

                port_ref = ea.follow_all_ref(sig_trig, "I-SIGNAL-PORT-REF")

                for port in port_ref:
                    comm_direction = ea.get_child(port, "COMMUNICATION-DIRECTION")
                    if comm_direction is not None and comm_direction.text == "IN":
                        sys_signal = ea.follow_ref(isignal, "SYSTEM-SIGNAL-REF")
                        ecu_name = ea.get_element_name(port.getparent().getparent().getparent().getparent())
                        # port points in ECU; probably more stable to go up
                        # from each ECU than to go down in XML...
                        if sys_signal in signal_rxs:
                            signal_rxs[sys_signal].add_receiver(ecu_name)
                            # find ECUs:
        nodes = ea.findall('ECU-INSTANCE')
        for node in nodes:  # type: _Element
            ecu = process_ecu(node, db, ea, multiplex_translation)
            desc = ea.get_child(node, "DESC", )
            l2 = ea.get_child(desc, "L-2")
            if l2 is not None:
                ecu.add_comment(l2.text)

            db.add_ecu(ecu)


        for frame in db.frames:
            sig_value_hash = dict()
            for sig in frame.signals:
                try:
                    sig_value_hash[sig.name] = sig.phys2raw()
                except AttributeError:
                    sig_value_hash[sig.name] = 0
            frame_data = frame.encode(sig_value_hash)
            frame.add_attribute("GenMsgStartValue", "".join(["%02x" % x for x in frame_data]))
            frame.update_receiver()
        found_matrixes[bus_name] = db


    return found_matrixes

def load(file, **options):
    # type: (typing.IO, **typing.Any) -> typing.Dict[str, canmatrix.CanMatrix]

    global pdu_frame_mapping
    pdu_frame_mapping = {}
    global signal_rxs
    signal_rxs = {}

    float_factory = options.get("float_factory", default_float_factory)  # type: typing.Callable
    ignore_cluster_info = options.get("arxmlIgnoreClusterInfo", False)
    use_ar_xpath = options.get("arxmlUseXpath", False)
    decode_ethernet = options.get("decode_ethernet", False)
    decode_flexray = options.get("decode_flexray", False)

    result = {}
    logger.debug("Read arxml ...")

    ea = Earxml(use_ar_xpath)
    ea.open(file)

    logger.debug("Build arTree ...")

    ea.build_ar_tree()
    com_module = ea.get_short_name_path("ActiveEcuC/Com")

    if com_module is not None and len(com_module) > 0:
        logger.info("seems to be a ECUC arxml. Very limited support for extracting canmatrix.")
        return extract_cm_from_ecuc(com_module, ea)

    frames = ea.findall('CAN-FRAME')  # AR4.2
    if frames is None:
        frames = ea.findall('FRAME')  # AR3.2-4.1?
    
    logger.debug("%d frames in arxml...", len(frames))
    can_triggers = ea.findall('CAN-FRAME-TRIGGERING')
    logger.debug("%d can-frame-triggering in arxml...", len(can_triggers))

    sig_pdu_map = ea.findall('SIGNAL-TO-PDU-MAPPINGS')
    logger.debug("%d SIGNAL-TO-PDU-MAPPINGS in arxml...", len(sig_pdu_map))

    sig_ipdu = ea.findall('I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug("%d I-SIGNAL-TO-I-PDU-MAPPING in arxml...", len(sig_ipdu))

    if decode_ethernet:
        result.update(decode_ethernet_helper(ea, float_factory))

    if decode_flexray:
        result.update(decode_flexray_helper(ea, float_factory))

    result.update(decode_can_helper(ea, float_factory, ignore_cluster_info))

    return result
