from __future__ import division

import math


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

class FrameList(object):
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

class BoardUnit(object):
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

class BoardUnitListe(object):
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

class Signal(object):
    """
    contains on Signal of canmatrix-object
    with following attributes:
            _name, _startbit,_signalsize (in Bits)
            _is_little_endian (1: Intel, 0: Motorola)
            _is_signed ()
            _factor, _offset, _min, _max
            _receiver  (Boarunit/ECU-Name)
            _attributes, _values, _unit, _comment
            _multiplex ('Multiplexor' or Number of Multiplex)
    """
#    def __init__(self, name, startbit, signalsize, is_little_endian, is_signed=False, factor=1, offset=0, min=0, max=0, unit="", receiver=[], multiplex=None):
    def __init__(self, name, **kwargs):

        if 'startBit' in kwargs:
            self._startbit = int(kwargs["startBit"])
        else:
            self._startbit = 0
 
        if 'signalSize' in kwargs:
            self._signalsize = int(kwargs["signalSize"])
        else:
            self._signalsize = 0

        if 'is_little_endian' in kwargs:
            self._is_little_endian = kwargs["is_little_endian"]
        else:
            self._is_little_endian = True

        if 'is_signed' in kwargs:
            self._is_signed = kwargs["is_signed"]
        else:
            self._is_signed = True

        if 'factor' in kwargs:
            self._factor = float(kwargs["factor"])
        else:
            self._factor = float(1)

        if 'offset' in kwargs:
            self._offset = float(kwargs["offset"])
        else:
            self._offset = float(0)
 
        if 'unit' in kwargs:
            self._unit = kwargs["unit"]
        else:
            self._unit = ""

        if 'receiver' in kwargs:
            self._receiver = kwargs["receiver"]
        else:
            self._receiver = []

        if 'comment' in kwargs:
            self._comment = kwargs["comment"]
        else:
            self._comment = None

        if 'multiplex' in kwargs:
            if kwargs["multiplex"] is not None and kwargs["multiplex"] != 'Multiplexor':
                multiplex = int(kwargs["multiplex"])
            else:
                multiplex = kwargs["multiplex"]
            self._multiplex = multiplex
        else:
            self._multiplex = None

        if 'min' in kwargs:
            min = kwargs["min"]
        else:
            min = None

        if min is None:
            self.setMin()
        else:
            self._min = float(min)

        if 'max' in kwargs:
            max = kwargs["max"]
        else:
            max = None

        if max is None:
            self.setMax()
        else:
            self._max = float(max)

        self._name = name
        self._attributes = {}
        self._values = {}

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
    def setMsbReverseStartbit(self, msbStartBitReverse, length=None):
        if self._is_little_endian == 1:
            #Intel
            self._startbit = msbStartBitReverse
        else:
            startByte = math.floor(msbStartBitReverse / 8)
            startBit = msbStartBitReverse % 8
            startBit = (7-startBit)
            startBit += startByte * 8
            self.setMsbStartbit(startBit, length)
    def setMsbStartbit(self, msbStartBit, length=None):
        """
        set startbit while given startbit is most significant bit
        if length is not given, use length from object
        """
        if self._is_little_endian == 1:
            #Intel
            self._startbit = msbStartBit
        else:
            if length == None:
                length = self._signalsize
            # following code is from https://github.com/julietkilo/CANBabel/blob/master/src/main/java/com/github/canbabel/canio/dbc/DbcReader.java:
            pos = 7 - (msbStartBit % 8) + (length - 1)
            if (pos < 8):
                self._startbit = msbStartBit - length + 1;
            else:
                cpos = 7 - (pos % 8);
                bytes = int(pos / 8);
                self._startbit = cpos + (bytes * 8) + int(msbStartBit/8) * 8;
    def setLsbStartbit(self, lsbStartBit):
        """
        set startbit while given startbit is least significant bit
        """
        self._startbit = lsbStartBit
        
    def getMsbReverseStartbit(self):
        if self._is_little_endian == 1:
            #Intel
            return self._startbit
        else:
            startBit = self.getMsbStartbit()
            startByte = math.floor(startBit / 8)
            startBit = startBit % 8
            startBit = (7-startBit)
            startBit += startByte * 8
            return int(startBit)

    def getMsbStartbit(self):
        if self._is_little_endian == 1:
            #Intel
            return self._startbit
        else:
            #code from https://github.com/rbei-etas/busmaster/blob/master/Sources/Format%20Converter/DBF2DBCConverter/Signal.cpp
            nByte = int(self._signalsize/8);
            if (self._signalsize % 8) != 0:
                nByte += 1

            nStartBit = (1 - nByte) * 8;
            nBitSize = self._signalsize - (8 * (nByte - 1))+ self._startbit;

            if(nBitSize == 0):
                ucStartBit = self._startbit + self._signalsize;
            else:
                ucStartBit = nStartBit + nBitSize-1;
            return int(ucStartBit)

    def getLsbStartbit(self):
        return int(self._startbit)

    def calculateRawRange(self):
        rawRange = 2 ** self._signalsize

        if self._is_signed:
            rawRange /= 2

        return (-rawRange if self._is_signed else 0,
                rawRange - 1)

    def setMin(self, min=None):
        self._min = min

        if self._min is None:
            rawMin = self.calculateRawRange()[0]
            self._min = self._offset + (rawMin * self._factor)

    def setMax(self, max=None):
        self._max = max

        if self._max is None:
            rawMax = self.calculateRawRange()[1]
            self._max = self._offset + (rawMax * self._factor)


class SignalGroup(object):
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

class Frame(object):
    """
    contains one Frame with following attributes
    _Id, _name, _Transmitter (list of boardunits/ECU-names), _Size (= DLC),
    _signals (list of signal-objects), _attributes (list of attributes),
    _receiver (list of boardunits/ECU-names), _extended (Extended Frame = 1), _comment
    """
#    def __init__(self,bid, name, size, transmitter):
    def __init__(self, name, **kwargs):
        self._name = name
        if 'Id' in kwargs:
            self._Id = int(kwargs["Id"])
        else:
            self._Id = 0

        if 'dlc' in kwargs:
            self._Size = int(kwargs["dlc"])
        else:
            self._Size = 0

        if 'transmitter' in kwargs:
            self._Transmitter = [kwargs["transmitter"]]
        else:
            self._Transmitter = []

        if 'extended' in kwargs:
            self._extended = kwargs["extended"]
        else:
            self._extended = 0

        if 'comment' in kwargs:
            self._comment = kwargs["comment"]
        else:
            self._comment = None

        if 'signals' in kwargs:
            self._signals = kwargs["signals"]
        else:
            self._signals = []

        self._attributes = {}
        self._receiver = []
        self._SignalGroups = []

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

    def addReceiver(self, receiver):
        """
        add receiver Boardunit/ECU-Name to Frame
        """
        if receiver not in self._receiver:
            self._receiver.append(receiver)


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
            self._attributes[attribute]=str(value)

    def addComment(self, comment):
        """
        set comment of frame
        """
        self._comment = comment
        
    def calcDLC(self):
        """
        calc minimal DLC/length for frame (using signal information)
        """
        maxBit = 0
        for sig in self._signals:
            if sig._is_little_endian == 1  and sig.getLsbStartbit() + int(sig._signalsize) > maxBit:
                # check intel signal (startbit + length):
                maxBit = sig.getLsbStartbit() + int(sig._signalsize)
            elif sig._is_little_endian == 0  and sig.getLsbStartbit() > maxBit:
                #check motorola signal (starbit is least significant bit):
                maxBit = sig.getLsbStartbit()
        self._Size =  max(self._Size, math.ceil(maxBit / 8))
    
    def updateReceiver(self):
        """
        collect receivers of frame out of receiver given in each signal        
        """
        for sig in self._signals:
            for receiver in sig._receiver:            
                self.addReceiver(receiver)

class Define(object):
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

class CanMatrix(object):
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
    
    def deleteZeroSignals(self):
        for frame in self._fl._list:
            for signal in frame._signals:
                if 0 == signal._signalsize:
                    frame._signals.remove(signal)

    def recalcDLC(self, strategy):
        for frame in self._fl._list:
            originalDlc = frame._Size
            if "max" == strategy:
                frame.calcDLC()
            if "force" == strategy:
                maxBit = 0
                for sig in frame._signals:
                    if sig._is_little_endian == 1  and sig.getLsbStartbit() + int(sig._signalsize) > maxBit:
                        # check intel signal (startbit + length):
                        maxBit = sig.getLsbStartbit() + int(sig._signalsize)
                    elif sig._is_little_endian == 0  and sig.getLsbStartbit() > maxBit:
                        #check motorola signal (starbit is least significant bit):
                        maxBit = sig.getLsbStartbit()
                frame._Size = math.ceil(maxBit / 8)


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
        firstbyte = math.floor(startbit/8)-1
        lastbyte = math.floor((lastbit-1)/8)
        # im lastbyte mit dem msb anfangen
        # im firstbyte mit dem lsb aufhoeren
        for i in range(lastbyte, firstbyte, -1):
            if lastbit %8 != 0:
                nbits = lastbit % 8
            else:
                nbits = min(len, 8)
            nbits = min(len, nbits)

            start = lastbit-1 - int(math.floor((lastbit-1)/8))*8
            end = lastbit-nbits - int(math.floor((lastbit-nbits)/8))*8

            len -= nbits
            mask = (0xff >> 7-start) << end
            mask &= 0xff;
            frame[i] |= (((value >> len ) << end) & mask)
            lastbit = startbit + len
    else: # Motorola
		  # TODO needs review, is probably wrong till we use LSB for startbit 
        firstbyte = math.floor(startbit/8)
        bitsInfirstByte = startbit % 8 + 1
        restnBits = len - bitsInfirstByte
        lastbyte = firstbyte + math.floor(restnBits/8)
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


class CanId(object):
    """
    Split Id into Global source addresses (source, destination) off ECU and PGN
    """
    # TODO link to BoardUnit/ECU
    source = None  # Source Address
    destination = None  # Destination Address
    pgn = None  # PGN

    def __init__(self, id, extended=True):
        if extended:
            self.source = id & int('0xFF', 16)
            self.pgn = (id >> 8) & int('0xFFFF', 16)
            self.destination = id >> 8 * 3 & int('0xFF', 16)
        else:
            # TODO implement for standard Id
            pass

    def tuples(self):
        return self.destination, self.pgn, self.source

    def __str__(self):
        return "DA:{da:#02X} PGN:{pgn:#04X} SA:{sa:#02X}".format(da=self.destination, pgn=self.pgn, sa=self.source)
