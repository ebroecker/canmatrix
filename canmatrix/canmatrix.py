#!/usr/bin/env python

# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,   PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR  OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# TODO: Definitions should be disassembled

from __future__ import division
import math


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
        self._list[len(self._list) - 1].addSignal(signal)

    def addFrame(self, frame):
        """
        Adds a Frame
        """
        self._list.append(frame)
        return self._list[len(self._list) - 1]

    def remove(self, frame):
        """
        Adds a Frame
        """
        self._list.remove(frame)

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

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)


class BoardUnit(object):
    """
    Contains one Boardunit/ECU
    """

    def __init__(self, name):
        self._name = name.strip()
        self._attributes = {}
        self._comment = None

    def addAttribute(self, attribute, value):
        """
        adds some Attribute to current Boardunit/ECU
        """
        self._attributes[attribute] = value

    def addComment(self, comment):
        """
        Set comment of Signal
        """
        self._comment = comment

    def __str__(self):
        return self._name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def attributes(self):
        return self._attributes

    @property
    def comment(self):
        return self._comment


class BoardUnitList(object):
    """
    Contains all Boardunits/ECUs of a canmatrix in a list
    """

    def __init__(self):
        self._list = []

    def add(self, BU):
        """
        add Boardunit/ECU to list
        """
        if BU._name.strip() not in self._list:
            self._list.append(BU)

    def remove(self, BU):
        """
        remove Boardunit/ECU to list
        """
        if BU._name.strip() not in self._list:
            self._list.remove(BU)

    def byName(self, name):
        """
        returns Boardunit-Object of list by Name
        """
        for test in self._list:
            if test._name == name:
                return test
        return None

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)


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

        if 'is_float' in kwargs:
            self._is_float = kwargs["is_float"]
        else:
            self._is_float = False

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
            if kwargs["multiplex"] is not None and kwargs[
                    "multiplex"] != 'Multiplexor':
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

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def attributes(self):
        return self._attributes

    @property
    def comment(self):
        return self._comment

    @property
    def multiplex(self):
        return self._multiplex

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, valueTable):
        self._values = valueTable

    @property
    def comment(self):
        return self._comment

    @property
    def receiver(self):
        return self._receiver

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, unit):
        self._unit = unit

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def factor(self):
        return self._factor

    @factor.setter
    def factor(self, factor):
        self._factor = factor

    @property
    def is_float(self):
        return self._is_float

    @property
    def is_signed(self):
        return self._is_signed

    @property
    def is_little_endian(self):
        return self._is_little_endian

    @property
    def signalsize(self):
        return self._signalsize

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, value):
        self._min = value

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, value):
        self._max = value

    def addComment(self, comment):
        """
        Set comment of Signal
        """
        self._comment = comment

    def addReceiver(self, receiver):
        """
        add receiver Boardunit/ECU-Name to Signal
        """
        if receiver not in self._receiver:
            self._receiver.append(receiver)

    def addAttribute(self, attribute, value):
        """
        Add Attribute to Signal
        """
        if attribute not in self._attributes:
            self._attributes[attribute] = value.replace('"', '')

    def delAttribute(self, attribute):
        """
        Remove Attribute to Signal
        """

        if attribute in self._attributes:
            del self._attributes[attribute]

    def addValues(self, value, valueName):
        """
        Add Value/Description to Signal
        """
        self._values[int(value)] = valueName

    def setStartbit(self, startBit, bitNumbering=None, startLittle=None):
        """
        set startbit.
        bitNumbering is 1 for LSB0/LSBFirst, 0 for MSB0/MSBFirst.
        If bit numbering is consistent with byte order (little=LSB0, big=MSB0)
        (KCD, SYM), start bit unmodified.
        Otherwise reverse bit numbering. For DBC, ArXML (OSEK),
        both little endian and big endian use LSB0.
        If bitNumbering is None, assume consistent with byte order.
        If startLittle is set, given startBit is assumed start from lsb bit
        rather than the start of the signal data in the message data
        """
        # bit numbering not consistent with byte order. reverse
        if bitNumbering is not None and bitNumbering != self._is_little_endian:
            startBit = startBit - (startBit % 8) + 7 - (startBit % 8)
        # if given startbit is for the end of signal data (lsbit),
        # convert to start of signal data (msbit)
        if startLittle is True and self._is_little_endian is False:
            startBit = startBit + 1 - self._signalsize
        if startBit < 0:
            print("wrong startbit found Signal: %s Startbit: %d" %
                  (self.name, startBit))
            raise Exception("startbit lower zero")
        self._startbit = startBit

    def getStartbit(self, bitNumbering=None, startLittle=None):
        startBit = self._startbit
        # convert from big endian start bit at
        # start bit(msbit) to end bit(lsbit)
        if startLittle is True and self._is_little_endian is False:
            startBit = startBit + self._signalsize - 1
        # bit numbering not consistent with byte order. reverse
        if bitNumbering is not None and bitNumbering != self._is_little_endian:
            startBit = startBit - (startBit % 8) + 7 - (startBit % 8)
        return int(startBit)

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

    def __str__(self):
        return self._name


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

    @property
    def signals(self):
        return self._members

    @property
    def id(self):
        return self._Id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __str__(self):
        return self._name

    def __iter__(self):
        return iter(self._members)


class Frame(object):
    """
    contains one Frame with following attributes
    _Id, 
    _name, 
    _Transmitter (list of boardunits/ECU-names),
    _Size (= DLC),
    _signals (list of signal-objects), 
    _attributes (list of attributes),
    _receiver (list of boardunits/ECU-names),
    _extended (Extended Frame = 1),
    _comment
    """

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

    @property
    def attributes(self):
        return self._attributes

    @property
    def receiver(self):
        return self._receiver

    @property
    def SignalGroups(self):
        return self._SignalGroups

    @property
    def signals(self):
        return self._signals

    @property
    def transmitter(self):
        return self._Transmitter

    @property
    def size(self):
        return self._Size

    @size.setter
    def size(self, value):
        self._Size = value

    @property
    def id(self):
        return self._Id

    @id.setter
    def id(self, value):
        self._Id = value

    @property
    def comment(self):
        return self._comment

    @property
    def extended(self):
        return self._extended

    @extended.setter
    def extended(self, value):
        self._extended = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __iter__(self):
        return iter(self._signals)

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
        return self._signals[len(self._signals) - 1]

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
            self._attributes[attribute] = str(value)

    def delAttribute(self, attribute):
        """
        Remove attribute to attribute-list of frame
        """
        if attribute in self._attributes:
            del self._attributes[attribute]

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
            if sig.getStartbit() + int(sig._signalsize) > maxBit:
                maxBit = sig.getStartbit() + int(sig._signalsize)
        self._Size = max(self._Size, int(math.ceil(maxBit / 8)))

    def updateReceiver(self):
        """
        collect receivers of frame out of receiver given in each signal
        """
        for sig in self._signals:
            for receiver in sig._receiver:
                self.addReceiver(receiver)

    def __str__(self):
        return self._name


class Define(object):
    """
    these objects hold the defines and default-values
    """

    def __init__(self, definition):
        definition = definition.strip()
        self.definition = definition
        self.type = None

        # for any known type:
        if definition[0:3] == 'INT':
            self._type = 'INT'
            min, max = definition[4:].split(' ', 2)
            self.min = int(min)
            self.max = int(max)

        elif definition[0:6] == 'STRING':
            self.type = 'STRING'
            self.min = None
            self.max = None

        elif definition[0:4] == 'ENUM':
            self.type = 'ENUM'
            self.values = definition[5:].split(',')

        elif definition[0:3] == 'HEX':
            self.type = 'HEX'
            min, max = definition[4:].split(' ', 2)
            self.min = int(min)
            self.max = int(max)

        elif definition[0:5] == 'FLOAT':
            self.type = 'FLOAT'
            min, max = definition[6:].split(' ', 2)
            self.min = float(min)
            self.max = float(max)

        self._defaultValue = None

    def addDefault(self, default):
        self._defaultValue = default

    @property
    def defaultValue(self):
        return self._defaultValue


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
        self._BUs = BoardUnitList()
        self._fl = FrameList()
        self._signalDefines = {}
        self._frameDefines = {}
        self._globalDefines = {}
        self._buDefines = {}
        self._valueTables = {}

    @property
    def attributes(self):
        return self._attributes

    @property
    def boardUnits(self):
        return self._BUs

    @property
    def frames(self):
        return self._fl

    @property
    def signalDefines(self):
        return self._signalDefines

    @property
    def frameDefines(self):
        return self._frameDefines

    @property
    def globalDefines(self):
        return self._globalDefines

    @property
    def buDefines(self):
        return self._buDefines

    @property
    def valueTables(self):
        return self._valueTables

    def __iter__(self):
        return iter(self._fl)

    def addValueTable(self, name, valueTable):
        self._valueTables[name] = valueTable

    def addAttribute(self, attribute, value):
        """
        add attribute to attribute-list of canmatrix
        """
        if attribute not in self._attributes:
            self._attributes[attribute] = value

    def addSignalDefines(self, type, definition):
        """
        add signal-attribute definition to canmatrix
        """
        if type not in self._signalDefines:
            self._signalDefines[type] = Define(definition)

    def addFrameDefines(self, type, definition):
        """
        add frame-attribute definition to canmatrix
        """
        if type not in self._frameDefines:
            self._frameDefines[type] = Define(definition)

    def addBUDefines(self, type, definition):
        """
        add Boardunit-attribute definition to canmatrix
        """
        if type not in self._buDefines:
            self._buDefines[type] = Define(definition)

    def addGlobalDefines(self, type, definition):
        """
        add global-attribute definition to canmatrix
        """
        if type not in self._globalDefines:
            self._globalDefines[type] = Define(definition)

    def addDefineDefault(self, name, value):
        if name in self._signalDefines:
            self._signalDefines[name].addDefault(value)
        if name in self._frameDefines:
            self._frameDefines[name].addDefault(value)
        if name in self._buDefines:
            self._buDefines[name].addDefault(value)
        if name in self._globalDefines:
            self._globalDefines[name].addDefault(value)

    def deleteObsoleteDefines(self):
        toBeDeleted = []
        for frameDef in self.frameDefines:
            found = False
            for frame in self.frames:
                if frameDef in frame.attributes:
                    found = True
                    break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(frameDef)
        for element in toBeDeleted:
            del self.frameDefines[element]
        toBeDeleted = []
        for buDef in self.buDefines:
            found = False
            for ecu in self.boardUnits:
                if buDef in ecu.attributes:
                    found = True
                    break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(buDef)
        for element in toBeDeleted:
            del self.buDefines[element]

        toBeDeleted = []
        for signalDef in self.signalDefines:
            found = False
            for frame in self.frames:
                for signal in frame.signals:
                    if signalDef in signal.attributes:
                        found = True
                        break
            if found is False and found not in toBeDeleted:
                toBeDeleted.append(signalDef)
        for element in toBeDeleted:
            del self.signalDefines[element]

    def frameById(self, Id):
        return self._fl.byId(Id)

    def frameByName(self, name):
        return self._fl.byName(name)

    def boardUnitByName(self, name):
        return self._BUs.byName(name)

    def deleteZeroSignals(self):
        for frame in self.frames:
            for signal in frame.signals:
                if 0 == signal.signalsize:
                    frame.signals.remove(signal)

    def delSignalAttributes(self, unwantedAttributes):
        for frame in self.frames:
            for signal in frame.signals:
                for attrib in unwantedAttributes:
                    signal.delAttribute(attrib)

    def delFrameAttributes(self, unwantedAttributes):
        for frame in self.frames:
            for attrib in unwantedAttributes:
                frame.delAttribute(attrib)

    def recalcDLC(self, strategy):
        for frame in self.frames:
            originalDlc = frame.size
            if "max" == strategy:
                frame.calcDLC()
            if "force" == strategy:
                maxBit = 0
                for sig in frame.signals:
                    if sig.getStartbit() + int(sig._signalsize) > maxBit:
                        maxBit = sig.getStartbit() + int(sig._signalsize)
                frame._Size = math.ceil(maxBit / 8)

    def renameEcu(self, old, newName):
        if type(old).__name__ == 'instance':
            pass
        else:
            old = self.boardUnitByName(old)
            oldName = old.name
        old.name = newName
        for frame in self.frames:
            if oldName in frame.transmitter:
                frame.transmitter.remove(oldName)
                frame.addTransmitter(newName)
            for signal in frame.signals:
                if oldName in signal.receiver:
                    signal.receiver.remove(oldName)
                    signal.addReceiver(newName)
            frame.updateReceiver()

    def delEcu(self, ecu):
        if type(ecu).__name__ == 'instance':
            pass
        else:
            ecu = self.boardUnitByName(ecu)
        self.boardUnits.remove(ecu)
        for frame in self.frames:
            if ecu.name in frame.transmitter:
                frame.transmitter.remove(ecu.name)
            for signal in frame.signals:
                if ecu.name in signal.receiver:
                    signal.receiver.remove(ecu.name)
            frame.updateReceiver()

    def renameFrame(self, old, newName):
        if type(old).__name__ == 'instance':
            pass
        else:
            old = self.frameByName(old)
        oldName = old.name
        old.name = newName
        for frame in self.frames:
            if frame.name == oldName:
                frame.name = newName

    def delFrame(self, frame):
        if type(frame).__name__ == 'instance':
            pass
        else:
            frame = self.frameByName(frame)
        self.frames.remove(frame)

    def renameSignal(self, old, newName):
        if type(old).__name__ == 'instance':
            old.name = newName
        else:
            for frame in self.frames:
                signal = frame.signalByName(old)
                if signal is not None:
                    signal.name = newName

    def delSignal(self, signal):
        if type(signal).__name__ == 'instance':
            for frame in self.frames:
                if signal in frame.signals:
                    frame.signals.remove(sig)
        else:
            for frame in self.frames:
                sig = frame.signalByName(signal)
                if sig is not None:
                    frame.signals.remove(sig)


#
#
#
def putSignalValueInFrame(startbit, len, format, value, frame):
    """
    puts a signal-value to the right position in a frame
    """

    if format == 1:  # Intel
        lastbit = startbit + len
        firstbyte = math.floor(startbit / 8) - 1
        lastbyte = math.floor((lastbit - 1) / 8)
        # im lastbyte mit dem msb anfangen
        # im firstbyte mit dem lsb aufhoeren
        for i in range(lastbyte, firstbyte, -1):
            if lastbit % 8 != 0:
                nbits = lastbit % 8
            else:
                nbits = min(len, 8)
            nbits = min(len, nbits)

            start = lastbit - 1 - int(math.floor((lastbit - 1) / 8)) * 8
            end = lastbit - nbits - int(math.floor((lastbit - nbits) / 8)) * 8

            len -= nbits
            mask = (0xff >> 7 - start) << end
            mask &= 0xff
            frame[i] |= (((value >> len) << end) & mask)
            lastbit = startbit + len
    else:  # Motorola
        # TODO needs review, is probably wrong till we use LSB for startbit
        firstbyte = math.floor(startbit / 8)
        bitsInfirstByte = startbit % 8 + 1
        restnBits = len - bitsInfirstByte
        lastbyte = firstbyte + math.floor(restnBits / 8)
        if restnBits % 8 > 0:
            lastbyte += 1
        restLen = len
        nbits = bitsInfirstByte
        for i in range(firstbyte, lastbyte + 1):
            end = 0
            if restLen < 8:
                end = 8 - restLen
            mask = (0xff >> (8 - nbits)) << end
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
        return "DA:{da:#02X} PGN:{pgn:#04X} SA:{sa:#02X}".format(
            da=self.destination, pgn=self.pgn, sa=self.source)
