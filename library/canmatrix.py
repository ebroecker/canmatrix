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

import cPickle as pickle
import json


class BotschaftenListe:
	"""
	Keeps all Frames of a Canmatrix
	"""
	def __init__(self):
		self._liste = []

	def addSignalToLastBotschaft(self, signal):
		"""
		Adds a Signal to the last addes Frame, this is mainly for importers
		"""
		self._liste[len(self._liste)-1].addSignal(signal)
	def addBotschaft(self, botschaft):
		"""
		Adds a Frame
		"""
		self._liste.append(botschaft)
		return self._liste[len(self._liste)-1]

	def byId(self, Id):
		"""
		returns a Frame-Object by given Frame-ID
		"""
		for test in self._liste:
			if test._Id == int(Id):
				return test
		return 0
	def byName(self, Name):
		"""
		returns a Frame-Object by given Frame-Name
		"""
		for test in self._liste:
			if test._name == Name:
				return test
		return None
		
class BoardUnit:
	"""
	Contains one Boardunit/ECU
	"""
	def __init__(self,name):
		self._name = name.strip()
		self._attributes = {}
	def addAttribute(self, attribute, value):
		"""
		adds some Attribute to current Boardunit/ECU		
		"""
		self._attributes[attribute]=value

class BoardUnitListe:
	"""
	Contains all Boardunits/ECUs of a canmatrix in a list
	"""
	def __init__(self):
		self._liste = []
	def add(self,BU):
		"""
		add Boardunit/EDU to list
		"""
		if BU._name.strip() not in self._liste:
			self._liste.append(BU)
			
	def byName(self, name):
		"""
		returns Boardunit-Object of list by Name
		"""
		for test in self._liste:
			if test._name == name:
				return test
		return None

class Signal:
	"""
	contains on Signal of canmatrix-object
	with following attributes:
		_name, _startbit,_signalsize (in Bits)
		_byteorder (1: Intel, 0: Motorola)
		_valuetype ()
		_factor, _offset, _min, _max
		_reciever  (Boarunit/ECU-Name)
		_attributes, _values, _unit, _comment
		_multiplex ('Multiplexor' or Number of Multiplex)
	"""
	def __init__(self, name, startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, multiplex=None):
		self._name = name
		self._startbit = int(startbit)
		self._signalsize = int(signalsize)
		self._byteorder = int(byteorder)
		# byteorder: 1: Intel, 0: Motorola
		self._valuetype = valuetype
		self._factor = float(factor)
		self._offset = float(offset)
		self._min = float(min)
		self._max = float(max)
		self._reciever = reciever
		self._attributes = {}
		self._values = {}
		self._unit = unit
		self._comment = ""
		self._multiplex = multiplex
	def addComment(self, comment):
		"""
		Set comment of Signal
		"""
		self._comment = comment
	def addAttribute(self, attribute, value):
		"""
		Add Attribute to Signal
		"""
		if attribute not in self._attributes:
			self._attributes[attribute]=value
	def addValues(self, value, valueName):
		"""
		Add Value/Description to Signal
		"""
		self._values[int(value)] = valueName

class Botschaft:
	"""
	contains one Frame with following attributes
	_Id, _name, _Transmitter (list of boardunits/ECU-names), _Size (= DLC), 
	_signals (list of signal-objects), _attributes (list of attributes),
	_Reciever (list of boardunits/ECU-names), _extended (Extended Frame = 1), _comment
	"""
	def __init__(self,bid, name, size, transmitter): 
		self._Id = int(bid)
		self._name = name
		if transmitter is not None:
			self._Transmitter = [transmitter]
		else:
			self._Transmitter = []
		self._Size = int(size)
		self._signals = []
		self._attributes = {}
		self._Reciever = []
		self._extended = 0
		self._comment = ""

	def addSignal(self, signal):
		"""
		add Signal to Frame
		"""
		self._signals.append(signal)
		return self._signals[len(self._signals)-1]

	def addTransmitter(self, transmitter):
		"""
		add transmitter Boardunit/ECU-Name to Frame
		"""
		if transmitter not in self._Transmitter:
			self._Transmitter.append(transmitter)
		
	def signalByName(self, name):
		"""
		returns signal-object by signalname
		"""
		for signal in self._signals:
			if signal._name == name:
				return signal
		return 0
	def addAttribute(self, attribute, value):
		"""
		add attribute to attribute-list of frame
		"""
		if attribute not in self._attributes:
			self._attributes[attribute]=value
		
	def addComment(self, comment):
		"""
		set comment of frame
		"""
		self._comment = comment


class CanMatrix:
	"""
	The Can-Matrix-Object
	_attributes (global canmatrix-attributes), 
	_BUs (list of boardunits/ECUs),
	_bl (list of Frames)
	_signalDefines (list of signal-attribute types)
	_frameDefines (list of frame-attribute types)
	_buDefines (list of BoardUnit-attribute types)
	_globalDefines (list of global attribute types)
	"""
	def __init__(self):
		self._attributes = {}
		self._BUs = BoardUnitListe()
		self._bl = BotschaftenListe()
		self._signalDefines = {}
		self._frameDefines = {}
		self._globalDefines = {}
		self._buDefines = {}
 
	def addAttribute(self, attribute, value):
		"""
		add attribute to attribute-list of canmatrix
		"""
		if attribute not in self._attributes:
			self._attributes[attribute]=value

	def addSignalDefines(self, type, definition):
		"""
		add signal-attribute definition to canmatrix
		"""
		if type not in self._signalDefines:
			self._signalDefines[type]=definition
	
	def addFrameDefines(self, type, definition):
		"""
		add frame-attribute definition to canmatrix
		"""
		if type not in self._frameDefines:
			self._frameDefines[type]=definition

	def addBUDefines(self, type, definition):
		"""
		add Boardunit-attribute definition to canmatrix
		"""
		if type not in self._buDefines:
			self._buDefines[type]=definition

	def addGlobalDefines(self, type, definition):
		"""
		add global-attribute definition to canmatrix
		"""
		if type not in self._globalDefines:
			self._globalDefines[type]=definition
	

def loadPkl(filename):
	"""
	helper for loading a python-object-dump of canmatrix
	"""
        pkl_file = open(filename, 'rb')
        db1 = pickle.load(pkl_file)
        pkl_file.close()
        return db1

def savePkl(db, filename):
	"""
	helper for saving a python-object-dump of canmatrix
	"""
        output = open(filename, 'wb')
        pickle.dump(db, output)
        output.close()

def putSignalValueInFrame(startbit, len, format, value, frame):
	"""
	puts a signal-value to the right position in a frame
	"""

	if format == 1: # Intel
		lastbit = startbit + len
		firstbyte = startbit/8-1
		lastbyte = (lastbit-1)/8
		# im lastbyte mit dem msb anfangen
		# im firstbyte mit dem lsb aufhoeren
		for i in range(lastbyte, firstbyte, -1):
			if lastbit %8 != 0:
				nbits = lastbit % 8
			else:
				nbits = min(len, 8)
			nbits = min(len, nbits)
				
			start = lastbit-1 - int((lastbit-1)/8)*8
			end = lastbit-nbits - int((lastbit-nbits)/8)*8
			
			len -= nbits
			mask = (0xff >> 7-start) << end
			mask &= 0xff;
			frame[i] |= (((value >> len ) << end) & mask)
			lastbit = startbit + len
	else: # Motorola
		firstbyte = startbit/8
		bitsInfirstByte = startbit % 8 + 1 
		restnBits = len - bitsInfirstByte
		lastbyte = firstbyte + restnBits/8
		if restnBits %8 > 0:
			lastbyte += 1
		restLen = len
		nbits = bitsInfirstByte
		for i in range(firstbyte, lastbyte+1):
			end = 0
			if restLen < 8:
				end = 8-restLen
			mask = (0xff >> (8-nbits)) << end
			restLen -= nbits
			frame[i] |= ((value >> restLen) << end) & mask 
			nbits = min(restLen, 8)			

def copyBU (buId, sourceDb, targetDb):
	"""
	This function copys a Boardunit identified by Name or as Object from source-Canmatrix to target-Canmatrix
	while copying is easy, this function additionally copys all relevant Defines
	"""
	# check wether buId is object or symbolic name
	if type(buId).__name__ == 'instance':
		bu = buId
	else:
		bu = sourceDb._BUs.byName(buId)
	
	targetDb._BUs.add(bu)
	
	# copy all bu-defines
	attributes = bu._attributes
	for attribute in attributes:
		targetDb.addBUDefines(attribute, sourceDb._buDefines[attribute])

		
def copyFrame (frameId, sourceDb, targetDb):
	"""
	This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
	while copying is easy, this function additionally copys all relevant Boardunits, and Defines
	"""

	# check wether frameId is object, id or symbolic name
	if type(frameId).__name__ == 'int':
		frame = sourceDb._bl.byId(frameId)
	elif type(frameId).__name__ == 'instance':
		frame = frameId
	else:
		frame = sourceDb._bl.byName(frameId)


	# copy Frame-Object:
	targetDb._bl.addBotschaft(frame)
	
	## Boardunits:
	# each transmitter of Frame could be ECU that is not listed already
	for transmitter in frame._Transmitter:
		targetBU = targetDb._BUs.byName(transmitter)
		sourceBU = sourceDb._BUs.byName(transmitter)
		if targetBU is None:
			copyBU(sourceBU, sourceDb, targetDb)
			
	#trigger all signals of Frame
	for sig in frame._signals:			
		# each reciever of Signal could be ECU that is not listed already
		for reciever in sig._reciever:
			targetBU = targetDb._BUs.byName(transmitter)
			sourceBU = sourceDb._BUs.byName(transmitter)
			if targetBU is None:
				copyBU(sourceBU, sourceDb, targetDb)

	# copy all frame-defines
	attributes = frame._attributes
	for attribute in attributes:
		targetDb.addFrameDefines(attribute, sourceDb._frameDefines[attribute])

	#trigger all signals of Frame
	for sig in frame._signals:
		# delete all 'unknown' attributes 
		attributes = sig._attributes
		for attribute in attributes:
			targetDb.addSignalDefines(attribute, sourceDb._signalDefines[attribute])
	