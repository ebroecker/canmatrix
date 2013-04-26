#!/usr/bin/env python
from lxml import etree
from canmatrix import *

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



#TODO default-frame-info for CAN-Simulation is missing (only default signals available => calculation required
#TODO Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;  
#TODO sender of frames and recievers of signals are missing

class arTree:
	def __init__(self,name="", ref=None):
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
		if name is not None:
			arParseTree(child, ardict.new(name.text, child), namespace)
		else:
			arParseTree(child, ardict, namespace)

def arGetPath(ardict, path):
	ptr = ardict
	for p in path.split('/'):
		if p.strip():
			ptr = ptr.getChild(p)
	return ptr._ref


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
		Reciever = ""

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
		if initvalue is not None:
			pass

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
			startbit = int(startBit.text)	
			if 0 == byteorder:	
				startbit = reverseStartbit(startbit)
			newSig = Signal(name.text, startbit, length.text, byteorder, valuetype, factor, offset, Min, Max, Unit, Reciever)
			#newSig Description, 
			for key,value in values.items():			
				newSig.addValues(key, value)
			Bo.addSignal(newSig)

def getFrame(frame, arDict, ns):
	idele = arGetChild(frame, "IDENTIFIER", arDict, ns)
	frameR = arGetChild(frame, "FRAME", arDict, ns)
	dlc = arGetChild(frameR, "FRAME-LENGTH", arDict, ns)
	pdumappings = arGetChild(frameR, "PDU-TO-FRAME-MAPPINGS", arDict, ns)
	pdumapping = arGetChild(pdumappings, "PDU-TO-FRAME-MAPPING", arDict, ns)
	pdu = arGetChild(pdumapping, "PDU", arDict, ns) # SIGNAL-I-PDU
	name = arGetChild(pdu,"SHORT-NAME", arDict, ns)

	newBo = Botschaft(int(idele.text), name.text, int(dlc.text), "") #TODO Transmitter fehlt noch

	timingSpec = arGetChild(pdu,"I-PDU-TIMING-SPECIFICATION", arDict, ns)
	cyclicTiming = arGetChild(timingSpec,"CYCLIC-TIMING", arDict, ns)
	repeatingTime = arGetChild(cyclicTiming,"REPEATING-TIME", arDict, ns)
	value = arGetChild(repeatingTime,"VALUE", arDict, ns)
	if value is not None:	
		newBo.addAttribute("GenMsgCycleTime",value.text) 

	pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
	pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
	getSignals(pdusigmapping, newBo, arDict, ns)
	return newBo



def arGetChild(parent, tagname, arTranslationTable, namespace):
	if parent is None:
		return None
	ret = parent.find('./' + namespace + tagname)
	if ret is None:
		ret = parent.find('./' + namespace + tagname + '-REF')
		if ret is not None:
			ret = arGetPath(arTranslationTable, ret.text)
	return ret

def arGetChildren(parent, tagname, arTranslationTable, namespace):
	if parent is None:
		return []
	ret = parent.findall('./' + namespace + tagname)
	if ret is None:
		retlist = parent.findall('./' + namespace + tagname + '-REF')
		rettemp = {}
		for ret in retlist:
			rettemp.append(arGetPath(arTranslationTable, ret.text))
		ret = rettemp
	return ret

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
	busname = arGetChild(cc, "SHORT-NAME", arDict, ns)
	speed = arGetChild(cc, "SPEED", arDict, ns)
	print "Busname: " + busname.text + " Speed: " + speed.text
	physicalChannels = arGetChild(cc, "PHYSICAL-CHANNELS", arDict, ns)
	physicalChannel = arGetChild(physicalChannels, "PHYSICAL-CHANNEL", arDict, ns)
	frametriggerings = arGetChild(physicalChannel, "FRAME-TRIGGERINGSS", arDict, ns)
	canframetrig = arGetChildren(frametriggerings, "CAN-FRAME-TRIGGERING", arDict, ns)

	for frame in canframetrig:
		db._bl.addBotschaft(getFrame(frame, arDict, ns))

	# find ECUs:
	nodes = root.findall('.//' + ns +'ECU-INSTANCE')
	for node in nodes:
		name = node.find('.//' + ns + 'SHORT-NAME')	
		db._BUs.add(BoardUnit(name.text))

	return db	

