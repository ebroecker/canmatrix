#!/usr/bin/env python
from lxml import etree
from canmatrix import *
from autosarhelper import *

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


#TODO default-frame-info for CAN-Simulation Motorola format is missing (only default signals available => calculation required
#TODO Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;  
#TODO recievers of signals are missing
#TODO MULTIPLEXED-I-PDU support!

def getSignals(signalarray, Bo, arDict, ns):
	for signal in signalarray:	
		values = {}
		motorolla = arGetChild(signal, "PACKING-BYTE-ORDER", arDict, ns)
		startBit = arGetChild(signal, "START-POSITION", arDict, ns)
		isignal = arGetChild(signal, "SIGNAL", arDict, ns)
		syssignal = arGetChild(isignal, "SYSTEM-SIGNAL", arDict, ns)
		length = arGetChild(syssignal,  "LENGTH", arDict, ns)
		name = arGetChild(syssignal,  "SHORT-NAME", arDict, ns)

		Min = 0
		Max = 1
		factor = 1.0
		offset = 0
		Unit = ""
		Reciever = []

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

		int2phy = arGetChild(compmethod, "COMPU-INTERNAL-TO-PHYS", arDict, ns)
		compuscalescontainer = arGetChild(int2phy, "COMPU-SCALES", arDict, ns)
		compuscales = arGetChildren(compuscalescontainer, "COMPU-SCALE", arDict, ns)

		initvalueelement = arGetChild(syssignal, "INIT-VALUE", arDict, ns)
		initvalue = arGetChild(initvalueelement, "VALUE", arDict, ns)

		for compuscale in compuscales:	
			ll = arGetChild(compuscale, "LOWER-LIMIT", arDict, ns)
			ul = arGetChild(compuscale, "UPPER-LIMIT", arDict, ns)
			sl = arGetChild(compuscale, "SHORT-LABEL", arDict, ns)

			if ll is not None and sl is not None and int(ul.text) == int(ll.text):
				values[ll.text] = sl.text			
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
					print "unknown Compu-Method: " + compmethod.get('UUID')
		byteorder = 0		
		if motorolla.text == 'MOST-SIGNIFICANT-BYTE-LAST':
			byteorder = 1	
		valuetype = '+' # unsigned
		if startBit is not None:
			newSig = Signal(name.text, startBit.text, length.text, byteorder, valuetype, factor, offset, Min, Max, Unit, Reciever)
			
			if initvalue is not None:
				if initvalue.text == "false":
					initvalue.text = "0"
				elif initvalue.text == "true":
					initvalue.text = "1"
				newSig._initValue = int(initvalue.text)
			else:
				newSig._initValue = 0
			#newSig Description, 
			for key,value in values.items():			
				newSig.addValues(key, value)
			Bo.addSignal(newSig)

def getFrame(frame, arDict, ns):
	extEle = arGetChild(frame, "CAN-ADDRESSING-MODE", arDict, ns)
	idele = arGetChild(frame, "IDENTIFIER", arDict, ns)
	frameR = arGetChild(frame, "FRAME", arDict, ns)
	dlc = arGetChild(frameR, "FRAME-LENGTH", arDict, ns)
	pdumappings = arGetChild(frameR, "PDU-TO-FRAME-MAPPINGS", arDict, ns)
	pdumapping = arGetChild(pdumappings, "PDU-TO-FRAME-MAPPING", arDict, ns)
	pdu = arGetChild(pdumapping, "PDU", arDict, ns) # SIGNAL-I-PDU
	
	sn = arGetChild(frame, "SHORT-NAME", arDict, ns)
	if "MULTIPLEXED-I-PDU" in pdu.tag:
		sn = arGetChild(pdu, "SHORT-NAME", arDict, ns)
		print "multiplex not supportet yet: " + sn.text

	idNum = int(idele.text)


	newBo = Botschaft(idNum, arGetName(pdu, ns), int(dlc.text), None) 
#	newBo.addComment(getDesc(frame, arDict, ns))
	
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
		newBo.addAttribute("GenMsgSendType", "5")	 # CycleAndSpontan
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

	pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
	pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
	getSignals(pdusigmapping, newBo, arDict, ns)
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

def processEcu(ecu, db, arDict, ns):
#	print arGetName(ecu, ns) + ":"
	connectors = arGetChild(ecu, "CONNECTORS", arDict, ns)
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
			frame = db._bl.byName(out)
			if frame is not None:
				frame.addTransmitter(arGetName(ecu, ns))
			else:
				print "not found: " + out 

		for inf in inFrame:
			frame = db._bl.byName(inf)
			if frame is not None:
				for signal in frame._signals:
					signal._reciever.append(arGetName(ecu, ns))
			else:
				print "not found: " + inf
	bu = BoardUnit(arGetName(ecu, ns))
	if nmAddress is not None:
		bu.addAttribute("NWM-Stationsadresse", nmAddress.text)
		bu.addAttribute("NWM-Knoten", "1")
	else:
		bu.addAttribute("NWM-Stationsadresse", "0")
		bu.addAttribute("NWM-Knoten", "0")
	return bu
		
def importArxml(filename):
	db = CanMatrix() 

	print "Read arxml ..."
	tree = etree.parse(filename)
	root = tree.getroot()
	print " Done\n"

	ns = "{" + tree.xpath('namespace-uri(.)') + "}"
	nsp = tree.xpath('namespace-uri(.)')

	topLevelPackages = root.find('./' + ns + 'TOP-LEVEL-PACKAGES')

	print "Build arTree ..."
	arDict = arTree()
	arParseTree(topLevelPackages, arDict, ns)
	print " Done\n"


	cc = root.find('.//' + ns + 'CAN-CLUSTER')
	speed = arGetChild(cc, "SPEED", arDict, ns)
	print "Busname: " + arGetName(cc,ns) + " Speed: " + speed.text
	physicalChannels = arGetChild(cc, "PHYSICAL-CHANNELS", arDict, ns)
	nmLowerId = arGetChild(cc, "NM-LOWER-CAN-ID", arDict, ns)
	
	physicalChannel = arGetChild(physicalChannels, "PHYSICAL-CHANNEL", arDict, ns)
	frametriggerings = arGetChild(physicalChannel, "FRAME-TRIGGERINGSS", arDict, ns)
	canframetrig = arGetChildren(frametriggerings, "CAN-FRAME-TRIGGERING", arDict, ns)
	
	
	for frame in canframetrig:
		db._bl.addBotschaft(getFrame(frame, arDict, ns))

	# find ECUs:
	nodes = root.findall('.//' + ns +'ECU-INSTANCE')
	for node in nodes:
		bu = processEcu(node, db, arDict, ns)			
		db._BUs.add(bu)

	for bo in db._bl._liste:
		frame = [0, 0, 0, 0, 0, 0, 0, 0]
		for sig in bo._signals:
			if sig._initValue != 0:
				putSignalValueInFrame(sig._startbit, sig._signalsize, sig._byteorder, sig._initValue, frame)
		hexStr = '"'
		for i in range(bo._Size):
			hexStr += "%02X" % frame[i]
		hexStr += '"'
		bo.addAttribute("GenMsgStartValue", hexStr)
		
	return db	

