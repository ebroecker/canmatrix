#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
logger = logging.getLogger('root')

from builtins import *
import math
from lxml import etree
from .canmatrix import *
from .autosarhelper import *

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
# this script imports arxml-files to a canmatrix-object
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
#


#TODO Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;

signalRxs = {}

def getSysSignals(syssignal, syssignalarray, Bo, Id, ns):
    members = []
    for signal in syssignalarray:
        members.append(arGetName(signal, ns))
    Bo.addSignalGroup( arGetName(syssignal, ns), 1, members)


def getSignals(signalarray, Bo, arDict, ns, multiplexId):
    GroupId = 1
    for signal in signalarray:
        values = {}
        motorolla = arGetChild(signal, "PACKING-BYTE-ORDER", arDict, ns)
        startBit = arGetChild(signal, "START-POSITION", arDict, ns)
        isignal = arGetChild(signal, "SIGNAL", arDict, ns)
        if isignal == None:
            isignal = arGetChild(signal, "I-SIGNAL", arDict, ns)
        if isignal == None:
            isignal = arGetChild(signal, "I-SIGNAL-GROUP", arDict, ns)
            if isignal != None:
                isignalarray = arGetXchildren(isignal, "I-SIGNAL", arDict, ns)
                getSysSignals(isignal, isignalarray, Bo, GroupId, ns)
                GroupId = GroupId + 1
                continue
        if isignal == None:
            logger.debug('Frame %s, no isignal for %s found', Bo._name, arGetChild(signal,  "SHORT-NAME", arDict, ns).text)
        syssignal = arGetChild(isignal, "SYSTEM-SIGNAL", arDict, ns)
        if syssignal == None:
            logger.debug('Frame %s, signal %s has no systemsignal', isignal.tag, Bo._name)

        if "SYSTEM-SIGNAL-GROUP" in  syssignal.tag:
            syssignalarray = arGetXchildren(syssignal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", arDict, ns)
            getSysSignals(syssignal, syssignalarray, Bo, GroupId, ns)
            GroupId = GroupId + 1
            continue

        length = arGetChild(isignal,  "LENGTH", arDict, ns)
        if length == None:
            length = arGetChild(syssignal,  "LENGTH", arDict, ns)
        name = arGetChild(syssignal,  "SHORT-NAME", arDict, ns)
  
        Min = None
        Max = None
        factor = 1.0
        offset = 0
        Unit = ""
        receiver = []

        signalDescription = getDesc(syssignal, arDict, ns)

        datatype = arGetChild(syssignal, "DATA-TYPE", arDict, ns)

        lower = arGetChild(datatype, "LOWER-LIMIT", arDict, ns)
        upper = arGetChild(datatype, "UPPER-LIMIT", arDict, ns)
        if lower is not None and upper is not None:
            Min =  int(lower.text)
            Max = int(upper.text)

        datdefprops = arGetChild(datatype, "SW-DATA-DEF-PROPS", arDict, ns)


        compmethod = arGetChild(datdefprops, "COMPU-METHOD", arDict, ns)
        unit = arGetChild(compmethod, "UNIT", arDict, ns)
        if unit is not None:
            longname = arGetChild(unit, "LONG-NAME", arDict, ns)
            l4 = arGetChild(longname, "L-4", arDict, ns)
            if l4 is not None:
                Unit = l4.text

        compuscales = arGetXchildren(compmethod, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE", arDict, ns)
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

            if ll is not None and desc is not None and int(ul.text) == int(ll.text):
                values[ll.text] = desc

            scaleDesc = getDesc(compuscale, arDict, ns)
            rational = arGetChild(compuscale, "COMPU-RATIONAL-COEFFS", arDict, ns)
            if rational is not None:
                numerator = arGetChild(rational, "COMPU-NUMERATOR", arDict, ns)
                zaehler = arGetChildren(numerator, "V", arDict, ns)
                denominator = arGetChild(rational, "COMPU-DENOMINATOR", arDict, ns)
                nenner = arGetChildren(denominator, "V", arDict, ns)

                factor = float(zaehler[1].text) / float(nenner[0].text)
                offset = float(zaehler[0].text)
            else:
                const = arGetChild(compuscale, "COMPU-CONST", arDict, ns)
                # value hinzufuegen
                if const is None:
                    logger.warn("unknown Compu-Method: " + compmethod.get('UUID'))
        is_little_endian = False
        if motorolla.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False # unsigned
        if name == None:
            logger.debug('no name for signal given')
        if startBit == None:
            logger.debug('no startBit for signal given')
        if length == None:
            logger.debug('no length for signal given')

        if startBit is not None:
            newSig = Signal(name.text, 
                                  startBit = startBit.text, 
                                  signalSize = length.text,
                                  is_little_endian=is_little_endian, 
                                  is_signed = is_signed, 
                                  factor=factor, 
                                  offset=offset,
                                  min=Min,
                                  max=Max,
                                  unit=Unit,
                                  receiver=receiver,
                                  multiplex=multiplexId)     
 
            if newSig._is_little_endian == 0:
                # startbit of motorola coded signals are MSB in arxml
                newSig.setMsbStartbit(int(startBit.text))                
            
            newSig._isigRef = isignal.text
            signalRxs[isignal.text] = newSig

            basetype = arGetChild(datdefprops, "BASE-TYPE", arDict, ns)
            if basetype is not None:
                temp = arGetChild(basetype, "SHORT-NAME", arDict, ns)
                if temp is not None and "boolean" == temp.text:
                    newSig.addValues(1,"TRUE")
                    newSig.addValues(0,"FALSE")

            if initvalue is not None and initvalue.text is not None:
                if initvalue.text == "false":
                    initvalue.text = "0"
                elif initvalue.text == "true":
                    initvalue.text = "1"
                newSig._initValue = int(initvalue.text)
                newSig.addAttribute("GenSigStartValue", str(newSig._initValue))
            else:
                newSig._initValue = 0

            for key,value in list(values.items()):
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
        pdumapping = arGetChild(pdumappings, "PDU-TO-FRAME-MAPPING", arDict, ns)
        pdu = arGetChild(pdumapping, "PDU", arDict, ns) # SIGNAL-I-PDU
#        newBo = Frame(idNum, arGetName(frameR, ns), int(dlc.text), None)
        newBo = Frame(arGetName(frameR, ns), 
                      Id=idNum,
                      dlc=int(dlc.text))
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF" % (sn))        
        ipduTriggeringRefs = arGetChild(frameTriggering, "I-PDU-TRIGGERING-REFS", arDict, ns)
        ipduTriggering = arGetChild(ipduTriggeringRefs, "I-PDU-TRIGGERING", arDict, ns)
        pdu = arGetChild(ipduTriggering, "I-PDU", arDict, ns)
        dlc = arGetChild(pdu, "LENGTH", arDict, ns)
#        newBo = Frame(idNum, sn.text, int(int(dlc.text)/8), None)
        newBo = Frame(sn.text, 
                      Id=idNum,
                      dlc=int(dlc.text)/8)
        
        if pdu == None:
            logger.error("ERROR: pdu")
        else:
            logger.debug (arGetName(pdu, ns))
 

    if "MULTIPLEXED-I-PDU" in pdu.tag:
        selectorByteOrder = arGetChild(pdu, "SELECTOR-FIELD-BYTE-ORDER", arDict, ns)
        selectorLen = arGetChild(pdu, "SELECTOR-FIELD-LENGTH", arDict, ns)
        selectorStart = arGetChild(pdu, "SELECTOR-FIELD-START-POSITION", arDict, ns)
        is_little_endian = False
        if selectorByteOrder.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False # unsigned
        multiplexor = Signal("Multiplexor", 
                              startBit = selectorStart.text, 
                              signalSize = selectorLen.text,
                              is_little_endian=is_little_endian, 
                              multiplex="Multiplexor")     

        multiplexor._initValue = 0
        newBo.addSignal(multiplexor)
        staticPart = arGetChild(pdu, "STATIC-PART", arDict, ns)
        ipdu = arGetChild(staticPart, "I-PDU", arDict, ns)
        if ipdu is not None:
            pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
            pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
            getSignals(pdusigmapping, newBo, arDict, ns, None)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu,ns)

        dynamicPart = arGetChild(pdu, "DYNAMIC-PART", arDict, ns)
#               segmentPositions = arGetChild(dynamicPart, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamicPartAlternatives = arGetChild(dynamicPart, "DYNAMIC-PART-ALTERNATIVES", arDict, ns)
        dynamicPartAlternativeList = arGetChildren(dynamicPartAlternatives, "DYNAMIC-PART-ALTERNATIVE", arDict, ns)
        for alternative in dynamicPartAlternativeList:
            selectorId = arGetChild(alternative, "SELECTOR-FIELD-CODE", arDict, ns)
            ipdu = arGetChild(alternative, "I-PDU", arDict, ns)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu,ns)
            if ipdu is not None:
                pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
                pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                getSignals(pdusigmapping, newBo, arDict, ns, selectorId.text)

    newBo.addComment(getDesc(pdu, arDict, ns))

    if extEle is not None:
        if extEle.text == 'EXTENDED':
            newBo._extended = 1

    timingSpec = arGetChild(pdu,"I-PDU-TIMING-SPECIFICATION", arDict, ns)
    cyclicTiming = arGetChild(timingSpec,"CYCLIC-TIMING", arDict, ns)
    repeatingTime = arGetChild(cyclicTiming,"REPEATING-TIME", arDict, ns)

    eventTiming = arGetChild(timingSpec,"EVENT-CONTROLLED-TIMING", arDict, ns)
    repeats = arGetChild(eventTiming, "NUMBER-OF-REPEATS", arDict, ns)
    minimumDelay = arGetChild(timingSpec,"MINIMUM-DELAY", arDict, ns)
    startingTime = arGetChild(timingSpec,"STARTING-TIME", arDict, ns)

    if cyclicTiming is not None and eventTiming is not None:
        newBo.addAttribute("GenMsgSendType", "5")        # CycleAndSpontan
        if minimumDelay is not None:
            newBo.addAttribute("GenMsgDelayTime", str(int(float(minimumDelay.text)*1000)))
        if repeats is not None:
            newBo.addAttribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclicTiming is not None:
        newBo.addAttribute("GenMsgSendType", "0") # CycleX
        if minimumDelay is not None:
            newBo.addAttribute("GenMsgDelayTime", str(int(float(minimumDelay.text)*1000)))
        if repeats is not None:
            newBo.addAttribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        newBo.addAttribute("GenMsgSendType", "1") # Spontan
        if minimumDelay is not None:
            newBo.addAttribute("GenMsgDelayTime", str(int(float(minimumDelay.text)*1000)))
        if repeats is not None:
            newBo.addAttribute("GenMsgNrOfRepetitions", repeats.text)


    if startingTime is not None:
        value = arGetChild(startingTime,"VALUE", arDict, ns)
        newBo.addAttribute("GenMsgStartDelayTime", str(int(float(value.text)*1000)))



    value = arGetChild(repeatingTime,"VALUE", arDict, ns)
    if value is not None:
        newBo.addAttribute("GenMsgCycleTime",str(int(float(value.text)*1000)))

#    pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if pdusigmappings is None or pdusigmappings.__len__() == 0:
#        logger.debug("DEBUG: Frame %s no SIGNAL-TO-PDU-MAPPINGS found" % (newBo._name))
    pdusigmapping = arGetChildren(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
    if pdusigmapping is None or pdusigmapping.__len__() == 0:
        logger.debug("DEBUG: Frame %s no I-SIGNAL-TO-I-PDU-MAPPING found" % (newBo._name))
    getSignals(pdusigmapping, newBo, arDict, ns, None)
    return newBo

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
    #TODO: use diagAddress for frame-classification
    commconnector = arGetChild(connectors, "COMMUNICATION-CONNECTOR", arDict, ns)
    nmAddress = arGetChild(commconnector, "NM-ADDRESS", arDict, ns)
    assocRefs = arGetChild(ecu, "ASSOCIATED-I-PDU-GROUP-REFS", arDict, ns)
    assoc = arGetChildren(assocRefs, "ASSOCIATED-I-PDU-GROUP", arDict, ns)
    inFrame = []
    outFrame = []

    for ref in assoc:
        direction = arGetChild(ref, "COMMUNICATION-DIRECTION", arDict, ns)
        groupRefs = arGetChild(ref, "CONTAINED-I-PDU-GROUPS-REFS", arDict, ns)
        pdurefs = arGetChild(ref, "I-PDU-REFS", arDict, ns)

        #local defined pdus
        pdus = arGetChildren(pdurefs, "I-PDU", arDict, ns)
        for pdu in pdus:
            if direction.text == "IN":
                inFrame.append(arGetName(pdu, ns))
            else:
                outFrame.append(arGetName(pdu, ns))

        #grouped pdus
        group = arGetChildren(groupRefs, "CONTAINED-I-PDU-GROUPS", arDict, ns)
        for t in group:
            if direction is None:
                direction = arGetChild(t, "COMMUNICATION-DIRECTION", arDict, ns)
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
                #print "out not found: " + out

#               for inf in inFrame:
#                       if inf in multiplexTranslation:
#                               inf = multiplexTranslation[inf]
#                       frame = db.frameByName(inf)
#                       if frame is not None:
#                               for signal in frame._signals:
#                                       rec_name = arGetName(ecu, ns)
#                                       if rec_name not in  signal._receiver:
#                                               signal._receiver.append(rec_name)
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

def importArxml(filename, **options):
    if 'arxmlIgnoreClusterInfo' in options:
        ignoreClusterInfo=options["arxmlIgnoreClusterInfo"]
    else:
        ignoreClusterInfo=False

    result = {}
    logger.debug("Read arxml ...")
    tree = etree.parse(filename)

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
    logger.debug("DEBUG %d can-frame-triggering in arxml..." % (canTriggers.__len__()))    

    sigpdumap = root.findall('.//' + ns + 'SIGNAL-TO-PDU-MAPPINGS')
    logger.debug("DEBUG %d SIGNAL-TO-PDU-MAPPINGS in arxml..." % (sigpdumap.__len__()))  

    sigIpdu = root.findall('.//' + ns + 'I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug("DEBUG %d I-SIGNAL-TO-I-PDU-MAPPING in arxml..." % (sigIpdu.__len__()))  
  

    if ignoreClusterInfo == True:
        ccs = {"ignoreClusterInfo"}    
    else:
        ccs = root.findall('.//' + ns + 'CAN-CLUSTER')
    for cc in ccs:
        db = CanMatrix()
#Defines not jet imported...
        db.addBUDefines("NWM-Stationsadresse",  'HEX 0 63')
        db.addBUDefines("NWM-Knoten",  'ENUM  "nein","ja"')
        db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')
        db.addFrameDefines("GenMsgDelayTime",  'INT 0 65535')
        db.addFrameDefines("GenMsgNrOfRepetitions",  'INT 0 65535')
        db.addFrameDefines("GenMsgStartValue",  'STRING')
        db.addFrameDefines("GenMsgSendType",  'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
        db.addSignalDefines("GenSigStartValue", 'HEX 0 4294967295')

        if ignoreClusterInfo == True:
            canframetrig = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
            busname = ""
        else:
            speed = arGetChild(cc, "SPEED", arDict, ns)
            logger.debug("Busname: " + arGetName(cc,ns))
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            busname = arGetName(cc,ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

#            physicalChannels = arGetChild(cc, "PHYSICAL-CHANNELS", arDict, ns)
            physicalChannels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")
            if physicalChannels == None:
                logger.error("Error - PHYSICAL-CHANNELS not found")

            nmLowerId = arGetChild(cc, "NM-LOWER-CAN-ID", arDict, ns)

            physicalChannel = arGetChild(physicalChannels, "PHYSICAL-CHANNEL", arDict, ns)
            if physicalChannel == None:
                physicalChannel = arGetChild(physicalChannels, "CAN-PHYSICAL-CHANNEL", arDict, ns)
            if physicalChannel == None:
                logger.debug("Error - PHYSICAL-CHANNEL not found")
#            frametriggerings = arGetChild(physicalChannel, "FRAME-TRIGGERINGSS", arDict, ns)
#            if frametriggerings == None:
#                logger.debug("Error - FRAME-TRIGGERINGS not found")
            canframetrig = arGetChildren(physicalChannel, "CAN-FRAME-TRIGGERING", arDict, ns)
            if canframetrig == None:
                logger.error("Error - CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug("%d frames found in arxml\n" % (canframetrig.__len__()))

        multiplexTranslation = {}
        for frameTrig in canframetrig:
            db._fl.addFrame(getFrame(frameTrig, arDict,multiplexTranslation, ns))


        if ignoreClusterInfo == True:
            pass
            # no support for signal direction 
        else:
            isignaltriggerings = arGetXchildren(physicalChannel, "I-SIGNAL-TRIGGERING", arDict, ns)
            for sigTrig in isignaltriggerings:
                isignal = arGetChild(sigTrig, 'SIGNAL', arDict, ns)
                if isignal == None:
                    isignal = arGetChild(sigTrig, 'I-SIGNAL', arDict, ns)  
                if isignal == None:
                    logger.debug("no isignal for %s" % arGetName(sigTrig, ns))
                    continue
                portRef =  arGetChildren(sigTrig, "I-SIGNAL-PORT", arDict, ns)

                for port in portRef:
                    comDir = arGetChild(port, "COMMUNICATION-DIRECTION", arDict, ns)
                    if comDir.text == "IN":
                        ecuName = arGetName(port.getparent().getparent().getparent().getparent(), ns)
                        if isignal.text in signalRxs:
                            if ecuName not in signalRxs[isignal.text]._receiver:
                                signalRxs[isignal.text]._receiver.append(ecuName)
    #                               for fr in db._fl._list:
    #                                       for sig in fr._signals:
    #                                               if hasattr(sig, "_isigRef")  and sig._isigRef == isignal.text:
    #                                                       sig._receiver.append(ecuName)
                        #TODO

    # find ECUs:
        nodes = root.findall('.//' + ns +'ECU-INSTANCE')
        for node in nodes:
            bu = processEcu(node, db, arDict, multiplexTranslation, ns)
            db._BUs.add(bu)

        for bo in db._fl._list:
            frame = [0, 0, 0, 0, 0, 0, 0, 0]
            for sig in bo._signals:
                if sig._initValue != 0:
                    putSignalValueInFrame(sig.getLsbStartbit(), sig._signalsize, sig._is_little_endian, sig._initValue, frame)
            hexStr = '"'
            for i in range(bo._Size):
                hexStr += "%02X" % frame[i]
            hexStr += '"'
            bo.addAttribute("GenMsgStartValue", hexStr)

        result[busname] = db
    return result
