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
# this script exports fibex-files from a canmatrix-object
# fibex-files are the network-matrix-definitions; Canmatrix exports CAN
# only (fibex: Field Bus Exchange Format //
# https://de.wikipedia.org/wiki/Field_Bus_Exchange_Format)

import os
import typing
from builtins import *
import lxml.etree
import logging
import canmatrix
import re
import decimal

clusterImporter = 1

logger = logging.getLogger(__name__)

fx = "http://www.asam.net/xml/fbx"
ho = "http://www.asam.net/xml"
can = "http://www.asam.net/xml/fbx/can"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
ns_ho = "{%s}" % ho
ns_fx = "{%s}" % fx
ns_can = "{%s}" % can
ns_xsi = "{%s}" % xsi

extension = "xml"

# noinspection PyProtectedMember
_Element = lxml.etree._Element


def create_short_name_desc(parent, short_name, desc):
    # type: (_Element, str, str) -> None
    short_name_elem = lxml.etree.SubElement(parent, ns_ho + "SHORT-NAME")
    short_name_elem.text = short_name
    desc_elem = lxml.etree.SubElement(parent, ns_ho + "DESC")
    desc_elem.text = desc


def create_sub_element_fx(parent, element_name, element_text=None):
    # type: (_Element, str, typing.Optional[str]) -> _Element
    new = lxml.etree.SubElement(parent, ns_fx + element_name)
    if element_text is not None:
        new.text = element_text
    return new


def create_sub_element_ho(parent, element_name, element_text=None):
    # type: (_Element, str, typing.Optional[str]) -> _Element
    new = lxml.etree.SubElement(parent, ns_ho + element_name)
    if element_text is not None:
        new.text = element_text
    return new


def create_signal_instance(parent, signal, signal_id):
    # type: (_Element, Signal, str) -> _Element
    signal_instance = create_sub_element_fx(parent, "SIGNAL-INSTANCE")
    signal_instance.set("ID", "PDUINST_" + signal_id)
    create_sub_element_fx(signal_instance, "BIT-POSITION", str(signal.get_startbit(bit_numbering=1)))
    create_sub_element_fx(signal_instance, "IS-HIGH-LOW-BYTE-ORDER", "false" if signal.is_little_endian else "true")
    return signal_instance


def create_signal_ref(parent, signal_ref_id):
    # type: (_Element, str) -> _Element
    signal_ref = create_sub_element_fx(parent, "SIGNAL-REF")
    signal_ref.set("ID-REF", "SIG_" + signal_ref_id)
    return signal_ref


def bits_to_byte_str(bits, name):
    b = int(bits)
    if b % 8 == 0:
        return str(int(b/8))
    else:
        ret = int(b/8) + 1
        #if name is not None:
        #    print(f"Warning: {name} not byte aligned! {b} bits -> {ret} bytes")
        return str(ret)


def create_signal_id(frame, signal):
    # type: (Frame, Signal) -> str
    return f"{frame.name}.{signal.name}_{str(signal.mux_val)}" if signal.mux_val else f"{frame.name}.{signal.name}"


def get_multiplexing_parts_infos(signals, frame_name, start_pos=-1, end_pos=-1, seg_big_endian=None):
    # type: (list[Signal], str, int, int, bool) -> (int, int, bool)

    for signal in signals:
        if start_pos == -1 or signal.start_bit < start_pos:
            start_pos = signal.start_bit

        tmp_end_pos = signal.start_bit + signal.size
        if end_pos == -1 or tmp_end_pos > end_pos:
            end_pos = tmp_end_pos

        if seg_big_endian is not None and seg_big_endian == signal.is_little_endian:
            mux_info = f" with mux_val {signal.mux_val}" if signal.mux_val else ""
            print(f"Warning: Inconsistent Byte Order for frame {frame_name} {signal.name}{mux_info}")
        seg_big_endian = not signal.is_little_endian

    return start_pos, end_pos, seg_big_endian

def get_base_data_type(signal):
    # type: (Signal) -> str
    if signal.is_float:
        if (signal.size<=32):
            return "A_FLOAT32"
        else:
            return "A_FLOAT64"
    
    if signal.size > 0 and signal.size <= 8:
        if signal.is_signed:
            return "A_INT8"
        elif not signal.is_signed:
            return "A_UINT8"
        
    elif signal.size > 8 and signal.size <= 16:
            if signal.is_signed:
                return "A_INT16"
            elif not signal.is_signed:
                return "A_UINT16"
    elif signal.size > 16 and signal.size <= 32:
            if signal.is_signed:
                return "A_INT32"
            elif not signal.is_signed:
                return "A_UINT32"
    elif signal.size > 32 and signal.size <= 64:
            if signal.is_signed:
                return "A_INT64"
            elif not signal.is_signed:
                return "A_UINT64"
class Fe:
    def __init__(self, filename):
        self.tree = lxml.etree.parse(filename)
        self.root = self.tree.getroot()  # type: _Element

        self.ns = "{" + self.tree.xpath('namespace-uri(.)') + "}"  # type: str
        self.nsp = self.tree.xpath('namespace-uri(.)')
        self.ans = "{http://www.asam.net/xml}"
        self._id_cache = {a.attrib["ID"]:a for a in self.root.xpath(".//*[@ID]")}
        self._id_rev_cache = {}
        for referencer in self.root.xpath(".//*[@ID-REF]"):
            ref_id = referencer.attrib["ID-REF"]
            if ref_id not in self._id_rev_cache:
                self._id_rev_cache[ref_id] = [referencer]
            else:
                self._id_rev_cache[ref_id].append(referencer)

    def sn(self, tag):
        sn = tag.find("./" + self.ans + "SHORT-NAME").text
        return sn

    def get_referencable_parent(self, xml_element):
        path = ""
        while xml_element != self.root:
            try:
               current_short_name = self.sn(xml_element)
               return xml_element
            except AttributeError:
                pass
            xml_element = xml_element.getparent()
        return xml_element

    def find_parent(self, start_element, parent_tag):
        while start_element != self.root:
            if start_element.tag == self.ns + parent_tag or start_element == self.ans + parent_tag:
                return start_element
            start_element = start_element.getparent()
        return None

    def get_desc_or_longname(self, element):
        long_name_elements = self.selector(element, "./!LONG-NAME")
        if len(long_name_elements) > 0:
            return long_name_elements[0].text

        desc_elements = self.selector(element, "./!DESC")
        if len(desc_elements) > 0:
            return desc_elements[0].text

        return ""

    def selector(self, start_element, selector):
        start_pos = 0
        token = ""
        result_list = [start_element]
        last_found_token = 0
        while start_pos < len(selector):
            token_match = re.search(r'//|/!|/|!|>>|>!|<<!|<<|\^|>|$', selector[start_pos:])
            found_token = token_match.span()
            if start_pos > 0:  # at least one Token found...
                value = selector[last_found_token:start_pos + found_token[0]]
                if token == "//":
                    result_list = [c for a in result_list for c in a.findall(".//" + self.ns + value)]
                elif token == "/!":
                    result_list = [c for a in result_list for c in a.findall(".//" + self.ans + value)]
                elif token == "/":
                    if value == "..":
                        result_list = [a.getparent() for a in result_list]
                    else:
                        result_list = [a.find("./" + self.ns + value) for a in result_list]
                elif token == "!":
                    result_list = [a.find("./" + self.ans + value) for a in result_list]
                elif token == ">":
                    start_points = [a.find("./" + self.ns + value).attrib["ID-REF"] for a in result_list]
                    result_list = [self._id_cache[a] for a in start_points]
                elif token == "<<":
                    id_list = [a.attrib["ID"] for a in result_list]
                    result_list = [b for a in id_list for b in self._id_rev_cache[a]]
                    result_list = [a for a in result_list if self.get_referencable_parent(a) is not None and self.get_referencable_parent(a).tag.endswith(value)]
                elif token == "<<!":
                    id_list = [a.attrib["ID"] for a in result_list]
                    result_list = [b for a in id_list for b in self._id_rev_cache[a]]
                elif token == ">>":
                    start_points = [c.attrib["ID-REF"] for a in result_list for c in a.findall(".//" + self.ns + value)]
                    result_list = [self._id_cache[a] for a in start_points]
                elif token == ">!":
                    start_points = [c.attrib["ID-REF"] for a in result_list for c in a.findall(".//" + self.ans + value)]
                    result_list = [self._id_cache[a] for a in start_points]
                elif token == ">>":
                    start_points = [c.attrib["ID-REF"] for a in result_list for c in a.findall(".//" + self.ns + value)]
                    result_list = [self._id_cache[a] for a in start_points]
                elif token == "^":
                    result_list = [self.find_parent(a, value) for a in result_list if a is not None and self.find_parent(a, value) is not None]

            result_list = [a for a in result_list if a is not None]
            last_found_token = found_token[1] + start_pos
            token = selector[start_pos + found_token[0]:start_pos + found_token[1]]
            start_pos += found_token[1]
        return sorted(result_list, key=lambda element: element.sourceline)


def get_signals_for_pdu(fe, pdu, overall_startbit = 0):
    signals = []
    ecus = []
    for signal_instance in fe.selector(pdu, "//SIGNAL-INSTANCE"):
        byte_order_element = fe.selector(signal_instance, "/IS-HIGH-LOW-BYTE-ORDER")
        if byte_order_element[0].text == "false":
            is_little_endian = True
        else:
            is_little_endian = False

        start_bit = int(fe.selector(signal_instance, "/BIT-POSITION")[0].text, 0) + overall_startbit
        signal = fe.selector(signal_instance, ">SIGNAL-REF")[0]
        ecu_instance_refs = fe.selector(signal_instance, "<<ECU")
        receiver_ecus = []
        for ecu_instance_ref in ecu_instance_refs:
            if len(fe.selector(ecu_instance_ref, "^INPUT-PORT")) > 0:
                ecu_name = fe.sn(fe.get_referencable_parent(ecu_instance_ref))
                receiver_ecus.append(ecu_name)
                ecus.append(canmatrix.Ecu(name=ecu_name.strip()))

        signal_name = fe.sn(signal)
        coding = fe.selector(signal, ">CODING-REF")[0]
        is_signed = False
        try:
            basedatatype = fe.selector(coding, "/!CODED-TYPE")[0].attrib[fe.ans + "BASE-DATA-TYPE"]
            if "UINT" in basedatatype:
                is_signed = False
            elif "INT" in basedatatype:
                is_signed = True
        except:
            pass
        bit_length = int(fe.selector(coding, "/!BIT-LENGTH")[0].text)
        compu_methods = fe.selector(coding, "/!COMPU-METHOD")
        sig = canmatrix.Signal(name=signal_name, is_signed=is_signed)
        for compu_method in compu_methods:
            category = fe.selector(compu_method, "/!CATEGORY")
            if len(category) > 0 and category[0].text == "LINEAR":
                numerator = fe.selector(compu_method, "/!COMPU-NUMERATOR")[0]
                denominator = fe.selector(compu_method, "/!COMPU-DENOMINATOR")[0]
                teiler = decimal.Decimal(fe.selector(denominator, "/!V")[0].text)
                [offset, factor] = [decimal.Decimal(a.text) for a in fe.selector(numerator, "/!V")]
                [offset, factor] = [a / teiler for a in [offset, factor]]
                sig.offset = offset
                sig.factor = factor
                try:
                    sig.min = decimal.Decimal(fe.selector(compu_method, "!PHYS-CONSTRS!LOWER-LIMIT")[0].text)
                    sig.max = decimal.Decimal(fe.selector(compu_method, "!PHYS-CONSTRS!UPPER-LIMIT")[0].text)
                except:
                    pass
                unit = fe.selector(compu_method, ">!UNIT-REF")
                if len(unit) > 0:
                    try:
                        sig.unit = fe.selector(unit[0], "!DISPLAY-NAME")[0].text
                    except:
                        pass
            elif len(category) > 0 and category[0].text == "TEXTTABLE":
                for compu_scale in fe.selector(compu_method, "/!COMPU-SCALE"):
                    try:
                        value_name = fe.selector(compu_scale, "!COMPU-CONST!VT")[0].text
                    except IndexError:
                        value_name = fe.get_desc_or_longname(compu_scale)
                    value_value = fe.selector(compu_scale, "!LOWER-LIMIT")[0].text
                    sig.add_values(value_value, value_name)
        sig.is_little_endian = is_little_endian
        if not sig.is_little_endian:
            sig.set_startbit(start_bit, bitNumbering=1)
        else:
            sig.start_bit = start_bit
        sig.size = bit_length
        sig.receivers = list(set(receiver_ecus))

        sig.add_comment(fe.get_desc_or_longname(signal))
        signals.append(sig)
    return signals, ecus


def load(f, **_options):
    fe = Fe(f)
    result = {}
    sig_group_counter = 0

    clusters = fe.selector(fe.root, "//CLUSTER")
    names = [fe.sn(a) for a in clusters]
    logger.info("Found clusters: " + ",".join(names))

    for cluster in clusters:
        if "CAN" not in fe.selector(cluster, "//PROTOCOL")[0].text:
            logger.info(fe.sn(cluster) + " seems not to be a CAN cluster - ignoring")
            continue

        db = canmatrix.CanMatrix()
        result[fe.sn(cluster)] = db
        channels = fe.selector(cluster, ">>CHANNEL-REF")
        for channel in channels:
            for ft in fe.selector(channel, "//FRAME-TRIGGERING"):
                ports = fe.selector(ft, "<<ECU/..")
                output_ports = [a for a in ports if a.tag == fe.ns + "OUTPUT-PORT"]
                sending_ecus = [fe.get_referencable_parent(a) for a in output_ports]
                arbitration_id_element = fe.selector(ft, "//IDENTIFIER-VALUE")[0]
                arbitration_id = int(arbitration_id_element.text)
                extended = arbitration_id_element.attrib.get("EXTENDED-ADDRESSING", 'false') == 'true'
                frame_element = fe.selector(ft, ">FRAME-REF")[0]
                frame_size = int(fe.selector(frame_element, "/BYTE-LENGTH")[0].text)

                pdu_instances = fe.selector(frame_element, "//PDU-INSTANCE")

                if len(pdu_instances) > 1:
                    frame_name = fe.sn(frame_element)
                    frame = canmatrix.Frame(name=frame_name)
                    for pdu_instance in pdu_instances:
                        pdu = fe.selector(pdu_instance, ">PDU-REF")[0]
                        pdu_startbit_position = int(fe.selector(pdu_instance, "/BIT-POSITION")[0].text, 0)
                        signals, ecus = get_signals_for_pdu(fe, pdu, pdu_startbit_position)
                        for sig in signals:
                            frame.add_signal(sig)
                        for ecu in ecus:
                            db.add_ecu(ecu)

                        frame.add_signal_group(fe.sn(pdu), sig_group_counter, [sig.name for sig in signals])
                        sig_group_counter += 1
                else:
                    pdu = fe.selector(pdu_instances[0], ">PDU-REF")[0]
                    frame_name = fe.sn(pdu)
                    frame = canmatrix.Frame(name=frame_name)

                    signals, ecus = get_signals_for_pdu(fe, pdu)
                    for sig in signals:
                        frame.add_signal(sig)
                    for ecu in ecus:
                        db.add_ecu(ecu)

                #                fe.selector(pdu, "<<!PDU-TRIGGERING")
                frame.size = frame_size
                if len(output_ports) > 0:
                    pdu_triggerings = fe.selector(output_ports[0], ">>PDU-TRIGGERING-REF")
                    if len(pdu_triggerings) > 0:
                        cyclic_timing_element = fe.selector(pdu_triggerings[0],
                                                    "/TIMINGS/CYCLIC-TIMING/REPEATING-TIME-RANGE/VALUE")
                        if len(cyclic_timing_element) > 0:
                            time_value_string = cyclic_timing_element[0].text
                            if time_value_string.startswith("PT") and time_value_string.endswith("S"):
                                frame.cycle_time = decimal.Decimal(time_value_string[2:-1])*1000
                frame.transmitters = [fe.sn(a) for a in sending_ecus]
                for ecu_element in sending_ecus:
                    ecu_name = fe.sn(ecu_element)
                    cm_ecu = canmatrix.Ecu(ecu_name)
                    cm_ecu.add_comment(fe.get_desc_or_longname(ecu_element))
                    db.add_ecu(cm_ecu)
                frame.arbitration_id = canmatrix.ArbitrationId(extended=extended, id=arbitration_id)

                frame.add_comment(fe.get_desc_or_longname(pdu))
                if "CAN-FD" in [a.text for a in
                     fe.selector(ft, "//CAN-FRAME-TX-BEHAVIOR") + fe.selector(ft, "//CAN-FRAME-RX-BEHAVIOR")]:
                    frame.is_fd = True

                db.add_frame(frame)
    return result


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    ns_map = {"fx": fx, "ho": ho, "can": can, "xsi": xsi}
    root = lxml.etree.Element(ns_fx + "FIBEX", nsmap=ns_map)
    root.attrib[
        '{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://www.asam.net/xml/fbx ..\\..\\xml_schema\\fibex.xsd http://www.asam.net/xml/fbx/can  ..\\..\\xml_schema\\fibex4can.xsd'

    #
    # Make sure that we can even write to FIBEX
    #

    # make frame names unique by adding suffix, if needed
    frame_names = dict()
    for frame in db.frames:
        if frame.name in frame_names:
            # conflict resolution
            tmp = 2
            while f"{frame.name}_{str(tmp)}" in frame_names:
                tmp += 1

            new_name = f"{frame.name}_{str(tmp)}"
            print(f"Warning: Changing frame name due to conflict: {frame.name} -> {new_name}")
            frame.name = new_name

        frame_names[frame.name] = frame


    #
    # PROJECT
    #
    project = create_sub_element_fx(root, "PROJECT")
    project.set('ID', 'canmatrixExport')
    create_short_name_desc(project, "CAN", "Canmatrix Export")

    #
    # ELEMENTS
    #
    elements = create_sub_element_fx(root, "ELEMENTS")
    
    #
    # CLUSTERS
    #
    clusters = create_sub_element_fx(elements, "CLUSTERS")
    cluster = lxml.etree.SubElement(clusters, ns_fx + "CLUSTER")
    cluster.set('ID', 'canCluster1')
    # add the file name as a suffix in the cluster name
    cluster_name = f"cluster_{os.path.basename(f.name).split('.')[0]}"
    create_short_name_desc(cluster, cluster_name, "clusterDesc")
    create_sub_element_fx(cluster, "SPEED", "500")
    create_sub_element_fx(cluster, "IS-HIGH-LOW-BIT-ORDER", "true")
    create_sub_element_fx(cluster, "BIT-COUNTING-POLICY", "MONOTONE")
    protocol = create_sub_element_fx(cluster, "PROTOCOL", "CAN")
    protocol.attrib['{{{pre}}}type'.format(pre=xsi)] = "can:PROTOCOL-TYPE"
    create_sub_element_fx(cluster, "PROTOCOL-VERSION", "20")
    channel_refs = create_sub_element_fx(cluster, "CHANNEL-REFS")
    # for each channel
    channel_ref = create_sub_element_fx(channel_refs, "CHANNEL-REF")
    channel_ref.set("ID-REF", "CANCHANNEL01")

    #
    # CHANNELS
    #
    channels = create_sub_element_fx(elements, "CHANNELS")
    channel = create_sub_element_fx(channels, "CHANNEL")
    # for each channel
    channel.set('ID', 'CANCHANNEL01')
    create_short_name_desc(channel, "CANCHANNEL01", "Can Channel Description")

    # for pdu triggerings
    pdu_triggerings = create_sub_element_fx(channel, "PDU-TRIGGERINGS")
    for pdu in db.frames:
        pdu_triggering = create_sub_element_fx(
            pdu_triggerings, "PDU-TRIGGERING")
        pdu_triggering.set("ID", "PDU_" + pdu.name)
        pdu_timings = create_sub_element_fx(pdu_triggering, "TIMINGS")
        if pdu.cycle_time > 0:
            cyclic_timing = create_sub_element_fx(pdu_timings, "CYCLIC-TIMING")
            repeating_time_range = create_sub_element_fx(cyclic_timing, "REPEATING-TIME-RANGE")
            create_sub_element_fx(repeating_time_range, "VALUE", "PT" + str(pdu.cycle_time/1000.0) + "S")

        pdu_ref = create_sub_element_fx(pdu_triggering, "PDU-REF")
        pdu_ref.set("ID-REF", "PDU_" + pdu.name)

    frame_triggerings = create_sub_element_fx(channel, "FRAME-TRIGGERINGS")
    for frame in db.frames:
        frame_triggering = create_sub_element_fx(
            frame_triggerings, "FRAME-TRIGGERING")
        frame_triggering.set("ID", "FT_" + frame.name)
        identifier = create_sub_element_fx(frame_triggering, "IDENTIFIER")
        create_sub_element_fx(identifier, "IDENTIFIER-VALUE", str(frame.arbitration_id.id))
        frame_ref = create_sub_element_fx(frame_triggering, "FRAME-REF")
        frame_ref.set("ID-REF", "FRAME_" + frame.name)
        if (frame.is_fd):
            create_sub_element_fx(frame_triggering, "CAN-FRAME-TX-BEHAVIOR","CAN-FD")
            create_sub_element_fx(frame_triggering, "CAN-FRAME-RX-BEHAVIOR","CAN-FD")

    #
    # ECUS
    #
    ecus = create_sub_element_fx(elements, "ECUS")
    for bu in db.ecus:
        ecu = create_sub_element_fx(ecus, "ECU")
        ecu.set("ID", bu.name)
        create_short_name_desc(ecu, bu.name, bu.comment)
        function_refs = create_sub_element_fx(ecu, "FUNCTION-REFS")
        func_ref = create_sub_element_fx(function_refs, "FUNCTION-REF")
        func_ref.set("ID-REF", "FCT_" + bu.name)

        controllers = create_sub_element_fx(ecu, "CONTROLLERS")
        controller = create_sub_element_fx(controllers, "CONTROLLER")
        create_short_name_desc(controller, bu.name, bu.comment)
        controller.set('ID', 'Controller_' + bu.name)

        connectors = create_sub_element_fx(ecu, "CONNECTORS")
        connector = create_sub_element_fx(connectors, "CONNECTOR")
        connector.set('ID', 'Connector' + bu.name)
        channel_ref = create_sub_element_fx(connector, "CHANNEL-REF")
        channel_ref.set("ID-REF", "CANCHANNEL01")
        controller_ref = create_sub_element_fx(connector, "CONTROLLER-REF")
        controller_ref.set("ID-REF", 'Controller_' + bu.name)
        inputs = create_sub_element_fx(connector, "INPUTS")
        for frame in db.frames:
            if bu.name in frame.receivers:
                input_port = create_sub_element_fx(inputs, "INPUT-PORT")
                frame_triggering_ref = create_sub_element_fx(input_port, "FRAME-TRIGGERING-REF")
                frame_triggering_ref.set("ID-REF", "FT_" + frame.name)
                # Reference to PDUs
                included_pdus = create_sub_element_fx(input_port, "INCLUDED-PDUS")
                included_pdu = create_sub_element_fx(included_pdus, "INCLUDED-PDU")
                included_pdu.set('ID', 'input_included_pdu_' + frame.name)
                pdu_triggering_ref = create_sub_element_fx(included_pdu, "PDU-TRIGGERING-REF")
                pdu_triggering_ref.set("ID-REF", "PDU_" + frame.name)
                
        outputs = create_sub_element_fx(connector, "OUTPUTS")
        for frame in db.frames:
            if bu.name in frame.transmitters:
                input_port = create_sub_element_fx(outputs, "OUTPUT-PORT")
                frame_triggering_ref = create_sub_element_fx(input_port, "FRAME-TRIGGERING-REF")
                frame_triggering_ref.set("ID-REF", "FT_" + frame.name)
                # Reference to PDUs
                included_pdus = create_sub_element_fx(input_port, "INCLUDED-PDUS")
                included_pdu = create_sub_element_fx(included_pdus, "INCLUDED-PDU")
                included_pdu.set('ID', 'output_included_pdu_' + frame.name)
                pdu_triggering_ref = create_sub_element_fx(included_pdu, "PDU-TRIGGERING-REF")
                pdu_triggering_ref.set("ID-REF", "PDU_" + frame.name)

        # ignore CONTROLLERS/CONTROLLER

    #
    # PDUS
    #
    pdus = create_sub_element_fx(elements, "PDUS")
    for frame in db.frames:
        pdu = create_sub_element_fx(pdus, "PDU")
        pdu.set("ID", "PDU_" + frame.name)
        create_short_name_desc(pdu, "PDU_" + frame.name, frame.comment)
        create_sub_element_fx(pdu, "BYTE-LENGTH", str(frame.size))  # DLC
        create_sub_element_fx(pdu, "PDU-TYPE", "APPLICATION")

        if frame.is_multiplexed:
            mux = create_sub_element_fx(pdu, "MULTIPLEXER")

            signals_static = []
            signals_dynamic = {}
            signals_switch = []

            for signal in frame.signals:
                if signal.is_multiplexer:
                    signals_switch.append(signal)
                elif signal.multiplex is not None or signal.mux_val is not None:
                    if signal.multiplex != signal.mux_val:
                        print(f"Warning: Signal {signal.name} mux_val {signal.mux_val} != multiplex {signal.multiplex}")
                    sigs = signals_dynamic.setdefault(signal.mux_val, [])
                    sigs.append(signal)
                else:
                    signals_static.append(signal)

            if len(signals_switch) != 1 or len(signals_dynamic) == 0:
                print(f"Warning: Frame {frame.name} has an invalid multiplexer or dyn Part! "
                      f"Switch Signals: {len(signals_switch)} "
                      f"Dyn Signals: {len(signals_dynamic)} "
                      f"Static Signals: {len(signals_static)}")

            # SWITCH
            mux_switch = create_sub_element_fx(mux, "SWITCH")
            mux_switch.set("ID", "PDU_" + frame.name + "_SWITCH")
            create_sub_element_ho(mux_switch, "SHORT-NAME", signals_switch[0].name)
            create_sub_element_fx(mux_switch, "BIT-POSITION", str(signals_switch[0].start_bit))
            create_sub_element_fx(mux_switch, "IS-HIGH-LOW-BYTE-ORDER",
                                  "false" if signals_switch[0].is_little_endian else "true")
            create_sub_element_ho(mux_switch, "BIT-LENGTH", str(signals_switch[0].size))

            # DYNAMIC PART
            start_pos = -1
            end_pos = -1
            seg_be = None

            for sigs in signals_dynamic.values():
                start_pos, end_pos, seg_be = get_multiplexing_parts_infos(sigs,
                                                                          frame.name,
                                                                          start_pos=start_pos,
                                                                          end_pos=end_pos,
                                                                          seg_big_endian=seg_be)

            if seg_be is None:
                seg_be = False

            if start_pos >= 0:
                mux_dynpart = create_sub_element_fx(mux, "DYNAMIC-PART")
                mux_dynpart.set("ID", "PDU_" + frame.name + "_DYN_PART")
                create_sub_element_ho(mux_dynpart, "SHORT-NAME", signal.name)

                seg_positions = create_sub_element_fx(mux_dynpart, "SEGMENT-POSITIONS")
                seg_position = create_sub_element_fx(seg_positions, "SEGMENT-POSITION")
                create_sub_element_fx(seg_position, "BIT-POSITION", str(start_pos))
                create_sub_element_fx(seg_position, "IS-HIGH-LOW-BYTE-ORDER", "true" if seg_be else "false")
                create_sub_element_ho(seg_position, "BIT-LENGTH", str(end_pos - start_pos))

                sw_pdu_instances = create_sub_element_fx(mux_dynpart, "SWITCHED-PDU-INSTANCES")

                for mux_key in sorted(signals_dynamic.keys()):
                    # create PDU for these signals
                    mux_key_pdu = create_sub_element_fx(pdus, "PDU")
                    mux_key_pdu_id = f"PDU_{frame.name}_DYNPART_{str(mux_key)}"
                    mux_key_pdu.set("ID", mux_key_pdu_id)
                    create_short_name_desc(mux_key_pdu, mux_key_pdu_id, "")
                    create_sub_element_fx(mux_key_pdu, "BYTE-LENGTH",
                                          bits_to_byte_str(end_pos - start_pos, mux_key_pdu_id))
                    create_sub_element_fx(mux_key_pdu, "PDU-TYPE", "APPLICATION")

                    signal_instances = create_sub_element_fx(mux_key_pdu, "SIGNAL-INSTANCES")
                    for signal in signals_dynamic[mux_key]:
                        signal_id = create_signal_id(frame, signal)
                        signal_instance = create_signal_instance(signal_instances, signal, signal_id)
                        create_signal_ref(signal_instance, signal_id)

                    # create SWITCHED-PDU-INSTANCE that refs mux_key_pdu_id
                    switched_pdu_inst = create_sub_element_fx(sw_pdu_instances, "SWITCHED-PDU-INSTANCE")
                    switched_pdu_inst.set("ID", mux_key_pdu_id + "_SWITCHED_PDU_INSTANCE")
                    pdu_ref = create_sub_element_fx(switched_pdu_inst, "PDU-REF")
                    pdu_ref.set("ID-REF", mux_key_pdu_id)
                    create_sub_element_fx(switched_pdu_inst, "SWITCH-CODE", str(mux_key))

            # STATIC PART
            start_pos, end_pos, seg_be = get_multiplexing_parts_infos(signals_static, frame.name)

            if start_pos != -1 and end_pos != -1:
                static_part = create_sub_element_fx(mux, "STATIC-PART")
                static_part.set("ID", "PDU_" + frame.name + "_STATIC_PART")
                create_sub_element_ho(static_part, "SHORT-NAME", signal.name)
                seg_positions = create_sub_element_fx(static_part, "SEGMENT-POSITIONS")
                seg_position = create_sub_element_fx(seg_positions, "SEGMENT-POSITION")
                create_sub_element_fx(seg_position, "BIT-POSITION", str(start_pos))
                create_sub_element_fx(seg_position, "IS-HIGH-LOW-BYTE-ORDER", "true" if seg_be else "false")
                create_sub_element_ho(seg_position, "BIT-LENGTH", str(end_pos - start_pos))

                # create static PDU
                static_pdu = create_sub_element_fx(pdus, "PDU")
                static_pdu_key = f"PDU_{frame.name}_STATIC_PART_PDU"
                static_pdu.set("ID", static_pdu_key)
                create_short_name_desc(static_pdu, static_pdu_key, "")
                create_sub_element_fx(static_pdu, "BYTE-LENGTH", bits_to_byte_str(end_pos - start_pos, frame.name))
                create_sub_element_fx(static_pdu, "PDU-TYPE", "APPLICATION")
                signal_instances = create_sub_element_fx(static_pdu, "SIGNAL-INSTANCES")
                for signal in signals_static:
                    signal_id = create_signal_id(frame, signal)
                    signal_instance = create_signal_instance(signal_instances, signal, signal_id)
                    create_signal_ref(signal_instance, signal_id)

                # create STATIC-PDU-INSTANCE that refs static_pdu_key
                static_pdu_inst = create_sub_element_fx(static_part, "STATIC-PDU-INSTANCE")
                static_pdu_inst.set("ID", static_pdu_key + "_SWITCHED-PDU-INSTANCE")
                pdu_ref = create_sub_element_fx(static_pdu_inst, "PDU-REF")
                pdu_ref.set("ID-REF", static_pdu_key)

        else:
            # PDU without Multiplexing
            signal_instances = create_sub_element_fx(pdu, "SIGNAL-INSTANCES")
            for signal in frame.signals:
                signal_id = create_signal_id(frame, signal)
                signal_instance = create_signal_instance(signal_instances, signal, signal_id)
                create_signal_ref(signal_instance, signal_id)

    # FRAMES
    #
    frames = create_sub_element_fx(elements, "FRAMES")
    for frame in db.frames:
        frame_element = create_sub_element_fx(frames, "FRAME")
        frame_element.set("ID", "FRAME_" + frame.name)
        create_short_name_desc(frame_element, frame.name, frame.comment)
        create_sub_element_fx(frame_element, "BYTE-LENGTH", str(frame.size))  # DLC
        create_sub_element_fx(frame_element, "PDU-TYPE", "APPLICATION")
        pdu_instances = create_sub_element_fx(frame_element, "PDU-INSTANCES")
        pdu_instance = create_sub_element_fx(pdu_instances, "PDU-INSTANCE")
        pdu_instance.set("ID", "PDUINSTANCE_" + frame.name)
        pdu_ref = create_sub_element_fx(pdu_instance, "PDU-REF")
        pdu_ref.set("ID-REF", "PDU_" + frame.name)
        create_sub_element_fx(pdu_instance, "BIT-POSITION", "0")
        create_sub_element_fx(pdu_instance, "IS-HIGH-LOW-BYTE-ORDER", "false")

    #
    # FUNCTIONS
    #
    functions = create_sub_element_fx(elements, "FUNCTIONS")
    for bu in db.ecus:
        function = create_sub_element_fx(functions, "FUNCTION")
        function.set("ID", "FCT_" + bu.name)
        create_short_name_desc(function, "FCT_" + bu.name, bu.comment)
        input_ports = create_sub_element_fx(function, "INPUT-PORTS")
        for frame in db.frames:
            for signal in frame.signals:
                signal_id = create_signal_id(frame, signal)
                if bu.name in signal.receivers:
                    input_port = create_sub_element_fx(input_ports, "INPUT-PORT")
                    input_port.set("ID", "INP_" + signal_id)
                    desc = lxml.etree.SubElement(input_port, ns_ho + "DESC")
                    desc.text = signal.comment
                    create_signal_ref(input_port, signal_id)

        output_ports = create_sub_element_fx(function, "OUTPUT-PORTS")
        for frame in db.frames:
            if bu.name in frame.transmitters:
                for signal in frame.signals:
                    signal_id = create_signal_id(frame, signal)
                    output_port = create_sub_element_fx(output_ports, "OUTPUT-PORT")
                    output_port.set("ID", "OUTP_" + signal_id)
                    desc = lxml.etree.SubElement(output_port, ns_ho + "DESC")
                    desc.text = "signalcomment"
                    create_signal_ref(output_port, frame.name + "_" + signal_id)

    #
    # SIGNALS
    #
    signals = create_sub_element_fx(elements, "SIGNALS")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = create_signal_id(frame, signal)
            signal_element = create_sub_element_fx(signals, "SIGNAL")
            signal_element.set("ID", "SIG_" + signal_id)
            create_short_name_desc(signal_element, signal.name, signal.comment)
            default_value = str(signal.phys2raw(signal.initial_value))
            create_sub_element_fx(signal_element, "DEFAULT-VALUE", default_value)
            coding_ref = create_sub_element_fx(signal_element, "CODING-REF")
            coding_ref.set("ID-REF", "CODING_" + signal_id)

    #
    # PROCESSING-INFORMATION
    #
    proc_info = lxml.etree.SubElement(root, ns_fx + "PROCESSING-INFORMATION", nsmap={"ho": ho})
    unit_spec = create_sub_element_ho(proc_info, "UNIT-SPEC")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = create_signal_id(frame, signal)
            unit = create_sub_element_ho(unit_spec, "UNIT")
            unit.set("ID", "UNIT_" + signal_id)
            create_sub_element_ho(unit, "SHORT-NAME", signal.name)
            create_sub_element_ho(unit, "DISPLAY-NAME", signal.unit)

    codings = create_sub_element_fx(proc_info, "CODINGS")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = create_signal_id(frame, signal)
            coding = create_sub_element_fx(codings, "CODING")
            coding.set("ID", "CODING_" + signal_id)
            create_short_name_desc(
                coding,
                "CODING_" +
                signal_id,
                "Coding for " +
                signal_id)
                
            coded = create_sub_element_ho(coding, "CODED-TYPE")
            base_data_type = get_base_data_type(signal)
            if base_data_type is not None:
                coded.set(ns_ho + "BASE-DATA-TYPE", base_data_type)
                coded.set("CATEGORY", "STANDARD-LENGTH-TYPE")
            create_sub_element_ho(coded, "BIT-LENGTH", str(signal.size))
            
            compu_methods = create_sub_element_ho(coding, "COMPU-METHODS")
            compu_method = create_sub_element_ho(compu_methods, "COMPU-METHOD")
            create_sub_element_ho(
                compu_method,
                "SHORT-NAME",
                "COMPUMETHOD_" +
                signal.name)
            create_sub_element_ho(compu_method, "CATEGORY", "LINEAR")
            unit_ref = create_sub_element_ho(compu_method, "UNIT-REF")
            unit_ref.set("ID-REF", "UNIT_" + signal_id)
            compu_internal_to_phys = create_sub_element_ho(
                compu_method, "COMPU-INTERNAL-TO-PHYS")
            compu_scales = create_sub_element_ho(
                compu_internal_to_phys, "COMPU-SCALES")
            compu_scale = create_sub_element_ho(compu_scales, "COMPU-SCALE")
            lower_limit = create_sub_element_ho(compu_scale, "LOWER-LIMIT", str(signal.min))  # Min
            lower_limit.set("INTERVAL-TYPE", "CLOSED")
            upper_limit = create_sub_element_ho(compu_scale, "UPPER-LIMIT", str(signal.max))  # Max
            upper_limit.set("INTERVAL-TYPE", "CLOSED")

            compu_rational_coeffs = create_sub_element_ho(
                compu_scale, "COMPU-RATIONAL-COEFFS")
            compu_numerator = create_sub_element_ho(
                compu_rational_coeffs, "COMPU-NUMERATOR")
            create_sub_element_ho(compu_numerator, "V", str(signal.offset))  # offset
            create_sub_element_ho(compu_numerator, "V", str(signal.factor))  # factor
            compu_denominator = create_sub_element_ho(compu_rational_coeffs, "COMPU-DENOMINATOR")
            create_sub_element_ho(compu_denominator, "V", "1")  # nenner
            # defaultValue = create_sub_element_ho(compuInternalToPhys,"COMPU-DEFAULT-VALUE")

            # CAN signal interpretation
            if signal.values:
                compu_method =  create_sub_element_ho(compu_methods, "COMPU-METHOD")
                create_sub_element_ho(compu_method, "SHORT-NAME",
                    "SIGNAL_INTERPRETATION_" + signal.name)
                create_sub_element_ho(compu_method, "CATEGORY", "TEXTTABLE")
                compu_int_to_phys = create_sub_element_ho(compu_method, "COMPU-INTERNAL-TO-PHYS")
                compu_scales = create_sub_element_ho(compu_int_to_phys, "COMPU-SCALES")

                for value, text in signal.values.items():
                    compu_scale = create_sub_element_ho(compu_scales, "COMPU-SCALE")

                    lower_limit = create_sub_element_ho(compu_scale, "LOWER-LIMIT", str(value))
                    lower_limit.set("INTERVAL-TYPE", "CLOSED")
                    upper_limit = create_sub_element_ho(compu_scale, "UPPER-LIMIT", str(value))
                    upper_limit.set("INTERVAL-TYPE", "CLOSED")

                    compu_const = create_sub_element_ho(compu_scale, "COMPU-CONST")
                    create_sub_element_ho(compu_const, "VT", text)

    #
    # REQUIREMENTS
    #
    # requirements = createSubElementFx(elements,  "REQUIREMENTS")

    f.write(lxml.etree.tostring(root, pretty_print=True))
