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

from lxml import etree
from canmatrix import *

def parseSignal(signal, mux, namespace, nodelist):
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

	reciever = []
	consumers = signal.findall('./' + namespace + 'Consumer')
	for consumer in consumers:
		noderefs = consumer.findall('./' + namespace + 'NodeRef')
		for noderef in noderefs:
			reciever.append(nodelist[noderef.get('id')])


	valuetype = '+'		
	newSig = Signal(signal.get('name'), startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, mux)

	notes = signal.findall('./' + namespace + 'Notes')
	comment = ""
	for note in notes:
		if note.text is not None:
			comment += note.text
			newSig.addComment(comment)
		
	labelsets = signal.findall('./' + namespace + 'LabelSet')
	for labelset in  labelsets:
		labels = labelset.findall('./' + namespace + 'Label')
		for label in labels:
			name = label.get('name')
			value = label.get('value')
			newSig.addValues(value, name)

	return newSig


def importKcd(filename):
	tree = etree.parse(filename)
	root = tree.getroot()
	namespace = "{" + tree.xpath('namespace-uri(.)') + "}"
 
	db = CanMatrix()
	db.addFrameDefines("GenMsgCycleTime",  'INT 0 65535')

	nodelist = {}
	nodes = root.findall('./' + namespace + 'Node')
	for node in nodes:
		db._BUs.add(BoardUnit(node.get('name')))	
		nodelist[node.get('id')] = node.get('name')

	bus = root.find('./' + namespace + 'Bus')

	messages = bus.findall('./' + namespace + 'Message')

	for message in messages:
		dlc = None
		newBo = Frame(int(message.get('id'), 16), message.get('name'), 1, None)

		if 'triggered' in message.attrib:
			newBo.addAttribute("GenMsgCycleTime", message.get('interval'))	

		
		if 'length' in message.attrib:
			dlc = int(message.get('length'))

		multiplex = message.find('./' + namespace + 'Multiplex')
		maxBit = 0;

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
			
			min = 0
			max = 1
			values = multiplex.find('./' + namespace + 'Value')
			if values is not None:
				if 'min' in values.attrib:
					min = values.get('min')
				if 'max' in values.attrib:
					max = values.get('max')

			unit = ""
			offset = 0
			factor = 1
			valuetype = '+'		
	
			reciever = ""
			consumers = multiplex.findall('./' + namespace + 'Consumer')
			for consumer in consumers:
				noderefs = consumer.findall('./' + namespace + 'NodeRef')
				for noderef in noderefs:
					reciever += nodelist[noderef.get('id')] + ' '

			newSig = Signal(multiplex.get('name'), startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, 'Multiplexor')

			notes = multiplex.findall('./' + namespace + 'Notes')
			comment = ""
			for note in notes:
				comment += note.text
			newSig.addComment(comment)


			labelsets = multiplex.findall('./' + namespace + 'LabelSet')
			for labelset in  labelsets:
				labels = labelset.findall('./' + namespace + 'Label')
				for label in labels:
					name = label.get('name')
					value = label.get('value')
					newSig.addValues(value, name)

			newBo.addSignal(newSig)
			
			muxgroups = multiplex.findall('./' + namespace + 'MuxGroup')
			for muxgroup in muxgroups:
				mux = muxgroup.get('count')
				signales = muxgroup.findall('./' + namespace + 'Signal')			
				for signal in signales:
					newSig = parseSignal(signal, mux, namespace, nodelist)	
					if int(newSig._startbit) + int(newSig._signalsize) > maxBit:
						maxBit = int(newSig._startbit) + int(newSig._signalsize)
					newBo.addSignal(newSig)

		signales = message.findall('./' + namespace + 'Signal')
		
		producers = message.findall('./' + namespace + 'Producer')
		for producer in producers:
			noderefs = producer.findall('./' + namespace + 'NodeRef')
			for noderef in noderefs:
				newBo.addTransmitter(nodelist[noderef.get('id')])
		
		for signal in signales:
			newSig = parseSignal(signal, None, namespace, nodelist)
		
			if int(newSig._startbit) + int(newSig._signalsize) > maxBit:
				maxBit = int(newSig._startbit) + int(newSig._signalsize)
			
			newBo.addSignal(newSig)

		
		notes = message.findall('./' + namespace + 'Notes')
		comment = ""
		for note in notes:
			comment += note.text
		newBo.addComment(comment)
	
		if dlc is None:
			newBo._Size = int((maxBit-1) / 8)+1
		else:
			newBo._Size = dlc
		
		
		db._fl.addFrame(newBo)
	return db

