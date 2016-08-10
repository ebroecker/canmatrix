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

from __future__ import absolute_import
from builtins import *
from lxml import etree
from .canmatrix import *
import os
import re

def createSignal(signal, nodeList, typeEnums):
    sig = etree.Element('Signal', name=signal.name, offset=str(signal.getStartbit()))
    if signal.signalsize > 1:
        sig.set("length", str(signal.signalsize))
    if signal.is_little_endian == 0:
        sig.set('endianess',"big")

    comment = signal.comment

    if len(signal.attributes.items()) > 0:
        if comment is None:
            comment = ''
        else:
            comment += '\n'

    for attrib,val in sorted(signal.attributes.items()):
        try:
            if attrib in typeEnums and int(val) < len(typeEnums[attrib]):
                val = typeEnums[attrib][int(val)]
            comment += ( "\n" + attrib + ': ' + val)
        except:
            pass
        
    if comment is not None:
        notes = etree.Element('Notes')
        notes.text = comment
        sig.append(notes)

    value = etree.Element('Value')
    if signal.is_signed:
        value.set('type',"signed")

    if float(signal.factor) != 1:
        value.set('slope',str("%g" % signal.factor))
    if float(signal.offset) != 0:
        value.set('intercept',str("%g" % signal.offset))
    if float(signal.min) != 0:
        value.set('min',str("{:.16g}".format(signal.min)))
    if float(signal.max) != 1 and float(signal.max) != 0:
        value.set('max',str("{:.16g}".format(signal.max)))
    if len(signal.unit) > 0:
        value.set('unit',signal.unit)

    if len(value.attrib) > 0:
        sig.append(value)

    if len(signal.values) > 0:
        labelset = etree.Element('LabelSet')
        for valueVal,valName in sorted(signal.values.items(), key=lambda x: int(x[0])):
            label = etree.Element('Label', name=valName.replace('"',''), value=str(valueVal))
            labelset.append(label)
        sig.append(labelset)

    consumer = etree.Element('Consumer')
    for receiver in signal.receiver:
        if len(receiver) > 1 and receiver in nodeList:
            noderef = etree.Element('NodeRef', id=str(nodeList[receiver]))
            consumer.append(noderef)
        if consumer.__len__() > 0:
            sig.append(consumer)
    return sig


def exportKcd(db, filename):

    signalTypeEnums = {}
    for (typename,define) in list(db.signalDefines.items()):
        defines = re.split(r"\s+", define.definition)
        define_type = defines[0]
        if define_type != 'ENUM':
            continue
        defines = defines[1].strip('"')
        defines = defines.split('","')
        signalTypeEnums[typename] = defines

    # create XML
    root = etree.Element('NetworkDefinition')
    root.set("xmlns","http://kayak.2codeornot2code.org/1.0")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "schemaLocation", "Definition.xsd")


    #root.append(etree.Element('Document'))
    # another child with text

    child = etree.Element('Document')
    child.set("name","Some Document Name")
    child.text = 'some text'
    root.append(child)


    # Nodes:
    id = 1
    nodeList = {};
    for bu in db.boardUnits:
        node = etree.Element('Node', name=bu.name, id="%d" %id)
        root.append(node)
        nodeList[bu.name] = id;
        id += 1
    # Bus
    if 'Baudrate' in db.attributes:
        bus = etree.Element('Bus', baudrate=db.attributes['Baudrate'])
    else:
        bus = etree.Element('Bus')

    bus.set("name",os.path.splitext(filename)[0])

    for frame in db.frames:
        message = etree.Element('Message', id="0x%03X" % frame.id, name=frame.name, length = str(int(frame.size)))

        if frame.extended == 1:
            message.set("format", "extended")
        if "GenMsgCycleTime" in frame.attributes:
            cycleTime = int(frame.attributes["GenMsgCycleTime"])
            if cycleTime > 0:
                message.set("triggered", "true")
                message.set("interval", "%d" % cycleTime)

        producer = etree.Element('Producer')

        for transmitter in frame.transmitter:
            if len(transmitter) > 1 and transmitter in nodeList:
                noderef = etree.Element('NodeRef', id=str(nodeList[transmitter]))
                producer.append(noderef)
        if producer.__len__() > 0:
            message.append(producer)

        comment = etree.Element('Notes')
        if frame.comment is not None:
            comment.text = frame.comment
            message.append(comment)


        # standard-signals:
        for signal in frame.signals:
            if signal.multiplex is None:
                sig = createSignal(signal, nodeList, signalTypeEnums)
                message.append(sig)

        # check Multiplexor if present:
        multiplexor = None
        for signal in frame.signals:
            if signal.multiplex is not None and signal.multiplex == 'Multiplexor':
                multiplexor = etree.Element('Multiplex', name=signal.name, offset=str(signal.getStartbit()), length=str(int(signal.signalsize)))
                value = etree.Element('Value')
                if float(signal.min) != 0:
                    value.set('min', "%g" % signal.min)
                if float(signal.max) != 1:
                    value.set('max', "%g" % signal.max)
                multiplexor.append(value)
                labelset = etree.Element('LabelSet')
                for valueVal,valName in sorted(signal.values.items(), key=lambda x: int(x[0])):
                    label = etree.Element('Label', name=valName.replace('"',''), value=str(valueVal))
                    labelset.append(label)
                multiplexor.append(labelset)



        # multiplexor found
        if multiplexor is not None:
            # ticker all potential muxgroups
            for i in range(0,1<<int(multiplexor.get('length'))):
                empty = 0
                muxgroup = etree.Element('MuxGroup', count=str(i))
                for signal in frame.signals:
                    if signal.multiplex is not None and signal.multiplex == i:
                        sig = createSignal(signal, nodeList, signalTypeEnums)
                        muxgroup.append(sig)
                        empty = 1
                if empty == 1:
                    multiplexor.append(muxgroup)
            message.append(multiplexor)

        bus.append(message)

    root.append(bus)
    f = open(filename,"wb");
    f.write(etree.tostring(root, pretty_print=True))
