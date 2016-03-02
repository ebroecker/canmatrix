from __future__ import absolute_import
from builtins import *
#!/usr/bin/env python
from lxml import etree
from .canmatrix import *
from .autosarhelper import *
from .importdbc import *

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
#

#TODO Well, ..., this is the first attempt to export a arxml-file; I did this without reading any spec;
#TODO receivers of signals are missing

def createSubElement(elem, strElement, strName):
    sn = etree.SubElement(elem, strElement)
    sn.text = str(strName)


def exportArxml(db, filename):
    # create XML
    for frame in db._fl._list:
        for signal in frame._signals:
            for rec in signal._receiver:
                if rec.strip() not in frame._receiver:
                    frame._receiver.append(rec.strip())

    root = etree.Element('AUTOSAR')
# xsi:schemaLocation="http://autosar.org/3.1.4.DAI.3 AUTOSAR_314DAI3.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#       root.set("xmlns","http://autosar.org/3.1.4")
#       NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
#       root.set(NS_XSI + "schemaLocation", "Definition.xsd")

    toplevelPackages = etree.SubElement(root,'TOP-LEVEL-PACKAGES')

    #
    #AR-PACKAGE Cluster
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Cluster')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    cancluster = etree.SubElement(elements,'CAN-CLUSTER')
    createSubElement(cancluster, 'SHORT-NAME', 'CAN')
#TODO: insert Speed - if possible
    createSubElement(cancluster, 'SPEED', '50000')
    physicalChannels = etree.SubElement(cancluster, 'PHYSICAL-CHANNELS')
    physicalChannel = etree.SubElement(physicalChannels, 'PHYSICAL-CHANNEL')
    createSubElement(physicalChannels, 'SHORT-NAME', 'CAN')
    frameTriggering = etree.SubElement(physicalChannel, 'FRAME-TRIGGERINGSS')
    for frame in db._fl._list:
        canFrameTriggering = etree.SubElement(frameTriggering, 'CAN-FRAME-TRIGGERING')
        createSubElement(canFrameTriggering, 'SHORT-NAME', frame._name)
        createSubElement(canFrameTriggering, 'IDENTIFIER', str(frame._Id))
        if frame._extended == 0:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
        else:
            createSubElement(canFrameTriggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')
        frameRef = etree.SubElement(canFrameTriggering, 'FRAME-REF')
        frameRef.set('DEST','FRAME')
        frameRef.text = "/Frame/FRAME_" + frame._name

        pduTriggeringRefs = etree.SubElement(canFrameTriggering, 'I-PDU-TRIGGERING-REFS')
        pduTriggeringRef = etree.SubElement(pduTriggeringRefs, 'I-PDU-TRIGGERING-REF')
        pduTriggeringRef.set('DEST','I-PDU-TRIGGERING')
        pduTriggeringRef.text = "/Cluster/CAN/IPDUTRIGG_" + frame._name

        framePortRefs = etree.SubElement(canFrameTriggering, 'FRAME-PORT-REFS')
        for transmitter in frame._Transmitter:
            framePortRef = etree.SubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + transmitter + "/" + frame._name
        for rec in frame._receiver:
            framePortRef = etree.SubElement(framePortRefs, 'FRAME-PORT-REF')
            framePortRef.set('DEST','FRAME-PORT')
            framePortRef.text = "/ECU/" + rec + "/" + frame._name


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
    #
    #AR-PACKAGE FRAME
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'Frame')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        frameEle = etree.SubElement(elements,'FRAME')
        createSubElement(frameEle, 'SHORT-NAME', "FRAME_" + frame._name)
        createSubElement(frameEle, 'FRAME-LENGTH', "%d" % frame._Size)
        pdumappings = etree.SubElement(frameEle, 'PDU-TO-FRAME-MAPPINGS')
        pdumapping = etree.SubElement(pdumappings, 'PDU-TO-FRAME-MAPPING')
        createSubElement(pdumapping, 'SHORT-NAME', frame._name)
        createSubElement(pdumapping, 'PACKING-BYTE-ORDER', "MOST-SIGNIFICANT-BYTE-LAST")
        createSubElement(pdumapping, 'START-POSITION', '0')
        pduRef = etree.SubElement(pdumapping, 'PDU-REF')
        pduRef.text = "/PDU/PDU_" + frame._name
        pduRef.set('DEST','SIGNAL-I-PDU')

    #
    #AR-PACKAGE PDU
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'PDU')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        signalIpdu = etree.SubElement(elements,'SIGNAL-I-PDU')
        createSubElement(signalIpdu, 'SHORT-NAME', "PDU_" + frame._name)
        createSubElement(signalIpdu, 'LENGTH', "%d" % int(frame._Size*8))
        # I-PDU-TIMING-SPECIFICATION
        signalToPduMappings = etree.SubElement(signalIpdu,'SIGNAL-TO-PDU-MAPPINGS')
        for signal in frame._signals:
            signalToPduMapping = etree.SubElement(signalToPduMappings,'I-SIGNAL-TO-I-PDU-MAPPING')
            createSubElement(signalToPduMapping, 'SHORT-NAME', signal._name)
            createSubElement(signalToPduMapping, 'START-POSITION', str(signal.getMsbStartbit()))
            if signal._is_little_endian == 1: # Intel
                createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-LAST')
            else: #Motorola
                createSubElement(signalToPduMapping, 'PACKING-BYTE-ORDER', 'MOST-SIGNIFICANT-BYTE-FIRST')

            # laut xsd nur signal-ref erlaubt
            signalRef = etree.SubElement(signalToPduMapping, 'SIGNAL-REF')
            signalRef.text = "/ISignal/" + signal._name
            signalRef.set('DEST','I-SIGNAL')
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
            createSubElement(signalEle, 'LENGTH', str(signal._signalsize))
            dataTypeRef = etree.SubElement(signalEle, 'DATA-TYPE-REF')
            dataTypeRef.set('DEST','INTEGER-TYPE')
            dataTypeRef.text = "/DataType/" + signal._name
        for group in frame._SignalGroups:
            groupEle = etree.SubElement(elements, 'SYSTEM-SIGNAL-GROUP')
            createSubElement(signalEle, 'SHORT-NAME', group._name)
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
    #AR-PACKAGE Datatyle
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'DataType')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for frame in db._fl._list:
        for signal in frame._signals:
            intType = etree.SubElement(elements,'INTEGER-TYPE')
            createSubElement(intType, 'SHORT-NAME', signal._name)
            swDataDefProps = etree.SubElement(intType,'SW-DATA-DEF-PROPS')
            compuMethodRef = etree.SubElement(swDataDefProps,'COMPU-METHOD-REF')
            compuMethodRef.set('DEST','COMPU-METHOD')
            compuMethodRef.text = "/DataType/Semantics/" + signal._name

    subpackages = etree.SubElement(arPackage,'SUB-PACKAGES')
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
        connectors = etree.SubElement(ecuInstance,'CONNECTORS')
        commConnector = etree.SubElement(connectors,'COMMUNICATION-CONNECTOR')
        ecuCommPortInstances = etree.SubElement(commConnector,'ECU-COMM-PORT-INSTANCES')
        assoIpduGroupRefs = etree.SubElement(ecuInstance,'ASSOCIATED-I-PDU-GROUP-REFS')

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
                    signalPort = etree.SubElement(ecuCommPortInstances,'SIGNAL-PORT')
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
                        signalPort = etree.SubElement(ecuCommPortInstances,'SIGNAL-PORT')
                        createSubElement(signalPort, 'SHORT-NAME', signal._name)
                        createSubElement(signalPort, 'COMMUNICATION-DIRECTION', 'IN')

        if recTemp is not None:
            assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
            assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Rx"

        if sendTemp is not None:
            assoIpduGroupRef = etree.SubElement(assoIpduGroupRefs,'ASSOCIATED-I-PDU-GROUP-REF')
            assoIpduGroupRef.set('DEST',"I-PDU-GROUP")
            assoIpduGroupRef.text = "/IPDUGroup/" + ecu._name + "_Tx"


    #
    #AR-PACKAGE IPDUGroup
    #
    arPackage = etree.SubElement(toplevelPackages,'AR-PACKAGE')
    createSubElement(arPackage, 'SHORT-NAME', 'IPDUGroup')
    elements = etree.SubElement(arPackage,'ELEMENTS')
    for pdugrp in txIPduGroups:
        ipduGrp = etree.SubElement(elements,'I-PDU-GROUP')
        createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
        createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "OUT")

        ipduRefs = etree.SubElement(ipduGrp,'I-PDU-REFS')
        for frame in txIPduGroups[pdugrp]:
            ipduRef = etree.SubElement(ipduRefs,'I-PDU-REF')
            ipduRef.set('DEST', "SIGNAL-I-PDU")
            ipduRef.text = "/PDU/PDU_" + frame

    for pdugrp in rxIPduGroups:
        ipduGrp = etree.SubElement(elements,'I-PDU-GROUP')
        createSubElement(ipduGrp, 'SHORT-NAME', pdugrp)
        createSubElement(ipduGrp, 'COMMUNICATION-DIRECTION', "IN")

        ipduRefs = etree.SubElement(ipduGrp,'I-PDU-REFS')
        for frame in rxIPduGroups[pdugrp]:
            ipduRef = etree.SubElement(ipduRefs,'I-PDU-REF')
            ipduRef.set('DEST', "SIGNAL-I-PDU")
            ipduRef.text = "/PDU/PDU_" + frame

    f = open(filename,"wb");
    f.write(etree.tostring(root, pretty_print=True))
