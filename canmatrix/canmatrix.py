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

import logging
logger = logging.getLogger('root')


class FrameList(object):
    """
    Keeps all Frames of a Canmatrix
    """

    def __init__(self):
        self.list = []

    def addSignalToLastFrame(self, signal):
        """
        Adds a Signal to the last addes Frame, this is mainly for importers
        """
        self.list[len(self.list) - 1].addSignal(signal)

    def addFrame(self, frame):
        """
        Adds a Frame
        """
        self.list.append(frame)
        return self.list[len(self.list) - 1]

    def remove(self, frame):
        """
        Adds a Frame
        """
        self.list.remove(frame)

    def byId(self, Id):
        """
        returns a Frame-Object by given Frame-ID
        """
        for test in self.list:
            if test.id == int(Id):
                return test
        return None

    def byName(self, Name):
        """
        returns a Frame-Object by given Frame-Name
        """
        for test in self.list:
            if test.name == Name:
                return test
        return None

    def __iter__(self):
        return iter(self.list)

    def __len__(self):
        return len(self.list)


class BoardUnit(object):
    """
    Contains one Boardunit/ECU
    """

    def __init__(self, name):
        self.name = name.strip()
        self.attributes = {}
        self.comment = None

    def addAttribute(self, attribute, value):
        """
        adds some Attribute to current Boardunit/ECU
        """
        self.attributes[attribute] = value

    def addComment(self, comment):
        """
        Set comment of Signal
        """
        self.comment = comment

    def __str__(self):
        return self.name


class BoardUnitList(object):
    """
    Contains all Boardunits/ECUs of a canmatrix in a list
    """

    def __init__(self):
        self.list = []

    def add(self, BU):
        """
        add Boardunit/ECU to list
        """
        if BU.name.strip() not in self.list:
            self.list.append(BU)

    def remove(self, BU):
        """
        remove Boardunit/ECU to list
        """
        if BU.name.strip() not in self.list:
            self.list.remove(BU)

    def byName(self, name):
        """
        returns Boardunit-Object of list by Name
        """
        for test in self.list:
            if test.name == name:
                return test
        return None

    def __iter__(self):
        return iter(self.list)

    def __len__(self):
        return len(self.list)


def normalizeValueTable(table):
    return {int(k): v for k, v in table.items()}


class Signal(object):
    """
    contains on Signal of canmatrix-object
    with following attributes:
            name, startbit,signalsize (in Bits)
            is_little_endian (1: Intel, 0: Motorola)
            is_signed ()
            factor, offset, min, max
            receiver  (Boarunit/ECU-Name)
            attributes, values, unit, comment
            multiplex ('Multiplexor' or Number of Multiplex)
    """

    def __init__(self, name, **kwargs):

        def multiplex(value):
            if value is not None and value != 'Multiplexor':
                multiplex = int(value)
            else:
                multiplex = value
            return multiplex
                        

        args = [
            ('startBit', 'startbit', int, 0),
            ('signalSize', 'signalsize', int, 0),
            ('is_little_endian', 'is_little_endian', bool, True),
            ('is_signed', 'is_signed', bool, True),
            ('factor', 'factor', float, 1),
            ('offset', 'offset', float, 0),
            ('min', 'min', float, None),
            ('max', 'max', float, None),
            ('unit', 'unit', None, ""),
            ('receiver', 'receiver', None, []),
            ('comment', 'comment', None, None),
            ('multiplex', 'multiplex', multiplex, None),
            ('is_float', 'is_float', bool, False),
            ('enumeration', 'enumeration', str, None),
            ('comments', 'comments', None, {}),
            ('attributes', 'attributes', None, {}),
            ('values', '_values', None, {}),
        ]

        for arg_name, destination, function, default in args:
            try:
                value = kwargs[arg_name]
            except KeyError:
                value = default
            else:
                kwargs.pop(arg_name)
            if function is not None and value is not None:
                value = function(value)
            setattr(self, destination, value)
            
        if len(kwargs) > 0:
            raise TypeError('{}() got unexpected argument{} {}'.format(
                self.__class__.__name__,
                's' if len(kwargs) > 1 else '',
                ', '.join(kwargs.keys())
            ))


        # be shure to calc min/max after parsing all arguments 
        if self.min is None:
            self.setMin()

        if self.max is None:
            self.setMax()

        self.name = name


    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, valueTable):
        self._values = normalizeValueTable(valueTable)

    def addComment(self, comment):
        """
        Set comment of Signal
        """
        self.comment = comment

    def addReceiver(self, receiver):
        """
        add receiver Boardunit/ECU-Name to Signal
        """
        if receiver not in self.receiver:
            self.receiver.append(receiver)

    def addAttribute(self, attribute, value):
        """
        Add Attribute to Signal
        """
        if attribute not in self.attributes:
            self.attributes[attribute] = value

    def delAttribute(self, attribute):
        """
        Remove Attribute to Signal
        """

        if attribute in self.attributes:
            del self.attributes[attribute]

    def addValues(self, value, valueName):
        """
        Add Value/Description to Signal
        """
        self.values[int(value)] = valueName

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
        if bitNumbering is not None and bitNumbering != self.is_little_endian:
            startBit = startBit - (startBit % 8) + 7 - (startBit % 8)
        # if given startbit is for the end of signal data (lsbit),
        # convert to start of signal data (msbit)
        if startLittle is True and self.is_little_endian is False:
            startBit = startBit + 1 - self.signalsize
        if startBit < 0:
            print("wrong startbit found Signal: %s Startbit: %d" %
                  (self.name, startBit))
            raise Exception("startbit lower zero")
        self.startbit = startBit

    def getStartbit(self, bitNumbering=None, startLittle=None):
        startBit = self.startbit
        # convert from big endian start bit at
        # start bit(msbit) to end bit(lsbit)
        if startLittle is True and self.is_little_endian is False:
            startBit = startBit + self.signalsize - 1
        # bit numbering not consistent with byte order. reverse
        if bitNumbering is not None and bitNumbering != self.is_little_endian:
            startBit = startBit - (startBit % 8) + 7 - (startBit % 8)
        return int(startBit)

    def calculateRawRange(self):
        rawRange = 2 ** self.signalsize
        if self.is_signed:
            rawRange /= 2
        return (-rawRange if self.is_signed else 0,
                rawRange - 1)

    def setMin(self, min=None):
        self.min = min
        if self.min is None:
            self.min = self.calcMin()

        return self.min

    def calcMin(self):
        rawMin = self.calculateRawRange()[0]

        return self.offset + (rawMin * self.factor)

    def setMax(self, max=None):
        self.max = max

        if self.max is None:
            self.max = self.calcMax()

        return self.max
            
    def calcMax(self):
        rawMax = self.calculateRawRange()[1]

        return self.offset + (rawMax * self.factor)

    def __str__(self):
        return self.name


class SignalGroup(object):
    """
    contains Signals, which belong to signal-group
    """

    def __init__(self, name, id):
        self.members = []
        self.name = name
        self.id = id

    def addSignal(self, signal):
        if signal not in self.members:
            self.members.append(signal)

    def delSignal(self, signal):
        if signal in self.members:
            self.members[signal].remove()

    def byName(self, name):
        """
        returns Signalobject-Object of list by Name
        """
        for test in self.members:
            if test.name == name:
                return test
        return None

    @property
    def signals(self):
        return self.members

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter(self.members)


class Frame(object):
    """
    contains one Frame with following attributes
    id,
    name,
    transmitter (list of boardunits/ECU-names),
    size (= DLC),
    signals (list of signal-objects),
    attributes (list of attributes),
    receiver (list of boardunits/ECU-names),
    extended (Extended Frame = 1),
    signalGroups
    comment
    """

    def __init__(self, name, **kwargs):
        self.name = name
            
        args = [
            ('id', 'id', int, 0),
            ('dlc', 'size', int, 0),
            ('transmitter', 'transmitter', None, []),
            ('extended', 'extended', bool, False),
            ('comment', 'comment', str, None),
            ('signals', 'signals', None, []),
            ('mux_names', 'mux_names', None, {}),
            ('attributes', 'attributes', None, {}),
            ('receiver', 'receiver', None, []),
            ('signalGroups', 'signalGroups', None, []),
        ]

        for arg_name, destination, function, default in args:
            try:
                value = kwargs[arg_name]
            except KeyError:
                value = default
            else:
                kwargs.pop(arg_name)
            if function is not None and value is not None:
                value = function(value)
            setattr(self, destination, value)
            
        if len(kwargs) > 0:
            raise TypeError('{}() got unexpected argument{} {}'.format(
                self.__class__.__name__,
                's' if len(kwargs) > 1 else '',
                ', '.join(kwargs.keys())
            ))


    def __iter__(self):
        return iter(self.signals)

    def addSignalGroup(self, Name, Id, signalNames):
        newGroup = SignalGroup(Name, Id)
        self.signalGroups.append(newGroup)
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
        for signalGroup in self.signalGroups:
            if signalGroup._name == name:
                return signalGroup
        return None

    def addSignal(self, signal):
        """
        add Signal to Frame
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def addTransmitter(self, transmitter):
        """
        add transmitter Boardunit/ECU-Name to Frame
        """
        if transmitter not in self.transmitter:
            self.transmitter.append(transmitter)

    def addReceiver(self, receiver):
        """
        add receiver Boardunit/ECU-Name to Frame
        """
        if receiver not in self.receiver:
            self.receiver.append(receiver)

    def signalByName(self, name):
        """
        returns signal-object by signalname
        """
        for signal in self.signals:
            if signal.name == name:
                return signal
        return None

    def addAttribute(self, attribute, value):
        """
        add attribute to attribute-list of frame
        """
        if attribute not in self.attributes:
            self.attributes[attribute] = str(value)

    def delAttribute(self, attribute):
        """
        Remove attribute to attribute-list of frame
        """
        if attribute in self.attributes:
            del self.attributes[attribute]

    def addComment(self, comment):
        """
        set comment of frame
        """
        self.comment = comment

    def calcDLC(self):
        """
        calc minimal DLC/length for frame (using signal information)
        """
        maxBit = 0
        for sig in self.signals:
            if sig.getStartbit() + int(sig.signalsize) > maxBit:
                maxBit = sig.getStartbit() + int(sig.signalsize)
        self.size = max(self.size, int(math.ceil(maxBit / 8)))
        
    def findNotUsedBits(self):
        """
        find unused bits in frame
        return dict with position and length-tuples
        """
        bitfield = []
        bitfieldLe = []
        bitfieldBe = []
        
        for i in range(0,64):
            bitfieldBe.append(0)
            bitfieldLe.append(0)
            bitfield.append(0)
        i = 0

        for sig in self.signals:
            i += 1
            for bit in range(sig.getStartbit(),  sig.getStartbit() + int(sig.signalsize)):
                if sig.is_little_endian:
                    bitfieldLe[bit] = i
                else:
                    bitfieldBe[bit] = i

        for i in range(0,8):
            for j in range(0,8):
                bitfield[i*8+j] = bitfieldLe[i*8+(7-j)]

        for i in range(0,8):
            for j in range(0,8):
                if bitfield[i*8+j] == 0:
                    bitfield[i*8+j] = bitfieldBe[i*8+j]
        

        return bitfield
    
    def createDummySignals(self):
        bitfield = self.findNotUsedBits()
#        for i in range(0,8):
#            print (bitfield[(i)*8:(i+1)*8])
        startBit = -1
        sigCount = 0
        for i in range(0,64):
            if bitfield[i] == 0 and startBit == -1:
                startBit = i
            if (i == 63 or bitfield[i] != 0) and startBit != -1:
                if i == 63:
                    i = 64
                self.addSignal(Signal("_Dummy_%s_%d" % (self.name,sigCount),signalSize=i-startBit, startBit=startBit, is_little_endian = False))
                startBit = -1
                sigCount +=1
                
#        bitfield = self.findNotUsedBits()
#        for i in range(0,8):
#            print (bitfield[(i)*8:(i+1)*8])
                
            
                

    def updateReceiver(self):
        """
        collect receivers of frame out of receiver given in each signal
        """
        for sig in self.signals:
            for receiver in sig.receiver:
                self.addReceiver(receiver)

    def __str__(self):
        return self.name


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
            self.type = 'INT'
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

        self.defaultValue = None

    def addDefault(self, default):
        self.defaultValue = default



class CanMatrix(object):
    """
    The Can-Matrix-Object
    attributes (global canmatrix-attributes),
    boardUnits (list of boardunits/ECUs),
    frames (list of Frames)
    signalDefines (list of signal-attribute types)
    frameDefines (list of frame-attribute types)
    buDefines (list of BoardUnit-attribute types)
    globalDefines (list of global attribute types)
    valueTables (global defined values)
    """

    def __init__(self):
        self.attributes = {}
        self.boardUnits = BoardUnitList()
        self.frames = FrameList()
        self.signalDefines = {}
        self.frameDefines = {}
        self.globalDefines = {}
        self.buDefines = {}
        self.valueTables = {}

    def __iter__(self):
        return iter(self.frames)

    def addValueTable(self, name, valueTable):
        self.valueTables[name] = normalizeValueTable(valueTable)

    def addAttribute(self, attribute, value):
        """
        add attribute to attribute-list of canmatrix
        """
        if attribute not in self.attributes:
            self.attributes[attribute] = value

    def addSignalDefines(self, type, definition):
        """
        add signal-attribute definition to canmatrix
        """
        if type not in self.signalDefines:
            self.signalDefines[type] = Define(definition)

    def addFrameDefines(self, type, definition):
        """
        add frame-attribute definition to canmatrix
        """
        if type not in self.frameDefines:
            self.frameDefines[type] = Define(definition)

    def addBUDefines(self, type, definition):
        """
        add Boardunit-attribute definition to canmatrix
        """
        if type not in self.buDefines:
            self.buDefines[type] = Define(definition)

    def addGlobalDefines(self, type, definition):
        """
        add global-attribute definition to canmatrix
        """
        if type not in self.globalDefines:
            self.globalDefines[type] = Define(definition)

    def addDefineDefault(self, name, value):
        if name in self.signalDefines:
            self.signalDefines[name].addDefault(value)
        if name in self.frameDefines:
            self.frameDefines[name].addDefault(value)
        if name in self.buDefines:
            self.buDefines[name].addDefault(value)
        if name in self.globalDefines:
            self.globalDefines[name].addDefault(value)

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
        return self.frames.byId(Id)

    def frameByName(self, name):
        return self.frames.byName(name)

    def boardUnitByName(self, name):
        return self.boardUnits.byName(name)

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
                    if sig.getStartbit() + int(sig.signalsize) > maxBit:
                        maxBit = sig.getStartbit() + int(sig.signalsize)
                frame.size = math.ceil(maxBit / 8)

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
                    frame.signals.remove(signal)
        else:
            for frame in self.frames:
                sig = frame.signalByName(signal)
                if sig is not None:
                    frame.signals.remove(sig)


#
#
#
def computeSignalValueInFrame(startbit, ln, fmt, value):
    """
    compute the signal value in the frame
    """
    import pprint

    frame = 0
    if fmt == 1:  # Intel
    # using "sawtooth bit counting policy" here
        pos = ((7 - (startbit % 8)) + 8*(int(startbit/8)))
        while ln > 0:
            # How many bits can we stuff in current byte?
            #  (Should be 8 for anything but the first loop)
            availbitsInByte = 1 + (pos % 8)
            # extract relevant bits from value
            valueInByte = value & ((1<<availbitsInByte)-1)
            # stuff relevant bits into frame at the "corresponding inverted bit"
            posInFrame = ((7 - (pos % 8)) + 8*(int(pos/8)))
            frame |= valueInByte << posInFrame
            # move to the next byte
            pos += 0xf
            # discard used bytes
            value = value >> availbitsInByte
            # reduce length by how many bits we consumed
            ln -= availbitsInByte

    else:  # Motorola
        # Work this out in "sequential bit counting policy"
        # Compute the LSB position in "sequential"
        lsbpos = ((7 - (startbit % 8)) + 8*(int(startbit/8)))
        # deduce the MSB position
        msbpos = 1 + lsbpos - ln
        # "reverse" the value
        cvalue = int(format(value, 'b')[::-1],2)
        # shift the value to the proper position in the frame
        frame = cvalue << msbpos

    # Return frame, to be accumulated by caller
    return frame


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
