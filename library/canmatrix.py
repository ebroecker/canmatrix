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

#TODO: Definitions should be imported with disassembling not as complete string
#import cPickle as pickle
#import json

class FrameList:
	"""
	Keeps all Frames of a Canmatrix
	"""
	def __init__(self):
		self._list = []

	def addSignalToLastFrame(self, signal):
		"""
		Adds a Signal to the last addes Frame, this is mainly for importers
		"""
		self._list[len(self._list)-1].addSignal(signal)
	def addFrame(self, botschaft):
		"""
		Adds a Frame
		"""
		self._list.append(botschaft)
		return self._list[len(self._list)-1]

	def byId(self, Id):
		"""
		returns a Frame-Object by given Frame-ID
		"""
		for test in self._list:
			if test._Id == int(Id):
				return test
		return None
	def byName(self, Name):
		"""
		returns a Frame-Object by given Frame-Name
		"""
		for test in self._list:
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
		self._comment = None
	def addAttribute(self, attribute, value):
		"""
		adds some Attribute to current Boardunit/ECU		
		"""
		self._attributes[attribute]=value
	def addComment(self, comment):
		"""
		Set comment of Signal
		"""
		self._comment = comment

class BoardUnitListe:
	"""
	Contains all Boardunits/ECUs of a canmatrix in a list
	"""
	def __init__(self):
		self._list = []
	def add(self,BU):
		"""
		add Boardunit/EDU to list
		"""
		if BU._name.strip() not in self._list:
			self._list.append(BU)
			
	def byName(self, name):
		"""
		returns Boardunit-Object of list by Name
		"""
		for test in self._list:
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
		self._factor = str(factor)
		self._offset = str(offset)
		self._min = str(min)
		self._max = str(max)
		self._reciever = reciever
		self._attributes = {}
		self._values = {}
		self._unit = unit
		self._comment = None
		if multiplex is not None and multiplex != 'Multiplexor':
			multiplex = int(multiplex)
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
			self._attributes[attribute]=value.replace('"','')
	def addValues(self, value, valueName):
		"""
		Add Value/Description to Signal
		"""
		self._values[int(value)] = valueName


class SignalGroup:
	"""
	contains Signals, which belong to signal-group
	"""
	def __init__(self, name, Id):
		self._members = []
		self._name = name
		self._Id = Id
	def addSignal(self, signal):
		if signal not in self._members:
			self._members.append(signal)
	def delSignal(self, signal):
		if signal in self._members:
			self._members[signal].remove()
	def byName(self, name):
		"""
		returns Signalobject-Object of list by Name
		"""
		for test in self._members:
			if test._name == name:
				return test
		return None

class Frame:
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
		self._SignalGroups = []
		self._extended = 0
		self._comment = None

	def addSignalGroup(self, Name, Id, signalNames):
		newGroup = SignalGroup(Name, Id)
		self._SignalGroups.append(newGroup)
		for signal in signalNames:
			signal = signal.strip()
			if signal.__len__() == 0:
				continue
			signalId = self.signalByName(signal)
			if signalId is not None:
				newGroup.addSignal(signalId)
	
	def signalGroupbyName(self, name):
		"""
		returns signalGroup-object by signalname
		"""
		for signalGroup in self._SignalGroups:
			if signalGroup._name == name:
				return signalGroup
		return None 
	
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
		return None
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
	


class Define:
	"""
	these objects hold the defines and default-values
	"""
	def __init__(self, definition):
		definition = definition.strip()
		self._definition = definition
		self._type = None
		
		# for any known type:
		if definition[0:3] == 'INT':
			self._type = 'INT'
			_min, _max = definition[4:].split(' ',2)
			self._min = int(_min)
			self._max = int(_max)			
		elif definition[0:6] == 'STRING':
			self._type = 'STRING'
			self._min = None
			self._max = None
		elif definition[0:4] == 'ENUM':
			self._type = 'ENUM'
			self._values = definition[5:].split(',')
		elif definition[0:3] == 'HEX':
			self._type = 'HEX'
			_min, _max = definition[4:].split(' ',2)
			self._min = int(_min)
			self._max = int(_max)			
		elif definition[0:5] == 'FLOAT':
			self._type = 'FLOAT'
			_min, _max = definition[6:].split(' ',2)
			self._min = float(_min)
			self._max = float(_max)			

		self._defaultValue = None
		
	def addDefault(self, default):
		self._defaultValue = default

class CanMatrix:
	"""
	The Can-Matrix-Object
	_attributes (global canmatrix-attributes), 
	_BUs (list of boardunits/ECUs),
	_fl (list of Frames)
	_signalDefines (list of signal-attribute types)
	_frameDefines (list of frame-attribute types)
	_buDefines (list of BoardUnit-attribute types)
	_globalDefines (list of global attribute types)
	_valueTables (global defined values)
	"""
	def __init__(self):
		self._attributes = {}
		self._BUs = BoardUnitListe()
		self._fl = FrameList()
		self._signalDefines = {}
		self._frameDefines = {}
		self._globalDefines = {}
		self._buDefines = {}
		self._valueTables = {}
	
	def addValueTable(self, name, valueTable):
		self._valueTables[name] = valueTable
 
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
			self._signalDefines[type]=Define(definition)
	
	def addFrameDefines(self, type, definition):
		"""
		add frame-attribute definition to canmatrix
		"""
		if type not in self._frameDefines:
			self._frameDefines[type]=Define(definition)

	def addBUDefines(self, type, definition):
		"""
		add Boardunit-attribute definition to canmatrix
		"""
		if type not in self._buDefines:
			self._buDefines[type]=Define(definition)

	def addGlobalDefines(self, type, definition):
		"""
		add global-attribute definition to canmatrix
		"""
		if type not in self._globalDefines:
			self._globalDefines[type]=Define(definition)
	
	def addDefineDefault(self, name, value):
		if name in self._signalDefines:
			self._signalDefines[name].addDefault(value)
		if name in self._frameDefines:
			self._frameDefines[name].addDefault(value)
		if name in self._buDefines:
			self._buDefines[name].addDefault(value)
		if name in self._globalDefines:
			self._globalDefines[name].addDefault(value)
	
	def frameById(self, Id):
		return self._fl.byId(Id)
	
	def frameByName(self, name):
		return self._fl.byName(name)

	def boardUnitByName(self, name):
		return self._BUs.byName(name)


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

		
#		
# 
#		
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


