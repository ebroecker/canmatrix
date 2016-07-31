#!/usr/bin/env python

#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

#
# this script axports arxml-files from a canmatrix-object
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
# currently Support for Autosar 3.2 and 4.0-4.3 is planned
#

#TODO receivers of signals are missing

from __future__ import absolute_import
from builtins import *
from lxml import etree
from .canmatrix import *
from .autosarhelper import *
from .importdbc import *


def createSubElement(elem, strElement, strName):
    sn = etree.SubElement(elem, strElement)
    sn.text = str(strName)


def exportArxml(db, filename, **options):
    if 'arVersion' in options:
        if options["arVersion"][0] == "3":
            arVersion="3.2.3"
        else:
            arVersion = "4.1.0"
    else:
        arVersion="3.2.3"


    for frame in db._fl._list:
        for signal in frame._signals:
            for rec in signal._receiver:
                if rec.strip() not in frame._receiver:
                    frame._receiver.append(rec.strip())

    if arVersion[0] == "3":
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element('AUTOSAR', nsmap={None: "http://autosar.org/3.2.3", 'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(pre=xsi)] = 'http://autosar.org/3.2.3 AUTOSAR_323.xsd'
        toplevelPackages = etree.SubElement(root,'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element('AUTOSAR', nsmap={None: "http://autosar.org/schema/r4.0", 'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(pre=xsi)] = 'http://autosar.org/schema/r4.0 AUTOSAR_' + arVersion.replace('.','-') + '.xsd'
        toplevelPackages = etree.SubElement(root,'AR-PACKAGES')

    #
    #AR-PACKAGE Cluster
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Cluster')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    cancluster = etree.SubElement(elements,'CAN-CLUSTER')
    createSubElement(cancluster, 'SHORT-NAME', 'CAN')
    if arVersion[0] == "3":
 #       createSubElement(cancluster, 'SPEED', '50000')
        physicalChannels = etree.SubElement(cancluster, 'PHYSICAL-CHANNELS')
        physicalChannel = etree.SubElement(physicalChannels, 'PHYSICAL-CHANNEL')
        createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
        frameTriggering = etree.SubElement(physicalChannel, 'FRAME-TRIGGERINGSS')
    else:
        canClusterVaraints = etree.SubElement(cancluster,'CAN-CLUSTER-VARIANTS')            
        canClusterConditional = etree.SubElement(canClusterVaraints,'CAN-CLUSTER-CONDITIONAL')            
        physicalChannels = etree.SubElement(canClusterConditional, 'PHYSICAL-CHANNELS')
        physicalChannel = etree.SubElement(physicalChannels, 'CAN-PHYSICAL-CHANNEL')
        createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
        frameTriggering = etree.SubElement(physicalChannel, 'FRAME-TRIGGERINGS')
    for frame in db._fl._list:
        canFrameTriggering = etree.SubElement(frameTriggering, 'CAN-FRAME-TRIGGERING')
        createSubElement(canFrameTriggering, 'SHORT-NAME', frame._name)
        framePortRefs = etree.SubElement(canFrameTriggering, 'FRAME-PORT-REFS')
        for transmitter in frame._Transmitter:
            framePortRef = etree.SubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + transmitter + "/CN_" + transmitter + "/" + frame._name
        for rec in frame._receiver:
            framePortRef = etree.SubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + rec + "/CN_" + rec + "/" + frame._name
        frameRef = etree.SubElement(canFrameTriggering, 'FRAME-REF')
        if arVersion[0] == "3":
            frameRef.set('DEST','FRAME')
            frameRef.text = "/Frame/FRAME_" + frame._name
            pduTriggeringRefs = etree.SubElement(canFrameTriggering, 'I-PDU-TRIGGERING-REFS')
            pduTriggeringRef = etree.SubElement(pduTriggeringRefs, 'I-PDU-TRIGGERING-REF')
            pduTriggeringRef.set('DEST','I-PDU-TRIGGERING')
        else:
            frameRef.set('DEST','CAN-FRAME')
            frameRef.text = "/CanFrame/FRAME_" + frame._name
            pduTriggering = etree.SubElement(canFrameTriggering, 'PDU-TRIGGERINGS')
            pduTriggeringRefConditional = etree.SubElement(pduTriggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
            pduTriggeringRef = etree.SubElement(pduTriggeringRefConditional, 'PDU-TRIGGERING-REF')
            pduTriggeringRef.set('DEST','PDU-TRIGGERING')
  
        if frame._extended == 0:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
        else:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')
        createSubElement(canFrameTriggering, 'IDENTIFIER', str(frame._Id))
  
        pduTriggeringRef.text = "/Cluster/CAN/IPDUTRIGG_" + frame._name
  
    if arVersion[0] == "3":
        ipduTriggerings = etree.SubElement(physicalChannel, 'I-PDU-TRIGGERINGS')
        for frame in db._fl._list:
            ipduTriggering = etree.SubElement(ipduTriggerings, 'I-PDU-TRIGGERING')
            createSubElement(ipduTriggering, 'SHORT-NAME', "IPDUTRIGG_" + frame._name)
            ipduRef = etree.SubElement(ipduTriggering, 'I-PDU-REF')
            ipduRef.set('DEST','SIGNAL-I-PDU')
            ipduRef.text = "/PDU/PDU_" + frame._name
        isignalTriggerings = etree.SubElement(physicalChannel, 'I-SIGNAL-TRIGGERINGS')
        for frame in db._fl._list:
            for signal in frame._signals:
                isignalTriggering = etree.SubElement(isignalTriggerings, 'I-SIGNAL-TRIGGERING')
                createSubElement(isignalTriggering, 'SHORT-NAME', signal._name)
                isignalRef = etree.SubElement(isignalTriggering, 'SIGNAL-REF')
                isignalRef.set('DEST','I-SIGNAL')
                isignalRef.text = "/ISignal/" + signal._name
    else:
        pass
#TODO


    if arVersion[0] == "3":
        pass  
    else:
        pass
#TODO
#        ipduTriggerings = etree.SubElement(physicalChannel, 'PDU-TRIGGERINGS')
#        for frame in db._fl._list:
#            ipduTriggering = etree.SubElement(ipduTriggerings, 'PDU-TRIGGERING')
#            createSubElement(ipduTriggering, 'SHORT-NAME', "PDUTRIGG_" + frame._name)
#            ipduRef = etree.SubElement(ipduTriggering, 'I-PDU-REF')
#            ipduRef.set('DEST','SIGNAL-I-PDU')
#            ipduRef.text = "/PDU/PDU_" + frame._name



    #
    #AR-PACKAGE FRAME
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    if arVersion[0] == "3":
        createSubElement(arPackage, 'SHORT-NAME', 'Frame')
    else:
        createSubElement(arPackage, 'SHORT-NAME', 'CanFrame')

    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        if arVersion[0] == "3":
            frameEle = etree.SubElement(elements,'FRAME')
        else:
            frameEle = etree.SubElement(elements,'CAN-FRAME')
        createSubElement(frameEle, 'SHORT-NAME', "FRAME_" + frame._name)
        createSubElement(frameEle, 'FRAME-LENGTH', "%d" % frame._Size)
        pdumappings = etree.SubElement(frameEle, 'PDU-TO-FRAME-MAPPINGS')
        pdumapping = etree.SubElement(pdumappings, 'PDU-TO-FRAME-MAPPING')
        createSubElement(pdumapping, 'SHORT-NAME', frame._name)
        createSubElement(pdumapping, 'PACKING-BYTE-ORDER', "MOST-SIGNIFICANT-BYTE-LAST")
        pduRef = etree.SubElement(pdumapping, 'PDU-REF')
        createSubElement(pdumapping, 'START-POSITION', '0')
        pduRef.text = "/PDU/PDU_" + frame._name
        if arVersion[0] == "3":
            pduRef.set('DEST','SIGNAL-I-PDU')
        else:
            pduRef.set('DEST','I-SIGNAL-I-PDU')

    #
    #AR-PACKAGE PDU
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'PDU')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        if arVersion[0] == "3":
            signalIpdu = etree.SubElement(elements,'SIGNAL-I-PDU')
            createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame._name)
            createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame._Size*8))
        else:
            signalIpdu = etree.SubElement(elements,'I-SIGNAL-I-PDU')
            createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame._name)
            createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame._Size))

        # I-PDU-TIMING-SPECIFICATION
        if arVersion[0] == "3":
            signalToPduMappings = etree.SubElement(signalIpdu,'SIGNAL-TO-PDU-MAPPINGS')
        else:
            signalToPduMappings = etree.SubElement(signalIpdu,'I-SIGNAL-TO-PDU-MAPPINGS')

        for signal in frame._signals:
            signalToPduMapping = etree.SubElement(signalToPduMappings,'I-SIGNAL-TO-I-PDU-MAPPING')
            createSubElement(signalToPduMapping, 'SHORT-NAME', signal._name)
        
            if arVersion[0] == "3":
                if signal._is_little_endian == 1: # Intel
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-LAST')
                else: #Motorola
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-FIRST')
                signalRef = etree.SubElement(signalToPduMapping, 'SIGNAL-REF')
            else:
                signalRef = etree.SubElement(signalToPduMapping, 'I-SIGNAL-REF')
                if signal._is_little_endian == 1: # Intel
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-LAST')
                else: #Motorola
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-FIRST')
            signalRef.text = "/ISignal/" + signal._name
            signalRef.set('DEST','I-SIGNAL')


            createSubElement(signalToPduMapping, 'START-POSITION', str(signal.getStartbit(bitNumbering = 1)))
            #TODO: TRANSFER-PROPERTY: PENDING???

        for group in frame._SignalGroups:
            signalToPduMapping = etree.SubElement(signalToPduMappings,'I-SIGNAL-TO-I-PDU-MAPPING')
            createSubElement(signalToPduMapping, 'SHORT-NAME', group._name)
            signalRef = etree.SubElement(signalToPduMapping, 'SIGNAL-REF')
            signalRef.text = "/ISignal/" + group._name
            signalRef.set('DEST','I-SIGNAL')
            #TODO: TRANSFER-PROPERTY: PENDING???



    #
    #AR-PACKAGE ISignal
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ISignal')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            signalEle = etree.SubElement(elements, 'I-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', signal._name)
            if arVersion[0] == "4":
               createSubElement(signalEle, 'LENGTH', str(signal._signalsize))
            sysSigRef = etree.SubElement(signalEle, 'SYSTEM-SIGNAL-REF')
            sysSigRef.text = "/Signal/" + signal._name
            sysSigRef.set('DEST','SYSTEM-SIGNAL')
        for group in frame._SignalGroups:
            signalEle = etree.SubElement(elements, 'I-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', group._name)
            sysSigRef = etree.SubElement(signalEle, 'SYSTEM-SIGNAL-REF')
            sysSigRef.text = "/Signal/" + group._name
            sysSigRef.set('DEST','SYSTEM-SIGNAL-GROUP')

    #
    #AR-PACKAGE System-Signal
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Signal')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            signalEle = etree.SubElement(elements, 'SYSTEM-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', signal._name)
            if arVersion[0] == "3":
                dataTypeRef = etree.SubElement(signalEle, 'DATA-TYPE-REF')
                dataTypeRef.set('DEST','INTEGER-TYPE')
                dataTypeRef.text = "/DataType/" + signal._name
                createSubElement(signalEle, 'LENGTH', str(signal._signalsize))
        for group in frame._SignalGroups:
            groupEle = etree.SubElement(elements, 'SYSTEM-SIGNAL-GROUP')
            createSubElement(signalEle, 'SHORT-NAME', group._name)
            if arVersion[0] == "3":
                dataTypeRef.set('DEST','INTEGER-TYPE')
            sysSignalRefs = etree.SubElement(groupEle, 'SYSTEM-SIGNAL-REFS')
            for member in group._members:
                memberEle = etree.SubElement(sysSignalRefs, 'SYSTEM-SIGNAL-REF')
                memberEle.set('DEST','SYSTEM-SIGNAL')
                memberEle.text = "/Signal/" + member._name

#                       initValueRef = etree.SubElement(signalEle, 'INIT-VALUE-REF')
#                       initValueRef.set('DEST','INTEGER-LITERAL')
#                       initValueRef.text = "/CONSTANTS/" + signal._name


    #
    #AR-PACKAGE Datatype
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'DataType')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    
    if arVersion[0] == "3":
        for frame in db._fl._list:
            for signal in frame._signals:
                intType = etree.SubElement(elements,'INTEGER-TYPE')
                createSubElement(intType, 'SHORT-NAME', signal._name)
                swDataDefProps = etree.SubElement(intType,'SW-DATA-DEF-PROPS')
                compuMethodRef = etree.SubElement(swDataDefProps,'COMPU-METHOD-REF')
                compuMethodRef.set('DEST','COMPU-METHOD')
                compuMethodRef.text = "/DataType/Semantics/" + signal._name
    else:
        pass
        #TODO

    if arVersion[0] == "3":
        subpackages = etree.SubElement(arPackage,'SUB-PACKAGES')
    else:
        subpackages = etree.SubElement(arPackage,'AR-PACKAGES')
    arPackage = etree.SubElement(subpackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Semantics')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            compuMethod = etree.SubElement(elements,'COMPU-METHOD')
            createSubElement(compuMethod, 'SHORT-NAME', signal._name)
            #UNIT-REF
            compuIntToPhys = etree.SubElement(compuMethod,'COMPU-INTERNAL-TO-PHYS')
            compuScales = etree.SubElement(compuIntToPhys,'COMPU-SCALES')
            for value in sorted(signal._values, key=lambda x: int(x)):
                compuScale = etree.SubElement(compuScales,'COMPU-SCALE')
                desc = etree.SubElement(compuScale,'DESC')
                l2 = etree.SubElement(desc,'L-2')
                l2.set('L','FOR-ALL')
                l2.text = signal._values[value]
                createSubElement(compuScale, 'LOWER-LIMIT', str(value))
                createSubElement(compuScale, 'UPPER-LIMIT', str(value))
                compuConst = etree.SubElement(compuScale,'COMPU-CONST')
                createSubElement(compuConst, 'VT', signal._values[value])
            else:
                compuScale = etree.SubElement(compuScales,'COMPU-SCALE')
                compuRationslCoeff = etree.SubElement(compuScale,'COMPU-RATIONAL-COEFFS')
                compuNumerator = etree.SubElement(compuRationslCoeff,'COMPU-NUMERATOR')
                createSubElement(compuNumerator, 'V', "%g" % signal._offset)
                createSubElement(compuNumerator, 'V', "%g" % signal._factor)
                compuDenomiator = etree.SubElement(compuRationslCoeff,'COMPU-DENOMINATOR')
                createSubElement(compuDenomiator, 'V', "1")

    txIPduGroups = {}
    rxIPduGroups = {}

    #
    #AR-PACKAGE ECU
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ECU')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for ecu in db._BUs._list:
        ecuInstance = etree.SubElement(elements,'ECU-INSTANCE')
        createSubElement(ecuInstance, 'SHORT-NAME', ecu._name)

        if arVersion[0] == "3":
            assoIpduGroupRefs = etree.SubElement(ecuInstance,'ASSOCIATED-I-PDU-GROUP-REFS')
            connectors = etree.SubElement(ecuInstance,'CONNECTORS')
            commConnector = etree.SubElement(connectors,'COMMUNICATION-CONNECTOR')
        else:
            assoIpduGroupRefs = etree.SubElement(ecuInstance,'ASSOCIATED-COM-I-PDU-GROUP-REFS')
            connectors = etree.SubElement(ecuInstance,'CONNECTORS')
            commConnector = etree.SubElement(connectors,'CAN-COMMUNICATION-CONNECTOR')

        createSubElement(commConnector, 'SHORT-NAME', 'CN_' + ecu._name)
        ecuCommPortInstances = etree.SubElement(commConnector,'ECU-COMM-PORT-INSTANCES')

        recTemp = None
        sendTemp = None


        for frame in db._fl._list:
            if ecu._name in frame._Transmitter:
                frameport = etree.SubElement(ecuCommPortInstances,'FRAME-PORT')
                createSubElement(frameport, 'SHORT-NAME', frame._name)
                createSubElement(frameport, 'COMMUNICATION-DIRECTION', 'OUT')
                sendTemp = 1
                if ecu._name + "_Tx" not in txIPduGroups:
                    txIPduGroups[ecu._name + "_Tx"] = []
                txIPduGroups[ecu._name + "_Tx"].append(frame._name)

                for signal in frame._signals:
                    if arVersion[0] == "3":
                       signalPort = etree.SubElement(ecuCommPortInstances,'SIGNAL-PORT')
                    else:
                       signalPort = etree.SubElement(ecuCommPortInstances,'I-SIGNAL-PORT')

                    createSubElement(signalPort, 'SHORT-NAME', signal._name)
                    createSubElement(signalPort, 'COMMUNICATION-DIRECTION', 'OUT')
            if ecu._name in frame._receiver:
                frameport = etree.SubElement(ecuCommPortInstances,'FRAME-PORT')
                createSubElement(frameport, 'SHORT-NAME', frame._name)
                createSubElement(frameport, 'COMMUNICATION-DIRECTION', 'IN')
                recTemp = 1
                if  ecu._name + "_Tx" not in rxIPduGroups:
                    rxIPduGroups[ecu._name + "_Rx"] = []
                rxIPduGroups[ecu._name + "_Rx"].append(frame._name)

                for signal in frame._signals:
                    if ecu._name in signal._receiver:
                        if arVersion[0] == "3":
                          signalPort = etree.SubElement(ecuCommPortInstances,'SIGNAL-PORT')
                        else:
                          signalPort = etree.SubElement(ecuCommPortInstances,'I-SIGNAL-PORT')

                        createSubElement(signalPort, 'SHORT-NAME', signal._name)
                        createSubElement(signalPort, 'COMMUNICATION-DIRECTION', 'IN')

        if recTemp is not None:
            if arVersion[0] == "3":
                assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            else:
                assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-COM-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-SIGNAL-I-PDU-GROUP")

            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Rx"

        if sendTemp is not None:
            if arVersion[0] == "3":
                assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            else:
                assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-COM-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-SIGNAL-I-PDU-GROUP")
            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Tx"


    #
    #AR-PACKAGE IPDUGroup
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'IPDUGroup')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for pdugrp in txIPduGroups:
        if arVersion[0] == "3":
            ipduGrp = etree.SubElement(elements,'I-PDU-GROUP')
        else:
            ipduGrp = etree.SubElement(elements,'I-SIGNAL-I-PDU-GROUP')

        createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
        createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "OUT")

        if arVersion[0] == "3":
            ipduRefs = etree.SubElement(ipduGrp,'I-PDU-REFS')
            for frame in txIPduGroups[pdugrp]:
                ipduRef = etree.SubElement(ipduRefs,'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
        else:
            isignalipdus = etree.SubElement(ipduGrp,'I-SIGNAL-I-PDUS')
            for frame in txIPduGroups[pdugrp]:
                isignalipdurefconditional = etree.SubElement(isignalipdus,'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipduRef = etree.SubElement(isignalipdurefconditional,'I-SIGNAL-I-PDU-REF')
                ipduRef.set('DEST', "I-SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
            


    if arVersion[0] == "3":
        for pdugrp in rxIPduGroups:
            ipduGrp = etree.SubElement(elements,'I-PDU-GROUP')
            createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
            createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")

            ipduRefs = etree.SubElement(ipduGrp,'I-PDU-REFS')
            for frame in rxIPduGroups[pdugrp]:
                ipduRef = etree.SubElement(ipduRefs,'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
    else:
        pass
#        isignalipdus = etree.SubElement(ipduGrp,'I-SIGNAL-I-PDUS')
#        for frame in rxIPduGroups[pdugrp]:
#            isignalipdurefconditional = etree.SubElement(isignalipdus,'I-SIGNAL-I-PDU-REF-CONDITIONAL')
#            ipduRef = etree.SubElement(isignalipdurefconditional,'I-SIGNAL-I-PDU-REF')
#            ipduRef.set('DEST', "I-SIGNAL-I-PDU")
#            ipduRef.text = "/PDU/PDU_" + frame
 
    f = open(filename,"wb");
    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True))

