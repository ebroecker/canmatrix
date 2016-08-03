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


def createSubElement(parent, elementName, strName = None):
    sn = etree.SubElement(parent, elementName)
    if strName != None:    
        sn.text = str(strName)
    return sn


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
        toplevelPackages = createSubElement(root,'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element('AUTOSAR', nsmap={None: "http://autosar.org/schema/r4.0", 'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(pre=xsi)] = 'http://autosar.org/schema/r4.0 AUTOSAR_' + arVersion.replace('.','-') + '.xsd'
        toplevelPackages = createSubElement(root,'AR-PACKAGES')

    #
    #AR-PACKAGE Cluster
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Cluster')
    elements = createSubElement(arPackage, 'ELEMENTS')
    cancluster = createSubElement(elements, 'CAN-CLUSTER')
    createSubElement(cancluster, 'SHORT-NAME', 'CAN')
    if arVersion[0] == "3":
 #       createSubElement(cancluster, 'SPEED', '50000')
        physicalChannels = createSubElement(cancluster, 'PHYSICAL-CHANNELS')
        physicalChannel = createSubElement(physicalChannels, 'PHYSICAL-CHANNEL')
        createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
        frameTriggering = createSubElement(physicalChannel, 'FRAME-TRIGGERINGSS')
    else:
        canClusterVaraints = createSubElement(cancluster,'CAN-CLUSTER-VARIANTS')            
        canClusterConditional = createSubElement(canClusterVaraints,'CAN-CLUSTER-CONDITIONAL')            
        physicalChannels = createSubElement(canClusterConditional, 'PHYSICAL-CHANNELS')
        physicalChannel = createSubElement(physicalChannels, 'CAN-PHYSICAL-CHANNEL')
        createSubElement(physicalChannel, 'SHORT-NAME', 'CAN')
        frameTriggering = createSubElement(physicalChannel, 'FRAME-TRIGGERINGS')
    for frame in db._fl._list:
        canFrameTriggering = createSubElement(frameTriggering, 'CAN-FRAME-TRIGGERING')
        createSubElement(canFrameTriggering, 'SHORT-NAME', frame._name)
        framePortRefs = createSubElement(canFrameTriggering, 'FRAME-PORT-REFS')
        for transmitter in frame._Transmitter:
            framePortRef = createSubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + transmitter + "/CN_" + transmitter + "/" + frame._name
        for rec in frame._receiver:
            framePortRef = createSubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + rec + "/CN_" + rec + "/" + frame._name
        frameRef = createSubElement(canFrameTriggering, 'FRAME-REF')
        if arVersion[0] == "3":
            frameRef.set('DEST','FRAME')
            frameRef.text = "/Frame/FRAME_" + frame._name
            pduTriggeringRefs = createSubElement(canFrameTriggering, 'I-PDU-TRIGGERING-REFS')
            pduTriggeringRef = createSubElement(pduTriggeringRefs, 'I-PDU-TRIGGERING-REF')
            pduTriggeringRef.set('DEST','I-PDU-TRIGGERING')
        else:
            frameRef.set('DEST','CAN-FRAME')
            frameRef.text = "/CanFrame/FRAME_" + frame._name
            pduTriggering = createSubElement(canFrameTriggering, 'PDU-TRIGGERINGS')
            pduTriggeringRefConditional = createSubElement(pduTriggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
            pduTriggeringRef = createSubElement(pduTriggeringRefConditional, 'PDU-TRIGGERING-REF')
            pduTriggeringRef.set('DEST','PDU-TRIGGERING')
  
        if frame._extended == 0:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
        else:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')
        createSubElement(canFrameTriggering, 'IDENTIFIER', str(frame._Id))
  
        pduTriggeringRef.text = "/Cluster/CAN/IPDUTRIGG_" + frame._name
  
    if arVersion[0] == "3":
        ipduTriggerings = createSubElement(physicalChannel, 'I-PDU-TRIGGERINGS')
        for frame in db._fl._list:
            ipduTriggering = createSubElement(ipduTriggerings, 'I-PDU-TRIGGERING')
            createSubElement(ipduTriggering, 'SHORT-NAME', "IPDUTRIGG_" + frame._name)
            ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
            ipduRef.set('DEST','SIGNAL-I-PDU')
            ipduRef.text = "/PDU/PDU_" + frame._name
        isignalTriggerings = createSubElement(physicalChannel, 'I-SIGNAL-TRIGGERINGS')
        for frame in db._fl._list:
            for signal in frame._signals:
                isignalTriggering = createSubElement(isignalTriggerings, 'I-SIGNAL-TRIGGERING')
                createSubElement(isignalTriggering, 'SHORT-NAME', signal._name)
                isignalRef = createSubElement(isignalTriggering, 'SIGNAL-REF')
                isignalRef.set('DEST','I-SIGNAL')
                isignalRef.text = "/ISignal/" + signal._name
    else:
        isignalTriggerings = createSubElement(physicalChannel, 'I-SIGNAL-TRIGGERINGS')
        for frame in db._fl._list:
            for signal in frame._signals:
                isignalTriggering = createSubElement(isignalTriggerings, 'I-SIGNAL-TRIGGERING')
                createSubElement(isignalTriggering, 'SHORT-NAME', signal._name)
                ## missing: I-SIGNAL-PORT-REFS
                isignalRef = createSubElement(isignalTriggering, 'I-SIGNAL-REF')
                isignalRef.set('DEST','I-SIGNAL')
                isignalRef.text = "/ISignal/" + signal._name
        ipduTriggerings = createSubElement(physicalChannel, 'PDU-TRIGGERINGS')
        for frame in db._fl._list:
            ipduTriggering = createSubElement(ipduTriggerings, 'PDU-TRIGGERING')
            createSubElement(ipduTriggering, 'SHORT-NAME', "IPDUTRIGG_" + frame._name)
            ## missing: I-PDU-PORT-REFS
            ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
            ipduRef.set('DEST','I-SIGNAL-I-PDU')
            ipduRef.text = "/PDU/PDU_" + frame._name
            ## missing: I-SIGNAL-TRIGGERINGS


    if arVersion[0] == "3":
        pass  
    else:
        pass
#TODO
#        ipduTriggerings = createSubElement(physicalChannel, 'PDU-TRIGGERINGS')
#        for frame in db._fl._list:
#            ipduTriggering = createSubElement(ipduTriggerings, 'PDU-TRIGGERING')
#            createSubElement(ipduTriggering, 'SHORT-NAME', "PDUTRIGG_" + frame._name)
#            ipduRef = createSubElement(ipduTriggering, 'I-PDU-REF')
#            ipduRef.set('DEST','SIGNAL-I-PDU')
#            ipduRef.text = "/PDU/PDU_" + frame._name



    #
    #AR-PACKAGE FRAME
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    if arVersion[0] == "3":
        createSubElement(arPackage, 'SHORT-NAME', 'Frame')
    else:
        createSubElement(arPackage, 'SHORT-NAME', 'CanFrame')

    elements = createSubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        if arVersion[0] == "3":
            frameEle = createSubElement(elements,'FRAME')
        else:
            frameEle = createSubElement(elements,'CAN-FRAME')
        createSubElement(frameEle, 'SHORT-NAME', "FRAME_" + frame._name)
        if frame._comment:
            desc = createSubElement(frameEle, 'DESC')
            l2 = createSubElement(desc, 'L-2')
            l2.set("L","FOR-ALL")
            l2.text = frame._comment
        createSubElement(frameEle, 'FRAME-LENGTH', "%d" % frame._Size)
        pdumappings = createSubElement(frameEle, 'PDU-TO-FRAME-MAPPINGS')
        pdumapping = createSubElement(pdumappings, 'PDU-TO-FRAME-MAPPING')
        createSubElement(pdumapping, 'SHORT-NAME', frame._name)
        createSubElement(pdumapping, 'PACKING-BYTE-ORDER', "MOST-SIGNIFICANT-BYTE-LAST")
        pduRef = createSubElement(pdumapping, 'PDU-REF')
        createSubElement(pdumapping, 'START-POSITION', '0')
        pduRef.text = "/PDU/PDU_" + frame._name
        if arVersion[0] == "3":
            pduRef.set('DEST','SIGNAL-I-PDU')
        else:
            pduRef.set('DEST','I-SIGNAL-I-PDU')

    #
    #AR-PACKAGE PDU
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'PDU')
    elements = createSubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        if arVersion[0] == "3":
            signalIpdu = createSubElement(elements,'SIGNAL-I-PDU')
            createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame._name)
            createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame._Size*8))
        else:
            signalIpdu = createSubElement(elements,'I-SIGNAL-I-PDU')
            createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame._name)
            createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame._Size))

        # I-PDU-TIMING-SPECIFICATION
        if arVersion[0] == "3":
            signalToPduMappings = createSubElement(signalIpdu,'SIGNAL-TO-PDU-MAPPINGS')
        else:
            signalToPduMappings = createSubElement(signalIpdu,'I-SIGNAL-TO-PDU-MAPPINGS')

        for signal in frame._signals:
            signalToPduMapping = createSubElement(signalToPduMappings,'I-SIGNAL-TO-I-PDU-MAPPING')
            createSubElement(signalToPduMapping, 'SHORT-NAME', signal._name)
        
            if arVersion[0] == "3":
                if signal._is_little_endian == 1: # Intel
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-LAST')
                else: #Motorola
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-FIRST')
                signalRef = createSubElement(signalToPduMapping, 'SIGNAL-REF')
            else:
                signalRef = createSubElement(signalToPduMapping, 'I-SIGNAL-REF')
                if signal._is_little_endian == 1: # Intel
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-LAST')
                else: #Motorola
                    createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-FIRST')
            signalRef.text = "/ISignal/" + signal._name
            signalRef.set('DEST','I-SIGNAL')


            createSubElement(signalToPduMapping, 'START-POSITION', str(signal.getStartbit(bitNumbering = 1)))
            #missing: TRANSFER-PROPERTY: PENDING/...

        for group in frame._SignalGroups:
            signalToPduMapping = createSubElement(signalToPduMappings,'I-SIGNAL-TO-I-PDU-MAPPING')
            createSubElement(signalToPduMapping, 'SHORT-NAME', group._name)
            signalRef = createSubElement(signalToPduMapping, 'SIGNAL-REF')
            signalRef.text = "/ISignal/" + group._name
            signalRef.set('DEST','I-SIGNAL')
            #TODO: TRANSFER-PROPERTY: PENDING???



    #
    #AR-PACKAGE ISignal
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ISignal')
    elements = createSubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            signalEle = createSubElement(elements, 'I-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', signal._name)
            if arVersion[0] == "4":
               createSubElement(signalEle, 'LENGTH', str(signal._signalsize))
            sysSigRef = createSubElement(signalEle, 'SYSTEM-SIGNAL-REF')
            sysSigRef.text = "/Signal/" + signal._name
            #missing:  <NETWORK-REPRESENTATION-PROPS><SW-DATA-DEF-PROPS-VARIANTS><SW-DATA-DEF-PROPS-CONDITIONAL><COMPU-METHOD-REF DEST="COMPU-METHOD">/DataType/Semantics/BLABLUB</COMPU-METHOD-REF>								<UNIT-REF DEST="UNIT">/DataType/Unit/U_specialCharUnitd_</UNIT-REF>							</SW-DATA-DEF-PROPS-CONDITIONAL></SW-DATA-DEF-PROPS-VARIANTS>					</NETWORK-REPRESENTATION-PROPS>
            sysSigRef.set('DEST','SYSTEM-SIGNAL')
        for group in frame._SignalGroups:
            signalEle = createSubElement(elements, 'I-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', group._name)
            sysSigRef = createSubElement(signalEle, 'SYSTEM-SIGNAL-REF')
            sysSigRef.text = "/Signal/" + group._name
            sysSigRef.set('DEST','SYSTEM-SIGNAL-GROUP')

    #
    #AR-PACKAGE Signal
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Signal')
    elements = createSubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            signalEle = createSubElement(elements, 'SYSTEM-SIGNAL')
            createSubElement(signalEle, 'SHORT-NAME', signal._name)
            if signal._comment:
                desc = createSubElement(signalEle, 'DESC')
                l2 = createSubElement(desc, 'L-2')
                l2.set("L","FOR-ALL")
                l2.text = signal._comment
            if arVersion[0] == "3":
                dataTypeRef = createSubElement(signalEle, 'DATA-TYPE-REF')
                dataTypeRef.set('DEST','INTEGER-TYPE')
                dataTypeRef.text = "/DataType/" + signal._name
                createSubElement(signalEle, 'LENGTH', str(signal._signalsize))
        for group in frame._SignalGroups:
            groupEle = createSubElement(elements, 'SYSTEM-SIGNAL-GROUP')
            createSubElement(signalEle, 'SHORT-NAME', group._name)
            if arVersion[0] == "3":
                dataTypeRef.set('DEST','INTEGER-TYPE')
            sysSignalRefs = createSubElement(groupEle, 'SYSTEM-SIGNAL-REFS')
            for member in group._members:
                memberEle = createSubElement(sysSignalRefs, 'SYSTEM-SIGNAL-REF')
                memberEle.set('DEST','SYSTEM-SIGNAL')
                memberEle.text = "/Signal/" + member._name

#                       initValueRef = createSubElement(signalEle, 'INIT-VALUE-REF')
#                       initValueRef.set('DEST','INTEGER-LITERAL')
#                       initValueRef.text = "/CONSTANTS/" + signal._name


    #
    #AR-PACKAGE Datatype
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'DataType')
    elements = createSubElement(arPackage,'ELEMENTS')
    
    if arVersion[0] == "3":
        for frame in db._fl._list:
            for signal in frame._signals:
                intType = createSubElement(elements,'INTEGER-TYPE')
                createSubElement(intType, 'SHORT-NAME', signal._name)
                swDataDefProps = createSubElement(intType,'SW-DATA-DEF-PROPS')
                compuMethodRef = createSubElement(swDataDefProps,'COMPU-METHOD-REF')
                compuMethodRef.set('DEST','COMPU-METHOD')
                compuMethodRef.text = "/DataType/Semantics/" + signal._name
    else:
        # SW-BASE-TYPE missing
        pass
        #TODO

    if arVersion[0] == "3":
        subpackages = createSubElement(arPackage,'SUB-PACKAGES')
    else:
        subpackages = createSubElement(arPackage,'AR-PACKAGES')
    arPackage = createSubElement(subpackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Semantics')
    elements = createSubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            compuMethod = createSubElement(elements,'COMPU-METHOD')
            createSubElement(compuMethod, 'SHORT-NAME', signal._name)
            #missing: UNIT-REF
            compuIntToPhys = createSubElement(compuMethod,'COMPU-INTERNAL-TO-PHYS')
            compuScales = createSubElement(compuIntToPhys,'COMPU-SCALES')
            for value in sorted(signal._values, key=lambda x: int(x)):
                compuScale = createSubElement(compuScales,'COMPU-SCALE')
                desc = createSubElement(compuScale,'DESC')
                l2 = createSubElement(desc,'L-2')
                l2.set('L','FOR-ALL')
                l2.text = signal._values[value]
                createSubElement(compuScale, 'LOWER-LIMIT', str(value))
                createSubElement(compuScale, 'UPPER-LIMIT', str(value))
                compuConst = createSubElement(compuScale,'COMPU-CONST')
                createSubElement(compuConst, 'VT', signal._values[value])
            else:
                compuScale = createSubElement(compuScales,'COMPU-SCALE')
#                createSubElement(compuScale, 'LOWER-LIMIT', str(#TODO))
#                createSubElement(compuScale, 'UPPER-LIMIT', str(#TODO))              
                compuRationslCoeff = createSubElement(compuScale,'COMPU-RATIONAL-COEFFS')
                compuNumerator = createSubElement(compuRationslCoeff,'COMPU-NUMERATOR')
                createSubElement(compuNumerator, 'V', "%g" % signal._offset)
                createSubElement(compuNumerator, 'V', "%g" % signal._factor)
                compuDenomiator = createSubElement(compuRationslCoeff,'COMPU-DENOMINATOR')
                createSubElement(compuDenomiator, 'V', "1")
    #missing AR-PACKAGE Unit

    txIPduGroups = {}
    rxIPduGroups = {}

    #
    #AR-PACKAGE ECU
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'ECU')
    elements = createSubElement(arPackage,'ELEMENTS')
    for ecu in db._BUs._list:
        ecuInstance = createSubElement(elements,'ECU-INSTANCE')
        createSubElement(ecuInstance, 'SHORT-NAME', ecu._name)
        if ecu._comment:
            desc = createSubElement(ecuInstance,'DESC')
            l2 = createSubElement(desc,'L-2')
            l2.set('L','FOR-ALL')
            l2.text = ecu._comment

        if arVersion[0] == "3":
            assoIpduGroupRefs = createSubElement(ecuInstance,'ASSOCIATED-I-PDU-GROUP-REFS')
            connectors = createSubElement(ecuInstance,'CONNECTORS')
            commConnector = createSubElement(connectors,'COMMUNICATION-CONNECTOR')
        else:
            assoIpduGroupRefs = createSubElement(ecuInstance,'ASSOCIATED-COM-I-PDU-GROUP-REFS')
            connectors = createSubElement(ecuInstance,'CONNECTORS')
            commConnector = createSubElement(connectors,'CAN-COMMUNICATION-CONNECTOR')

        createSubElement(commConnector, 'SHORT-NAME', 'CN_' + ecu._name)
        ecuCommPortInstances = createSubElement(commConnector,'ECU-COMM-PORT-INSTANCES')

        recTemp = None
        sendTemp = None


        for frame in db._fl._list:
            if ecu._name in frame._Transmitter:
                frameport = createSubElement(ecuCommPortInstances,'FRAME-PORT')
                createSubElement(frameport, 'SHORT-NAME', frame._name)
                createSubElement(frameport, 'COMMUNICATION-DIRECTION', 'OUT')
                sendTemp = 1
                if ecu._name + "_Tx" not in txIPduGroups:
                    txIPduGroups[ecu._name + "_Tx"] = []
                txIPduGroups[ecu._name + "_Tx"].append(frame._name)

                #missing I-PDU-PORT
                for signal in frame._signals:
                    if arVersion[0] == "3":
                       signalPort = createSubElement(ecuCommPortInstances,'SIGNAL-PORT')
                    else:
                       signalPort = createSubElement(ecuCommPortInstances,'I-SIGNAL-PORT')

                    createSubElement(signalPort, 'SHORT-NAME', signal._name)
                    createSubElement(signalPort, 'COMMUNICATION-DIRECTION', 'OUT')
            if ecu._name in frame._receiver:
                frameport = createSubElement(ecuCommPortInstances,'FRAME-PORT')
                createSubElement(frameport, 'SHORT-NAME', frame._name)
                createSubElement(frameport, 'COMMUNICATION-DIRECTION', 'IN')
                recTemp = 1
                if  ecu._name + "_Tx" not in rxIPduGroups:
                    rxIPduGroups[ecu._name + "_Rx"] = []
                rxIPduGroups[ecu._name + "_Rx"].append(frame._name)

                #missing I-PDU-PORT
                for signal in frame._signals:
                    if ecu._name in signal._receiver:
                        if arVersion[0] == "3":
                          signalPort = createSubElement(ecuCommPortInstances,'SIGNAL-PORT')
                        else:
                          signalPort = createSubElement(ecuCommPortInstances,'I-SIGNAL-PORT')

                        createSubElement(signalPort, 'SHORT-NAME', signal._name)
                        createSubElement(signalPort, 'COMMUNICATION-DIRECTION', 'IN')

        if recTemp is not None:
            if arVersion[0] == "3":
                assoIpduGroupRef = createSubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            else:
                assoIpduGroupRef = createSubElement(assoIpduGroupRefs,'ASSOCIATED-COM-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-SIGNAL-I-PDU-GROUP")

            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Rx"

        if sendTemp is not None:
            if arVersion[0] == "3":
                assoIpduGroupRef = createSubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            else:
                assoIpduGroupRef = createSubElement(assoIpduGroupRefs,'ASSOCIATED-COM-I-PDU-GROUP-REF')
                assoIpduGroupRef.set('DEST',"I-SIGNAL-I-PDU-GROUP")
            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Tx"


    #
    #AR-PACKAGE IPDUGroup
    #
    arPackage = createSubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'IPDUGroup')
    elements = createSubElement(arPackage,'ELEMENTS')
    for pdugrp in txIPduGroups:
        if arVersion[0] == "3":
            ipduGrp = createSubElement(elements,'I-PDU-GROUP')
        else:
            ipduGrp = createSubElement(elements,'I-SIGNAL-I-PDU-GROUP')

        createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
        createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "OUT")

        if arVersion[0] == "3":
            ipduRefs = createSubElement(ipduGrp,'I-PDU-REFS')
            for frame in txIPduGroups[pdugrp]:
                ipduRef = createSubElement(ipduRefs,'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
        else:
            isignalipdus = createSubElement(ipduGrp,'I-SIGNAL-I-PDUS')
            for frame in txIPduGroups[pdugrp]:
                isignalipdurefconditional = createSubElement(isignalipdus,'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipduRef = createSubElement(isignalipdurefconditional,'I-SIGNAL-I-PDU-REF')
                ipduRef.set('DEST', "I-SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
            


    if arVersion[0] == "3":
        for pdugrp in rxIPduGroups:
            ipduGrp = createSubElement(elements,'I-PDU-GROUP')
            createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
            createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")

            ipduRefs = createSubElement(ipduGrp,'I-PDU-REFS')
            for frame in rxIPduGroups[pdugrp]:
                ipduRef = createSubElement(ipduRefs,'I-PDU-REF')
                ipduRef.set('DEST', "SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
    else:
        for pdugrp in rxIPduGroups:
            ipduGrp = createSubElement(elements,'I-SIGNAL-I-PDU-GROUP')
            createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
            createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")
            isignalipdus = createSubElement(ipduGrp,'I-SIGNAL-I-PDUS')
            for frame in rxIPduGroups[pdugrp]:
                isignalipdurefconditional = createSubElement(isignalipdus,'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipduRef = createSubElement(isignalipdurefconditional,'I-SIGNAL-I-PDU-REF')
                ipduRef.set('DEST', "I-SIGNAL-I-PDU")
                ipduRef.text = "/PDU/PDU_" + frame
 
    f = open(filename,"wb");
    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True))

