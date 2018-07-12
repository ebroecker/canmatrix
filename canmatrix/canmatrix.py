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
import attr

from collections import OrderedDict

import logging
import fnmatch

defaultFloatFactory = float
try:
    from decimal import *
    defaultFloatFactory = Decimal
except:
    defaultFloatFactory = float


logger = logging.getLogger('root')
try:
    import bitstruct
except:
    bitstruct = None
    logger.info("bitstruct could not be imported // No signal de/encoding possible // try pip install bitstruct")

from past.builtins import basestring
import copy

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
        lastFrame = self._list[len(self._list) - 1]
        lastFrame.addSignal(signal)
        return lastFrame

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

    def byId(self, Id, extended=None):
        """
        returns a Frame-Object by given Frame-ID
        """
        Id = int(Id)
        extendedMarker = 0x80000000
        for test in self._list:
            if test.id == Id:
                if extended is None:
                    # found ID while ignoring extended or standard
                    return test
                elif test.extended == extended:
                    # found ID while checking extended or standard
                    return test
            else:
                if extended is not None:
                    # what to do if Id is not equal and extended is also provided ???
                    pass
                else:
                    if test.extended and Id & extendedMarker:
                        # check regarding common used extended Bit 31
                        if test.id == Id - extendedMarker:
                            return test
        return None

    def byName(self, Name):
        """
        returns a Frame-Object by given Frame-Name
        """
        for test in self._list:
            if test.name == Name:
                return test
        return None

    def glob(self, globStr):
        """
        returns array of frame-objects by given globstr
        :param globStr:
        :return: array
        """
        returnArray = []
        for test in self._list:
            if fnmatch.fnmatchcase(test.name, globStr):
                returnArray.append(test)
        return returnArray


    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)


class BoardUnit(object):
    """
    Contains one Boardunit/ECU
    """

    def __init__(self, name):
        self.name = name.strip()
        self.attributes = {}
        self.comment = None

    def attribute(self, db, attributeName):
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        else:
            if attributeName in db.buDefines:
                define = db.buDefines[attributeName]
                return define.defaultValue


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
        self._list = []

    def add(self, BU):
        """
        add Boardunit/ECU to list
        """
        for bu in self._list:
            if BU.name.strip() == bu.name:
                return
        self._list.append(BU)

    def remove(self, BU):
        """
        remove Boardunit/ECU to list
        """
        if BU.name.strip() in self._list:
            self._list.remove(BU)

    def byName(self, name):
        """
        returns Boardunit-Object of list by Name
        """
        for test in self._list:
            if test.name == name:
                return test
        return None

    def glob(self, globStr):
        """
        returns array of ecu-objects by given globstr
        :param globStr:
        :return: array
        """
        returnArray = []
        for test in self._list:
            if fnmatch.fnmatchcase(test.name, globStr):
                returnArray.append(test)
        return returnArray


    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)


def normalizeValueTable(table):
    return {int(k): v for k, v in table.items()}


@attr.s(cmp=False)
class Signal(object):
    """
    contains on Signal of canmatrix-object
    with following attributes:
            name, startbit,signalsize (in Bits)
            is_little_endian (1: Intel, 0: Motorola)
            is_signed ()
            factor, offset, min, max
            receiver  (Boarunit/ECU-Name)
            attributes, _values, _unit, _comment
            _multiplex ('Multiplexor' or Number of Multiplex)
    """



    name = attr.ib(default = "")
#    float_factory = attr.ib(default=defaultFloatFactory)
    float_factory = defaultFloatFactory
    startBit = attr.ib(type=int, default=0)
    signalSize = attr.ib(type=int, default = 0)
    is_little_endian = attr.ib(type=bool, default = True)
    is_signed = attr.ib(type=bool, default = True)
    offset = attr.ib(converter = float_factory, default = float_factory(0.0))
    factor = attr.ib(converter = float_factory, default = float_factory(0.0))

    #    offset = attr.ib(converter = float_factory, default = 0.0)

    min  = attr.ib(converter=float_factory)
    @min.default
    def setDefaultMin(self):
        return  self.calcMin()

    max =  attr.ib(converter = float_factory)
    @max.default
    def setDefaultMax(self):
        return  self.calcMax()

    unit = attr.ib(type=str, default ="")
    receiver = attr.ib(default =[])
    comment = attr.ib(default = None)
    _multiplex  = attr.ib(default =None)

    mux_value = attr.ib(default = None)
    is_float = attr.ib(type=bool, default = False)
    enumeration = attr.ib(type=str, default = None),
    comments = attr.ib(type=dict, default ={})
    attributes = attr.ib(type=dict, default ={})
    values = attr.ib(type=dict, convert=normalizeValueTable, default ={})
    calc_min_for_none = attr.ib(type=bool, default = True)
    calc_max_for_none = attr.ib(type=bool, default = True)
    muxValMax = attr.ib(default = 0)
    muxValMin = attr.ib(default = 0)
    muxerForSignal= attr.ib(type=str, default = None)

    def __attrs_post_init__(self):
        self.multiplex(self._multiplex)


    @property
    def spn(self):
        if "SPN" in self.attributes:
            return self.attributes["SPN"]
        else:
            return None

    def multiplex(self, value):
        self.mux_val = None
        self.is_multiplexer = False
        if value is not None and value != 'Multiplexor':
            ret_multiplex = int(value)
            self.mux_val = int(value)
        else:
            self.is_multiplexer = True
            ret_multiplex = value
        return ret_multiplex


    def attribute(self, db, attributeName):
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        else:
            if attributeName in db.signalDefines:
                define = db.signalDefines[attributeName]
                return define.defaultValue

    def addComment(self, comment):
        """
        Set comment of Signal
        """
        self.comment = comment

    def addReceiver(self, receiver):
        """
        add receiver Boardunit/ECU-Name to signal
        """
        if receiver not in self.receiver:
            self.receiver.append(receiver)

    def delReceiver(self, receiver):
        """
        remove receiver Boardunit/ECU-Name from signal
        """
        if receiver in self.receiver:
            self.receiver.remove(receiver)

    def addAttribute(self, attribute, value):
        """
        Add Attribute to Signal
        """
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
        startBit = self.startBit
        # convert from big endian start bit at
        # start bit(msbit) to end bit(lsbit)
        if startLittle is True and self.is_little_endian is False:
            startBit = startBit + self.signalSize - 1
        # bit numbering not consistent with byte order. reverse
        if bitNumbering is not None and bitNumbering != self.is_little_endian:
            startBit = startBit - (startBit % 8) + 7 - (startBit % 8)
        return int(startBit)

    def calculateRawRange(self):
        rawRange = 2 ** self.signalSize
        if self.is_signed:
            rawRange /= 2
        return (self.float_factory(-rawRange if self.is_signed else 0),
                self.float_factory(rawRange - 1))

    def setMin(self, min=None):
        self.min = min
        if self.calc_min_for_none and self.min is None:
            self.min = self.calcMin()

        return self.min

    def calcMin(self):
        rawMin = self.calculateRawRange()[0]

        return self.offset + (rawMin * self.factor)

    def setMax(self, max=None):
        self.max = max

        if self.calc_max_for_none and self.max is None:
            self.max = self.calcMax()

        return self.max
            
    def calcMax(self):
        rawMax = self.calculateRawRange()[1]

        return self.offset + (rawMax * self.factor)

    def bitstruct_format(self):
        """Get the bit struct format for this signal

        :return: str        """
        endian = '<' if self.is_little_endian else '>'
        if self.is_float:
            bit_type = 'f'
        else:
            bit_type = 's' if self.is_signed else 'u'

        return endian + bit_type + str(self.signalsize)

    def phys2raw(self, value=None):
        """Return the raw value (= as is on CAN)

        :param value: (scaled) value or value choice to encode
        :return: raw unscaled value as it appears on the bus
        """
        if value is None:
            return int(self.attributes.get('GenSigStartValue', 0))

        if isinstance(value, basestring):
            for value_key, value_string in self.values.items():
                if value_string == value:
                    value = value_key
                    break
            else:
                raise ValueError(
                        "{} is invalid value choice for {}".format(value, self)
                )

        if not (self.min <= value <= self.max):
            logger.info(
                "Value {} is not valid for {}. Min={} and Max={}".format(
                    value, self, self.min, self.max)
                )
        raw_value = (value - self.offset) / self.factor

        if not self.is_float:
            raw_value = int(raw_value)
        return raw_value

    def raw2phys(self, value, decodeToStr=False):
        """Decode the given raw value (= as is on CAN)
        :param value: raw value
        :return: physical value (scaled)
        """

        value = value * self.factor + self.offset
        if decodeToStr:
            for value_key, value_string in self.values.items():
                if value_key == value:
                    value = value_string
                    break

        return value

    def __str__(self):
        return self.name


class SignalGroup(object):
    """
    contains Signals, which belong to signal-group
    """

    def __init__(self, name, Id):
        self.signals = []
        self.name = name
        self.Id = Id

    def addSignal(self, signal):
        if signal not in self.signals:
            self.signals.append(signal)

    def delSignal(self, signal):
        if signal in self.signals:
            self.signals[signal].remove()

    def byName(self, name):
        """
        returns Signalobject-Object of list by Name
        """
        for test in self.signals:
            if test.name == name:
                return test
        return None

    @property
    def id(self):
        return self.Id

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter(self.signals)


class Frame(object):
    """
    contains one Frame with following attributes
    _Id, 
    name,
    transmitter (list of boardunits/ECU-names),
    size (= DLC),
    signals (list of signal-objects),
    attributes (list of attributes),
    receiver (list of boardunits/ECU-names),
    extended (Extended Frame = 1),
    comment
    """

    def __init__(self, name, **kwargs):
        self.name = name
            
        args = [
            ('Id', '_Id', int, 0),
            ('dlc', 'size', int, 0),
            ('transmitter', 'transmitter', None, []),
            ('extended', 'extended', bool, False),
            ('is_complex_multiplexed', 'is_complex_multiplexed', bool, False),
            ('is_fd', 'is_fd', bool, False),
            ('comment', 'comment', str, None),
            ('signals', 'signals', None, []),
            ('mux_names', 'mux_names', None, {}),
            ('attributes', 'attributes', None, {}),
            ('receiver', 'receiver', None, []),
            ('signalGroups', 'signalGroups', None, []),
            ('j1939_pgn', '_j1939_pgn', int, None),
            ('j1939_source', '_j1939_source', int, 0),
            ('j1939_prio', '_j1939_prio', int, 0),
            ('is_j1939', 'is_j1939', bool, False),
            #            ('cycleTime', '_cycleTime', int, None),
            #            ('sendType', '_sendType', str, None),
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

        if self._j1939_pgn is not None:
            self.recalcJ1939Id()
        # we got a j1939 PGN,


    @property
    def id(self):
        return self._Id

    @id.setter
    def id(self, value):
        self._Id = value

    @property
    def is_multiplexed(self):
        for sig in self.signals:
            if sig.is_multiplexer:
                return True
        return False

    @property
    def pgn(self):
        return CanId(self._Id).pgn

    @pgn.setter
    def pgn(self, value):
        self._j1939_pgn = value
        self.recalcJ1939Id()

    @property
    def priority(self):
        return self._j1939_prio

    @priority.setter
    def priority(self, value):
        self._j1939_prio = value
        self.recalcJ1939Id()

    @property
    def source(self):
        return self._j1939_source

    @source.setter
    def pgn(self, value):
        self._j1939_source = value
        self.recalcJ1939Id()

    def recalcJ1939Id(self):
        self.id = (self._j1939_source & 0xff) + ((self._j1939_pgn & 0xffff) << 8) + ((self._j1939_prio & 0x7) << 26)
        self.extended = True
        self.is_j1939 = True

    #    @property
#    def cycleTime(self):
#        if self._cycleTime is None:
#            self._cycleTime = self.attribute(None, "GenMsgCycleTime")
#        return self._cycleTime

#    @property
#    def sendType(self, db = None):
#        if self._sendType is None:
#            self._sendType = self.attribute(None, "GenMsgSendType")
 #       return self._sendType

#    @cycleTime.setter
#    def cycleTime(self, value):
#        self._cycleTime = value
#        self.attributes["GenMsgCycleTime"] = value

#    @sendType.setter
#    def sendType(self, value):
 #       self._sendType = value
 #       self.attributes["GenMsgCycleTime"] = value



    def attribute(self, db, attributeName):
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        elif db is not None:
            if attributeName in db.frameDefines:
                define = db.frameDefines[attributeName]
                return define.defaultValue
        else:
            return None

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
            if signalGroup.name == name:
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

    def delTransmitter(self, transmitter):
        """
        del transmitter Boardunit/ECU-Name from Frame
        """
        if transmitter in self.transmitter:
            self.transmitter.remove(transmitter)

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

    def globSignals(self, globStr):
        """
        returns signal-object by signalname
        """
        returnArray = []
        for signal in self.signals:
            if fnmatch.fnmatchcase(signal.name, globStr):
                returnArray.append(signal)
        return returnArray

    def addAttribute(self, attribute, value):
        """
        add attribute to attribute-list of frame; If Attribute already exits, modify value
        """
        try:
            self.attributes[attribute] = str(value)
        except:
            self.attributes[attribute] = value

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

    def bitstruct_format(self, signalsToDecode = None):
        """Returns the Bitstruct format string of this frame

        :return: Bitstruct format string.
        """
        fmt = []
        frame_size = self.size * 8
        end = frame_size
        if signalsToDecode is None:
            signals = sorted(self.signals, key=lambda s: s.getStartbit())
        else:
            signals = sorted(signalsToDecode, key=lambda s: s.getStartbit())

        for signal in signals:
            start = frame_size - signal.getStartbit() - signal.signalsize
            padding = end - (start + signal.signalsize)
            if padding > 0:
                fmt.append('p' + str(padding))
            fmt.append(signal.bitstruct_format())
            end = start
        if end != 0:
            fmt.append('p' + str(end))
        # assert bitstruct.calcsize(''.join(fmt)) == frame_size
        return ''.join(fmt)

    def encode(self, data=None):
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param data: data dictionary
        :return: A byte string of the packed values.
        """
        if bitstruct is None:
            logger.error("message decoding not supported due bitstruct import error // try pip install bitstruct")
            return None

        data = {} if data is None else data

        if self.is_complex_multiplexed:
            # TODO
            pass
        elif self.is_multiplexed:
            # search for mulitplexer-signal
            muxSignal = None
            for signal in self.signals:
                if signal.is_multiplexer:
                    muxSignal = signal
                    muxVal = data.get(signal.name)
            # create list of signals which belong to muxgroup
            encodeSignals = [muxSignal]
            for signal in self.signals:
                if signal.mux_val == muxVal or signal.mux_val is None:
                    encodeSignals.append(signal)
            fmt = self.bitstruct_format(encodeSignals)
            signals = sorted(encodeSignals, key=lambda s: s.getStartbit())
        else:
            fmt = self.bitstruct_format()
            signals = sorted(self.signals, key=lambda s: s.getStartbit())
        signal_value = []
        for signal in signals:
            signal_value.append(
                signal.phys2raw(data.get(signal.name))
            )

        return bitstruct.pack(fmt, *signal_value)

    def decode(self, data, decodeToStr=False):
        """Return OrderedDictionary with Signal Name: Signal Value

        :param data: Iterable or bytes.
            i.e. (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8)
        :return: OrderedDictionary
        """
        if bitstruct is None:
            logger.error("message decoding not supported due bitstruct import error // try pip install bitstruct")
            return None

        if self.is_complex_multiplexed:
            # TODO
            pass
        elif self.is_multiplexed:
            # find multiplexer and decode only its value:
            for signal in self.signals:
                if signal.is_multiplexer:
                    fmt = self.bitstruct_format([signal])
                    signals = sorted(self.signals, key=lambda s: s.getStartbit())
                    signals_values = OrderedDict()
                    for signal, value in zip(signals, bitstruct.unpack(fmt, data)):
                        signals_values[signal.name] = signal.raw2phys(value, decodeToStr)
                muxVal = int(signals_values.values()[0])
            # find all signals with the identified multiplexer-value
            muxedSignals = []
            for signal in self.signals:
                if signal.mux_val == muxVal or signal.mux_val is None:
                    muxedSignals.append(signal)
            fmt = self.bitstruct_format(muxedSignals)
            signals = sorted(muxedSignals, key=lambda s: s.getStartbit())
        else:
            fmt = self.bitstruct_format()
            signals = sorted(self.signals, key=lambda s: s.getStartbit())

        #decode
        signals_values = OrderedDict()
        for signal, value in zip(signals, bitstruct.unpack(fmt, data)):
            signals_values[signal.name] = signal.raw2phys(value, decodeToStr)

        return signals_values


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
        self.defaultValue = None

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
            tempValues = definition[5:].split(',')
            self.values = []
            for value in tempValues:
                value = value.strip()
                if value[0] == '"':
                    value = value[1:]
                if value[-1] == '"':
                    value = value[:-1]
                self.values.append(value)

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


    def addDefault(self, default):
        if default is not None and len(default) > 1 and default[0] == '"' and default[-1] =='"':
            default = default[1:-1]
        self.defaultValue = default

    def update(self):
        if self.type != 'ENUM':
            return
        self.definition = 'ENUM "' + '","' .join(self.values) +'"'


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

    @property
    def contains_fd(self):
        for frame in self.frames:
            if frame.is_fd:
                return True
        return False

    @property
    def contains_j1939(self):
        for frame in self.frames:
            if frame.is_j1939:
                return True
        return False


    def attribute(self, attributeName):
        if attributeName in self.attributes:
            return self.attributes[attributeName]
        else:
            if attributeName in self.globalDefines:
                define = self.globalDefines[attributeName]
                return define.defaultValue

    def addValueTable(self, name, valueTable):
        self.valueTables[name] = normalizeValueTable(valueTable)

    def addAttribute(self, attribute, value):
        """
        add attribute to attribute-list of canmatrix
        """
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

    def globFrames(self, globStr):
        return self.frames.glob(globStr)

    def boardUnitByName(self, name):
        return self.boardUnits.byName(name)

    def globBoardUnits(self, globStr):
        return self.boardUnits.glob(globStr)


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
                    if sig.getStartbit() + int(sig.signalSize) > maxBit:
                        maxBit = sig.getStartbit() + int(sig.signalSize)
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
            ecuList = [ecu]
        else:
            ecuList = self.globBoardUnits(ecu)
        for ecu in ecuList:
            self.boardUnits.remove(ecu)
            for frame in self.frames:
                if ecu.name in frame.transmitter:
                    frame.transmitter.remove(ecu.name)
                for signal in frame.signals:
                    if ecu.name in signal.receiver:
                        signal.receiver.remove(ecu.name)
                frame.updateReceiver()

    def updateEcuList(self):
        for frame in self.frames:
            for ecu in frame.transmitter:
                self.boardUnits.add(BoardUnit(ecu))
            frame.updateReceiver()
            for signal in frame.signals:
                for ecu in signal.receiver:
                    self.boardUnits.add(BoardUnit(ecu))

    def renameFrame(self, old, newName):
        if type(old).__name__ == 'instance':
            oldName = old.name
        for frame in self.frames:
            if old[-1] == '*':
                oldPrefixLen = len(old)-1
                if frame.name[:oldPrefixLen] == old[:-1]:
                    frame.name = newName + frame.name[oldPrefixLen:]
            if old[0] == '*':
                oldSuffixLen = len(old)-1
                if frame.name[-oldSuffixLen:] == old[1:]:
                    frame.name = frame.name[:-oldSuffixLen] + newName
            elif frame.name == old:
                frame.name = newName

    def delFrame(self, frame):
        if type(frame).__name__ == 'instance' or type(frame).__name__ == 'Frame':
            pass
        else:
            frame = self.frameByName(frame)
        self.frames.remove(frame)

    def renameSignal(self, old, newName):
        if type(old).__name__ == 'instance' or type(old).__name__ == 'Signal':
            old.name = newName
        else:
            for frame in self.frames:
                if old[-1] == '*':
                    oldPrefixLen = len(old) - 1
                    for signal in frame.signals:
                        if signal.name[:oldPrefixLen] == old[:-1]:
                            signal.name = newName + signal.name[oldPrefixLen:]
                if old[0] == '*':
                    oldSuffixLen = len(old) - 1
                    for signal in frame.signals:
                        if signal.name[-oldSuffixLen:] == old[1:]:
                            signal.name = signal.name[:-oldSuffixLen] + newName

                else:
                    signal = frame.signalByName(old)
                    if signal is not None:
                        signal.name = newName

    def delSignal(self, signal):
        if type(signal).__name__ == 'instance' or type(signal).__name__ == 'Signal':
            for frame in self.frames:
                if signal in frame.signals:
                    frame.signals.remove(signal)
        else:
            for frame in self.frames:
                signalList = frame.globSignals(signal)
                for sig in signalList:
                    frame.signals.remove(sig)

    def addSignalReceiver(self, frameName, signalName, ecu):
        frames = self.globFrames(frameName)
        for frame in frames:
            signal = frame.signalByName(signalName)
            if signal is not None:
                signal.addReceiver(ecu)
                for signal in frame.globSignals(signalName):
                    signal.addReceiver(ecu)
                frame.updateReceiver()

    def delSignalReceiver(self, frameName, signalName, ecu):
        frames = self.globFrames(frameName)
        for frame in frames:
            signal = frame.signalByName(signalName)
            if signal is not None:
                signal.addReceiver(ecu)
                for signal in frame.globSignals(signalName):
                    signal.delReceiver(ecu)
                frame.updateReceiver()

    def addFrameTransmitter(self, frameName, ecu):
        frames = self.globFrames(frameName)
        for frame in frames:
            frame.addTransmitter(ecu)

    def addFrameReceiver(self, frameName, ecu):
        frames = self.globFrames(frameName)
        for frame in frames:
            for signal in frame.signals:
                signal.addReceiver(ecu)

    def delFrameTransmitter(self, frameName, ecu):
        frames = self.globFrames(frameName)
        for frame in frames:
            frame.delTransmitter(ecu)

    def merge(self, mergeArray):
        for dbTemp in mergeArray:
            for frame in dbTemp.frames:
                copyResult = copy.copyFrame(frame.id, dbTemp, self)
                if copyResult == False:
                    logger.error(
                        "ID Conflict, could not copy/merge frame " + frame.name + "  %xh " % frame.id + self.frameById(frame.id).name)

    def setFdType(self):
        for frame in self.frames:
            if frame.size > 8:
                frame.is_fd = True

    def encode(self, frame_id, data):
        """Return a byte string containing the values from data packed
        according to the frame format.

        :param frame_id: frame id
        :param data: data dictionary
        :return: A byte string of the packed values.
        """

        return self.frameById(frame_id).encode(data)

    def decode(self, frame_id, data, decodeToStr=False):
        """Return OrderedDictionary with Signal Name: Signal Value

        :param frame_id: frame id
        :param data: Iterable or bytes.
            i.e. (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8)
        :return: OrderedDictionary
        """
        return self.frameById(frame_id).decode(data, decodeToStr)

    def EnumAttribs2Values(self):
        for define in self.buDefines:
            if self.buDefines[define].type == "ENUM":
                for bu in self.boardUnits:
                    if define in bu.attributes:
                        bu.attributes[define] = self.buDefines[define].values[int(bu.attributes[define])]

        for define in self.frameDefines:
            if self.frameDefines[define].type == "ENUM":
                for frame in self.frames:
                    if define in frame.attributes:
                        frame.attributes[define] = self.frameDefines[define].values[int(frame.attributes[define])]

        for define in self.signalDefines:
            if self.signalDefines[define].type == "ENUM":
                for frame in self.frames:
                    for signal in frame.signals:
                        if define in signal.attributes:
                            signal.attributes[define] = self.signalDefines[define].values[int(signal.attributes[define])]

    def EnumAttribs2Keys(self):
        for define in self.buDefines:
            if self.buDefines[define].type == "ENUM":
                for bu in self.boardUnits:
                    if define in bu.attributes:
                        if len(bu.attributes[define]) > 0:
                            bu.attributes[define] = self.buDefines[define].values.index(bu.attributes[define])
                            bu.attributes[define] = str(bu.attributes[define])
        for define in self.frameDefines:
            if self.frameDefines[define].type == "ENUM":
                for frame in self.frames:
                    if define in frame.attributes:
                        if len(frame.attributes[define]) > 0:
                            frame.attributes[define] = self.frameDefines[define].values.index(frame.attributes[define])
                            frame.attributes[define] = str(frame.attributes[define])
        for define in self.signalDefines:
            if self.signalDefines[define].type == "ENUM":
                for frame in self.frames:
                    for signal in frame.signals:
                        if define in signal.attributes:
                            signal.attributes[define] = self.signalDefines[define].values.index(signal.attributes[define])
                            signal.attributes[define] = str(signal.attributes[define])
#
#
#
def computeSignalValueInFrame(startbit, ln, fmt, value):
    """
    compute the signal value in the frame
    """

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
