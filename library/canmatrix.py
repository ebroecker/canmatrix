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
		self._definition = definition.strip()
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


# ############################
# Copy functions:
# ############################
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
		targetDb.addBUDefines(attribute, sourceDb._buDefines[attribute]._definition)
		targetDb.addDefineDefault(attribute, sourceDb._buDefines[attribute]._defaultValue)


	
def copyFrame (frameId, sourceDb, targetDb):
	"""
	This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
	while copying is easy, this function additionally copys all relevant Boardunits, and Defines
	"""

	# check wether frameId is object, id or symbolic name
	if type(frameId).__name__ == 'int':
		frame = sourceDb._fl.byId(frameId)
	elif type(frameId).__name__ == 'instance':
		frame = frameId
	else:
		frame = sourceDb._fl.byName(frameId)


	# copy Frame-Object:
	targetDb._fl.addFrame(frame)
	
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
		targetDb.addFrameDefines(attribute, sourceDb._frameDefines[attribute]._definition)
		targetDb.addDefineDefault(attribute, sourceDb._frameDefines[attribute]._defaultValue)

	#trigger all signals of Frame
	for sig in frame._signals:
		# delete all 'unknown' attributes 
		attributes = sig._attributes
		for attribute in attributes:
			targetDb.addSignalDefines(attribute, sourceDb._signalDefines[attribute]._definition)
			targetDb.addDefineDefault(attribute, sourceDb._signalDefines[attribute]._defaultValue)

# ############################
# Compare functions:
# ############################

class compareResult:
	def __init__(self, result= None, type= None, ref= None, changes = None):
		# equal, added, deleted, changed
		self._result = result
		# db, bu, frame, signal, attribute
		self._type = type
		#reference to related object
		self._ref = ref
		self._changes = changes
		self._children = []
	def addChild(self, child):
		self._children.append(child)

def compareDb(db1, db2):
	result = compareResult() 
	for f1 in db1._fl._list:
		f2 = db2.frameById(f1._Id)
		if f2 is None:
			result.addChild(compareResult("deleted", "FRAME", f1))
		else:
			result.addChild(compareFrame(f1, f2))
	for f2 in db2._fl._list:
		f1 = db1.frameById(f2._Id)
		if f1 is None:
			result.addChild(compareResult("added", "FRAME", f2))

	result.addChild(compareAttributes(db1, db2))

		
	for bu1 in db1._BUs._list:
		bu2 = db2.boardUnitByName(bu1._name)
		if bu2 is None:
			result.addChild(compareResult("deleted", "ecu", bu1))
		else:
			result.addChild(compareBu(bu1, bu2))
	for bu2 in db2._BUs._list:
		bu1 = db1.boardUnitByName(bu2._name)
		if bu1 is None:
			result.addChild(compareResult("added", "ecu", bu2))


	result.addChild(compareDefineList(db1._globalDefines, db2._globalDefines))
	
	temp = compareDefineList(db1._buDefines, db2._buDefines)
	temp._type = "ECU Defines"
	result.addChild(temp)

	temp = compareDefineList(db1._frameDefines, db2._frameDefines)
	temp._type = "Frame Defines"
	result.addChild(temp)

	temp = compareDefineList(db1._signalDefines, db2._signalDefines)
	temp._type = "Signal Defines"
	result.addChild(temp)

	for vt1 in db1._valueTables:
		if vt1 not in db2._valueTables:
			result.addChild(compareResult("deleted", "valuetable " + vt1, db1._valueTables))
		else:
			result.addChild(compareValueTable(db1._valueTables[vt1], db2._valueTables[vt1]))
			
			
	for vt2 in db2._valueTables:
		if vt2 not in db1._valueTables:
			result.addChild(compareResult("added", "valuetable " + vt2, db2._valueTables))
	return result

def compareValueTable(vt1, vt2):
	result = compareResult("equal", "Valuetable", vt1)
	for value in vt1:
		if value not in vt2:
			result.addChild(compareResult("removed", "Value " + str(value), vt1[value]))
		elif vt1[value] != vt2[value]:
			result.addChild(compareResult("changed", "Value " + str(value) + " " + str(vt1[value]), [vt1[value], vt2[value]]))	
	for value in vt2:
		if value not in vt1:
			result.addChild(compareResult("added", "Value " + str(value), vt2[value]))
	return result

def compareSignalGroup(sg1, sg2):
	result = compareResult("equal", "SignalGroup", sg1)

	if sg1._name != sg2._name:
		result.addChild(compareResult("changed", "SignalName", [sg1._name, sg2._name] ))
	if sg1._Id != sg2._Id:
		result.addChild(compareResult("changed", "SignalName", [str(sg1._Id), str(sg2._Id)] ))

	if sg1._members == None or sg2._members == None:
		print "Strange - sg wo members???"
		return result
	for member in sg1._members:
		if sg2.byName(member._name) is None:
			result.addChild(compareResult("deleted", str(member._name), member))
	for member in sg2._members:
		if sg1.byName(member._name) is None:
			result.addChild(compareResult("added", str(member._name), member))
	return result			

	
def compareDefineList(d1list, d2list):
	result = compareResult("equal", "DefineList", d1list)
	for definition in d1list:
		if definition not in d2list:
			result.addChild(compareResult("deleted", "Define" + str(definition), d1list))
		else:
			d2 = d2list[definition]
			d1 = d1list[definition]
			if d1._definition != d2._definition:
				result.addChild(compareResult("changed", "Definition", [d1._definition, d2._definition] ))

			if d1._defaultValue != d2._defaultValue:
				result.addChild(compareResult("changed", "DefaultValue", [d1._defaultValue, d2._defaultValue] ))
	for definition in d2list:
		if definition not in d1list:
			result.addChild(compareResult("added", "Define" + str(definition), d2list))
	return result
	
def compareAttributes(ele1, ele2):
	result = compareResult("equal", "ATTRIBUTES", ele1)	
	for attribute in ele1._attributes:
		if attribute not in ele2._attributes:
			result.addChild(compareResult("deleted", str(attribute), ele1._attributes[attribute]))
		elif ele1._attributes[attribute] != ele2._attributes[attribute]:
			result.addChild(compareResult("changed", str(attribute), ele1._attributes[attribute], 	 [ ele1._attributes[attribute] , ele2._attributes[attribute]] ))

	for attribute in ele2._attributes:
		if attribute not in ele1._attributes:
			result.addChild(compareResult("added", str(attribute), ele2._attributes[attribute]))
	return result
			
def compareBu(bu1, bu2):
	result = compareResult("equal", "ECU", bu1)

	if bu1._comment != bu2._comment:
		result.addChild(compareResult("changed", "ECU", bu1, [ bu1._comment,  bu2._comment]))
	result.addChild(compareAttributes(bu1, bu2))
	return result
	
def compareFrame(f1, f2):
	result = compareResult("equal", "FRAME", f1)

	for s1 in f1._signals:
		s2 = f2.signalByName(s1._name)
		if not s2:
			result.addChild(compareResult("deleted", "SIGNAL", s1))
		else:
			result.addChild(compareSignal(s1, s2))

	if f1._name != f2._name:
		result.addChild(compareResult("changed", "Name", f1, [f1._name, f2._name]))
	if f1._Size != f2._Size:
		result.addChild(compareResult("changed", "dlc", f1, ["dlc: %d" % f1._Size, "dlc: %d" % f2._Size]))
	if f1._extended != f2._extended:
		result.addChild(compareResult("changed", "FRAME", f1, ["extended-Flag: %d" % f1._extended, "extended-Flag: %d" % f2._extended]))
	if f1._comment != f2._comment:
		result.addChild(compareResult("changed", "FRAME", f1, ["comment: " +  f1._comment , "comment: " +  f1._comment]))
		
	for s2 in f2._signals:
		s1 = f1.signalByName(s2._name)
		if not s1:
			result.addChild(compareResult("added", "SIGNAL", s2))

	result.addChild(compareAttributes(f1, f2))

	for transmitter in f1._Transmitter:
		if transmitter not in f2._Transmitter:
			result.addChild(compareResult("removed", "Frame-Transmitter", f1))
	for transmitter in f2._Transmitter:
		if transmitter not in f1._Transmitter:
			result.addChild(compareResult("added", "Frame-Transmitter", f2))

	for sg1 in f1._SignalGroups:
		sg2 = f2.signalGroupbyName(sg1._name)
		if sg2 is None:
			result.addChild(compareResult("removed", "Signalgroup", sg1))
		else:
			result.addChild(compareSignalGroup(sg1,sg2))

	for sg2 in f2._SignalGroups:
		if f1.signalGroupbyName(sg2._name) is None:
			result.addChild(compareResult("added", "Signalgroup", sg1))
	return result

def compareSignal(s1,s2):
	result = compareResult("equal", "SIGNAL", s1)

	if s1._startbit != s2._startbit:
		result.addChild(compareResult("changed", "startbit", s1, [" %d" % s1._startbit, " %d" % s2._startbit]))
	if s1._signalsize != s2._signalsize:
		result.addChild(compareResult("changed", "signalsize", s1, [" %d" % s1._signalsize, " %d" % s2._signalsize]))
	if s1._factor != s2._factor:
		result.addChild(compareResult("changed", "factor", s1, [" %f" % s1._factor, " %f" % s2._factor]))
	if s1._offset != s2._offset:
		result.addChild(compareResult("changed", "offset", s1, [" %d" % s1._offset, " %d" % s2._offset]))
	if s1._min != s2._min:
		result.addChild(compareResult("changed", "min", s1, [" %f" % s1._min, " %f" % s2._min]))
	if s1._max != s2._max:
		result.addChild(compareResult("changed", "max", s1, [" %f" % s1._max, " %f" % s2._max]))
	if s1._byteorder != s2._byteorder:
		result.addChild(compareResult("changed", "byteorder", s1, [" %d" % s1._byteorder, " %d" % s2._byteorder]))
	if s1._valuetype != s2._valuetype:
		result.addChild(compareResult("changed", "valuetype", s1, [" %d" % s1._valuetype, " %d" % s2._valuetype]))
	if s1._multiplex != s2._multiplex:
		result.addChild(compareResult("changed", "multiplex", s1, [str(s1._multiplex), str(s2._multiplex)]))
	if s1._unit != s2._unit:
		result.addChild(compareResult("changed", "unit", s1, [ s1._unit,  s2._unit]))
	if s1._comment != s2._comment:
		result.addChild(compareResult("changed", "comment", s1, [ s1._comment,  s2._comment]))
	
	for reciever in s1._reciever:
		if reciever not in s2._reciever:
			result.addChild(compareResult("removed", "Reciever " + reciever, s1._reciever))

	for reciever in s2._reciever:
		if reciever not in s1._reciever:
			result.addChild(compareResult("added", "Reciever " + reciever, s1._reciever))

	result.addChild(compareAttributes(s1, s2))
	result.addChild(compareValueTable(s1._values,s2._values))
			
	return result
