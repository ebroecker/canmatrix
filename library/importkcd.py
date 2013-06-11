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
# this script imports kcd-files to a canmatrix-object
# kcd-files are the can-matrix-definitions of the kayak (http://kayak.2codeornot2code.org/)
#
#TODO baudrate missing
#TODO name save
#TODO defaults for CAN-Simulation missing
#TODO LabelGroup not supported
#TODO multiple Transmitter

from lxml import etree
from canmatrix import *

def parseSignal(signal, mux, namespace):
	startbit = 0
	if 'offset' in signal.attrib:
		startbit = signal.get('offset')

	signalsize = 1
	if 'length' in signal.attrib:
		signalsize = signal.get('length')


	byteorder = 1
	if 'endianess' in signal.attrib:		
		if signal.get('endianess') == 'little':
			byteorder = 0

	unit = ""
	offset = 0
	factor = 1
	min = 0
	max = 1

	values = signal.find('./' + namespace + 'Value')
	if values is not None:
		if 'slope' in values.attrib:
			factor = values.get('slope')
		if 'intercept' in values.attrib:
			offset = values.get('intercept')
		if 'unit' in values.attrib:
			unit = values.get('unit')
		if 'min' in values.attrib:
			min = values.get('min')
		if 'max' in values.attrib:
			max = values.get('max')

	reciever = ""
	producers = signal.findall('./' + namespace + 'Producer')
	for producer in producers:
		noderefs = producer.findall('./' + namespace + 'NodeRef')
		for noderef in noderefs:
			reciever += nodelist[noderef.get('id')] + ' '

	valuetype = '+'		
	newSig = Signal(signal.get('name'), startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, mux)

	labelsets = signal.findall('./' + namespace + 'LabelSet')
	for labelset in  labelsets:
		labels = labelset.findall('./' + namespace + 'Label')
		for label in labels:
			name = '"' + label.get('name') + '"'
			value = label.get('value')
			newSig.addValues(value, name)

	return newSig


def importKcd(filename):
	tree = etree.parse(filename)
	root = tree.getroot()
	namespace = "{" + tree.xpath('namespace-uri(.)') + "}"
 
	db = CanMatrix()

	nodelist = {}
	nodes = root.findall('./' + namespace + 'Node')
	for node in nodes:
		db._BUs.add(BoardUnit(node.get('name')))	
		nodelist[node.get('id')] = node.get('name')

	bus = root.find('./' + namespace + 'Bus')

	messages = bus.findall('./' + namespace + 'Message')

	for message in messages:
		dlc = 1
		newBo = Botschaft(int(message.get('id'), 16), message.get('name'), dlc, None)

		if 'triggered' in message.attrib:
			newBo.addAttribute("GenMsgCycleTime", message.get('interval'))	

		multiplex = message.find('./' + namespace + 'Multiplex')
		if multiplex is not None:	
			startbit = 0
			if 'offset' in multiplex.attrib:
				startbit = multiplex.get('offset')

			signalsize = 1
			if 'length' in multiplex.attrib:
				signalsize = multiplex.get('length')
			

			byteorder = 1
			if int(startbit) + int(signalsize) > maxBit:
				maxBit = int(startbit) + int(signalsize)
			
			unit = ""
			offset = 0
			factor = 1
			min = 0
			max = 1
			valuetype = '+'		

			reciever = ""
			producers = signal.findall('./' + namespace + 'Producer')
			for producer in producers:
				noderefs = producer.findall('./' + namespace + 'NodeRef')
				for noderef in noderefs:
					reciever += nodelist[noderef.get('id')] + ' '

			newSig = Signal(multiplex.get('name'), startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, 'Multiplexor')
			newBo.addSignal(newSig)
			
			muxgroups = multiplex.findall('./' + namespace + 'MuxGroup')
			for muxgroup in muxgroups:
				mux = muxgroup.get('count')
				signales = muxgroup.findall('./' + namespace + 'Signal')			
				for signal in signales:
					newSig = parseSignal(signal, mux, namespace)	
					if int(newSig._startbit) + int(newSig._signalsize) > maxBit:
						maxBit = int(newSig._startbit) + int(newSig._signalsize)
					newBo.addSignal(newSig)

		signales = message.findall('./' + namespace + 'Signal')
		maxBit = 0;
		for signal in signales:
			newSig = parseSignal(signal, None, namespace)
		
			if int(newSig._startbit) + int(newSig._signalsize) > maxBit:
				maxBit = int(newSig._startbit) + int(newSig._signalsize)
			
			newBo.addSignal(newSig)
		newBo._Size = int(maxBit / 8)
		if newBo._Size < maxBit / 8 + 1 :
			newBo._Size = int(maxBit / 8)+1

		db._bl.addBotschaft(newBo)
	return db

