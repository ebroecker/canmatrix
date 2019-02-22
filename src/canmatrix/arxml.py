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
import canmatrix.utils
import logging

from builtins import *
from lxml import etree

from .canmatrix import *

import decimal

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal


clusterExporter = 1
clusterImporter = 1


def createSubElement(parent, elementName, strName=None):
    sn = etree.SubElement(parent, elementName)
    if strName is not None:
        sn.text = str(strName)
    return sn

def getBaseTypeOfSignal(signal):
    if signal.is_float:
        if signal.signalsize > 32:
            createType = "double"
            size = 64
        else:
            createType = "single"
            size = 32
    else:
        if signal.signalsize > 32:
            if signal.is_signed:
                createType = "sint64"
            else:
                createType = "uint64"
            size = 64                            
        elif signal.signalsize > 16:
            if signal.is_signed:
                createType = "sint32"
            else:
                createType = "uint32"
            size = 32                            
        elif signal.signalsize > 8:
            if signal.is_signed:
                createType = "sint16"
            else:
                createType = "uint16"
            size = 16
        else:
            if signal.is_signed:
                createType = "sint8"
            else:
                createType = "uint8"
            size = 8
    return createType, size


def dump(dbs, f, **options):
    arVersion = options.get("arVersion", "3.2.3")

    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            for signal in frame.signals:
                for rec in signal.receiver:
                    if rec.strip() not in frame.receivers:
                        frame.receivers.append(rec.strip())

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
            if frame.is_complex_multiplexed:
                logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
                continue
            canFrameTriggering = createSubElement(
                frameTriggering, 'CAN-FRAME-TRIGGERING')
            createSubElement(canFrameTriggering, 'SHORT-NAME', frame.name)
            framePortRefs = createSubElement(
                canFrameTriggering, 'FRAME-PORT-REFS')
            for transmitter in frame.transmitters:
                framePortRef = createSubElement(
                    framePortRefs, 'FRAME-PORT-REF')
                framePortRef.set('DEST', 'FRAME-PORT')
                framePortRef.text = "/ECU/" + transmitter + \
                    "/CN_" + transmitter + "/" + frame.name
            for rec in frame.receivers:
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
                if frame.is_complex_multiplexed:
                    continue

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
                if frame.is_complex_multiplexed:
                    continue

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
                if frame.is_complex_multiplexed:
                    continue

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
                if frame.is_complex_multiplexed:
                    continue

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
            if frame.is_complex_multiplexed:
                continue

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
            if frame.is_complex_multiplexed:
                continue

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
                                 str(signal.get_startbit(bit_numbering=1)))
                # missing: TRANSFER-PROPERTY: PENDING/...

            for group in frame.signalGroups:
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
            if frame.is_complex_multiplexed:
                continue

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
                    
                    baseTypeRef = createSubElement(swDataDefPropsConditional, 'BASE-TYPE-REF')
                    baseTypeRef.set('DEST', 'SW-BASE-TYPE')
                    createType, size = getBaseTypeOfSignal(signal)
                    baseTypeRef.text = "/DataType/" + createType
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
            for group in frame.signalGroups:
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
            if frame.is_complex_multiplexed:
                continue

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
                    if signal.is_float:
                        dataTypeRef.set('DEST', 'REAL-TYPE')
                    else:
                        dataTypeRef.set('DEST', 'INTEGER-TYPE')
                    dataTypeRef.text = "/DataType/" + signal.name
                    createSubElement(signalEle, 'LENGTH',
                                     str(signal.size))
            for group in frame.signalGroups:
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
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    if signal.is_float:
                        typeEle = createSubElement(elements, 'REAL-TYPE')
                    else:
                        typeEle = createSubElement(elements, 'INTEGER-TYPE')
                    createSubElement(typeEle, 'SHORT-NAME', signal.name)
                    swDataDefProps = createSubElement(
                        typeEle, 'SW-DATA-DEF-PROPS')
                    if signal.is_float:
                        encoding = createSubElement(typeEle, 'ENCODING')                        
                        if signal.signalsize > 32:
                            encoding.text = "DOUBLE"
                        else:
                            encoding.text = "SINGLE"
                    compuMethodRef = createSubElement(
                        swDataDefProps, 'COMPU-METHOD-REF')
                    compuMethodRef.set('DEST', 'COMPU-METHOD')
                    compuMethodRef.text = "/DataType/Semantics/" + signal.name
    else:
        createdTypes = []
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    createType, size = getBaseTypeOfSignal(signal)
                    if createType not in createdTypes:
                        createdTypes.append(createType)
                        swBaseType = createSubElement(elements, 'SW-BASE-TYPE')
                        sname = createSubElement(swBaseType, 'SHORT-NAME')
                        sname.text = createType
                        cat = createSubElement(swBaseType, 'CATEGORY')
                        cat.text = "FIXED_LENGTH"
                        baseTypeSize = createSubElement(swBaseType, 'BASE-TYPE-SIZE')
                        baseTypeSize.text = str(size)
                        if signal.is_float:
                            enc = createSubElement(swBaseType, 'BASE-TYPE-ENCODING')
                            enc.text = "IEEE754"

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
            if frame.is_complex_multiplexed:
                continue

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
            if frame.is_complex_multiplexed:
                continue

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
        for ecu in db.ecus:
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
                if frame.is_complex_multiplexed:
                    continue

                if ecu.name in frame.transmitters:
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
                if ecu.name in frame.receivers:
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


def arPath2xPath(arPath, destElement=None):
    arPathElements = arPath.strip('/').split('/')
    xpath = "."

    for element in arPathElements[:-1]:
        xpath += "//A:SHORT-NAME[text()='" + element + "']/.."
    if destElement:
        xpath +=  "//A:" + destType + "/A:SHORT-NAME[text()='" + arPathElements[-1] + "']/.."
    else:
        xpath +=  "//A:SHORT-NAME[text()='" + arPathElements[-1] + "']/.."

    return xpath


ArCache = dict()

def getArPath(tree, arPath, namespaces):
    global ArCache
    namespaceMap = {'A': namespaces[1:-1]}
    baseARPath = arPath[:arPath.rfind('/')]
    if baseARPath in ArCache:
        baseElement = ArCache[baseARPath]
    else:
        xbasePath= arPath2xPath(baseARPath)
        baseElement = tree.xpath(xbasePath, namespaces=namespaceMap)[0]
        ArCache[baseARPath] = baseElement
    found = baseElement.xpath(".//A:SHORT-NAME[text()='" + arPath[arPath.rfind('/')+1:] + "']/..", namespaces=namespaceMap)[0]
    return found


def arGetPath(ardict, path):
    ptr = ardict
    for p in path.split('/'):
        if p.strip():
            if ptr is not None:
                try:
                    ptr = ptr.getChild(p)
                except:
                    return None
            else:
                return None
    if ptr is not None:
        return ptr._ref
    else:
        return None


def arGetChild(parent, tagname, xmlRoot, namespace):
    #    logger.debug("getChild: " + tagname)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tagname)
    if ret is None:
        ret = parent.find('.//' + namespace + tagname + '-REF')
        if ret is not None:
            if isinstance(xmlRoot, type(arTree())):
                ret = arGetPath(xmlRoot, ret.text)
            else:
                ret = getArPath(xmlRoot, ret.text, namespace)
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
    Bo.add_signal_group(arGetName(syssignal, ns), 1, members)


def decodeCompuMethod(compuMethod, arDict, ns, float_factory):
    values = {}
    factor = float_factory(1.0)
    offset = float_factory(0)
    unit = arGetChild(compuMethod, "UNIT", arDict, ns)
    const = None
    compuscales = arGetXchildren(compuMethod, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE", arDict, ns)
    for compuscale in compuscales:
        ll = arGetChild(compuscale, "LOWER-LIMIT", arDict, ns)
        ul = arGetChild(compuscale, "UPPER-LIMIT", arDict, ns)
        sl = arGetChild(compuscale, "SHORT-LABEL", arDict, ns)
        if sl is None:
            desc = getDesc(compuscale, arDict, ns)
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

        scaleDesc = getDesc(compuscale, arDict, ns)
        rational = arGetChild(compuscale, "COMPU-RATIONAL-COEFFS", arDict, ns)
        if rational is not None:
            numerator = arGetChild(rational, "COMPU-NUMERATOR", arDict, ns)
            zaehler = arGetChildren(numerator, "V", arDict, ns)
            denominator = arGetChild(rational, "COMPU-DENOMINATOR", arDict, ns)
            nenner = arGetChildren(denominator, "V", arDict, ns)

            factor = float_factory(zaehler[1].text) / float_factory(nenner[0].text)
            offset = float_factory(zaehler[0].text) / float_factory(nenner[0].text)
        else:
            const = arGetChild(compuscale, "COMPU-CONST", arDict, ns)
            # value hinzufuegen
            if const is None:
                logger.warn(
                    "unknown Compu-Method: at sourceline %d " % compuMethod.sourceline)
    return values, factor, offset, unit, const

def getSignals(signalarray, Bo, xmlRoot, ns, multiplexId, float_factory):
    global signalRxs
    GroupId = 1
    if signalarray is None:  # Empty signalarray - nothing to do
        return
    for signal in signalarray:
        compmethod = None
        motorolla = arGetChild(signal, "PACKING-BYTE-ORDER", xmlRoot, ns)
        startBit = arGetChild(signal, "START-POSITION", xmlRoot, ns)

        isignal = arGetChild(signal, "SIGNAL", xmlRoot, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL", xmlRoot, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL-GROUP", xmlRoot, ns)
            if isignal is not None:
                logger.debug("getSignals: found I-SIGNAL-GROUP ")

                isignalarray = arGetXchildren(isignal, "I-SIGNAL", xmlRoot, ns)
                getSysSignals(isignal, isignalarray, Bo, GroupId, ns)
                GroupId = GroupId + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                Bo.name,arGetChild(signal,"SHORT-NAME",xmlRoot,ns).text)

        baseType = arGetChild(isignal,"BASE-TYPE", xmlRoot, ns)
        sig_long_name = arGetChild(isignal, "LONG-NAME", xmlRoot, ns)
        if sig_long_name is not None:
            sig_long_name = arGetChild(sig_long_name, "L-4", xmlRoot, ns)
            if sig_long_name is not None:
                sig_long_name = sig_long_name.text
        syssignal = arGetChild(isignal, "SYSTEM-SIGNAL", xmlRoot, ns)
        if syssignal is None:
            logger.debug('Frame %s, signal %s has no systemsignal',isignal.tag,Bo.name)

        if "SYSTEM-SIGNAL-GROUP" in syssignal.tag:
            syssignalarray = arGetXchildren(syssignal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", xmlRoot, ns)
            getSysSignals(syssignal, syssignalarray, Bo, GroupId, ns)
            GroupId = GroupId + 1
            continue

        length = arGetChild(isignal, "LENGTH", xmlRoot, ns)
        if length is None:
            length = arGetChild(syssignal, "LENGTH", xmlRoot, ns)

        name = arGetChild(syssignal, "SHORT-NAME", xmlRoot, ns)
        unitElement = arGetChild(isignal, "UNIT", xmlRoot, ns)
        displayName = arGetChild(unitElement, "DISPLAY-NAME", xmlRoot, ns)
        if displayName is not None:
            Unit = displayName.text
        else:
            Unit = ""

        Min = None
        Max = None
        receiver = []

        signalDescription = getDesc(syssignal, xmlRoot, ns)

        datatype = arGetChild(syssignal, "DATA-TYPE", xmlRoot, ns)
        if datatype is None:  # AR4?
            dataConstr = arGetChild(isignal,"DATA-CONSTR", xmlRoot, ns)
            compmethod = arGetChild(isignal,"COMPU-METHOD", xmlRoot, ns)
            baseType  = arGetChild(isignal,"BASE-TYPE", xmlRoot, ns)
            lower = arGetChild(dataConstr, "LOWER-LIMIT", xmlRoot, ns)
            upper = arGetChild(dataConstr, "UPPER-LIMIT", xmlRoot, ns)
            encoding = None # TODO - find encoding in AR4
        else:
            lower = arGetChild(datatype, "LOWER-LIMIT", xmlRoot, ns)
            upper = arGetChild(datatype, "UPPER-LIMIT", xmlRoot, ns)
            encoding = arGetChild(datatype, "ENCODING", xmlRoot, ns)

        if encoding is not None and (encoding.text == "SINGLE" or encoding.text == "DOUBLE"):
            is_float = True
        else:
            is_float = False
        
        if lower is not None and upper is not None:
            Min = float_factory(lower.text)
            Max = float_factory(upper.text)

        datdefprops = arGetChild(datatype, "SW-DATA-DEF-PROPS", xmlRoot, ns)

        if compmethod is None:
            compmethod = arGetChild(datdefprops, "COMPU-METHOD", xmlRoot, ns)
        if compmethod is None:  # AR4
            compmethod = arGetChild(isignal, "COMPU-METHOD", xmlRoot, ns)
            baseType = arGetChild(isignal, "BASE-TYPE", xmlRoot, ns)
            encoding = arGetChild(baseType, "BASE-TYPE-ENCODING", xmlRoot, ns)
            if encoding is not None and encoding.text == "IEEE754":
                is_float = True
        if compmethod == None:
            logger.debug('No Compmethod found!! - try alternate scheme 1.')
            networkrep = arGetChild(isignal, "NETWORK-REPRESENTATION-PROPS", xmlRoot, ns)
            datdefpropsvar = arGetChild(networkrep, "SW-DATA-DEF-PROPS-VARIANTS", xmlRoot, ns)
            datdefpropscond = arGetChild(datdefpropsvar, "SW-DATA-DEF-PROPS-CONDITIONAL", xmlRoot ,ns)
            if datdefpropscond != None:
                try:
                    compmethod = arGetChild(datdefpropscond, "COMPU-METHOD", xmlRoot, ns)
                except:
                    logger.debug('No valid compu method found for this - check ARXML file!!')
                    compmethod = None
        #####################################################################################################
        # no found compu-method fuzzy search in systemsignal:
        #####################################################################################################
        if compmethod == None:
            logger.debug('No Compmethod found!! - fuzzy search in syssignal.')
            compmethod = arGetChild(syssignal, "COMPU-METHOD", xmlRoot, ns)

        # decode compuMethod:
        (values, factor, offset, unit, const) = decodeCompuMethod(compmethod, xmlRoot, ns, float_factory)

        if Min is not None:
            Min *= factor
            Min += offset
        if Max is not None:
            Max *= factor
            Max += offset

        if baseType is None:
            baseType = arGetChild(datdefprops, "BASE-TYPE", xmlRoot, ns)
        if baseType is not None:
            typeName = arGetName(baseType, ns)
            if typeName[0] == 'u':
                is_signed = False  # unsigned
            else:
                is_signed = True  # signed
        else:
            is_signed = True  # signed

        if unit is not None:
            longname = arGetChild(unit, "LONG-NAME", xmlRoot, ns)
        #####################################################################################################
        # Modification to support obtaining the Signals Unit by DISPLAY-NAME. 07June16
        #####################################################################################################
            try:
              displayname = arGetChild(unit, "DISPLAY-NAME", xmlRoot, ns)
            except:
              logger.debug('No Unit Display name found!! - using long name')
            if displayname is not None:
              Unit = displayname.text
            else:
              l4 = arGetChild(longname, "L-4", xmlRoot, ns)
              if l4 is not None:
                Unit = l4.text

        initvalue = arGetXchildren(syssignal, "INIT-VALUE/VALUE", xmlRoot, ns)

        if initvalue is None or initvalue.__len__() == 0:
            initvalue = arGetXchildren(isignal, "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE", xmlRoot, ns) ##AR4.2
        if initvalue is not None and initvalue.__len__() >= 1:
            initvalue = initvalue[0]
        else:
            initvalue = None

        is_little_endian = False
        if motorolla is not None:
            if motorolla.text == 'MOST-SIGNIFICANT-BYTE-LAST':
                is_little_endian = True
        else:
            logger.debug('no name byte order for signal' + name.text)

        if name is None:
            logger.debug('no name for signal given')
        if startBit is None:
            logger.debug('no startBit for signal given')
        if length is None:
            logger.debug('no length for signal given')

        if startBit is not None:
            newSig = Signal(name.text,
                            start_bit=int(startBit.text),
                            size=int(length.text),
                            is_little_endian=is_little_endian,
                            is_signed=is_signed,
                            factor=factor,
                            offset=offset,
                            unit=Unit,
                            receiver=receiver,
                            multiplex=multiplexId,
                            comment=signalDescription,
                            is_float=is_float)

            if Min is not None:
                Signal.min = Min
            if Max is not None:
                Signal.mex = Max

            if newSig.is_little_endian == 0:
                # startbit of motorola coded signals are MSB in arxml
                newSig.set_startbit(int(startBit.text), bitNumbering=1)

            # save signal, to determin receiver-ECUs for this signal later
            signalRxs[syssignal] = newSig

            if baseType is not None:
                temp = arGetChild(baseType, "SHORT-NAME", xmlRoot, ns)
                if temp is not None and "boolean" == temp.text:
                    newSig.add_values(1, "TRUE")
                    newSig.add_values(0, "FALSE")


            if initvalue is not None and initvalue.text is not None:
                initvalue.text = canmatrix.utils.guess_value(initvalue.text)
                newSig._initValue = int(initvalue.text)
                newSig.add_attribute("GenSigStartValue", str(newSig._initValue))
            else:
                newSig._initValue = 0

            for key, value in list(values.items()):
                newSig.add_values(key, value)
            if sig_long_name is not None:
                newSig.add_attribute("LongName", sig_long_name)
            Bo.add_signal(newSig)


def getFrame(frameTriggering, xmlRoot, multiplexTranslation, ns, float_factory):
    global pduFrameMapping
    extEle = arGetChild(frameTriggering, "CAN-ADDRESSING-MODE", xmlRoot, ns)
    idele = arGetChild(frameTriggering, "IDENTIFIER", xmlRoot, ns)
    frameR = arGetChild(frameTriggering, "FRAME", xmlRoot, ns)

    sn = arGetChild(frameTriggering, "SHORT-NAME", xmlRoot, ns)
    logger.debug("processing Frame: %s", sn.text)
    if idele is None:
        logger.info("found Frame %s without arbitration id %s", sn.text)
        return None
    idNum = int(idele.text)

    if None != frameR:
        dlc = arGetChild(frameR, "FRAME-LENGTH", xmlRoot, ns)
        pdumappings = arGetChild(frameR, "PDU-TO-FRAME-MAPPINGS", xmlRoot, ns)
        pdumapping = arGetChild(pdumappings, "PDU-TO-FRAME-MAPPING", xmlRoot, ns)
        pdu = arGetChild(pdumapping, "PDU", xmlRoot, ns)  # SIGNAL-I-PDU

        if pdu is not None and 'SECURED-I-PDU' in pdu.tag:
            logger.info("found secured pdu - no signal extraction possible: %s", arGetName(pdu,ns))

        pduFrameMapping[pdu] = arGetName(frameR, ns)

        newFrame = Frame(arGetName(frameR, ns), id=idNum, size=int(dlc.text))
        comment = getDesc(frameR, xmlRoot, ns)
        if comment is not None:
            newFrame.add_comment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF" % (sn))
        ipduTriggeringRefs = arGetChild(frameTriggering, "I-PDU-TRIGGERING-REFS", xmlRoot, ns)
        ipduTriggering = arGetChild(ipduTriggeringRefs, "I-PDU-TRIGGERING", xmlRoot, ns)
        pdu = arGetChild(ipduTriggering, "I-PDU", xmlRoot, ns)
        if pdu is None:
            pdu = arGetChild(ipduTriggering, "I-SIGNAL-I-PDU", xmlRoot, ns) ## AR4.2
        dlc = arGetChild(pdu, "LENGTH", xmlRoot, ns)
        newFrame = Frame(sn.text,id=idNum,dlc=int(dlc.text) / 8)

    if pdu is None:
        logger.error("ERROR: pdu")
    else:
        logger.debug(arGetName(pdu, ns))

    if pdu is not None and "MULTIPLEXED-I-PDU" in pdu.tag:
        selectorByteOrder = arGetChild(pdu, "SELECTOR-FIELD-BYTE-ORDER", xmlRoot, ns)
        selectorLen = arGetChild(pdu, "SELECTOR-FIELD-LENGTH", xmlRoot, ns)
        selectorStart = arGetChild(pdu, "SELECTOR-FIELD-START-POSITION", xmlRoot, ns)
        is_little_endian = False
        if selectorByteOrder.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False  # unsigned
        multiplexor = Signal("Multiplexor",start_bit=int(selectorStart.text),size=int(selectorLen.text),
                             is_little_endian=is_little_endian,multiplex="Multiplexor")

        multiplexor._initValue = 0
        newFrame.add_signal(multiplexor)
        staticPart = arGetChild(pdu, "STATIC-PART", xmlRoot, ns)
        ipdu = arGetChild(staticPart, "I-PDU", xmlRoot, ns)
        if ipdu is not None:
            pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
            pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)
            getSignals(pdusigmapping, newFrame, xmlRoot, ns, None, float_factory)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)

        dynamicPart = arGetChild(pdu, "DYNAMIC-PART", xmlRoot, ns)
#               segmentPositions = arGetChild(dynamicPart, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamicPartAlternatives = arGetChild(dynamicPart, "DYNAMIC-PART-ALTERNATIVES", xmlRoot, ns)
        dynamicPartAlternativeList = arGetChildren(dynamicPartAlternatives, "DYNAMIC-PART-ALTERNATIVE", xmlRoot, ns)
        for alternative in dynamicPartAlternativeList:
            selectorId = arGetChild(alternative, "SELECTOR-FIELD-CODE", xmlRoot, ns)
            ipdu = arGetChild(alternative, "I-PDU", xmlRoot, ns)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)
            if ipdu is not None:
                pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
                pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)
                getSignals(pdusigmapping,newFrame,xmlRoot,ns,selectorId.text, float_factory)

    if newFrame.comment is None:
        newFrame.add_comment(getDesc(pdu, xmlRoot, ns))

    if extEle is not None:
        if extEle.text == 'EXTENDED':
            newFrame.extended = 1

    timingSpec = arGetChild(pdu, "I-PDU-TIMING-SPECIFICATION", xmlRoot, ns)
    if timingSpec is None:
        timingSpec = arGetChild(pdu, "I-PDU-TIMING-SPECIFICATIONS", xmlRoot, ns)
    cyclicTiming = arGetChild(timingSpec, "CYCLIC-TIMING", xmlRoot, ns)
    repeatingTime = arGetChild(cyclicTiming, "REPEATING-TIME", xmlRoot, ns)

    eventTiming = arGetChild(timingSpec, "EVENT-CONTROLLED-TIMING", xmlRoot, ns)
    repeats = arGetChild(eventTiming, "NUMBER-OF-REPEATS", xmlRoot, ns)
    minimumDelay = arGetChild(timingSpec, "MINIMUM-DELAY", xmlRoot, ns)
    startingTime = arGetChild(timingSpec, "STARTING-TIME", xmlRoot, ns)

    timeOffset = arGetChild(cyclicTiming, "TIME-OFFSET", xmlRoot, ns)
    timePeriod = arGetChild(cyclicTiming, "TIME-PERIOD", xmlRoot, ns)

    if cyclicTiming is not None and eventTiming is not None:
        newFrame.add_attribute("GenMsgSendType", "cyclicAndSpontanX")        # CycleAndSpontan
        if minimumDelay is not None:
            newFrame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclicTiming is not None:
        newFrame.add_attribute("GenMsgSendType", "cyclicX")  # CycleX
        if minimumDelay is not None:
            newFrame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        newFrame.add_attribute("GenMsgSendType", "spontanX")  # Spontan
        if minimumDelay is not None:
            newFrame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            newFrame.add_attribute("GenMsgNrOfRepetitions", repeats.text)

    if startingTime is not None:
        value = arGetChild(startingTime, "VALUE", xmlRoot, ns)
        newFrame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))
    elif cyclicTiming is not None:
        value = arGetChild(timeOffset, "VALUE", xmlRoot, ns)
        if value is not None:
            newFrame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))

    value = arGetChild(repeatingTime, "VALUE", xmlRoot, ns)
    if value is not None:
        newFrame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))
    elif cyclicTiming is not None:
        value = arGetChild(timePeriod, "VALUE", xmlRoot, ns)
        if value is not None:
            newFrame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))


#    pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if pdusigmappings is None or pdusigmappings.__len__() == 0:
#        logger.debug("DEBUG: Frame %s no SIGNAL-TO-PDU-MAPPINGS found" % (newFrame.name))
    pdusigmapping = arGetChildren(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)

    if pdusigmapping is not None and pdusigmapping.__len__() > 0:
        getSignals(pdusigmapping, newFrame, xmlRoot, ns, None, float_factory)

    # Seen some pdusigmapping being [] and not None with some arxml 4.2
    else: ##AR 4.2
        pdutrigs = arGetChildren(frameTriggering, "PDU-TRIGGERINGS", xmlRoot, ns)
        if pdutrigs is not None:
            for pdutrig in pdutrigs:
                trigrefcond = arGetChild(pdutrig, "PDU-TRIGGERING-REF-CONDITIONAL", xmlRoot, ns)
                trigs = arGetChild(trigrefcond, "PDU-TRIGGERING", xmlRoot, ns)
                ipdus = arGetChild(trigs, "I-PDU", xmlRoot, ns)

                signaltopdumaps = arGetChild(ipdus, "I-SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
                if signaltopdumaps is None:
                    signaltopdumaps = arGetChild(ipdus, "I-SIGNAL-TO-I-PDU-MAPPINGS", xmlRoot, ns)

                if signaltopdumaps is None:
                    logger.debug("DEBUG: AR4.x PDU %s no SIGNAL-TO-PDU-MAPPINGS found - no signal extraction!" % (arGetName(ipdus, ns)))
#                signaltopdumap = arGetChild(signaltopdumaps, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                getSignals(signaltopdumaps, newFrame, xmlRoot, ns, None, float_factory)
        else:
            logger.debug("DEBUG: Frame %s (assuming AR4.2) no PDU-TRIGGERINGS found" % (newFrame.name))
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
    global pduFrameMapping
    connectors = arGetChild(ecu, "CONNECTORS", arDict, ns)
    diagAddress = arGetChild(ecu, "DIAGNOSTIC-ADDRESS", arDict, ns)
    diagResponse = arGetChild(ecu, "RESPONSE-ADDRESSS", arDict, ns)
    # TODO: use diagAddress for frame-classification
    commconnector = arGetChild(connectors,"COMMUNICATION-CONNECTOR",arDict,ns)
    if commconnector is None:
        commconnector = arGetChild(connectors, "CAN-COMMUNICATION-CONNECTOR", arDict, ns)
    frames = arGetXchildren(commconnector,"ECU-COMM-PORT-INSTANCES/FRAME-PORT",arDict,ns)
    nmAddress = arGetChild(commconnector, "NM-ADDRESS", arDict, ns)
    assocRefs = arGetChild(ecu, "ASSOCIATED-I-PDU-GROUP-REFS", arDict, ns)

    if assocRefs is not None:
        assoc = arGetChildren(assocRefs, "ASSOCIATED-I-PDU-GROUP", arDict, ns)
    else:  # AR4
        assocRefs = arGetChild(ecu, "ASSOCIATED-COM-I-PDU-GROUP-REFS", arDict, ns)
        assoc = arGetChildren(assocRefs,"ASSOCIATED-COM-I-PDU-GROUP",arDict,ns)

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
            frame = db.frame_by_name(out)
            if frame is not None:
                frame.add_transmitter(arGetName(ecu, ns))
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
    bu = ecu(arGetName(ecu, ns))
    if nmAddress is not None:
        bu.add_attribute("NWM-Stationsadresse", nmAddress.text)
        bu.add_attribute("NWM-Knoten", "ja")
    else:
        bu.add_attribute("NWM-Stationsadresse", "0")
        bu.add_attribute("NWM-Knoten", "nein")
    return bu

def ecuc_extract_signal(signal_node, ns):
    attributes = signal_node.findall(".//" + ns + "DEFINITION-REF")
    start_bit = None
    size = 0
    endianness = None
    init_value = 0
    signal_type = None
    timeout = 0
    for attribute in attributes:
        if attribute.text.endswith("ComBitPosition"):
            start_bit = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComBitSize"):
            size = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComSignalEndianness"):
            endianness = (attribute.getparent().find(".//" +ns + "VALUE").text)
            if "LITTLE_ENDIAN" in endianness:
                is_little = True
            else:
                is_little = False
        if attribute.text.endswith("ComSignalInitValue"):
            init_value = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComSignalType"):
            signal_type = (attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComTimeout"):
            timeout = int(attribute.getparent().find(".//" +ns + "VALUE").text)
    return canmatrix.Signal(arGetName(signal_node,ns), start_bit = start_bit, size=size, is_little_endian = is_little)

def extract_cm_from_ecuc(com_module, search_point, ns):
    db = CanMatrix()
    definitions = com_module.findall('.//' + ns + "DEFINITION-REF")
    for definition in definitions:
        if definition.text.endswith("ComIPdu"):
            container = definition.getparent()
            frame = canmatrix.Frame(arGetName(container, ns))
            db.add_frame(frame)
            allReferences = arGetChildren(container,"ECUC-REFERENCE-VALUE",search_point,ns)
            for reference in allReferences:
                value = arGetChild(reference,"VALUE",search_point,ns)
                if value is not None:
                    signal_definition = value.find('./' + ns + "DEFINITION-REF")
                    if signal_definition.text.endswith("ComSignal"):
                        signal = ecuc_extract_signal(value,ns)
                        frame.add_signal(signal)
    db.recalc_dlc(strategy = "max")
    return {"": db}

def load(file, **options):
    global ArCache
    ArCache = dict()
    global pduFrameMapping
    pduFrameMapping = {}
    global signalRxs
    signalRxs = {}

    float_factory = options.get("float_factory", default_float_factory)
    ignoreClusterInfo = options.get("arxmlIgnoreClusterInfo", False)
    useArXPath = options.get("arxmlUseXpath", False)

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

    if useArXPath:
        searchPoint = topLevelPackages
    else:
        arDict = arTree()
        arParseTree(topLevelPackages, arDict, ns)
        searchPoint = arDict

    logger.debug(" Done\n")


    com_module = arGetPath(searchPoint, "ActiveEcuC/Com")
    if com_module is not None:
        logger.info("seems to be a ECUC arxml. Very limited support for extracting canmatrix." )
        return extract_cm_from_ecuc(com_module, searchPoint, ns)

    frames = root.findall('.//' + ns + 'CAN-FRAME')  ## AR4.2
    if frames is None:
        frames = root.findall('.//' + ns + 'FRAME') ## AR3.2-4.1?
    
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

        if ignoreClusterInfo == True:
            canframetrig = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
            busname = ""
        else:
            speed = arGetChild(cc, "SPEED", searchPoint, ns)
            logger.debug("Busname: " + arGetName(cc, ns))

            busname = arGetName(cc, ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            physicalChannels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")
            if physicalChannels is None:
                logger.error("Error - PHYSICAL-CHANNELS not found")

            nmLowerId = arGetChild(cc, "NM-LOWER-CAN-ID", searchPoint, ns)

            physicalChannel = arGetChild(
                physicalChannels, "PHYSICAL-CHANNEL", searchPoint, ns)
            if physicalChannel is None:
                physicalChannel = arGetChild(
                    physicalChannels, "CAN-PHYSICAL-CHANNEL", searchPoint, ns)
            if physicalChannel is None:
                logger.debug("Error - PHYSICAL-CHANNEL not found")
            canframetrig = arGetChildren(
                physicalChannel, "CAN-FRAME-TRIGGERING", searchPoint, ns)
            if canframetrig is None:
                logger.error("Error - CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug(
                    "%d frames found in arxml\n" %
                    (canframetrig.__len__()))

        multiplexTranslation = {}
        for frameTrig in canframetrig:
            frameObject = getFrame(frameTrig,searchPoint,multiplexTranslation,ns, float_factory)
            if frameObject is not None:
                db.add_frame(frameObject)
                
        if ignoreClusterInfo == True:
            pass
            # no support for signal direction
        else:
            isignaltriggerings = arGetXchildren(
                physicalChannel, "I-SIGNAL-TRIGGERING", searchPoint, ns)
            for sigTrig in isignaltriggerings:
                isignal = arGetChild(sigTrig, 'SIGNAL', searchPoint, ns)
                if isignal is None:
                    isignal = arGetChild(sigTrig, 'I-SIGNAL', searchPoint, ns)
                if isignal is None:
                    sigTrig_text = arGetName(sigTrig, ns) if sigTrig is not None else "None"
                    logger.debug("load: no isignal for %s" % sigTrig_text)
                    
                    continue

                portRef = arGetChildren(sigTrig, "I-SIGNAL-PORT", searchPoint, ns)

                for port in portRef:
                    comDir = arGetChild(
                        port, "COMMUNICATION-DIRECTION", searchPoint, ns)
                    if comDir is not None and comDir.text == "IN":
                        sysSignal = arGetChild(
                            isignal, "SYSTEM-SIGNAL", searchPoint, ns)
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
            bu = processEcu(node, db, searchPoint, multiplexTranslation, ns)
            desc = arGetChild(node, "DESC", searchPoint, ns)
            l2 = arGetChild(desc, "L-2", searchPoint, ns)
            if l2 is not None:
                bu.add_comment(l2.text)

            db.add_ecu(bu)

        for frame in db.frames:
            sig_value_hash = dict()
            for sig in frame.signals:
                sig_value_hash[sig.name] = sig._initValue
            frameData = frame.encode(sig_value_hash)
            frame.add_attribute("GenMsgStartValue", "".join(["%02x" % x for x in frameData]))
        result[busname] = db
    return result
