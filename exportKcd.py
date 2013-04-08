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
# this script exports kcd-files from a canmatrix-object
# kcd-files are the can-matrix-definitions of the kayak (http://kayak.2codeornot2code.org/)
#

from lxml import etree
from canmatrix import *
import cPickle as pickle


def exportKcd(db, filename):
	# create XML 
	root = etree.Element('NetworkDefinition')
	root.set("xmlns","http://kayak.2codeornot2code.org/1.0")
	NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
	root.set(NS_XSI + "SchemaLocation", "Definition.xsd")


	#root.append(etree.Element('Document'))
	# another child with text

	child = etree.Element('Document')
	child.set("name","Some Document Name")
	child.text = 'some text'
	root.append(child)


	# Nodes:
	id = 1
	nodeList = {};
	for bu in db._BUs._liste:
		node = etree.Element('Node', name=bu._name, id="%d" %id)
		root.append(node)
		nodeList[bu._name] = id;
		id += 1


	# Bus

	if 'Baudrate' in db._attributes:
		bus = etree.Element('Bus', baudrate=db._attributes['Baudrate'])
	else:
		bus = etree.Element('Bus')

	bus.set("name","chassis")

	for bo in db._bl._liste:
		message = etree.Element('Message', id="0x%X" % bo._Id, name=bo._name)

		if "GenMsgCycleTime" in bo._attributes:
			cycleTime = int(bo._attributes["GenMsgCycleTime"])	
			if cycleTime > 0:				
				message.set("triggered", "true")
				message.set("interval", "%d" % cycleTime)

		producer = etree.Element('Producer')
		if len(bo._Transmitter) > 1:				
			noderef = etree.Element('NodeRef', id=str(nodeList[bo._Transmitter]))
		producer.append(noderef)
		message.append(producer)
		for signal in bo._signals:
			sig = etree.Element('Signal', name=signal._name, offset=str(signal._startbit))
			if signal._signalsize > 1:		
				sig.set("length", str(signal._signalsize))
			if signal._byteorder == 0:	
				sig.set('endianess',"little")
	
			notes = etree.Element('Notes')
			notes.text = signal._comment		
			sig.append(notes)

			value = etree.Element('Value')
			if float(signal._factor) != 1:	
				value.set('slope',str(signal._factor))
			if float(signal._offset) != 0:	
				value.set('intercept',str(signal._offset))
			if float(signal._min) != 0:	
				value.set('min',str(signal._min))
			if float(signal._max) != 1:	
				value.set('max',str(signal._max))
	#		if len(signal._unit) > 0:		
	#			value.set('unit',signal._unit)
			sig.append(value)


			labelset = etree.Element('LabelSet')
			for valueVal,valName in signal._values.items():
				label = etree.Element('Label', name=valName.replace('"',''), value=str(valueVal))
				labelset.append(label)			
			sig.append(labelset)

			consumer = etree.Element('Consumer')
			for reciever in signal._reciever:
				if len(reciever) > 1:				
					noderef = etree.Element('NodeRef', id=str(nodeList[reciever]))
					consumer.append(noderef)

			sig.append(consumer)
			message.append(sig)
		
		bus.append(message)

	root.append(bus)
	f = open(filename,"w");
	f.write(etree.tostring(root, pretty_print=True))

def test():
	db = loadPkl('test.pkl')
	exportKcd(db, "test.kcd")

