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

from __future__ import absolute_import, division, print_function

import typing
from builtins import *

import lxml.etree

import canmatrix

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


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    ns_map = {"fx": fx, "ho": ho, "can": can, "xsi": xsi}
    root = lxml.etree.Element(ns_fx + "FIBEX", nsmap=ns_map)
    root.attrib[
        '{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://www.asam.net/xml/fbx ..\\..\\xml_schema\\fibex.xsd http://www.asam.net/xml/fbx/can  ..\\..\\xml_schema\\fibex4can.xsd'

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
    create_short_name_desc(cluster, "clusterShort", "clusterDesc")
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
                
        
        # ignore CONTROLERS/CONTROLER

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
        signal_instances = create_sub_element_fx(pdu, "SIGNAL-INSTANCES")
        for signal in frame.signals:
            signal_id = frame.name + "." + signal.name
            signal_instance = create_sub_element_fx(
                signal_instances, "SIGNAL-INSTANCE")
            signal_instance.set("ID", "PDUINST_" + signal_id)
            # startBit: TODO - find out correct BYTEORDER ...
            create_sub_element_fx(signal_instance, "BIT-POSITION",
                                  str(signal.start_bit))
            if signal.is_little_endian:
                create_sub_element_fx(
                    signal_instance,
                    "IS-HIGH-LOW-BYTE-ORDER",
                    "false")  # true:big endian; false:little endian
            else:
                create_sub_element_fx(
                    signal_instance, "IS-HIGH-LOW-BYTE-ORDER", "true")
            signal_ref = create_sub_element_fx(signal_instance, "SIGNAL-REF")
            signal_ref.set("ID-REF", "SIG_" + signal_id)

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
                signal_id = frame.name + "." + signal.name
                if bu.name in signal.receivers:
                    input_port = create_sub_element_fx(input_ports, "INPUT-PORT")
                    input_port.set("ID", "INP_" + signal_id)
                    desc = lxml.etree.SubElement(input_port, ns_ho + "DESC")
                    desc.text = signal.comment
                    signal_ref = create_sub_element_fx(input_port, "SIGNAL-REF")
                    signal_ref.set("ID-REF", "SIG_" + signal_id)

        output_ports = create_sub_element_fx(function, "OUTPUT-PORTS")
        for frame in db.frames:
            if bu.name in frame.transmitters:
                for signal in frame.signals:
                    signal_id = frame.name + "." + signal.name
                    output_port = create_sub_element_fx(output_ports, "OUTPUT-PORT")
                    output_port.set("ID", "OUTP_" + signal_id)
                    desc = lxml.etree.SubElement(output_port, ns_ho + "DESC")
                    desc.text = "signalcomment"
                    signal_ref = create_sub_element_fx(output_port, "SIGNAL-REF")
                    signal_ref.set("ID-REF", "SIG_" + frame.name + "_" + signal_id)

    #
    # SIGNALS
    #
    signals = create_sub_element_fx(elements, "SIGNALS")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = frame.name + "." + signal.name
            signal_element = create_sub_element_fx(signals, "SIGNAL")
            signal_element.set("ID", "SIG_" + signal_id)
            create_short_name_desc(signal_element, signal.name, signal.comment)
            coding_ref = create_sub_element_fx(signal_element, "CODING-REF")
            coding_ref.set("ID-REF", "CODING_" + signal_id)

    #
    # PROCESSING-INFORMATION
    #
    proc_info = lxml.etree.SubElement(root, ns_fx + "PROCESSING-INFORMATION", nsmap={"ho": ho})
    unit_spec = create_sub_element_ho(proc_info, "UNIT-SPEC")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = frame.name + "." + signal.name
            unit = create_sub_element_ho(unit_spec, "UNIT")
            unit.set("ID", "UNIT_" + signal_id)
            create_sub_element_ho(unit, "SHORT-NAME", signal.name)
            create_sub_element_ho(unit, "DISPLAY-NAME", signal.unit)

    codings = create_sub_element_fx(proc_info, "CODINGS")
    for frame in db.frames:
        for signal in frame.signals:
            signal_id = frame.name + "." + signal.name
            coding = create_sub_element_fx(codings, "CODING")
            coding.set("ID", "CODING_" + signal_id)
            create_short_name_desc(
                coding,
                "CODING_" +
                signal_id,
                "Coding for " +
                signal_id)
                
            coded = create_sub_element_ho(coding, "CODED-TYPE")
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
