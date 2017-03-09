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
# this script exports fibex-files from a canmatrix-object
# gibex-files are the network-matrix-definitions; Canmatrix exports CAN
# only (fibex: Field Bus Exchange Format //
# https://de.wikipedia.org/wiki/Field_Bus_Exchange_Format)

from __future__ import absolute_import
from builtins import *
from lxml import etree

from .canmatrix import *
import os.path

fx = "http://www.asam.net/xml/fbx"
ho = "http://www.asam.net/xml"
can = "http://www.asam.net/xml/fbx/can"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
ns_ho = "{%s}" % ho
ns_fx = "{%s}" % fx
ns_can = "{%s}" % can
ns_xsi = "{%s}" % xsi


extension = "xml"


def createShortNameDesc(parent, shortname, desc):
    ShortName = etree.SubElement(parent, ns_ho + "SHORT-NAME")
    ShortName.text = shortname
    Desc = etree.SubElement(parent, ns_ho + "DESC")
    Desc.text = desc


def createSubElementFx(parent, elementName, elementText=None):
    new = etree.SubElement(parent, ns_fx + elementName)
    if elementText is not None:
        new.text = elementText
    return new


def createSubElementHo(parent, elementName, elementText=None):
    new = etree.SubElement(parent, ns_ho + elementName)
    if elementText is not None:
        new.text = elementText
    return new


def dump(db, f, **options):
    nsmap = {"fx": fx, "ho": ho, "can": can, "xsi": xsi}
    root = etree.Element(ns_fx + "FIBEX", nsmap=nsmap)
    root.attrib[
        '{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://www.asam.net/xml/fbx ..\\..\\xml_schema\\fibex.xsd http://www.asam.net/xml/fbx/can  ..\\..\\xml_schema\\fibex4can.xsd'

    #
    # PROJECT
    #
    project = createSubElementFx(root, "PROJECT")
    project.set('ID', 'canmatrixExport')
    createShortNameDesc(project, "CAN", "Canmatrix Export")

    #
    # ELEMENTS
    #
    elements = createSubElementFx(root, "ELEMENTS")

    #
    # CLUSTERS
    #
    clusters = createSubElementFx(elements, "CLUSTERS")
    cluster = etree.SubElement(clusters, ns_fx + "CLUSTER")
    cluster.set('ID', 'canCluster1')
    createShortNameDesc(cluster, "clusterShort", "clusterDesc")
    createSubElementFx(cluster, "SPEED", "500")
    createSubElementFx(cluster, "IS-HIGH-LOW-BIT-ORDER", "false")
    createSubElementFx(cluster, "BIT-COUNTING-POLICY", "MONOTONE")
    protocol = createSubElementFx(cluster, "PROTOCOL", "CAN")
    protocol.attrib['{{{pre}}}type'.format(pre=xsi)] = "can:PROTOCOL-TYPE"
    createSubElementFx(cluster, "PROTOCOL-VERSION", "20")
    channelRefs = createSubElementFx(cluster, "CHANNEL-REFS")
    # for each channel
    channelRef = createSubElementFx(channelRefs, "CHANNEL-REF")
    channelRef.set("ID-REF", "CANCHANNEL01")

    #
    # CHANNELS
    #
    channels = createSubElementFx(elements, "CHANNELS")
    channel = createSubElementFx(channels, "CHANNEL")
    # for each channel
    createShortNameDesc(channel, "CANCHANNEL01", "Can Channel Description")
    frameTriggerings = createSubElementFx(channel, "FRAME-TRIGGERINGS")
    for frame in db.frames:
        frameTriggering = createSubElementFx(
            frameTriggerings, "FRAME-TRIGGERING")
        frameTriggering.set("ID", "FT_" + frame.name)
        identifier = createSubElementFx(frameTriggering, "IDENTIFIER")
        createSubElementFx(identifier, "IDENTIFIER-VALUE", str(frame.id))
        frameRef = createSubElementFx(frameTriggering, "FRAME-REF")
        frameRef.set("ID-REF", "FRAME_" + frame.name)

    #
    # ECUS
    #
    ecus = createSubElementFx(elements, "ECUS")
    for bu in db.boardUnits:
        ecu = createSubElementFx(ecus, "ECU")
        ecu.set("ID", bu.name)
        createShortNameDesc(ecu, bu.name, bu.comment)
        functionRefs = createSubElementFx(ecu, "FUNCTION-REFS")
        funcRef = createSubElementFx(functionRefs, "FUNCTION-REF")
        funcRef.set("ID-REF", "FCT_" + bu.name)
        # ignore CONTROLERS/CONTROLER

    #
    # PDUS
    #
    pdus = createSubElementFx(elements, "PDUS")
    for frame in db.frames:
        pdu = createSubElementFx(pdus, "PDU")
        pdu.set("ID", "PDU_" + frame.name)
        createShortNameDesc(pdu, "PDU_" + frame.name, frame.comment)
        createSubElementFx(pdu, "BYTE-LENGTH", str(frame.size))  # DLC
        createSubElementFx(pdu, "PDU-TYPE", "APPLICATION")
        signalInstances = createSubElementFx(pdu, "SIGNAL-INSTANCES")
        for signal in frame.signals:
            signalInstance = createSubElementFx(
                signalInstances, "SIGNAL-INSTANCE")
            signalInstance.set("ID", "PDUINST_" + signal.name)
            # startBit: TODO - find out correct BYTEORDER ...
            createSubElementFx(signalInstance, "BIT-POSITION",
                               str(signal._startbit))
            if signal.is_little_endian:
                createSubElementFx(
                    signalInstance,
                    "IS-HIGH-LOW-BYTE-ORDER",
                    "false")  # true:big endian; false:littele endian
            else:
                createSubElementFx(
                    signalInstance, "IS-HIGH-LOW-BYTE-ORDER", "true")
            signalRef = createSubElementFx(signalInstance, "SIGNAL-REF")
            signalRef.set("ID-REF", signal.name)

    # FRAMES
    #
    frames = createSubElementFx(elements, "FRAMES")
    for frame in db.frames:
        frameEle = createSubElementFx(frames, "FRAME")
        frameEle.set("ID", "FRAME_" + frame.name)
        createShortNameDesc(frameEle, "FRAME_" + frame.name, frame.comment)
        createSubElementFx(frameEle, "BYTE-LENGTH", str(frame.size))  # DLC
        createSubElementFx(frameEle, "PDU-TYPE", "APPLICATION")
        pduInstances = createSubElementFx(frameEle, "PDU-INSTANCES")
        pduInstance = createSubElementFx(pduInstances, "PDU-INSTANCE")
        pduInstance.set("ID", "PDUINSTANCE_" + frame.name)
        pduref = createSubElementFx(pduInstance, "PDU-REF")
        pduref.set("ID-REF", "PDU_" + frame.name)
        createSubElementFx(pduInstance, "BIT-POSITION", "0")
        createSubElementFx(pduInstance, "IS-HIGH-LOW-BYTE-ORDER", "false")

    #
    # FUNCTIONS
    #
    functions = createSubElementFx(elements, "FUNCTIONS")
    for bu in db.boardUnits:
        function = createSubElementFx(functions, "FUNCTION")
        function.set("ID", "FCT_" + bu.name)
        createShortNameDesc(function, "FCT_" + bu.name, bu.comment)
        inputPorts = createSubElementFx(function, "INPUT-PORTS")
        for frame in db.frames:
            for signal in frame.signals:
                if bu.name in signal.receiver:
                    inputPort = createSubElementFx(inputPorts, "INPUT-PORT")
                    inputPort.set("ID", "INP_" + signal.name)
                    desc = etree.SubElement(inputPort, ns_ho + "DESC")
                    desc.text = signal.comment
                    signalRef = createSubElementFx(inputPort, "SIGNAL-REF")
                    signalRef.set("ID-REF", "SIG_" + signal.name)

        for frame in db.frames:
            if bu.name in frame.transmitter:
                for signal in frame.signals:
                    outputPort = createSubElementFx(inputPorts, "OUTPUT-PORT")
                    outputPort.set("ID", "OUTP_" + signal.name)
                    desc = etree.SubElement(outputPort, ns_ho + "DESC")
                    desc.text = "signalcomment"
                    signalRef = createSubElementFx(outputPort, "SIGNAL-REF")
                    signalRef.set("ID-REF", "SIG_" + signal.name)

    #
    # SIGNALS
    #
    for frame in db.frames:
        signals = createSubElementFx(elements, "SIGNALS")
        for signal in frame.signals:
            signalEle = createSubElementFx(signals, "SIGNAL")
            signalEle.set("ID", "SIG_" + signal.name)
            createShortNameDesc(signalEle, signal.name, signal.comment)
            codingRef = createSubElementFx(signalEle, "CODING-REF")
            codingRef.set("ID-REF", "CODING_" + signal.name)

    #
    # PROCESSING-INFORMATION
    #
    procInfo = etree.SubElement(elements, ns_fx +
                                "PROCESSING-INFORMATION", nsmap={"ho": ho})
    unitSpec = createSubElementHo(procInfo, "UNIT-SPEC")
    for frame in db.frames:
        for signal in frame.signals:
            unit = createSubElementHo(unitSpec, "UNIT")
            unit.set("ID", "UNIT_" + signal.name)
            createSubElementHo(unit, "SHORT-NAME", signal.name)
            createSubElementHo(unit, "DISPLAY-NAME", signal.unit)

    codings = createSubElementFx(procInfo, "CODINGS")
    for frame in db.frames:
        for signal in frame.signals:
            coding = createSubElementFx(codings, "CODING")
            coding.set("ID", "CODING_" + signal.name)
            createShortNameDesc(
                coding,
                "CODING_" +
                signal.name,
                "Coding for " +
                signal.name)
            # ignore CODE-TYPE
            compumethods = createSubElementHo(coding, "COMPU-METHODS")
            compumethod = createSubElementHo(compumethods, "COMPU-METHOD")
            createSubElementHo(
                compumethod,
                "SHORT-NAME",
                "COMPUMETHOD_" +
                signal.name)
            createSubElementHo(compumethod, "CATEGORY", "LINEAR")
            unitRef = createSubElementHo(compumethod, "UNIT-REF")
            unitRef.set("ID-REF", "UNIT_" + signal.name)
            compuInternalToPhys = createSubElementHo(
                compumethod, "COMPU-INTERNAL-TO-PHYS")
            compuscales = createSubElementHo(
                compuInternalToPhys, "COMPU-SCALES")
            compuscale = createSubElementHo(compuscales, "COMPU-SCALE")
            lowerLimit = createSubElementHo(
                compuscale, "LOWER-LIMIT", str(signal.min))  # Min
            lowerLimit.set("INTERVAL-TYPE", "CLOSED")
            upperLimit = createSubElementHo(
                compuscale, "UPPER-LIMIT", str(signal.max))  # Max
            upperLimit.set("INTERVAL-TYPE", "CLOSED")

            compuRationalCoeffs = createSubElementHo(
                compuscale, "COMPU-RATIONAL-COEFFS")
            compuNumerator = createSubElementHo(
                compuRationalCoeffs, "COMPU-NUMERATOR")
            createSubElementHo(
                compuNumerator, "V", str(
                    signal.offset))  # offset
            createSubElementHo(
                compuNumerator, "V", str(
                    signal.factor))  # factor
            compuDenomiator = createSubElementHo(
                compuRationalCoeffs, "COMPU-DENOMINATOR")
            createSubElementHo(compuDenomiator, "V", "1")  # nenner
            #defaultValue = createSubElementHo(compuInternalToPhys,"COMPU-DEFAULT-VALUE")

    #
    # REQUIREMENTS
    #
    #requirements = createSubElementFx(elements,  "REQUIREMENTS")

    f.write(etree.tostring(root, pretty_print=True))
