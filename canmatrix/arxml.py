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


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import logging
logger = logging.getLogger('root')

import math
import os

from builtins import *
from lxml import etree

from .canmatrix import *
from .autosarhelper import *

clusterExporter = 1
clusterImporter = 1


def createSubElement(parent, elementName, strName=None):
    sn = etree.SubElement(parent, elementName)
    if strName is not None:
        sn.text = str(strName)
    return sn


def dump(dbs, f, **options):
    if 'arVersion' in options:
        arVersion = options["arVersion"]
    else:
        arVersion = "3.2.3"

    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                for rec in signal.receiver:
                    if rec.strip() not in frame.receiver:
                        frame.receiver.append(rec.strip())

    if arVersion[0] == "3":
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: 'http://autosar.org/' + arVersion,
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/' + arVersion + ' AUTOSAR_' + arVersion.replace('.', '') + '.xsd'
        toplevelPackages = createSubElement(root, 'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: "http://autosar.org/schema/r4.0",
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/schema/r4.0 AUTOSAR_' + arVersion.replace('.', '-') + '.xsd'
        toplevelPackages = createSubElement(root, 'AR-PACKAGES')

    #
    # AR-PACKAGE Cluster
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Cluster')
    elements = createSubElement(arPackage, 'ELEMENTS')

    for name in dbs:
        db = dbs[name]
#        if len(name) == 0:
#            (path, ext) = os.path.splitext(filename)
#            busName = path
#        else:
        if len(name) > 0:
            busName = name
        else:
            busName = "CAN"

        cancluster = createSubElement(elements, 'CAN-CLUSTER')
        createSubElement(cancluster, 'SHORT-NAME', busName)
        if arVersion[0] == "3":
         #       createSubElement(cancluster, 'SPEED', '50000')
            physicalChannels = createSubElement(
                cancluster, 'PHYSICAL-CHANNELS')
            physicalChannel = createSubElement(
                physicalChannels, 'PHYSICAL-CHANNEL')
            createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
            frameTriggering = createSubElement(
                physicalChannel, 'FRAME-TRIGGERINGSS')
        else:
            canClusterVaraints = createSubElement(
                cancluster, 'CAN-CLUSTER-VARIANTS')
            canClusterConditional = createSubElement(
                canClusterVaraints, 'CAN-CLUSTER-CONDITIONAL')
            physicalChannels = createSubElement(
                canClusterConditional, 'PHYSICAL-CHANNELS')
            physicalChannel = createSubElement(
                physicalChannels, 'CAN-PHYSICAL-CHANNEL')
            createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
            frameTriggering = createSubElement(
                physicalChannel, 'FRAME-TRIGGERINGS')
        for frame in db.frames:
            canFrameTriggering = createSubElement(
                frameTriggering, 'CAN-FRAME-TRIGGERING')
            createSubElement(canFrameTriggering, 'SHORT-NAME', frame.name)
            framePortRefs = createSubElement(
                canFrameTriggering, 'FRAME-PORT-REFS')
            for transmitter in frame.transmitter:
                framePortRef = createSubElement(
                    framePortRefs, 'FRAME-PORT-REF')
                framePortRef.set('DEST', 'FRAME-PORT')
                framePortRef.text = "/ECU/" + transmitter + \
                    "/CN_" + transmitter + "/" + frame.name
            for rec in frame.receiver:
                framePortRef = createSubElement(
                    framePortRefs, 'FRAME-PORT-REF')
                framePortRef.set('DEST', 'FRAME-PORT')
                framePortRef.text = "/ECU/" + rec + "/CN_" + rec + "/" + frame.name
            frameRef = createSubElement(canFrameTriggering, 'FRAME-REF')
            if arVersion[0] == "3":
                frameRef.set('DEST', 'FRAME')
                frameRef.text = "/Frame/FRAME_" + frame.name
                pduTriggeringRefs = createSubElement(
                    canFrameTriggering, 'I-PDU-TRIGGERING-REFS')
                pduTriggeringRef = createSubElement(
                    pduTriggeringRefs, 'I-PDU-TRIGGERING-REF')
                pduTriggeringRef.set('DEST', 'I-PDU-TRIGGERING')
            else:
                frameRef.set('DEST', 'CAN-FRAME')
                frameRef.text = "/CanFrame/FRAME_" + frame.name
                pduTriggering = createSubElement(
                    canFrameTriggering, 'PDU-TRIGGERINGS')
                pduTriggeringRefConditional = createSubElement(
                    pduTriggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
                pduTriggeringRef = createSubElement(
                    pduTriggeringRefConditional, 'PDU-TRIGGERING-REF')
                pduTriggeringRef.set('DEST', 'PDU-TRIGGERING')

            if frame.extended == 0:
                createSubElement(
                    canFrameTriggering,
                    'CAN-ADDRESSING-MODE',
                    'STANDARD')
            else:
                createSubElement(
                    canFrameTriggering,
                    'CAN-ADDRESSING-MODE',
                    'EXTENDED')
            createSubElement(canFrameTriggering, 'IDENTIFIER', str(frame.id))

            pduTriggeringRef.text = "/Cluster/CAN/IPDUTRIGG_" + frame.name

        if arVersion[0] == "3":
            ipduTriggerings = createSubElement(
                physicalChannel, 'I-PDU-TRIGGERINGS')
            for frame in db.frames:
                ipduTriggering = createSubElement(
                    ipduTriggerings, 'I-PDU-TRIGGERING')
                createSubElement(
                    ipduTriggering,
                    'SHORT-NAME',
                    "IPDUTRIGG_" +
                    frame.name)
                ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
                ipduRef.set('DEST', 'SIGNAL-I-PDU')
                ipduRef.text = "/PDU/PDU_" + frame.name
            isignalTriggerings = createSubElement(
                physicalChannel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                for signal in frame.signals:
                    isignalTriggering = createSubElement(
                        isignalTriggerings, 'I-SIGNAL-TRIGGERING')
                    createSubElement(isignalTriggering,
                                     'SHORT-NAME', signal.name)
                    iSignalPortRefs = createSubElement(
                        isignalTriggering, 'I-SIGNAL-PORT-REFS')

                    for receiver in signal.receiver:
                        iSignalPortRef = createSubElement(
                            iSignalPortRefs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/' +
                            receiver +
                            '/CN_' +
                            receiver +
                            '/' +
                            signal.name)
                        iSignalPortRef.set('DEST', 'SIGNAL-PORT')

                    isignalRef = createSubElement(
                        isignalTriggering, 'SIGNAL-REF')
                    isignalRef.set('DEST', 'I-SIGNAL')
                    isignalRef.text = "/ISignal/" + signal.name
        else:
            isignalTriggerings = createSubElement(
                physicalChannel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                for signal in frame.signals:
                    isignalTriggering = createSubElement(
                        isignalTriggerings, 'I-SIGNAL-TRIGGERING')
                    createSubElement(isignalTriggering,
                                     'SHORT-NAME', signal.name)
                    iSignalPortRefs = createSubElement(
                        isignalTriggering, 'I-SIGNAL-PORT-REFS')
                    for receiver in signal.receiver:
                        iSignalPortRef = createSubElement(
                            iSignalPortRefs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/' +
                            receiver +
                            '/CN_' +
                            receiver +
                            '/' +
                            signal.name)
                        iSignalPortRef.set('DEST', 'I-SIGNAL-PORT')

                    isignalRef = createSubElement(
                        isignalTriggering, 'I-SIGNAL-REF')
                    isignalRef.set('DEST', 'I-SIGNAL')
                    isignalRef.text = "/ISignal/" + signal.name
            ipduTriggerings = createSubElement(
                physicalChannel, 'PDU-TRIGGERINGS')
            for frame in db.frames:
                ipduTriggering = createSubElement(
                    ipduTriggerings, 'PDU-TRIGGERING')
                createSubElement(
                    ipduTriggering,
                    'SHORT-NAME',
                    "IPDUTRIGG_" +
                    frame.name)
                # missing: I-PDU-PORT-REFS
                ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
                ipduRef.set('DEST', 'I-SIGNAL-I-PDU')
                ipduRef.text = "/PDU/PDU_" + frame.name
                # missing: I-SIGNAL-TRIGGERINGS

# TODO
#        ipduTriggerings = createSubElement(physicalChannel, 'PDU-TRIGGERINGS')
#        for frame in db.frames:
#            ipduTriggering = createSubElement(ipduTriggerings, 'PDU-TRIGGERING')
#            createSubElement(ipduTriggering, 'SHORT-NAME', "PDUTRIGG_" + frame.name)
#            ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
#            ipduRef.set('DEST','SIGNAL-I-PDU')
#            ipduRef.text = "/PDU/PDU_" + frame.name

    #
    # AR-PACKAGE FRAME
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    if arVersion[0] == "3":
        createSubElement(arPackage, 'SHORT-NAME', 'Frame')
    else:
        createSubElement(arPackage, 'SHORT-NAME', 'CanFrame')

    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        # TODO: reused frames will be paced multiple times in file
        for frame in db.frames:
            if arVersion[0] == "3":
                frameEle = createSubElement(elements, 'FRAME')
            else:
                frameEle = createSubElement(elements, 'CAN-FRAME')
            createSubElement(frameEle, 'SHORT-NAME', "FRAME_" + frame.name)
            if frame.comment:
                desc = createSubElement(frameEle, 'DESC')
                l2 = createSubElement(desc, 'L-2')
                l2.set("L", "FOR-ALL")
                l2.text = frame.comment
            createSubElement(frameEle, 'FRAME-LENGTH', "%d" % frame.size)
            pdumappings = createSubElement(frameEle, 'PDU-TO-FRAME-MAPPINGS')
            pdumapping = createSubElement(pdumappings, 'PDU-TO-FRAME-MAPPING')
            createSubElement(pdumapping, 'SHORT-NAME', frame.name)
            createSubElement(
                pdumapping,
                'PACKING-BYTE-ORDER',
                "MOST-SIGNIFICANT-BYTE-LAST")
            pduRef = createSubElement(pdumapping, 'PDU-REF')
            createSubElement(pdumapping, 'START-POSITION', '0')
            pduRef.text = "/PDU/PDU_" + frame.name
            if arVersion[0] == "3":
                pduRef.set('DEST', 'SIGNAL-I-PDU')
            else:
                pduRef.set('DEST', 'I-SIGNAL-I-PDU')

    #
    # AR-PACKAGE PDU
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'PDU')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if arVersion[0] == "3":
                signalIpdu = createSubElement(elements, 'SIGNAL-I-PDU')
                createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame.name)
                createSubElement(signalIpdu, 'LENGTH', "%d" %
                                 int(frame.size * 8))
            else:
                signalIpdu = createSubElement(elements, 'I-SIGNAL-I-PDU')
                createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame.name)
                createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame.size))

            # I-PDU-TIMING-SPECIFICATION
            if arVersion[0] == "3":
                signalToPduMappings = createSubElement(
                    signalIpdu, 'SIGNAL-TO-PDU-MAPPINGS')
            else:
                signalToPduMappings = createSubElement(
                    signalIpdu, 'I-SIGNAL-TO-PDU-MAPPINGS')

            for signal in frame.signals:
                signalToPduMapping = createSubElement(
                    signalToPduMappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                createSubElement(signalToPduMapping, 'SHORT-NAME', signal.name)

                if arVersion[0] == "3":
                    if signal.is_little_endian == 1:  # Intel
                        createSubElement(
                            signalToPduMapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        createSubElement(
                            signalToPduMapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                    signalRef = createSubElement(
                        signalToPduMapping, 'SIGNAL-REF')
                else:
                    signalRef = createSubElement(
                        signalToPduMapping, 'I-SIGNAL-REF')
                    if signal.is_little_endian == 1:  # Intel
                        createSubElement(
                            signalToPduMapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        createSubElement(
                            signalToPduMapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                signalRef.text = "/ISignal/" + signal.name
                signalRef.set('DEST', 'I-SIGNAL')

                createSubElement(signalToPduMapping, 'START-POSITION',
                                 str(signal.getStartbit(bitNumbering=1)))
                # missing: TRANSFER-PROPERTY: PENDING/...

            for group in frame.SignalGroups:
                signalToPduMapping = createSubElement(
                    signalToPduMappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                createSubElement(signalToPduMapping, 'SHORT-NAME', group.name)
                signalRef = createSubElement(signalToPduMapping, 'SIGNAL-REF')
                signalRef.text = "/ISignal/" + group.name
                signalRef.set('DEST', 'I-SIGNAL')
                # TODO: TRANSFER-PROPERTY: PENDING???

    #
    # AR-PACKAGE ISignal
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ISignal')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                signalEle = createSubElement(elements, 'I-SIGNAL')
                createSubElement(signalEle, 'SHORT-NAME', signal.name)
                if arVersion[0] == "4":
                    createSubElement(signalEle, 'LENGTH',
                                     str(signal.signalsize))

                    networkRepresentProps = createSubElement(
                        signalEle, 'NETWORK-REPRESENTATION-PROPS')
                    swDataDefPropsVariants = createSubElement(
                        networkRepresentProps, 'SW-DATA-DEF-PROPS-VARIANTS')
                    swDataDefPropsConditional = createSubElement(
                        swDataDefPropsVariants, 'SW-DATA-DEF-PROPS-CONDITIONAL')
                    compuMethodRef = createSubElement(
                        swDataDefPropsConditional,
                        'COMPU-METHOD-REF',
                        '/DataType/Semantics/' + signal.name)
                    compuMethodRef.set('DEST', 'COMPU-METHOD')
                    unitRef = createSubElement(
                        swDataDefPropsConditional,
                        'UNIT-REF',
                        '/DataType/Unit/' + signal.name)
                    unitRef.set('DEST', 'UNIT')

                sysSigRef = createSubElement(signalEle, 'SYSTEM-SIGNAL-REF')
                sysSigRef.text = "/Signal/" + signal.name

                sysSigRef.set('DEST', 'SYSTEM-SIGNAL')
            for group in frame.SignalGroups:
                signalEle = createSubElement(elements, 'I-SIGNAL')
                createSubElement(signalEle, 'SHORT-NAME', group.name)
                sysSigRef = createSubElement(signalEle, 'SYSTEM-SIGNAL-REF')
                sysSigRef.text = "/Signal/" + group.name
                sysSigRef.set('DEST', 'SYSTEM-SIGNAL-GROUP')

    #
    # AR-PACKAGE Signal
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Signal')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                signalEle = createSubElement(elements, 'SYSTEM-SIGNAL')
                createSubElement(signalEle, 'SHORT-NAME', signal.name)
                if signal.comment:
                    desc = createSubElement(signalEle, 'DESC')
                    l2 = createSubElement(desc, 'L-2')
                    l2.set("L", "FOR-ALL")
                    l2.text = signal.comment
                if arVersion[0] == "3":
                    dataTypeRef = createSubElement(signalEle, 'DATA-TYPE-REF')
                    dataTypeRef.set('DEST', 'INTEGER-TYPE')
                    dataTypeRef.text = "/DataType/" + signal.name
                    createSubElement(signalEle, 'LENGTH',
                                     str(signal.signalsize))
            for group in frame.SignalGroups:
                groupEle = createSubElement(elements, 'SYSTEM-SIGNAL-GROUP')
                createSubElement(signalEle, 'SHORT-NAME', group.name)
                if arVersion[0] == "3":
                    dataTypeRef.set('DEST', 'INTEGER-TYPE')
                sysSignalRefs = createSubElement(
                    groupEle, 'SYSTEM-SIGNAL-REFS')
                for member in group.signals:
                    memberEle = createSubElement(
                        sysSignalRefs, 'SYSTEM-SIGNAL-REF')
                    memberEle.set('DEST', 'SYSTEM-SIGNAL')
                    memberEle.text = "/Signal/" + member.name

#                       initValueRef = createSubElement(signalEle, 'INIT-VALUE-REF')
#                       initValueRef.set('DEST','INTEGER-LITERAL')
#                       initValueRef.text = "/CONSTANTS/" + signal.name

    #
    # AR-PACKAGE Datatype
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'DataType')
    elements = createSubElement(arPackage, 'ELEMENTS')

    if arVersion[0] == "3":
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                for signal in frame.signals:
                    intType = createSubElement(elements, 'INTEGER-TYPE')
                    createSubElement(intType, 'SHORT-NAME', signal.name)
                    swDataDefProps = createSubElement(
                        intType, 'SW-DATA-DEF-PROPS')
                    compuMethodRef = createSubElement(
                        swDataDefProps, 'COMPU-METHOD-REF')
                    compuMethodRef.set('DEST', 'COMPU-METHOD')
                    compuMethodRef.text = "/DataType/Semantics/" + signal.name
    else:
        # SW-BASE-TYPE missing
        pass
        # TODO

    if arVersion[0] == "3":
        subpackages = createSubElement(arPackage, 'SUB-PACKAGES')
    else:
        subpackages = createSubElement(arPackage, 'AR-PACKAGES')
    arPackage = createSubElement(subpackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Semantics')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                compuMethod = createSubElement(elements, 'COMPU-METHOD')
                createSubElement(compuMethod, 'SHORT-NAME', signal.name)
                # missing: UNIT-REF
                compuIntToPhys = createSubElement(
                    compuMethod, 'COMPU-INTERNAL-TO-PHYS')
                compuScales = createSubElement(compuIntToPhys, 'COMPU-SCALES')
                for value in sorted(signal.values, key=lambda x: int(x)):
                    compuScale = createSubElement(compuScales, 'COMPU-SCALE')
                    desc = createSubElement(compuScale, 'DESC')
                    l2 = createSubElement(desc, 'L-2')
                    l2.set('L', 'FOR-ALL')
                    l2.text = signal.values[value]
                    createSubElement(compuScale, 'LOWER-LIMIT', str(value))
                    createSubElement(compuScale, 'UPPER-LIMIT', str(value))
                    compuConst = createSubElement(compuScale, 'COMPU-CONST')
                    createSubElement(compuConst, 'VT', signal.values[value])
                else:
                    compuScale = createSubElement(compuScales, 'COMPU-SCALE')
    #                createSubElement(compuScale, 'LOWER-LIMIT', str(#TODO))
    #                createSubElement(compuScale, 'UPPER-LIMIT', str(#TODO))
                    compuRationslCoeff = createSubElement(
                        compuScale, 'COMPU-RATIONAL-COEFFS')
                    compuNumerator = createSubElement(
                        compuRationslCoeff, 'COMPU-NUMERATOR')
                    createSubElement(compuNumerator, 'V', "%g" % signal.offset)
                    createSubElement(compuNumerator, 'V', "%g" % signal.factor)
                    compuDenomiator = createSubElement(
                        compuRationslCoeff, 'COMPU-DENOMINATOR')
                    createSubElement(compuDenomiator, 'V', "1")

    arPackage = createSubElement(subpackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Unit')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                unit = createSubElement(elements, 'UNIT')
                createSubElement(unit, 'SHORT-NAME', signal.name)
                createSubElement(unit, 'DISPLAY-NAME', signal.unit)

    txIPduGroups = {}
    rxIPduGroups = {}

    #
    # AR-PACKAGE ECU
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ECU')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for ecu in db.boardUnits:
            ecuInstance = createSubElement(elements, 'ECU-INSTANCE')
            createSubElement(ecuInstance, 'SHORT-NAME', ecu.name)
            if ecu.comment:
                desc = createSubElement(ecuInstance, 'DESC')
                l2 = createSubElement(desc, 'L-2')
                l2.set('L', 'FOR-ALL')
                l2.text = ecu.comment

            if arVersion[0] == "3":
                assoIpduGroupRefs = createSubElement(
                    ecuInstance, 'ASSOCIATED-I-PDU-GROUP-REFS')
                connectors = createSubElement(ecuInstance, 'CONNECTORS')
                commConnector = createSubElement(
                    connectors, 'COMMUNICATION-CONNECTOR')
            else:
                assoIpduGroupRefs = createSubElement(
                    ecuInstance, 'ASSOCIATED-COM-I-PDU-GROUP-REFS')
                connectors = createSubElement(ecuInstance, 'CONNECTORS')
                commConnector = createSubElement(
                    connectors, 'CAN-COMMUNICATION-CONNECTOR')

            createSubElement(commConnector, 'SHORT-NAME', 'CN_' + ecu.name)
            ecuCommPortInstances = createSubElement(
                commConnector, 'ECU-COMM-PORT-INSTANCES')

            recTemp = None
            sendTemp = None

            for frame in db.frames:
                if ecu.name in frame.transmitter:
                    frameport = createSubElement(
                        ecuCommPortInstances, 'FRAME-PORT')
                    createSubElement(frameport, 'SHORT-NAME', frame.name)
                    createSubElement(
                        frameport, 'COMMUNICATION-DIRECTION', 'OUT')
                    sendTemp = 1
                    if ecu.name + "_Tx" not in txIPduGroups:
                        txIPduGroups[ecu.name + "_Tx"] = []
                    txIPduGroups[ecu.name + "_Tx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if arVersion[0] == "3":
                            signalPort = createSubElement(
                                ecuCommPortInstances, 'SIGNAL-PORT')
                        else:
                            signalPort = createSubElement(
                                ecuCommPortInstances, 'I-SIGNAL-PORT')

                        createSubElement(signalPort, 'SHORT-NAME', signal.name)
                        createSubElement(
                            signalPort, 'COMMUNICATION-DIRECTION', 'OUT')
                if ecu.name in frame.receiver:
                    frameport = createSubElement(
                        ecuCommPortInstances, 'FRAME-PORT')
                    createSubElement(frameport, 'SHORT-NAME', frame.name)
                    createSubElement(
                        frameport, 'COMMUNICATION-DIRECTION', 'IN')
                    recTemp = 1
                    if ecu.name + "_Tx" not in rxIPduGroups:
                        rxIPduGroups[ecu.name + "_Rx"] = []
                    rxIPduGroups[ecu.name + "_Rx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if ecu.name in signal.receiver:
                            if arVersion[0] == "3":
                                signalPort = createSubElement(
                                    ecuCommPortInstances, 'SIGNAL-PORT')
                            else:
                                signalPort = createSubElement(
                                    ecuCommPortInstances, 'I-SIGNAL-PORT')

                            createSubElement(
                                signalPort, 'SHORT-NAME', signal.name)
                            createSubElement(
                                signalPort, 'COMMUNICATION-DIRECTION', 'IN')

            if recTemp is not None:
                if arVersion[0] == "3":
                    assoIpduGroupRef = createSubElement(
                        assoIpduGroupRefs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    assoIpduGroupRef.set('DEST', "I-PDU-GROUP")
                else:
                    assoIpduGroupRef = createSubElement(
                        assoIpduGroupRefs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    assoIpduGroupRef.set('DEST', "I-SIGNAL-I-PDU-GROUP")

                assoIpduGroupRef.text = "/IPDUGroup/" + ecu.name + "_Rx"

            if sendTemp is not None:
                if arVersion[0] == "3":
                    assoIpduGroupRef = createSubElement(
                        assoIpduGroupRefs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    assoIpduGroupRef.set('DEST', "I-PDU-GROUP")
                else:
                    assoIpduGroupRef = createSubElement(
                        assoIpduGroupRefs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    assoIpduGroupRef.set('DEST', "I-SIGNAL-I-PDU-GROUP")
                assoIpduGroupRef.text = "/IPDUGroup/" + ecu.name + "_Tx"

    #
    # AR-PACKAGE IPDUGroup
    #
    arPackage = createSubElement(toplevelPackages, 'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'IPDUGroup')
    elements = createSubElement(arPackage, 'ELEMENTS')
    for pdugrp in txIPduGroups:
        if arVersion[0] == "3":
            ipduGrp = createSubElement(elements, 'I-PDU-GROUP')
        else:
            ipduGrp = createSubElement(elements, 'I-SIGNAL-I-PDU-GROUP')

        createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
        createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "OUT")

        if arVersion[0] == "3":
            ipduRefs = createSubElement(ipduGrp, 'I-PDU-REFS')
            for frame in txIPduGroups[pdugrp]:
                ipduRef = createSubElement(ipduRefs, 'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
        else:
            isignalipdus = createSubElement(ipduGrp, 'I-SIGNAL-I-PDUS')
            for frame in txIPduGroups[pdugrp]:
                isignalipdurefconditional = createSubElement(
                    isignalipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipduRef = createSubElement(
                    isignalipdurefconditional, 'I-SIGNAL-I-PDU-REF')
                ipduRef.set('DEST', "I-SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame

    if arVersion[0] == "3":
        for pdugrp in rxIPduGroups:
            ipduGrp = createSubElement(elements, 'I-PDU-GROUP')
            createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
            createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")

            ipduRefs = createSubElement(ipduGrp, 'I-PDU-REFS')
            for frame in rxIPduGroups[pdugrp]:
                ipduRef = createSubElement(ipduRefs, 'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
    else:
        for pdugrp in rxIPduGroups:
            ipduGrp = createSubElement(elements, 'I-SIGNAL-I-PDU-GROUP')
            createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
            createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")
            isignalipdus = createSubElement(ipduGrp, 'I-SIGNAL-I-PDUS')
            for frame in rxIPduGroups[pdugrp]:
                isignalipdurefconditional = createSubElement(
                    isignalipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipduRef = createSubElement(
                    isignalipdurefconditional, 'I-SIGNAL-I-PDU-REF')
                ipduRef.set('DEST', "I-SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame

    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True))

###################################
# read ARXML
###################################


class arTree(object):

    def __init__(self, name="", ref=None):
        self._name = name
        self._ref = ref
        self._array = []

    def new(self, name, child):
        temp = arTree(name, child)
        self._array.append(temp)
        return temp

    def getChild(self, path):
        for tem in self._array:
            if tem._name == path:
                return tem


def arParseTree(tag, ardict, namespace):
    for child in tag:
        name = child.find('./' + namespace + 'SHORT-NAME')
#               namel = child.find('./' + namespace + 'LONG-NAME')
        if name is not None and child is not None:
            arParseTree(child, ardict.new(name.text, child), namespace)
        if name is None and child is not None:
            arParseTree(child, ardict, namespace)
#
# some sort of X-Path in autosar-xml-files:
#


def arGetXchildren(root, path, arDict, ns):
    pathElements = path.split('/')
    ptr = root
    for element in pathElements[:-1]:
        ptr = arGetChild(ptr, element, arDict, ns)
    ptr = arGetChildren(ptr, pathElements[-1], arDict, ns)
    return ptr

#
# get path in tranlation-dictionary
#


def arGetPath(ardict, path):
    ptr = ardict
    for p in path.split('/'):
        if p.strip():
            if ptr is not None:
                ptr = ptr.getChild(p)
            else:
                return None
    if ptr is not None:
        return ptr._ref
    else:
        return None


def arGetChild(parent, tagname, arTranslationTable, namespace):
    #    logger.debug("getChild: " + tagname)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tagname)
    if ret is None:
        ret = parent.find('.//' + namespace + tagname + '-REF')
        if ret is not None:
            ret = arGetPath(arTranslationTable, ret.text)
    return ret


def arGetChildren(parent, tagname, arTranslationTable, namespace):
    if parent is None:
        return []
    ret = parent.findall('.//' + namespace + tagname)
    if ret.__len__() == 0:
        retlist = parent.findall('.//' + namespace + tagname + '-REF')
        rettemp = []
        for ret in retlist:
            rettemp.append(arGetPath(arTranslationTable, ret.text))
        ret = rettemp
    return ret


def arGetName(parent, ns):
    name = parent.find('./' + ns + 'SHORT-NAME')
    if name is not None:
        if name.text is not None:
            return name.text
    return ""


pduFrameMapping = {}
signalRxs = {}


def getSysSignals(syssignal, syssignalarray, Bo, Id, ns):
    members = []
    for signal in syssignalarray:
        members.append(arGetName(signal, ns))
    Bo.addSignalGroup(arGetName(syssignal, ns), 1, members)


def getSignals(signalarray, Bo, arDict, ns, multiplexId):
    GroupId = 1
    for signal in signalarray:
        values = {}
        motorolla = arGetChild(signal, "PACKING-BYTE-ORDER", arDict, ns)
        startBit = arGetChild(signal, "START-POSITION", arDict, ns)
        isignal = arGetChild(signal, "SIGNAL", arDict, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL", arDict, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL-GROUP", arDict, ns)
            if isignal is not None:
                isignalarray = arGetXchildren(isignal, "I-SIGNAL", arDict, ns)
                getSysSignals(isignal, isignalarray, Bo, GroupId, ns)
                GroupId = GroupId + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                Bo.name,
                arGetChild(
                    signal,
                    "SHORT-NAME",
                    arDict,
                    ns).text)
        syssignal = arGetChild(isignal, "SYSTEM-SIGNAL", arDict, ns)
        if syssignal is None:
            logger.debug(
                'Frame %s, signal %s has no systemsignal',
                isignal.tag,
                Bo.name)

        if "SYSTEM-SIGNAL-GROUP" in syssignal.tag:
            syssignalarray = arGetXchildren(
                syssignal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", arDict, ns)
            getSysSignals(syssignal, syssignalarray, Bo, GroupId, ns)
            GroupId = GroupId + 1
            continue

        length = arGetChild(isignal, "LENGTH", arDict, ns)
        if length is None:
            length = arGetChild(syssignal, "LENGTH", arDict, ns)
        name = arGetChild(syssignal, "SHORT-NAME", arDict, ns)

        unitElement = arGetChild(isignal, "UNIT", arDict, ns)
        displayName = arGetChild(unitElement, "DISPLAY-NAME", arDict, ns)
        if displayName is not None:
            Unit = displayName.text
        else:
            Unit = ""

        Min = None
        Max = None
        factor = 1.0
        offset = 0
        receiver = []

        signalDescription = getDesc(syssignal, arDict, ns)
        datatype = arGetChild(syssignal, "DATA-TYPE", arDict, ns)
        if datatype is None:  # AR4?
            print("no datatype reference")
        lower = arGetChild(datatype, "LOWER-LIMIT", arDict, ns)
        upper = arGetChild(datatype, "UPPER-LIMIT", arDict, ns)
        if lower is not None and upper is not None:
            Min = int(lower.text)
            Max = int(upper.text)

        datdefprops = arGetChild(datatype, "SW-DATA-DEF-PROPS", arDict, ns)

        compmethod = arGetChild(datdefprops, "COMPU-METHOD", arDict, ns)
        if compmethod is None:  # AR4
            compmethod = arGetChild(isignal, "COMPU-METHOD", arDict, ns)

        unit = arGetChild(compmethod, "UNIT", arDict, ns)
        if unit is not None:
            displayName = arGetChild(unit, "DISPLAY-NAME", arDict, ns)
            if displayName is not None:
                Unit = displayName.text
            else:
                longname = arGetChild(unit, "LONG-NAME", arDict, ns)
                l4 = arGetChild(longname, "L-4", arDict, ns)
                if l4 is not None:
                    Unit = l4.text

        compuscales = arGetXchildren(
            compmethod,
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE",
            arDict,
            ns)
        initvalue = arGetXchildren(syssignal, "INIT-VALUE/VALUE", arDict, ns)
        if initvalue is not None and initvalue.__len__() > 1:
            initvalue = initvalue[0]
        else:
            initvalue = None

        for compuscale in compuscales:
            ll = arGetChild(compuscale, "LOWER-LIMIT", arDict, ns)
            ul = arGetChild(compuscale, "UPPER-LIMIT", arDict, ns)
            sl = arGetChild(compuscale, "SHORT-LABEL", arDict, ns)
            if sl is None:
                desc = getDesc(compuscale, arDict, ns)
            else:
                desc = sl.text

            if ll is not None and desc is not None and int(
                    ul.text) == int(ll.text):
                values[ll.text] = desc

            scaleDesc = getDesc(compuscale, arDict, ns)
            rational = arGetChild(
                compuscale, "COMPU-RATIONAL-COEFFS", arDict, ns)
            if rational is not None:
                numerator = arGetChild(rational, "COMPU-NUMERATOR", arDict, ns)
                zaehler = arGetChildren(numerator, "V", arDict, ns)
                denominator = arGetChild(
                    rational, "COMPU-DENOMINATOR", arDict, ns)
                nenner = arGetChildren(denominator, "V", arDict, ns)

                factor = float(zaehler[1].text) / float(nenner[0].text)
                offset = float(zaehler[0].text)
            else:
                const = arGetChild(compuscale, "COMPU-CONST", arDict, ns)
                # value hinzufuegen
                if const is None:
                    logger.warn(
                        "unknown Compu-Method: " +
                        compmethod.get('UUID'))
        is_little_endian = False
        if motorolla.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False  # unsigned
        if name is None:
            logger.debug('no name for signal given')
        if startBit is None:
            logger.debug('no startBit for signal given')
        if length is None:
            logger.debug('no length for signal given')

        if startBit is not None:
            newSig = Signal(name.text,
                            startBit=startBit.text,
                            signalSize=length.text,
                            is_little_endian=is_little_endian,
                            is_signed=is_signed,
                            factor=factor,
                            offset=offset,
                            min=Min,
                            max=Max,
                            unit=Unit,
                            receiver=receiver,
                            multiplex=multiplexId,
                            comment=signalDescription)

            if newSig.is_little_endian == 0:
                # startbit of motorola coded signals are MSB in arxml
                newSig.setStartbit(int(startBit.text), bitNumbering=1)

            signalRxs[syssignal] = newSig

            basetype = arGetChild(datdefprops, "BASE-TYPE", arDict, ns)
            if basetype is not None:
                temp = arGetChild(basetype, "SHORT-NAME", arDict, ns)
                if temp is not None and "boolean" == temp.text:
                    newSig.addValues(1, "TRUE")
                    newSig.addValues(0, "FALSE")

            if initvalue is not None and initvalue.text is not None:
                if initvalue.text == "false":
                    initvalue.text = "0"
                elif initvalue.text == "true":
                    initvalue.text = "1"
                newSig._initValue = int(initvalue.text)
                newSig.addAttribute("GenSigStartValue", str(newSig._initValue))
            else:
                newSig._initValue = 0

            for key, value in list(values.items()):
                newSig.addValues(key, value)
            Bo.addSignal(newSig)


def getFrame(frameTriggering, arDict, multiplexTranslation, ns):
    extEle = arGetChild(frameTriggering, "CAN-ADDRESSING-MODE", arDict, ns)
    idele = arGetChild(frameTriggering, "IDENTIFIER", arDict, ns)
    frameR = arGetChild(frameTriggering, "FRAME", arDict, ns)

    sn = arGetChild(frameTriggering, "SHORT-NAME", arDict, ns)
    idNum = int(idele.text)

    if None != frameR:
        dlc = arGetChild(frameR, "FRAME-LENGTH", arDict, ns)
        pdumappings = arGetChild(frameR, "PDU-TO-FRAME-MAPPINGS", arDict, ns)
        pdumapping = arGetChild(
            pdumappings, "PDU-TO-FRAME-MAPPING", arDict, ns)
        pdu = arGetChild(pdumapping, "PDU", arDict, ns)  # SIGNAL-I-PDU
#        newFrame = Frame(idNum, arGetName(frameR, ns), int(dlc.text), None)
        pduFrameMapping[pdu] = arGetName(frameR, ns)

        newFrame = Frame(arGetName(frameR, ns),
                         Id=idNum,
                         dlc=int(dlc.text))
        comment = getDesc(frameR, arDict, ns)
        if comment is not None:
            newFrame.addComment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF" % (sn))
        ipduTriggeringRefs = arGetChild(
            frameTriggering, "I-PDU-TRIGGERING-REFS", arDict, ns)
        ipduTriggering = arGetChild(
            ipduTriggeringRefs, "I-PDU-TRIGGERING", arDict, ns)
        pdu = arGetChild(ipduTriggering, "I-PDU", arDict, ns)
        dlc = arGetChild(pdu, "LENGTH", arDict, ns)
#        newFrame = Frame(idNum, sn.text, int(int(dlc.text)/8), None)
        newFrame = Frame(sn.text,
                         Id=idNum,
                         dlc=int(dlc.text) / 8)

        if pdu is None:
            logger.error("ERROR: pdu")
        else:
            logger.debug(arGetName(pdu, ns))

    if "MULTIPLEXED-I-PDU" in pdu.tag:
        selectorByteOrder = arGetChild(
            pdu, "SELECTOR-FIELD-BYTE-ORDER", arDict, ns)
        selectorLen = arGetChild(pdu, "SELECTOR-FIELD-LENGTH", arDict, ns)
        selectorStart = arGetChild(
            pdu, "SELECTOR-FIELD-START-POSITION", arDict, ns)
        is_little_endian = False
        if selectorByteOrder.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False  # unsigned
        multiplexor = Signal("Multiplexor",
                             startBit=selectorStart.text,
                             signalSize=selectorLen.text,
                             is_little_endian=is_little_endian,
                             multiplex="Multiplexor")

        multiplexor._initValue = 0
        newFrame.addSignal(multiplexor)
        staticPart = arGetChild(pdu, "STATIC-PART", arDict, ns)
        ipdu = arGetChild(staticPart, "I-PDU", arDict, ns)
        if ipdu is not None:
            pdusigmappings = arGetChild(
                ipdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
            pdusigmapping = arGetChildren(
                pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
            getSignals(pdusigmapping, newFrame, arDict, ns, None)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)

        dynamicPart = arGetChild(pdu, "DYNAMIC-PART", arDict, ns)
#               segmentPositions = arGetChild(dynamicPart, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamicPartAlternatives = arGetChild(
            dynamicPart, "DYNAMIC-PART-ALTERNATIVES", arDict, ns)
        dynamicPartAlternativeList = arGetChildren(
            dynamicPartAlternatives, "DYNAMIC-PART-ALTERNATIVE", arDict, ns)
        for alternative in dynamicPartAlternativeList:
            selectorId = arGetChild(
                alternative, "SELECTOR-FIELD-CODE", arDict, ns)
            ipdu = arGetChild(alternative, "I-PDU", arDict, ns)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)
            if ipdu is not None:
                pdusigmappings = arGetChild(
                    ipdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
                pdusigmapping = arGetChildren(
                    pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                getSignals(
                    pdusigmapping,
                    newFrame,
                    arDict,
                    ns,
                    selectorId.text)

    if newFrame.comment is None:
        newFrame.addComment(getDesc(pdu, arDict, ns))

    if extEle is not None:
        if extEle.text == 'EXTENDED':
            newFrame.extended = 1

    timingSpec = arGetChild(pdu, "I-PDU-TIMING-SPECIFICATION", arDict, ns)
    cyclicTiming = arGetChild(timingSpec, "CYCLIC-TIMING", arDict, ns)
    repeatingTime = arGetChild(cyclicTiming, "REPEATING-TIME", arDict, ns)

    eventTiming = arGetChild(timingSpec, "EVENT-CONTROLLED-TIMING", arDict, ns)
    repeats = arGetChild(eventTiming, "NUMBER-OF-REPEATS", arDict, ns)
    minimumDelay = arGetChild(timingSpec, "MINIMUM-DELAY", arDict, ns)
    startingTime = arGetChild(timingSpec, "STARTING-TIME", arDict, ns)

    if cyclicTiming is not None and eventTiming is not None:
        newFrame.addAttribute("GenMsgSendType", "5")        # CycleAndSpontan
        if minimumDelay is not None:
            newFrame.addAttribute("GenMsgDelayTime", str(
                int(float(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.addAttribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclicTiming is not None:
        newFrame.addAttribute("GenMsgSendType", "0")  # CycleX
        if minimumDelay is not None:
            newFrame.addAttribute("GenMsgDelayTime", str(
                int(float(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.addAttribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        newFrame.addAttribute("GenMsgSendType", "1")  # Spontan
        if minimumDelay is not None:
            newFrame.addAttribute("GenMsgDelayTime", str(
                int(float(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.addAttribute("GenMsgNrOfRepetitions", repeats.text)

    if startingTime is not None:
        value = arGetChild(startingTime, "VALUE", arDict, ns)
        newFrame.addAttribute("GenMsgStartDelayTime",
                              str(int(float(value.text) * 1000)))

    value = arGetChild(repeatingTime, "VALUE", arDict, ns)
    if value is not None:
        newFrame.addAttribute("GenMsgCycleTime",
                              str(int(float(value.text) * 1000)))

#    pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if pdusigmappings is None or pdusigmappings.__len__() == 0:
#        logger.debug("DEBUG: Frame %s no SIGNAL-TO-PDU-MAPPINGS found" % (newFrame.name))
    pdusigmapping = arGetChildren(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
    if pdusigmapping is None or pdusigmapping.__len__() == 0:
        logger.debug(
            "DEBUG: Frame %s no I-SIGNAL-TO-I-PDU-MAPPING found" %
            (newFrame.name))
    getSignals(pdusigmapping, newFrame, arDict, ns, None)
    return newFrame


def getDesc(element, arDict, ns):
    desc = arGetChild(element, "DESC", arDict, ns)
    txt = arGetChild(desc, 'L-2[@L="DE"]', arDict, ns)
    if txt is None:
        txt = arGetChild(desc, 'L-2[@L="EN"]', arDict, ns)
    if txt is None:
        txt = arGetChild(desc, 'L-2', arDict, ns)
    if txt is not None:
        return txt.text
    else:
        return ""


def processEcu(ecu, db, arDict, multiplexTranslation, ns):
    connectors = arGetChild(ecu, "CONNECTORS", arDict, ns)
    diagAddress = arGetChild(ecu, "DIAGNOSTIC-ADDRESS", arDict, ns)
    diagResponse = arGetChild(ecu, "RESPONSE-ADDRESSS", arDict, ns)
    # TODO: use diagAddress for frame-classification
    commconnector = arGetChild(
        connectors,
        "COMMUNICATION-CONNECTOR",
        arDict,
        ns)
    if commconnector is None:
        commconnector = arGetChild(
            connectors, "CAN-COMMUNICATION-CONNECTOR", arDict, ns)
    frames = arGetXchildren(
        commconnector,
        "ECU-COMM-PORT-INSTANCES/FRAME-PORT",
        arDict,
        ns)
    nmAddress = arGetChild(commconnector, "NM-ADDRESS", arDict, ns)
    assocRefs = arGetChild(ecu, "ASSOCIATED-I-PDU-GROUP-REFS", arDict, ns)
    if assocRefs is not None:
        assoc = arGetChildren(assocRefs, "ASSOCIATED-I-PDU-GROUP", arDict, ns)
    else:  # AR4
        assocRefs = arGetChild(
            ecu, "ASSOCIATED-COM-I-PDU-GROUP-REFS", arDict, ns)
        assoc = arGetChildren(
            assocRefs,
            "ASSOCIATED-COM-I-PDU-GROUP",
            arDict,
            ns)

    inFrame = []
    outFrame = []

    # get direction of frames (is current ECU sender/receiver/...?)
    for ref in assoc:
        direction = arGetChild(ref, "COMMUNICATION-DIRECTION", arDict, ns)
        groupRefs = arGetChild(ref, "CONTAINED-I-PDU-GROUPS-REFS", arDict, ns)
        pdurefs = arGetChild(ref, "I-PDU-REFS", arDict, ns)
        if pdurefs is not None:  # AR3
           # local defined pdus
            pdus = arGetChildren(pdurefs, "I-PDU", arDict, ns)
            for pdu in pdus:
                if pdu in pduFrameMapping:
                    if direction.text == "IN":
                        inFrame.append(pduFrameMapping[pdu])
                    else:
                        outFrame.append(pduFrameMapping[pdu])
        else:  # AR4
            isigpdus = arGetChild(ref, "I-SIGNAL-I-PDUS", arDict, ns)
            isigconds = arGetChildren(
                isigpdus, "I-SIGNAL-I-PDU-REF-CONDITIONAL", arDict, ns)
            for isigcond in isigconds:
                pdus = arGetChildren(isigcond, "I-SIGNAL-I-PDU", arDict, ns)
                for pdu in pdus:
                    if pdu in pduFrameMapping:
                        if direction.text == "IN":
                            inFrame.append(pduFrameMapping[pdu])
                        else:
                            outFrame.append(pduFrameMapping[pdu])

        # grouped pdus
        group = arGetChildren(groupRefs, "CONTAINED-I-PDU-GROUPS", arDict, ns)
        for t in group:
            if direction is None:
                direction = arGetChild(
                    t, "COMMUNICATION-DIRECTION", arDict, ns)
            pdurefs = arGetChild(t, "I-PDU-REFS", arDict, ns)
            pdus = arGetChildren(pdurefs, "I-PDU", arDict, ns)
            for pdu in pdus:
                if direction.text == "IN":
                    inFrame.append(arGetName(pdu, ns))
                else:
                    outFrame.append(arGetName(pdu, ns))

        for out in outFrame:
            if out in multiplexTranslation:
                out = multiplexTranslation[out]
            frame = db.frameByName(out)
            if frame is not None:
                frame.addTransmitter(arGetName(ecu, ns))
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
    bu = BoardUnit(arGetName(ecu, ns))
    if nmAddress is not None:
        bu.addAttribute("NWM-Stationsadresse", nmAddress.text)
        bu.addAttribute("NWM-Knoten", "1")
    else:
        bu.addAttribute("NWM-Stationsadresse", "0")
        bu.addAttribute("NWM-Knoten", "0")
    return bu


def load(file, **options):
    pduFrameMapping = {}
    signalRxs = {}

    if 'arxmlIgnoreClusterInfo' in options:
        ignoreClusterInfo = options["arxmlIgnoreClusterInfo"]
    else:
        ignoreClusterInfo = False

    result = {}
    logger.debug("Read arxml ...")
    tree = etree.parse(file)

    root = tree.getroot()
    logger.debug(" Done\n")

    ns = "{" + tree.xpath('namespace-uri(.)') + "}"
    nsp = tree.xpath('namespace-uri(.)')

    topLevelPackages = root.find('./' + ns + 'TOP-LEVEL-PACKAGES')

    if None == topLevelPackages:
        # no "TOP-LEVEL-PACKAGES found, try root
        topLevelPackages = root

    logger.debug("Build arTree ...")
    arDict = arTree()
    arParseTree(topLevelPackages, arDict, ns)
    logger.debug(" Done\n")

    frames = root.findall('.//' + ns + 'FRAME')
    logger.debug("DEBUG %d frames in arxml..." % (frames.__len__()))
    canTriggers = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
    logger.debug(
        "DEBUG %d can-frame-triggering in arxml..." %
        (canTriggers.__len__()))

    sigpdumap = root.findall('.//' + ns + 'SIGNAL-TO-PDU-MAPPINGS')
    logger.debug(
        "DEBUG %d SIGNAL-TO-PDU-MAPPINGS in arxml..." %
        (sigpdumap.__len__()))

    sigIpdu = root.findall('.//' + ns + 'I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug(
        "DEBUG %d I-SIGNAL-TO-I-PDU-MAPPING in arxml..." %
        (sigIpdu.__len__()))

    if ignoreClusterInfo == True:
        ccs = {"ignoreClusterInfo"}
    else:
        ccs = root.findall('.//' + ns + 'CAN-CLUSTER')
    for cc in ccs:
        db = CanMatrix()
# Defines not jet imported...
        db.addBUDefines("NWM-Stationsadresse", 'HEX 0 63')
        db.addBUDefines("NWM-Knoten", 'ENUM  "nein","ja"')
        db.addFrameDefines("GenMsgCycleTime", 'INT 0 65535')
        db.addFrameDefines("GenMsgDelayTime", 'INT 0 65535')
        db.addFrameDefines("GenMsgNrOfRepetitions", 'INT 0 65535')
        db.addFrameDefines("GenMsgStartValue", 'STRING')
        db.addFrameDefines(
            "GenMsgSendType",
            'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
        db.addSignalDefines("GenSigStartValue", 'HEX 0 4294967295')

        if ignoreClusterInfo == True:
            canframetrig = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
            busname = ""
        else:
            speed = arGetChild(cc, "SPEED", arDict, ns)
            logger.debug("Busname: " + arGetName(cc, ns))
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            busname = arGetName(cc, ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            physicalChannels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")
            if physicalChannels is None:
                logger.error("Error - PHYSICAL-CHANNELS not found")

            nmLowerId = arGetChild(cc, "NM-LOWER-CAN-ID", arDict, ns)

            physicalChannel = arGetChild(
                physicalChannels, "PHYSICAL-CHANNEL", arDict, ns)
            if physicalChannel is None:
                physicalChannel = arGetChild(
                    physicalChannels, "CAN-PHYSICAL-CHANNEL", arDict, ns)
            if physicalChannel is None:
                logger.debug("Error - PHYSICAL-CHANNEL not found")
            canframetrig = arGetChildren(
                physicalChannel, "CAN-FRAME-TRIGGERING", arDict, ns)
            if canframetrig is None:
                logger.error("Error - CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug(
                    "%d frames found in arxml\n" %
                    (canframetrig.__len__()))

        multiplexTranslation = {}
        for frameTrig in canframetrig:
            db._fl.addFrame(
                getFrame(
                    frameTrig,
                    arDict,
                    multiplexTranslation,
                    ns))

        if ignoreClusterInfo == True:
            pass
            # no support for signal direction
        else:
            isignaltriggerings = arGetXchildren(
                physicalChannel, "I-SIGNAL-TRIGGERING", arDict, ns)
            for sigTrig in isignaltriggerings:
                test = arGetChild(sigTrig, 'SIGNAL-REF', arDict, ns)
                isignal = arGetChild(sigTrig, 'SIGNAL', arDict, ns)
                if isignal is None:
                    isignal = arGetChild(sigTrig, 'I-SIGNAL', arDict, ns)
                if isignal is None:
                    logger.debug("no isignal for %s" % arGetName(sigTrig, ns))
                    continue
                portRef = arGetChildren(sigTrig, "I-SIGNAL-PORT", arDict, ns)

                for port in portRef:
                    comDir = arGetChild(
                        port, "COMMUNICATION-DIRECTION", arDict, ns)
                    if comDir is not None and comDir.text == "IN":
                        sysSignal = arGetChild(
                            isignal, "SYSTEM-SIGNAL", arDict, ns)
                        ecuName = arGetName(
                            port.getparent().getparent().getparent().getparent(), ns)
                        # port points in ECU; probably more stable to go up
                        # from each ECU than to go down in XML...
                        if sysSignal in signalRxs:
                            if ecuName not in signalRxs[sysSignal].receiver:
                                signalRxs[sysSignal].receiver.append(ecuName)
    # find ECUs:
        nodes = root.findall('.//' + ns + 'ECU-INSTANCE')
        for node in nodes:
            bu = processEcu(node, db, arDict, multiplexTranslation, ns)
            desc = arGetChild(node, "DESC", arDict, ns)
            l2 = arGetChild(desc, "L-2", arDict, ns)
            if l2 is not None:
                bu.addComment(l2.text)

            db._BUs.add(bu)

        for bo in db.frames:
            frame = [0, 0, 0, 0, 0, 0, 0, 0]
            for sig in bo.signals:
                if sig._initValue != 0:
                    putSignalValueInFrame(
                        sig.getStartbit(
                            bitNumbering=1,
                            startLittle=True),
                        sig.signalsize,
                        sig.is_little_endian,
                        sig._initValue,
                        frame)
            hexStr = ""
            for i in range(bo.size):
                hexStr += "%02X" % frame[i]
            bo.addAttribute("GenMsgStartValue", hexStr)

        result[busname] = db
    return result
